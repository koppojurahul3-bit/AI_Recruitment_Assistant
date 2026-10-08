from backend.agents.orchestrator import RecruitmentOrchestrator
from backend.models.candidate import Candidate
from backend.repositories.candidate_repository import CandidateRepository


def create_repository():
    repository = CandidateRepository()

    repository.add(
        Candidate(
            candidate_id="C001",
            name="Rahul",
            email="rahul@example.com",
            skills=[
                "Python",
                "Machine Learning",
                "SQL",
            ],
            experience_years=3.0,
            education=["B.Tech"],
            projects=["ML Prediction System"],
        )
    )

    repository.add(
        Candidate(
            candidate_id="C002",
            name="Arjun",
            email="arjun@example.com",
            skills=[
                "Python",
                "NLP",
            ],
            experience_years=2.0,
            education=["B.Tech"],
            projects=["NLP Application"],
        )
    )

    repository.add(
        Candidate(
            candidate_id="C003",
            name="Kiran",
            email="kiran@example.com",
            skills=[
                "Java",
                "SQL",
            ],
            experience_years=5.0,
            education=["M.Tech"],
            projects=["Backend Platform"],
        )
    )

    return repository


def test_initialize_creates_recruitment_state():
    repository = create_repository()

    orchestrator = RecruitmentOrchestrator(
        candidate_repository=repository
    )

    state = orchestrator.initialize(
        recruiter_goal="Find strong Python ML candidates.",
        job_description=(
            "Looking for a Machine Learning Engineer with "
            "Python, Machine Learning and SQL skills."
        ),
    )

    assert state["recruiter_goal"] == (
        "Find strong Python ML candidates."
    )

    assert "Machine Learning Engineer" in state["job_description"]

    assert state["current_step"] == "initialized"


def test_run_retrieves_and_evaluates_candidates():
    repository = create_repository()

    orchestrator = RecruitmentOrchestrator(
        candidate_repository=repository
    )

    state = orchestrator.initialize(
        recruiter_goal="Find Python ML candidates.",
        job_description=(
            "Machine Learning Engineer with "
            "Python, Machine Learning and SQL."
        ),
    )

    state = orchestrator.run(
        state,
        skills=["Python"],
    )

    assert state["current_step"] == "completed"

    assert state["candidate_ids"] == [
        "C001",
        "C002",
    ]

    assert len(state["candidates"]) == 2

    assert len(state["evaluations"]) == 2

    assert len(state["rankings"]) == 2


def test_run_combines_skill_and_experience_filters():
    repository = create_repository()

    orchestrator = RecruitmentOrchestrator(
        candidate_repository=repository
    )

    state = orchestrator.initialize(
        recruiter_goal="Find experienced Python candidates.",
        job_description=(
            "Machine Learning Engineer with "
            "Python and Machine Learning."
        ),
    )

    state = orchestrator.run(
        state,
        skills=["Python"],
        minimum_experience_years=3,
    )

    assert state["current_step"] == "completed"

    assert state["candidate_ids"] == [
        "C001",
    ]

    assert len(state["evaluations"]) == 1

    assert len(state["rankings"]) == 1


def test_run_without_matching_candidates_fails_cleanly():
    repository = create_repository()

    orchestrator = RecruitmentOrchestrator(
        candidate_repository=repository
    )

    state = orchestrator.initialize(
        recruiter_goal="Find Kubernetes candidates.",
        job_description=(
            "DevOps Engineer with Kubernetes experience."
        ),
    )

    state = orchestrator.run(
        state,
        skills=["Kubernetes"],
    )

    assert state["current_step"] == "candidate_search_failed"

    assert len(state["errors"]) == 1

    assert "No candidates matched" in state["errors"][0]


def test_initialize_rejects_empty_recruiter_goal():
    repository = create_repository()

    orchestrator = RecruitmentOrchestrator(
        candidate_repository=repository
    )

    try:
        orchestrator.initialize(
            recruiter_goal="",
            job_description="Python developer.",
        )
        assert False
    except ValueError as exc:
        assert "Recruiter goal cannot be empty" in str(exc)


def test_initialize_rejects_empty_job_description():
    repository = create_repository()

    orchestrator = RecruitmentOrchestrator(
        candidate_repository=repository
    )

    try:
        orchestrator.initialize(
            recruiter_goal="Find Python developers.",
            job_description="",
        )
        assert False
    except ValueError as exc:
        assert "Job description cannot be empty" in str(exc)