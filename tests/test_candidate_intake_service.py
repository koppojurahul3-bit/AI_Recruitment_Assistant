from unittest.mock import Mock

import pytest

from backend.agents.orchestrator import RecruitmentOrchestrator
from backend.models.candidate import Candidate
from backend.repositories.candidate_repository import CandidateRepository
from backend.repositories.sqlite_candidate_repository import SQLiteCandidateRepository
from backend.services.candidate_intake_service import CandidateIntakeService


def test_default_service_uses_memory_repository_and_real_ingestion():
    service = CandidateIntakeService()
    try:
        assert isinstance(service.repository, CandidateRepository)
        assert service.ingestion_service.candidate_repository is service.repository
    finally:
        service.close()


def test_sqlite_storage_uses_configured_database(tmp_path):
    database_path = tmp_path / "candidates.sqlite3"
    ingestion = Mock()
    service = CandidateIntakeService(
        storage_backend="sqlite",
        database_path=database_path,
        ingestion_service=ingestion,
    )
    try:
        assert isinstance(service.repository, SQLiteCandidateRepository)
        assert service.repository is not None
    finally:
        service.close()


def test_ingest_pdf_delegates_with_correct_arguments():
    ingestion = Mock()
    expected_candidate = Candidate(candidate_id="candidate-001", name="Test Candidate")
    ingestion.ingest_pdf.return_value = expected_candidate
    service = CandidateIntakeService(ingestion_service=ingestion)
    try:
        result = service.ingest_pdf(
            filename="resume.pdf",
            file_bytes=b"%PDF-test",
            candidate_id="candidate-001",
        )
        assert result is expected_candidate
        ingestion.ingest_pdf.assert_called_once_with(
            filename="resume.pdf",
            file_bytes=b"%PDF-test",
            candidate_id="candidate-001",
        )
    finally:
        service.close()


def test_sqlite_candidate_persists_after_reopening(tmp_path):
    database_path = tmp_path / "candidates.sqlite3"
    first = CandidateIntakeService(storage_backend="sqlite", database_path=database_path)
    candidate = Candidate(
        candidate_id="persistent-001",
        name="Persistent Candidate",
        email="candidate@example.com",
        skills=["Python", "NLP"],
    )
    try:
        first.repository.add(candidate)
    finally:
        first.close()

    second = CandidateIntakeService(storage_backend="sqlite", database_path=database_path)
    try:
        restored = second.repository.get_by_id("persistent-001")
        assert restored is not None
        assert restored.name == "Persistent Candidate"
        assert restored.skills == ["Python", "NLP"]
    finally:
        second.close()


def test_intake_and_orchestrator_share_the_same_repository(tmp_path):
    service = CandidateIntakeService(
        storage_backend="sqlite",
        database_path=tmp_path / "shared.sqlite3",
    )
    try:
        orchestrator = RecruitmentOrchestrator(candidate_repository=service.repository)
        assert orchestrator.candidate_repository is service.repository
        assert orchestrator.retrieval_agent.candidate_repository is service.repository
        assert orchestrator.evaluation_agent.candidate_repository is service.repository
    finally:
        service.close()


def test_injected_ingestion_repository_mismatch_is_rejected():
    ingestion = Mock()
    ingestion.candidate_repository = CandidateRepository()
    other_repository = CandidateRepository()
    with pytest.raises(ValueError, match="same candidate repository"):
        CandidateIntakeService(
            candidate_repository=other_repository,
            ingestion_service=ingestion,
        )

def test_ingested_candidate_flows_through_retrieval_and_evaluation(tmp_path):
    from backend.agents.orchestrator import RecruitmentOrchestrator

    candidate = Candidate(
        candidate_id="integration-candidate-001",
        name="Integration Test Candidate",
        email="integration@example.com",
        skills=["Python", "Machine Learning", "SQL"],
        experience_years=2.0,
        education=["Bachelor of Technology"],
        projects=["Machine learning classification project"],
        resume_text=(
            "Python Machine Learning SQL. "
            "Two years of experience building machine learning projects."
        ),
    )

    class TestIngestionService:
        def __init__(self, candidate_repository):
            self.candidate_repository = candidate_repository

        def ingest_pdf(self, filename, file_bytes, candidate_id=None):
            self.candidate_repository.add(candidate)
            return candidate

    intake = CandidateIntakeService(
        storage_backend="sqlite",
        database_path=tmp_path / "recruitment-integration.sqlite3",
    )

    intake.ingestion_service = TestIngestionService(intake.repository)

    try:
        ingested = intake.ingest_pdf(
            filename="integration-resume.pdf",
            file_bytes=b"test-pdf-bytes",
            candidate_id=candidate.candidate_id,
        )

        assert ingested.candidate_id == candidate.candidate_id
        assert intake.repository.get_by_id(candidate.candidate_id) is not None

        orchestrator = RecruitmentOrchestrator(
            candidate_repository=intake.repository
        )

        assert orchestrator.retrieval_agent.candidate_repository is intake.repository
        assert orchestrator.evaluation_agent.candidate_repository is intake.repository

        state = orchestrator.initialize(
            recruiter_goal="Find a Python machine learning engineer",
            job_description=(
                "Python and Machine Learning engineer. "
                "SQL experience preferred."
            ),
        )

        result = orchestrator.run(
            state,
            skills=["Python"],
            minimum_experience_years=1.0,
        )

        assert candidate.candidate_id in result.get("candidate_ids", [])
        assert result.get("current_step") not in {
            "candidate_search_failed",
            "candidate_evaluation_failed",
            "orchestration_failed",
        }
        assert not result.get("errors")
        assert result.get("evaluations")
    finally:
        intake.close()
