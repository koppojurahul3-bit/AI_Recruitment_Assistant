
from copy import deepcopy
from typing import Any, Dict
from uuid import uuid4

from backend.models.state import RecruitmentState


class HumanApprovalAgent:
    """Records human decisions for simulated recruitment actions."""

    APPROVAL_REQUIRED_ACTIONS = {
        "send_interview_invitation",
        "schedule_interview",
        "send_candidate_email",
        "reject_candidate",
        "shortlist_candidate",
    }

    def __init__(self):
        self.name = "HumanApprovalAgent"

    def request_approval(
        self,
        state: RecruitmentState,
        action_type: str,
        candidate_id: str,
        details: Dict[str, Any] | None = None,
    ) -> RecruitmentState:
        if action_type not in self.APPROVAL_REQUIRED_ACTIONS:
            raise ValueError(f"Unsupported action type: {action_type}")

        if not isinstance(candidate_id, str) or not candidate_id.strip():
            raise ValueError("A valid candidate ID is required.")

        if details is not None and not isinstance(details, dict):
            raise TypeError("Action details must be a dictionary.")

        requested = state.setdefault("requested_actions", [])
        approved = state.setdefault("approved_actions", [])

        if not isinstance(requested, list) or not isinstance(approved, list):
            raise TypeError("Action records must be lists.")

        action_id = str(uuid4())
        while any(
            isinstance(item, dict) and item.get("action_id") == action_id
            for item in requested + approved
        ):
            action_id = str(uuid4())

        action = {
            "action_id": action_id,
            "action_type": action_type,
            "candidate_id": candidate_id.strip(),
            "details": deepcopy(details) if details is not None else {},
            "status": "pending",
            "requires_approval": True,
            "approved_by": None,
            "decision_reason": None,
        }

        requested.append(action)
        state["requires_approval"] = True
        state["approval_reason"] = (
            "One or more recruitment actions require human approval."
        )
        state["current_step"] = "human_approval"
        return state

    def approve_action(
        self,
        state: RecruitmentState,
        action_id: str,
        approved_by: str,
        reason: str = "",
    ) -> RecruitmentState:
        if not isinstance(approved_by, str) or not approved_by.strip():
            raise ValueError("The approver identity is required.")

        if not isinstance(reason, str):
            raise TypeError("Approval reason must be a string.")

        action = self._find_pending_action(state, action_id)
        action["status"] = "approved"
        action["approved_by"] = approved_by.strip()
        action["decision_reason"] = reason.strip()

        # Independent deep snapshot: nested details cannot be changed
        # by mutating the request after the approval decision.
        state.setdefault("approved_actions", []).append(deepcopy(action))
        self._refresh_approval_state(state)
        return state

    def deny_action(
        self,
        state: RecruitmentState,
        action_id: str,
        denied_by: str,
        reason: str,
    ) -> RecruitmentState:
        if not isinstance(denied_by, str) or not denied_by.strip():
            raise ValueError("The reviewer identity is required.")

        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("A reason is required when denying an action.")

        action = self._find_pending_action(state, action_id)
        action["status"] = "denied"
        action["approved_by"] = denied_by.strip()
        action["decision_reason"] = reason.strip()

        self._refresh_approval_state(state)
        return state

    def get_pending_actions(
        self,
        state: RecruitmentState,
    ) -> list[Dict[str, Any]]:
        return [
            deepcopy(action)
            for action in state.get("requested_actions", [])
            if isinstance(action, dict) and action.get("status") == "pending"
        ]

    @staticmethod
    def _find_pending_action(
        state: RecruitmentState,
        action_id: str,
    ) -> Dict[str, Any]:
        if not isinstance(action_id, str) or not action_id.strip():
            raise ValueError("A valid action ID is required.")

        matches = [
            item
            for item in state.get("requested_actions", [])
            if isinstance(item, dict) and item.get("action_id") == action_id
        ]

        if not matches:
            raise ValueError("Pending action was not found.")

        if len(matches) != 1:
            raise ValueError("Expected exactly one matching requested action.")

        action = matches[0]
        if action.get("status") != "pending":
            raise ValueError("This action has already been reviewed.")

        # Refuse to create a second approval decision for this action.
        if any(
            isinstance(item, dict) and item.get("action_id") == action_id
            for item in state.get("approved_actions", [])
        ):
            raise ValueError("This action has already been reviewed.")

        return action

    def _refresh_approval_state(self, state: RecruitmentState) -> None:
        pending = self.get_pending_actions(state)
        state["requires_approval"] = bool(pending)

        if pending:
            state["approval_reason"] = (
                f"{len(pending)} action(s) still require human approval."
            )
            state["current_step"] = "human_approval"
        else:
            state["approval_reason"] = None
            state["current_step"] = "approval_reviewed"
