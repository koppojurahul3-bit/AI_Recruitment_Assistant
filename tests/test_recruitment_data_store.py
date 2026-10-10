
from backend.agents.orchestrator import RecruitmentOrchestrator
from backend.models.candidate import Candidate
from backend.models.state import RecruitmentState
from backend.services.recruitment_data_store import RecruitmentDataStore


def make_state(job_description: str) -> RecruitmentState:
    return {
        "recruiter_goal": "Find suitable ML Engineer candidates.",
        "job_description": job_description,
        "job_requirements": [],
        "candidate_ids": [],
        "candidates": [],
        "evaluations": [],
        "rankings": [],
        "requested_actions": [],
        "approved_actions": [],
        "completed_actions": [],
        "requires_approval": False,
        "approval_reason": None,
        "final_response": None,
        "current_step": "initialized",
        "errors": [],
    }


def test_all_services_share_the_same_repository():
    with RecruitmentDataStore(storage_backend="memory") as store:
        assert store.intake_service.repository is store.repository
        assert store.orchestrator.candidate_repository is store.repository
        assert (
            store.orchestrator.retrieval_agent.candidate_repository
            is store.repository
        )
        assert (
            store.orchestrator.evaluation_agent.candidate_repository
            is store.repository
        )


def test_evaluation_can_read_a_candidate_from_shared_repository():
    with RecruitmentDataStore(storage_backend="memory") as store:
        store.repository.add(
            Candidate(
                candidate_id="module2-candidate-001",
                name="Test ML Candidate",
                email="candidate@example.com",
                skills=["Python", "Machine Learning", "SQL"],
                experience_years=3,
                education=["B.Tech Computer Science"],
            )
        )

        state = make_state(
            """
            ML Engineer.
            Required skills: Python, Machine Learning, SQL.
            Minimum experience: 2 years.
            Education: Computer Science.
            """
        )

        result = store.orchestrator.evaluation_agent.evaluate_candidate_ids(
            state,
            ["module2-candidate-001"],
        )

        assert result["current_step"] == "candidate_ranking"
        assert result["errors"] == []
        assert len(result["candidates"]) == 1
        assert len(result["evaluations"]) == 1
        assert len(result["rankings"]) == 1
        assert (
            result["evaluations"][0]["candidate_id"]
            == "module2-candidate-001"
        )


def test_sqlite_candidates_persist_between_data_store_instances(tmp_path):
    database_path = tmp_path / "recruitment.sqlite3"

    with RecruitmentDataStore(
        storage_backend="sqlite",
        database_path=database_path,
    ) as store:
        store.repository.add(
            Candidate(
                candidate_id="persistent-module2",
                name="Persistent Candidate",
                skills=["Python"],
            )
        )

    with RecruitmentDataStore(
        storage_backend="sqlite",
        database_path=database_path,
    ) as reopened:
        candidate = reopened.repository.get_by_id(
            "persistent-module2"
        )

        assert candidate is not None
        assert candidate.name == "Persistent Candidate"
        assert candidate.skills == ["Python"]


def test_orchestrator_repository_injection_remains_supported():
    with RecruitmentDataStore(storage_backend="memory") as store:
        orchestrator = RecruitmentOrchestrator(
            candidate_repository=store.repository
        )

        assert orchestrator.candidate_repository is store.repository
        assert (
            orchestrator.retrieval_agent.candidate_repository
            is store.repository
        )
        assert (
            orchestrator.evaluation_agent.candidate_repository
            is store.repository
        )
