from dataclasses import asdict
from typing import List, Optional

from backend.models.state import RecruitmentState
from backend.repositories.candidate_repository import CandidateRepository
from backend.services.job_requirement_service import JobRequirementService
from backend.services.matching_service import MatchingService
from backend.services.ranking_service import RankingService


class CandidateEvaluationAgent:
    """
    Evaluates candidates against a job description and produces
    deterministic candidate rankings.

    Responsibilities:
    1. Extract job requirements.
    2. Retrieve candidates.
    3. Match every candidate against the requirements.
    4. Rank candidates using RankingService.
    5. Store evaluation and ranking results in RecruitmentState.
    """

    def __init__(
        self,
        candidate_repository: Optional[CandidateRepository] = None,
        requirement_service: Optional[JobRequirementService] = None,
        matching_service: Optional[MatchingService] = None,
        ranking_service: Optional[RankingService] = None,
    ):
        self.name = "CandidateEvaluationAgent"

        self.candidate_repository = (
            candidate_repository
            if candidate_repository is not None
            else CandidateRepository()
        )

        self.requirement_service = (
            requirement_service
            if requirement_service is not None
            else JobRequirementService()
        )

        self.matching_service = (
            matching_service
            if matching_service is not None
            else MatchingService()
        )

        self.ranking_service = (
            ranking_service
            if ranking_service is not None
            else RankingService()
        )

    def evaluate(
        self,
        state: RecruitmentState,
    ) -> RecruitmentState:
        """
        Evaluate candidates contained in the recruitment state.

        The method updates:
        - job_requirements
        - candidates
        - evaluations
        - rankings
        - current_step
        - errors
        """

        state["current_step"] = "candidate_evaluation"

        try:
            job_description = state.get("job_description", "").strip()

            if not job_description:
                raise ValueError(
                    "Job description is required for candidate evaluation."
                )

            # --------------------------------------------------
            # STEP 1: Extract job requirements
            # --------------------------------------------------

            requirements = self.requirement_service.extract(
                job_description
            )

            state["job_requirements"] = requirements.required_skills

            # --------------------------------------------------
            # STEP 2: Retrieve candidates
            # --------------------------------------------------

            candidate_ids = state.get("candidate_ids", [])

            if candidate_ids:
                candidates = []

                for candidate_id in candidate_ids:
                    candidate = self.candidate_repository.get_by_id(
                        candidate_id
                    )

                    if candidate is not None:
                        candidates.append(candidate)
            else:
                candidates = self.candidate_repository.get_all()

            if not candidates:
                raise ValueError(
                    "No candidates available for evaluation."
                )

            state["candidates"] = [
                asdict(candidate)
                for candidate in candidates
            ]

            # --------------------------------------------------
            # STEP 3: Match candidates
            # --------------------------------------------------

            match_results = []

            for candidate in candidates:
                match_result = self.matching_service.match(
                    candidate,
                    requirements
                )

                match_results.append(match_result)

            # --------------------------------------------------
            # STEP 4: Store detailed evaluations
            # --------------------------------------------------

            state["evaluations"] = [
                asdict(match_result)
                for match_result in match_results
            ]

            # --------------------------------------------------
            # STEP 5: Rank candidates
            # --------------------------------------------------

            ranked_candidates = self.ranking_service.rank(
                match_results
            )

            state["rankings"] = [
                asdict(ranked_candidate)
                for ranked_candidate in ranked_candidates
            ]

            # --------------------------------------------------
            # STEP 6: Successful completion
            # --------------------------------------------------

            state["current_step"] = "candidate_ranking"

            return state

        except Exception as exc:
            state["errors"] = state.get("errors", [])
            state["errors"].append(str(exc))
            state["current_step"] = "candidate_evaluation_failed"

            return state

    def evaluate_candidate_ids(
        self,
        state: RecruitmentState,
        candidate_ids: List[str],
    ) -> RecruitmentState:
        """
        Evaluate only the explicitly supplied candidate IDs.
        """

        state["candidate_ids"] = candidate_ids

        return self.evaluate(state)