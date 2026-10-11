
from copy import deepcopy
from typing import Any, Dict

from backend.models.state import RecruitmentState


class ActionExecutionAgent:
    """Executes approved recruitment actions in simulation mode only."""

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
        state["current_step"] = "action_execution"

        try:
            if not isinstance(action_id, str) or not action_id.strip():
                raise ValueError("A valid action ID is required.")

            requested = state.get("requested_actions", [])
            approvals = state.get("approved_actions", [])
            completed = state.get("completed_actions", [])

            if not all(
                isinstance(records, list)
                for records in (requested, approvals, completed)
            ):
                raise ValueError("Action records must be lists.")

            matching_requests = [
                item
                for item in requested
                if isinstance(item, dict)
                and item.get("action_id") == action_id
            ]

            if not matching_requests:
                raise ValueError("Action was not found.")

            if len(matching_requests) != 1:
                raise ValueError(
                    "Execution blocked: expected exactly one requested action."
                )

            action = matching_requests[0]

            if any(
                isinstance(item, dict)
                and item.get("action_id") == action_id
                for item in completed
            ):
                raise ValueError("Action has already been completed.")

            if action.get("status") != "approved":
                raise PermissionError(
                    "Execution blocked: action is not approved."
                )

            # Validate the candidate before comparing the approval snapshot.
            if not isinstance(action.get("candidate_id"), str) or not (
                action["candidate_id"].strip()
            ):
                raise ValueError(
                    "Execution blocked: candidate ID is missing."
                )

            matching_approvals = [
                item
                for item in approvals
                if isinstance(item, dict)
                and item.get("action_id") == action_id
                and item.get("status") == "approved"
            ]

            if len(matching_approvals) == 0:
                raise PermissionError(
                    "Execution blocked: no valid approval record exists."
                )

            if len(matching_approvals) != 1:
                raise PermissionError(
                    "Execution blocked: multiple approval records exist."
                )

            approval = matching_approvals[0]

            # Ensure the approved action has not been modified.
            for field in ("action_type", "candidate_id", "details"):
                if approval.get(field) != action.get(field):
                    raise PermissionError(
                        "Execution blocked: approval and request "
                        f"disagree on {field}."
                    )

            if not isinstance(approval.get("approved_by"), str) or not (
                approval["approved_by"].strip()
            ):
                raise PermissionError(
                    "Execution blocked: approval reviewer identity is missing."
                )

            if action.get("action_type") not in self.SUPPORTED_ACTIONS:
                raise ValueError(
                    f"Unsupported action type: {action.get('action_type')}"
                )

            # Simulation only: no email, calendar, or external operation.
            completed_record: Dict[str, Any] = deepcopy(action)
            completed_record.update(
                {
                    "status": "completed",
                    "execution_mode": "simulated",
                    "external_operation_performed": False,
                }
            )

            action["status"] = "completed"
            action["execution_mode"] = "simulated"
            action["external_operation_performed"] = False

            state.setdefault("completed_actions", []).append(
                completed_record
            )

            state["current_step"] = "action_execution_completed"
            return state

        except (ValueError, PermissionError, TypeError) as exc:
            state.setdefault("errors", []).append(str(exc))
            state["current_step"] = "action_execution_blocked"
            return state
