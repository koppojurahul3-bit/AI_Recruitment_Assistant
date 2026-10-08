from dataclasses import dataclass
from typing import List

from backend.services.matching_service import MatchResult


@dataclass
class RankedCandidate:
    """
    Represents a candidate after ranking.
    """

    candidate_id: str
    rank: int
    overall_score: float
    recommendation: str


class RankingService:
    """
    Ranks candidates based on their matching results.
    """

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
        """
        Rank all candidates from strongest to weakest.
        """

        sorted_results = sorted(
            match_results,
            key=self._ranking_key,
            reverse=True,
        )

        ranked_candidates = []

        for index, result in enumerate(
            sorted_results,
            start=1,
        ):
            ranked_candidates.append(
                RankedCandidate(
                    candidate_id=result.candidate_id,
                    rank=index,
                    overall_score=result.overall_score,
                    recommendation=result.recommendation,
                )
            )

        return ranked_candidates

    def top_n(
        self,
        match_results: List[MatchResult],
        n: int,
    ) -> List[RankedCandidate]:
        """
        Return the strongest N candidates.
        """

        if n <= 0:
            raise ValueError(
                "N must be greater than zero."
            )

        ranked_candidates = self.rank(
            match_results
        )

        return ranked_candidates[:n]

    def shortlist(
        self,
        match_results: List[MatchResult],
        minimum_score: float = 70.0,
    ) -> List[RankedCandidate]:
        """
        Return candidates whose score meets the
        minimum shortlist threshold.
        """

        if not 0 <= minimum_score <= 100:
            raise ValueError(
                "Minimum score must be between 0 and 100."
            )

        ranked_candidates = self.rank(
            match_results
        )

        return [
            candidate
            for candidate in ranked_candidates
            if candidate.overall_score >= minimum_score
        ]

    @classmethod
    def _ranking_key(
        cls,
        result: MatchResult,
    ):
        """
        Ranking priority:

        1. Overall score
        2. Recommendation priority
        3. Skill match score
        4. Experience match score
        5. Candidate ID for deterministic ordering
        """

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