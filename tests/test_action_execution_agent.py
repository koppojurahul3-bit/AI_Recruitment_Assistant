
import pytest

from backend.agents.approval import HumanApprovalAgent
from backend.agents.execution import ActionExecutionAgent
from backend.models.state import RecruitmentState


def create_state() -> RecruitmentState:
    return {
        "recruiter_goal": "Hire a Python developer.",
        "job_description": "Python developer.",
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
        "current_step": "human_approval",
        "errors": [],
    }


def create_approved_action():
    state = create_state()
    approval_agent = HumanApprovalAgent()

    state = approval_agent.request_approval(
        state,
        action_type="send_interview_invitation",
        candidate_id="C001",
        details={"role": "Python Developer"},
    )

    action_id = state["requested_actions"][0]["action_id"]

    state = approval_agent.approve_action(
        state,
        action_id=action_id,
        approved_by="Recruiter",
        reason="Reviewed and approved.",
    )

    return state, action_id


def test_approved_action_executes_in_simulation():
    state, action_id = create_approved_action()
    agent = ActionExecutionAgent()

    state = agent.execute_action(state, action_id)

    assert state["current_step"] == "action_execution_completed"
    assert len(state["completed_actions"]) == 1

    completed = state["completed_actions"][0]
    assert completed["action_id"] == action_id
    assert completed["status"] == "completed"
    assert completed["execution_mode"] == "simulated"
    assert completed["external_operation_performed"] is False


def test_pending_action_is_blocked():
    state = create_state()
    approval_agent = HumanApprovalAgent()
    agent = ActionExecutionAgent()

    state = approval_agent.request_approval(
        state,
        action_type="send_candidate_email",
        candidate_id="C001",
    )

    action_id = state["requested_actions"][0]["action_id"]
    state = agent.execute_action(state, action_id)

    assert state["current_step"] == "action_execution_blocked"
    assert state["completed_actions"] == []
    assert "not approved" in state["errors"][-1]


def test_denied_action_is_blocked():
    state = create_state()
    approval_agent = HumanApprovalAgent()
    agent = ActionExecutionAgent()

    state = approval_agent.request_approval(
        state,
        action_type="reject_candidate",
        candidate_id="C001",
    )

    action_id = state["requested_actions"][0]["action_id"]

    state = approval_agent.deny_action(
        state,
        action_id=action_id,
        denied_by="Recruiter",
        reason="Needs further review.",
    )

    state = agent.execute_action(state, action_id)

    assert state["current_step"] == "action_execution_blocked"
    assert state["completed_actions"] == []


def test_missing_approval_record_is_blocked():
    state, action_id = create_approved_action()
    state["approved_actions"] = []
    agent = ActionExecutionAgent()

    state = agent.execute_action(state, action_id)

    assert state["current_step"] == "action_execution_blocked"
    assert state["completed_actions"] == []
    assert "no valid approval record" in state["errors"][-1]


def test_unknown_action_id_is_blocked():
    agent = ActionExecutionAgent()
    state = create_state()

    state = agent.execute_action(state, "unknown-action")

    assert state["current_step"] == "action_execution_blocked"
    assert "Action was not found" in state["errors"][-1]


def test_completed_action_cannot_execute_twice():
    state, action_id = create_approved_action()
    agent = ActionExecutionAgent()

    state = agent.execute_action(state, action_id)
    state = agent.execute_action(state, action_id)

    assert state["current_step"] == "action_execution_blocked"
    assert len(state["completed_actions"]) == 1
    assert "already been completed" in state["errors"][-1]


def test_unsupported_action_is_blocked():
    state, action_id = create_approved_action()

    state["requested_actions"][0]["action_type"] = "delete_database"
    state["approved_actions"][0]["action_type"] = "delete_database"

    agent = ActionExecutionAgent()
    state = agent.execute_action(state, action_id)

    assert state["current_step"] == "action_execution_blocked"
    assert state["completed_actions"] == []
    assert "Unsupported action type" in state["errors"][-1]


def test_missing_candidate_id_is_blocked():
    state, action_id = create_approved_action()

    state["requested_actions"][0]["candidate_id"] = ""
    agent = ActionExecutionAgent()

    state = agent.execute_action(state, action_id)

    assert state["current_step"] == "action_execution_blocked"
    assert state["completed_actions"] == []
    assert "candidate ID is missing" in state["errors"][-1]


def test_blank_action_id_is_blocked():
    agent = ActionExecutionAgent()
    state = create_state()

    state = agent.execute_action(state, " ")

    assert state["current_step"] == "action_execution_blocked"
    assert "valid action ID" in state["errors"][-1]


def test_successful_execution_preserves_approval_audit():
    state, action_id = create_approved_action()
    agent = ActionExecutionAgent()

    state = agent.execute_action(state, action_id)

    assert state["approved_actions"][0]["action_id"] == action_id
    assert state["approved_actions"][0]["approved_by"] == "Recruiter"
    assert state["requested_actions"][0]["status"] == "completed"
