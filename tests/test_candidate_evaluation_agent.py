from backend.agents.evaluation import CandidateEvaluationAgent
from backend.models.candidate import Candidate
from backend.models.state import RecruitmentState
from backend.repositories.candidate_repository import CandidateRepository


def create_state(job_description: str) -> RecruitmentState:
    return {
        "recruiter_goal": "Find the strongest ML Engineer candidates.",
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


def create_repository() -> CandidateRepository:
    repository = CandidateRepository()

    repository.add(
        Candidate(
            candidate_id="C001",
            name="Alice",
            email="alice@example.com",
            skills=[
                "Python",
                "Machine Learning",
                "SQL",
                "TensorFlow",
            ],
            experience_years=4,
            education=["B.Tech Computer Science"],
        )
    )

    repository.add(
        Candidate(
            candidate_id="C002",
            name="Bob",
            email="bob@example.com",
            skills=[
                "Python",
                "SQL",
            ],
            experience_years=1,
            education=["B.Tech Computer Science"],
        )
    )

    repository.add(
        Candidate(
            candidate_id="C003",
            name="Charlie",
            email="charlie@example.com",
            skills=[
                "Python",
                "Machine Learning",
                "SQL",
            ],
            experience_years=3,
            education=["B.Tech Computer Science"],
        )
    )

    return repository


def test_evaluation_agent_evaluates_all_candidates():
    repository = create_repository()

    agent = CandidateEvaluationAgent(
        candidate_repository=repository
    )

    state = create_state(
        """
        We are hiring an ML Engineer.
        Required skills: Python, Machine Learning, SQL.
        Minimum experience: 2 years.
        Education: B.Tech.
        """
    )

    result = agent.evaluate(state)

    assert len(result["candidates"]) == 3
    assert len(result["evaluations"]) == 3
    assert len(result["rankings"]) == 3
    assert result["current_step"] == "candidate_ranking"
    assert result["errors"] == []


def test_evaluation_agent_extracts_job_requirements():
    repository = create_repository()

    agent = CandidateEvaluationAgent(
        candidate_repository=repository
    )

    state = create_state(
        """
        ML Engineer role.
        Required skills: Python, Machine Learning, SQL.
        Minimum experience: 2 years.
        """
    )

    result = agent.evaluate(state)

    assert "Python" in result["job_requirements"]
    assert "Machine Learning" in result["job_requirements"]
    assert "SQL" in result["job_requirements"]


def test_evaluation_agent_produces_candidate_evaluations():
    repository = create_repository()

    agent = CandidateEvaluationAgent(
        candidate_repository=repository
    )

    state = create_state(
        """
        ML Engineer.
        Required skills: Python, Machine Learning, SQL.
        Minimum experience: 2 years.
        """
    )

    result = agent.evaluate(state)

    first_evaluation = result["evaluations"][0]

    assert "candidate_id" in first_evaluation
    assert "skill_match_score" in first_evaluation
    assert "experience_match_score" in first_evaluation
    assert "overall_score" in first_evaluation
    assert "recommendation" in first_evaluation


def test_evaluation_agent_ranks_candidates():
    repository = create_repository()

    agent = CandidateEvaluationAgent(
        candidate_repository=repository
    )

    state = create_state(
        """
        ML Engineer.
        Required skills: Python, Machine Learning, SQL.
        Minimum experience: 2 years.
        """
    )

    result = agent.evaluate(state)

    assert result["rankings"][0]["rank"] == 1
    assert result["rankings"][1]["rank"] == 2
    assert result["rankings"][2]["rank"] == 3

    assert (
        result["rankings"][0]["overall_score"]
        >= result["rankings"][1]["overall_score"]
    )


def test_evaluation_agent_can_evaluate_selected_candidates():
    repository = create_repository()

    agent = CandidateEvaluationAgent(
        candidate_repository=repository
    )

    state = create_state(
        """
        ML Engineer.
        Required skills: Python, Machine Learning.
        Minimum experience: 2 years.
        """
    )

    result = agent.evaluate_candidate_ids(
        state,
        ["C001", "C003"]
    )

    assert len(result["candidates"]) == 2
    assert len(result["evaluations"]) == 2
    assert len(result["rankings"]) == 2


def test_evaluation_agent_handles_missing_job_description():
    repository = create_repository()

    agent = CandidateEvaluationAgent(
        candidate_repository=repository
    )

    state = create_state("")

    result = agent.evaluate(state)

    assert result["current_step"] == "candidate_evaluation_failed"
    assert len(result["errors"]) == 1


def test_evaluation_agent_handles_no_candidates():
    repository = CandidateRepository()

    agent = CandidateEvaluationAgent(
        candidate_repository=repository
    )

    state = create_state(
        """
        ML Engineer.
        Required skills: Python, Machine Learning.
        """
    )

    result = agent.evaluate(state)

    assert result["current_step"] == "candidate_evaluation_failed"
    assert len(result["errors"]) == 1


def test_evaluation_agent_uses_selected_candidate_ids():
    repository = create_repository()

    agent = CandidateEvaluationAgent(
        candidate_repository=repository
    )

    state = create_state(
        """
        ML Engineer.
        Required skills: Python, Machine Learning.
        Minimum experience: 2 years.
        """
    )

    result = agent.evaluate_candidate_ids(
        state,
        ["C002"]
    )

    assert result["candidate_ids"] == ["C002"]
    assert len(result["candidates"]) == 1
    assert result["candidates"][0]["candidate_id"] == "C002"