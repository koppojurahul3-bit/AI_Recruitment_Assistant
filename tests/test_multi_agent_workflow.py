
from unittest.mock import Mock

import pytest

from backend.agents.orchestrator import RecruitmentOrchestrator
from backend.models.candidate import Candidate
from backend.repositories.candidate_repository import CandidateRepository


def populated_repository():
    repository = CandidateRepository()

    repository.add(
        Candidate(
            candidate_id="M3-001",
            name="Test Candidate",
            email="test@example.com",
            skills=["Python", "Machine Learning", "SQL"],
            experience_years=3,
            education=["B.Tech"],
            projects=["ML project"],
        )
    )

    return repository


def test_trace_records_successful_agent_handoffs():
    orchestrator = RecruitmentOrchestrator(
        candidate_repository=populated_repository()
    )

    state = orchestrator.initialize(
        "Find ML candidates",
        "Machine Learning Engineer with Python and SQL",
    )

    result = orchestrator.run(state, skills=["Python"])

    assert result["current_step"] == "completed"

    assert [
        (event["agent"], event["status"])
        for event in result["agent_trace"]
    ] == [
        ("coordinator", "started"),
        ("coordinator", "completed"),
        ("retrieval", "started"),
        ("retrieval", "completed"),
        ("evaluation", "started"),
        ("evaluation", "completed"),
    ]


def test_trace_records_retrieval_failure():
    orchestrator = RecruitmentOrchestrator(
        candidate_repository=CandidateRepository()
    )

    state = orchestrator.initialize(
        "Find candidates",
        "Python engineer",
    )

    result = orchestrator.run(state, skills=["Python"])

    assert result["current_step"] == "candidate_search_failed"
    assert result["agent_trace"][-1]["agent"] == "retrieval"
    assert result["agent_trace"][-1]["status"] == "failed"


def test_agent_repository_mismatch_is_rejected():
    repository = CandidateRepository()
    retrieval = Mock()
    retrieval.candidate_repository = CandidateRepository()

    with pytest.raises(ValueError, match="retrieval agent must use"):
        RecruitmentOrchestrator(
            candidate_repository=repository,
            retrieval_agent=retrieval,
        )


def test_evaluation_failure_is_not_marked_completed():
    repository = populated_repository()
    evaluation = Mock()
    evaluation.candidate_repository = repository
    evaluation.evaluate.side_effect = lambda state: {
        **state,
        "current_step": "candidate_evaluation_failed",
        "errors": ["evaluation failed"],
    }

    orchestrator = RecruitmentOrchestrator(
        candidate_repository=repository,
        evaluation_agent=evaluation,
    )

    state = orchestrator.initialize(
        "Find candidates",
        "Python engineer",
    )

    result = orchestrator.run(state, skills=["Python"])

    assert result["current_step"] == "candidate_evaluation_failed"
    assert result["agent_trace"][-1]["agent"] == "evaluation"
    assert result["agent_trace"][-1]["status"] == "failed"


def test_unexpected_coordinator_exception_is_recorded():
    coordinator = Mock()
    coordinator.initialize_state.return_value = {
        "recruiter_goal": "Find candidates",
        "job_description": "Python engineer",
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
    coordinator.run.side_effect = RuntimeError("coordinator exploded")

    orchestrator = RecruitmentOrchestrator(coordinator=coordinator)

    state = orchestrator.initialize(
        "Find candidates",
        "Python engineer",
    )

    result = orchestrator.run(state)

    assert result["current_step"] == "orchestration_failed"
    assert "RuntimeError: coordinator exploded" in result["errors"]
    assert result["agent_trace"][-1]["agent"] == "orchestrator"
    assert result["agent_trace"][-1]["status"] == "failed"
