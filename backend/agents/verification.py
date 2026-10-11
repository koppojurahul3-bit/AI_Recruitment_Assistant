
from typing import Any, Dict, List

from backend.models.state import RecruitmentState


class ExecutionVerificationAgent:
    """Verifies stored action, approval, and completion evidence."""

    def __init__(self):
        self.name = "ExecutionVerificationAgent"

    def verify_action(
        self,
        state: RecruitmentState,
        action_id: str,
    ) -> Dict[str, Any]:
        if not isinstance(action_id, str) or not action_id.strip():
            raise ValueError("A valid action ID is required.")

        requested = [
            item for item in state.get("requested_actions", [])
            if isinstance(item, dict) and item.get("action_id") == action_id
        ]
        approved = [
            item for item in state.get("approved_actions", [])
            if isinstance(item, dict)
            and item.get("action_id") == action_id
            and item.get("status") == "approved"
        ]
        completed = [
            item for item in state.get("completed_actions", [])
            if isinstance(item, dict) and item.get("action_id") == action_id
        ]

        issues: List[str] = []

        if len(requested) != 1:
            issues.append(
                "Expected exactly one matching requested action record."
            )
        if len(approved) != 1:
            issues.append("Expected exactly one valid approval record.")
        if len(completed) != 1:
            issues.append(
                "Expected exactly one matching completed action record."
            )

        if len(requested) == 1 and len(approved) == 1:
            request = requested[0]
            approval = approved[0]

            for field in ("action_type", "candidate_id", "details"):
                if request.get(field) != approval.get(field):
                    issues.append(
                        f"Approval and requested records disagree on {field}."
                    )

            if not isinstance(approval.get("approved_by"), str) or not (
                approval["approved_by"].strip()
            ):
                issues.append("Approval reviewer identity is missing.")

            if not isinstance(approval.get("decision_reason"), str):
                issues.append("Approval decision reason is invalid.")

        if len(requested) == 1 and len(completed) == 1:
            request = requested[0]
            completion = completed[0]

            if request.get("status") != "completed":
                issues.append("Requested action status is not completed.")

            if completion.get("status") != "completed":
                issues.append("Completion record status is not completed.")

            for field in ("action_type", "candidate_id", "details"):
                if request.get(field) != completion.get(field):
                    issues.append(
                        f"Requested and completed records disagree on {field}."
                    )

            if completion.get("execution_mode") != "simulated":
                issues.append(
                    "Execution mode is missing or is not simulated."
                )

            if completion.get("external_operation_performed") is not False:
                issues.append(
                    "External operation flag must explicitly be False "
                    "for this simulation-only module."
                )

        return {
            "action_id": action_id,
            "status": "verified" if not issues else "failed",
            "verified": not issues,
            "issues": issues,
            "checks": {
                "requested_record_count": len(requested),
                "valid_approval_record_count": len(approved),
                "completed_record_count": len(completed),
            },
            "verification_scope": "stored_records_only",
        }

    def verify_all(self, state: RecruitmentState) -> RecruitmentState:
        state["current_step"] = "verification"

        try:
            completed_actions = state.get("completed_actions", [])
            if not isinstance(completed_actions, list):
                raise TypeError("Completed action records must be a list.")

            action_ids = [
                item.get("action_id")
                for item in completed_actions
                if isinstance(item, dict) and item.get("action_id")
            ]

            results = [
                self.verify_action(state, action_id)
                for action_id in dict.fromkeys(action_ids)
            ]

            state["verification_results"] = results
            state["current_step"] = (
                "verification_completed"
                if all(result["verified"] for result in results)
                else "verification_failed"
            )
            return state

        except (ValueError, TypeError, KeyError) as exc:
            state.setdefault("errors", []).append(str(exc))
            state["current_step"] = "verification_failed"
            return state
