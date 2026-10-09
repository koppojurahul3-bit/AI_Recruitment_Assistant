
from typing import Any, Dict, List, Optional

from backend.models.state import RecruitmentState


class RecruitmentAnalyticsService:
    """Build recruiter-facing analytics from recruitment state."""

    def generate_report(
        self,
        state: RecruitmentState,
        audit_events: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        """Generate a report without modifying the supplied state."""

        candidates = state.get("candidates", [])
        evaluations = state.get("evaluations", [])
        rankings = state.get("rankings", [])
        requested_actions = state.get("requested_actions", [])
        approved_actions = state.get("approved_actions", [])
        completed_actions = state.get("completed_actions", [])
        verification_results = state.get("verification_results", [])
        audit_events = audit_events or []

        scores = [
            self._valid_score(item.get("overall_score"))
            for item in evaluations
        ]
        valid_scores = [score for score in scores if score is not None]

        recommendations: Dict[str, int] = {}
        for evaluation in evaluations:
            recommendation = evaluation.get("recommendation")
            if isinstance(recommendation, str) and recommendation.strip():
                label = recommendation.strip()
                recommendations[label] = recommendations.get(label, 0) + 1

        action_statuses: Dict[str, int] = {}
        for action in requested_actions:
            status = action.get("status", "unknown")
            if not isinstance(status, str):
                status = "unknown"
            action_statuses[status] = action_statuses.get(status, 0) + 1

        verified_count = sum(
            1 for result in verification_results
            if result.get("verified") is True
        )
        failed_verification_count = sum(
            1 for result in verification_results
            if result.get("verified") is False
        )

        average_score = (
            round(sum(valid_scores) / len(valid_scores), 2)
            if valid_scores
            else None
        )

        report = {
            "recruiter_goal": state.get("recruiter_goal", ""),
            "current_step": state.get("current_step", "unknown"),
            "summary": {
                "total_candidates": len(candidates),
                "evaluated_candidates": len(evaluations),
                "ranked_candidates": len(rankings),
                "average_match_score": average_score,
                "highest_match_score": (
                    max(valid_scores) if valid_scores else None
                ),
                "lowest_match_score": (
                    min(valid_scores) if valid_scores else None
                ),
            },
            "recommendation_breakdown": recommendations,
            "actions": {
                "requested": len(requested_actions),
                "approved_records": len(approved_actions),
                "completed": len(completed_actions),
                "pending_approval": sum(
                    1 for action in requested_actions
                    if action.get("status") == "pending"
                ),
                "denied": sum(
                    1 for action in requested_actions
                    if action.get("status") == "denied"
                ),
                "status_breakdown": action_statuses,
            },
            "verification": {
                "total_results": len(verification_results),
                "verified": verified_count,
                "failed": failed_verification_count,
            },
            "audit": {
                "event_count": len(audit_events),
                "outcome_breakdown": self._count_values(
                    audit_events, "outcome"
                ),
                "event_type_breakdown": self._count_values(
                    audit_events, "event_type"
                ),
            },
            "errors": list(state.get("errors", [])),
        }

        return report

    def get_top_candidates(
        self,
        state: RecruitmentState,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Return the highest-ranked candidates from ranking records."""

        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("Limit must be a positive integer.")

        candidate_lookup = {
            item.get("candidate_id"): item
            for item in state.get("candidates", [])
            if item.get("candidate_id")
        }

        ordered_rankings = sorted(
            state.get("rankings", []),
            key=lambda item: (
                self._valid_score(item.get("overall_score"))
                if self._valid_score(item.get("overall_score")) is not None
                else -1,
                -self._valid_rank(item.get("rank")),
            ),
            reverse=True,
        )

        results = []

        for ranking in ordered_rankings[:limit]:
            candidate_id = ranking.get("candidate_id")
            candidate = candidate_lookup.get(candidate_id, {})

            results.append({
                "candidate_id": candidate_id,
                "name": candidate.get("name", "Unknown"),
                "rank": ranking.get("rank"),
                "overall_score": ranking.get("overall_score"),
                "recommendation": ranking.get("recommendation"),
            })

        return results

    @staticmethod
    def _valid_score(value: Any) -> Optional[float]:
        """Return a finite score from 0–100, or None if invalid."""

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None

        score = float(value)

        if not 0 <= score <= 100:
            return None

        return score

    @staticmethod
    def _valid_rank(value: Any) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            return 0
        return value

    @staticmethod
    def _count_values(
        records: List[Any],
        field: str,
    ) -> Dict[str, int]:
        counts: Dict[str, int] = {}

        for record in records:
            if isinstance(record, dict):
                value = record.get(field)
            else:
                value = getattr(record, field, None)

            if isinstance(value, str) and value.strip():
                label = value.strip()
                counts[label] = counts.get(label, 0) + 1

        return counts
