
from backend.agents.approval import HumanApprovalAgent
from backend.agents.execution import ActionExecutionAgent
from backend.agents.verification import ExecutionVerificationAgent
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


def create_completed_state():
    state = create_state()
    approval_agent = HumanApprovalAgent()
    execution_agent = ActionExecutionAgent()

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

    state = execution_agent.execute_action(state, action_id)

    assert state["current_step"] == "action_execution_completed"

    return state, action_id


def test_valid_completion_is_verified():
    state, action_id = create_completed_state()
    agent = ExecutionVerificationAgent()

    result = agent.verify_action(state, action_id)

    assert result["verified"] is True
    assert result["status"] == "verified"
    assert result["issues"] == []
    assert result["verification_scope"] == "stored_records_only"


def test_missing_completion_record_fails():
    state, action_id = create_completed_state()
    state["completed_actions"] = []

    result = ExecutionVerificationAgent().verify_action(state, action_id)

    assert result["verified"] is False
    assert any("completed action record" in issue for issue in result["issues"])


def test_missing_approval_record_fails():
    state, action_id = create_completed_state()
    state["approved_actions"] = []

    result = ExecutionVerificationAgent().verify_action(state, action_id)

    assert result["verified"] is False
    assert any("approval record" in issue for issue in result["issues"])


def test_duplicate_completion_records_fail():
    state, action_id = create_completed_state()
    state["completed_actions"].append(
        state["completed_actions"][0].copy()
    )

    result = ExecutionVerificationAgent().verify_action(state, action_id)

    assert result["verified"] is False
    assert any("exactly one" in issue for issue in result["issues"])


def test_candidate_mismatch_fails():
    state, action_id = create_completed_state()
    state["completed_actions"][0]["candidate_id"] = "C999"

    result = ExecutionVerificationAgent().verify_action(state, action_id)

    assert result["verified"] is False
    assert any("candidate_id" in issue for issue in result["issues"])


def test_non_simulated_execution_fails():
    state, action_id = create_completed_state()
    state["completed_actions"][0]["execution_mode"] = "live"

    result = ExecutionVerificationAgent().verify_action(state, action_id)

    assert result["verified"] is False
    assert any("simulated" in issue for issue in result["issues"])


def test_external_operation_flag_must_be_false():
    state, action_id = create_completed_state()
    state["completed_actions"][0]["external_operation_performed"] = True

    result = ExecutionVerificationAgent().verify_action(state, action_id)

    assert result["verified"] is False
    assert any("External operation flag" in issue for issue in result["issues"])


def test_missing_reviewer_identity_fails():
    state, action_id = create_completed_state()
    state["approved_actions"][0]["approved_by"] = ""

    result = ExecutionVerificationAgent().verify_action(state, action_id)

    assert result["verified"] is False
    assert any("reviewer identity" in issue for issue in result["issues"])


def test_unknown_action_id_fails():
    state, _ = create_completed_state()

    result = ExecutionVerificationAgent().verify_action(
        state,
        "unknown-action",
    )

    assert result["verified"] is False
    assert len(result["issues"]) > 0


def test_blank_action_id_raises_error():
    agent = ExecutionVerificationAgent()

    try:
        agent.verify_action(create_state(), " ")
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "valid action ID" in str(exc)


def test_verify_all_stores_report_and_status():
    state, _ = create_completed_state()
    agent = ExecutionVerificationAgent()

    state = agent.verify_all(state)

    assert state["current_step"] == "verification_completed"
    assert len(state["verification_results"]) == 1
    assert state["verification_results"][0]["verified"] is True


def test_verify_all_flags_inconsistent_completion():
    state, _ = create_completed_state()
    state["completed_actions"][0]["candidate_id"] = "C999"

    state = ExecutionVerificationAgent().verify_all(state)

    assert state["current_step"] == "verification_failed"
    assert state["verification_results"][0]["verified"] is False
