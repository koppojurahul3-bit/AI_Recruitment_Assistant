
import pytest

from backend.agents.approval import HumanApprovalAgent
from backend.models.state import RecruitmentState


def create_state() -> RecruitmentState:
    return {
        "recruiter_goal": "Hire a Python developer.",
        "job_description": "Python developer with relevant experience.",
        "job_requirements": ["Python"],
        "candidate_ids": ["C001"],
        "candidates": [],
        "evaluations": [],
        "rankings": [],
        "requested_actions": [],
        "approved_actions": [],
        "completed_actions": [],
        "requires_approval": False,
        "approval_reason": None,
        "final_response": None,
        "current_step": "candidate_ranking",
        "errors": [],
    }


def request_interview(agent, state):
    return agent.request_approval(
        state=state,
        action_type="send_interview_invitation",
        candidate_id="C001",
        details={"role": "Python Developer"},
    )


def test_request_action_starts_pending():
    agent = HumanApprovalAgent()
    state = request_interview(agent, create_state())

    action = state["requested_actions"][0]

    assert action["status"] == "pending"
    assert action["requires_approval"] is True
    assert state["requires_approval"] is True
    assert state["current_step"] == "human_approval"
    assert state["approved_actions"] == []


def test_pending_actions_returns_only_pending_items():
    agent = HumanApprovalAgent()
    state = request_interview(agent, create_state())

    pending = agent.get_pending_actions(state)

    assert len(pending) == 1
    assert pending[0]["candidate_id"] == "C001"


def test_approval_records_reviewer_and_action():
    agent = HumanApprovalAgent()
    state = request_interview(agent, create_state())
    action_id = state["requested_actions"][0]["action_id"]

    state = agent.approve_action(
        state,
        action_id=action_id,
        approved_by="Recruiter",
        reason="Reviewed the candidate profile.",
    )

    assert state["requested_actions"][0]["status"] == "approved"
    assert state["approved_actions"][0]["action_id"] == action_id
    assert state["approved_actions"][0]["approved_by"] == "Recruiter"
    assert state["requires_approval"] is False
    assert state["current_step"] == "approval_reviewed"
    assert state["completed_actions"] == []


def test_denial_records_reason_without_approval():
    agent = HumanApprovalAgent()
    state = request_interview(agent, create_state())
    action_id = state["requested_actions"][0]["action_id"]

    state = agent.deny_action(
        state,
        action_id=action_id,
        denied_by="Recruiter",
        reason="Candidate needs further review.",
    )

    assert state["requested_actions"][0]["status"] == "denied"
    assert state["approved_actions"] == []
    assert state["requested_actions"][0]["decision_reason"] == (
        "Candidate needs further review."
    )
    assert state["requires_approval"] is False


def test_multiple_actions_keep_approval_pending_until_all_reviewed():
    agent = HumanApprovalAgent()
    state = request_interview(agent, create_state())

    state = agent.request_approval(
        state,
        action_type="shortlist_candidate",
        candidate_id="C001",
    )

    first_id = state["requested_actions"][0]["action_id"]
    second_id = state["requested_actions"][1]["action_id"]

    state = agent.approve_action(
        state,
        action_id=first_id,
        approved_by="Recruiter",
    )

    assert state["requires_approval"] is True
    assert len(agent.get_pending_actions(state)) == 1

    state = agent.deny_action(
        state,
        action_id=second_id,
        denied_by="Recruiter",
        reason="Shortlisting criteria not met.",
    )

    assert state["requires_approval"] is False
    assert agent.get_pending_actions(state) == []


def test_unsupported_action_is_rejected():
    agent = HumanApprovalAgent()

    with pytest.raises(ValueError, match="Unsupported action type"):
        agent.request_approval(
            create_state(),
            action_type="delete_database",
            candidate_id="C001",
        )


def test_missing_candidate_id_is_rejected():
    agent = HumanApprovalAgent()

    with pytest.raises(ValueError, match="candidate ID"):
        agent.request_approval(
            create_state(),
            action_type="reject_candidate",
            candidate_id=" ",
        )


def test_approval_requires_reviewer_identity():
    agent = HumanApprovalAgent()
    state = request_interview(agent, create_state())
    action_id = state["requested_actions"][0]["action_id"]

    with pytest.raises(ValueError, match="approver identity"):
        agent.approve_action(
            state,
            action_id=action_id,
            approved_by=" ",
        )


def test_denial_requires_reason():
    agent = HumanApprovalAgent()
    state = request_interview(agent, create_state())
    action_id = state["requested_actions"][0]["action_id"]

    with pytest.raises(ValueError, match="reason is required"):
        agent.deny_action(
            state,
            action_id=action_id,
            denied_by="Recruiter",
            reason=" ",
        )


def test_action_cannot_be_approved_twice():
    agent = HumanApprovalAgent()
    state = request_interview(agent, create_state())
    action_id = state["requested_actions"][0]["action_id"]

    agent.approve_action(
        state,
        action_id=action_id,
        approved_by="Recruiter",
    )

    with pytest.raises(ValueError, match="already been reviewed"):
        agent.approve_action(
            state,
            action_id=action_id,
            approved_by="Recruiter",
        )


def test_unknown_action_id_is_rejected():
    agent = HumanApprovalAgent()

    with pytest.raises(ValueError, match="Pending action was not found"):
        agent.approve_action(
            create_state(),
            action_id="unknown-id",
            approved_by="Recruiter",
        )
