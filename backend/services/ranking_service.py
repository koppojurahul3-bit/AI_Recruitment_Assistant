
from dataclasses import dataclass
from math import isfinite
from typing import List

from backend.services.matching_service import MatchResult


@dataclass
class RankedCandidate:
    """Candidate position in a ranked result set."""

    candidate_id: str
    rank: int
    overall_score: float
    recommendation: str


class RankingService:
    """Rank candidates deterministically using their matching results."""

    RECOMMENDATION_PRIORITY = {
        "Strong Match": 4,
        "Good Match": 3,
        "Potential Match": 2,
        "Low Match": 1,
    }

    def rank(
        self,
        match_results: List[MatchResult],
    ) -> List[RankedCandidate]:
        if not isinstance(match_results, list):
            raise TypeError("match_results must be a list.")

        for result in match_results:
            self._validate_result(result)

        sorted_results = sorted(
            match_results,
            key=self._ranking_key,
            reverse=True,
        )

        return [
            RankedCandidate(
                candidate_id=result.candidate_id,
                rank=index,
                overall_score=result.overall_score,
                recommendation=result.recommendation,
            )
            for index, result in enumerate(sorted_results, start=1)
        ]

    def top_n(
        self,
        match_results: List[MatchResult],
        n: int,
    ) -> List[RankedCandidate]:
        if isinstance(n, bool) or not isinstance(n, int):
            raise TypeError("N must be an integer.")

        if n <= 0:
            raise ValueError("N must be greater than zero.")

        return self.rank(match_results)[:n]

    def shortlist(
        self,
        match_results: List[MatchResult],
        minimum_score: float = 70.0,
    ) -> List[RankedCandidate]:
        if (
            isinstance(minimum_score, bool)
            or not isinstance(minimum_score, (int, float))
        ):
            raise TypeError("Minimum score must be a number.")

        if (
            not isfinite(minimum_score)
            or not 0 <= minimum_score <= 100
        ):
            raise ValueError(
                "Minimum score must be between 0 and 100."
            )

        return [
            candidate
            for candidate in self.rank(match_results)
            if candidate.overall_score >= minimum_score
        ]

    @classmethod
    def _ranking_key(cls, result: MatchResult):
        return (
            result.overall_score,
            cls.RECOMMENDATION_PRIORITY.get(
                result.recommendation,
                0,
            ),
            result.skill_match_score,
            result.experience_match_score,
            result.candidate_id,
        )

    @staticmethod
    def _validate_result(result: MatchResult) -> None:
        if not isinstance(result, MatchResult):
            raise TypeError("Every item must be a MatchResult.")

        if (
            not isinstance(result.candidate_id, str)
            or not result.candidate_id.strip()
        ):
            raise ValueError(
                "Every result must have a non-empty candidate ID."
            )

        score_fields = (
            "skill_match_score",
            "experience_match_score",
            "education_match_score",
            "overall_score",
        )

        for field_name in score_fields:
            value = getattr(result, field_name)

            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(value)
                or not 0 <= value <= 100
            ):
                raise ValueError(
                    f"{field_name} must be finite and between 0 and 100."
                )
