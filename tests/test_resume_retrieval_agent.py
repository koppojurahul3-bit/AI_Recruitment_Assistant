from backend.agents.retrieval import ResumeRetrievalAgent
from backend.models.state import RecruitmentState
from backend.models.candidate import Candidate
from backend.repositories.candidate_repository import CandidateRepository


def create_repository():
    repository = CandidateRepository()

    repository.add(
        Candidate(
            candidate_id="C001",
            name="Rahul",
            skills=["Python", "Machine Learning"],
            experience_years=3.0,
            education=["B.Tech"],
        )
    )

    repository.add(
        Candidate(
            candidate_id="C002",
            name="Arjun",
            skills=["Python", "NLP"],
            experience_years=2.0,
            education=["B.Tech"],
        )
    )

    repository.add(
        Candidate(
            candidate_id="C003",
            name="Kiran",
            skills=["Java"],
            experience_years=5.0,
            education=["M.Tech"],
        )
    )

    return repository


def create_state() -> RecruitmentState:
    return {
        "recruiter_goal": "Find strong Python candidates.",
        "job_description": "",
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


def test_search_by_skill():
    repository = create_repository()

    agent = ResumeRetrievalAgent(repository)

    result = agent.search_by_skill("Python")

    assert result == ["C001", "C002"]


def test_search_by_multiple_skills():
    repository = create_repository()

    agent = ResumeRetrievalAgent(repository)

    result = agent.search_by_skills(
        ["Python", "Java"]
    )

    assert result == ["C001", "C002", "C003"]


def test_search_by_experience():
    repository = create_repository()

    agent = ResumeRetrievalAgent(repository)

    result = agent.search_by_experience(3)

    assert result == ["C001", "C003"]


def test_retrieve_by_skill():
    repository = create_repository()

    agent = ResumeRetrievalAgent(repository)

    state = create_state()

    state = agent.retrieve(
        state,
        skills=["Python"],
    )

    assert state["candidate_ids"] == ["C001", "C002"]
    assert state["current_step"] == "candidate_search_completed"
    assert len(state["candidates"]) == 2


def test_retrieve_by_skill_and_experience():
    repository = create_repository()

    agent = ResumeRetrievalAgent(repository)

    state = create_state()

    state = agent.retrieve(
        state,
        skills=["Python"],
        minimum_experience_years=3,
    )

    assert state["candidate_ids"] == ["C001"]
    assert len(state["candidates"]) == 1


def test_retrieve_without_filters_returns_all_candidates():
    repository = create_repository()

    agent = ResumeRetrievalAgent(repository)

    state = create_state()

    state = agent.retrieve(state)

    assert state["candidate_ids"] == [
        "C001",
        "C002",
        "C003",
    ]

    assert len(state["candidates"]) == 3


def test_empty_skill_list_returns_all_candidates():
    repository = create_repository()

    agent = ResumeRetrievalAgent(repository)

    state = create_state()

    state = agent.retrieve(
        state,
        skills=[],
    )

    assert state["candidate_ids"] == [
        "C001",
        "C002",
        "C003",
    ]


def test_retrieve_for_state():
    repository = create_repository()

    agent = ResumeRetrievalAgent(repository)

    state = create_state()

    state = agent.retrieve_for_state(
        state,
        skills=["Java"],
        minimum_experience_years=5,
    )

    assert state["candidate_ids"] == ["C003"]


def test_invalid_experience_is_recorded_as_error():
    repository = create_repository()

    agent = ResumeRetrievalAgent(repository)

    state = create_state()

    state = agent.retrieve(
        state,
        skills=["Python"],
        minimum_experience_years=-1,
    )

    assert state["current_step"] == "candidate_search_failed"
    assert len(state["errors"]) == 1


def test_invalid_skill_input_is_recorded_as_error():
    repository = create_repository()

    agent = ResumeRetrievalAgent(repository)

    state = create_state()

    state = agent.retrieve(
        state,
        skills="Python",
    )

    assert state["current_step"] == "candidate_search_failed"
    assert len(state["errors"]) == 1