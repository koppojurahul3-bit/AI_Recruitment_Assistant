
from unittest.mock import Mock

from backend.models.candidate import Candidate
from backend.repositories.candidate_repository import CandidateRepository
from backend.repositories.sqlite_candidate_repository import (
    SQLiteCandidateRepository,
)
from backend.services.candidate_intake_service import CandidateIntakeService


def test_default_service_uses_memory_repository_and_real_ingestion():
    service = CandidateIntakeService()

    try:
        assert isinstance(service.repository, CandidateRepository)
        assert (
            service.ingestion_service.candidate_repository
            is service.repository
        )
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
    expected_candidate = Candidate(
        candidate_id="candidate-001",
        name="Test Candidate",
    )
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

    first = CandidateIntakeService(
        storage_backend="sqlite",
        database_path=database_path,
    )

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

    second = CandidateIntakeService(
        storage_backend="sqlite",
        database_path=database_path,
    )

    try:
        restored = second.repository.get_by_id("persistent-001")

        assert restored is not None
        assert restored.name == "Persistent Candidate"
        assert restored.skills == ["Python", "NLP"]
    finally:
        second.close()
