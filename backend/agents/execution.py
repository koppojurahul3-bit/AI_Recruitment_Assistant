
from typing import Any, Dict

from backend.models.state import RecruitmentState


class ActionExecutionAgent:
    """
    Controls execution of approved recruitment actions.

    This module uses simulated execution only. It does not contact
    candidates or perform external recruitment operations.
    """

    SUPPORTED_ACTIONS = {
        "send_interview_invitation",
        "schedule_interview",
        "send_candidate_email",
        "reject_candidate",
        "shortlist_candidate",
    }

    def __init__(self):
        self.name = "ActionExecutionAgent"

    def execute_action(
        self,
        state: RecruitmentState,
        action_id: str,
    ) -> RecruitmentState:
        """
        Execute an approved action in simulation mode.

        An action must:
        1. Exist in requested_actions.
        2. Have status 'approved'.
        3. Also exist in approved_actions.
        4. Be supported by this execution agent.
        5. Not have been completed already.
        """

        state["current_step"] = "action_execution"

        try:
            if not isinstance(action_id, str) or not action_id.strip():
                raise ValueError("A valid action ID is required.")

            requested_actions = state.get("requested_actions", [])
            approved_actions = state.get("approved_actions", [])
            completed_actions = state.get("completed_actions", [])

            action = next(
                (
                    item
                    for item in requested_actions
                    if item.get("action_id") == action_id
                ),
                None,
            )

            if action is None:
                raise ValueError("Action was not found.")

            if any(
                item.get("action_id") == action_id
                for item in completed_actions
            ):
                raise ValueError("Action has already been completed.")

            if action.get("status") != "approved":
                raise PermissionError(
                    "Execution blocked: action is not approved."
                )

            approved_record = next(
                (
                    item
                    for item in approved_actions
                    if item.get("action_id") == action_id
                    and item.get("status") == "approved"
                ),
                None,
            )

            if approved_record is None:
                raise PermissionError(
                    "Execution blocked: no valid approval record exists."
                )

            action_type = action.get("action_type")

            if action_type not in self.SUPPORTED_ACTIONS:
                raise ValueError(
                    f"Unsupported action type: {action_type}"
                )

            if not action.get("candidate_id"):
                raise ValueError(
                    "Execution blocked: candidate ID is missing."
                )

            # Simulation only: no external operation is performed.
            completed_record: Dict[str, Any] = {
                **action,
                "status": "completed",
                "execution_mode": "simulated",
                "external_operation_performed": False,
            }

            action["status"] = "completed"
            action["execution_mode"] = "simulated"
            action["external_operation_performed"] = False

            state.setdefault("completed_actions", []).append(
                completed_record
            )

            state["current_step"] = "action_execution_completed"
            return state

        except (ValueError, PermissionError) as exc:
            state.setdefault("errors", []).append(str(exc))
            state["current_step"] = "action_execution_blocked"
            return state
