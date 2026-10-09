
from typing import Any, Dict
from uuid import uuid4

from backend.models.state import RecruitmentState


class HumanApprovalAgent:
    """
    Controls human approval for consequential recruitment actions.

    This agent records requests and approval decisions.
    It does not send emails, schedule interviews, or reject candidates.
    """

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
        """Register an action that requires human review."""

        if action_type not in self.APPROVAL_REQUIRED_ACTIONS:
            raise ValueError(
                f"Unsupported action type: {action_type}"
            )

        if not isinstance(candidate_id, str) or not candidate_id.strip():
            raise ValueError("A valid candidate ID is required.")

        if details is not None and not isinstance(details, dict):
            raise TypeError("Action details must be a dictionary.")

        action = {
            "action_id": str(uuid4()),
            "action_type": action_type,
            "candidate_id": candidate_id.strip(),
            "details": details.copy() if details is not None else {},
            "status": "pending",
            "requires_approval": True,
            "approved_by": None,
            "decision_reason": None,
        }

        state.setdefault("requested_actions", []).append(action)
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
        """Approve one pending action and record the decision."""

        if not isinstance(approved_by, str) or not approved_by.strip():
            raise ValueError("The approver identity is required.")

        action = self._find_pending_action(state, action_id)

        action["status"] = "approved"
        action["approved_by"] = approved_by.strip()
        action["decision_reason"] = reason.strip()

        state.setdefault("approved_actions", []).append(action.copy())

        self._refresh_approval_state(state)
        return state

    def deny_action(
        self,
        state: RecruitmentState,
        action_id: str,
        denied_by: str,
        reason: str,
    ) -> RecruitmentState:
        """Deny a pending action without executing it."""

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
        """Return actions still awaiting human review."""

        return [
            action.copy()
            for action in state.get("requested_actions", [])
            if action.get("status") == "pending"
        ]

    @staticmethod
    def _find_pending_action(
        state: RecruitmentState,
        action_id: str,
    ) -> Dict[str, Any]:
        """Find a pending action or reject an invalid decision."""

        for action in state.get("requested_actions", []):
            if action.get("action_id") == action_id:
                if action.get("status") != "pending":
                    raise ValueError(
                        "This action has already been reviewed."
                    )
                return action

        raise ValueError("Pending action was not found.")

    def _refresh_approval_state(
        self,
        state: RecruitmentState,
    ) -> None:
        """Update state based on remaining pending actions."""

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
