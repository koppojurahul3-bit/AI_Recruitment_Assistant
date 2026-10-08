from typing import List, Optional

from backend.models.state import RecruitmentState
from backend.repositories.candidate_repository import CandidateRepository


class ResumeRetrievalAgent:
    """
    Retrieves relevant candidates from the candidate repository.

    Responsibilities:
    1. Search candidates by skills.
    2. Search candidates by multiple skills.
    3. Filter candidates by experience.
    4. Combine multiple retrieval conditions.
    5. Store retrieved candidates in RecruitmentState.
    """

    def __init__(
        self,
        candidate_repository: Optional[CandidateRepository] = None,
    ):
        self.name = "ResumeRetrievalAgent"

        self.candidate_repository = (
            candidate_repository
            if candidate_repository is not None
            else CandidateRepository()
        )

    def search_by_skill(
        self,
        skill: str,
    ) -> List[str]:
        """
        Retrieve candidate IDs matching a single skill.
        """

        if not isinstance(skill, str):
            raise TypeError("Skill must be a string.")

        skill = skill.strip()

        if not skill:
            return []

        candidates = self.candidate_repository.search_by_skill(skill)

        return [
            candidate.candidate_id
            for candidate in candidates
        ]

    def search_by_skills(
        self,
        skills: List[str],
    ) -> List[str]:
        """
        Retrieve candidate IDs matching at least one
        of the supplied skills.
        """

        if not isinstance(skills, list):
            raise TypeError("Skills must be provided as a list.")

        cleaned_skills = [
            skill.strip()
            for skill in skills
            if isinstance(skill, str) and skill.strip()
        ]

        if not cleaned_skills:
            return []

        candidates = self.candidate_repository.search_by_skills(
            cleaned_skills
        )

        return [
            candidate.candidate_id
            for candidate in candidates
        ]

    def search_by_experience(
        self,
        minimum_experience_years: float,
    ) -> List[str]:
        """
        Retrieve candidate IDs meeting the minimum
        experience requirement.
        """

        if minimum_experience_years < 0:
            raise ValueError(
                "Minimum experience cannot be negative."
            )

        candidates = self.candidate_repository.search_by_experience(
            minimum_experience_years
        )

        return [
            candidate.candidate_id
            for candidate in candidates
        ]

    def retrieve(
        self,
        state: RecruitmentState,
        skills: Optional[List[str]] = None,
        minimum_experience_years: Optional[float] = None,
    ) -> RecruitmentState:
        """
        Retrieve candidates using the supplied search conditions.

        If multiple conditions are supplied, candidates must satisfy
        all conditions.

        The retrieved candidate IDs are stored in:
            state["candidate_ids"]

        The retrieved candidate objects are stored in:
            state["candidates"]
        """

        state["current_step"] = "candidate_search"

        try:
            if skills is None:
                skills = []

            if not isinstance(skills, list):
                raise TypeError(
                    "Skills must be provided as a list."
                )

            cleaned_skills = [
                skill.strip()
                for skill in skills
                if isinstance(skill, str) and skill.strip()
            ]

            candidate_sets = []

            if cleaned_skills:
                skill_candidate_ids = set(
                    self.search_by_skills(cleaned_skills)
                )

                candidate_sets.append(skill_candidate_ids)

            if minimum_experience_years is not None:
                experience_candidate_ids = set(
                    self.search_by_experience(
                        minimum_experience_years
                    )
                )

                candidate_sets.append(experience_candidate_ids)

            if candidate_sets:
                matching_candidate_ids = set.intersection(
                    *candidate_sets
                )
            else:
                matching_candidate_ids = {
                    candidate.candidate_id
                    for candidate
                    in self.candidate_repository.get_all()
                }

            ordered_candidate_ids = [
                candidate.candidate_id
                for candidate in self.candidate_repository.get_all()
                if candidate.candidate_id in matching_candidate_ids
            ]

            candidates = [
                candidate
                for candidate in self.candidate_repository.get_all()
                if candidate.candidate_id in matching_candidate_ids
            ]

            state["candidate_ids"] = ordered_candidate_ids
            state["candidates"] = [
                {
                    "candidate_id": candidate.candidate_id,
                    "name": candidate.name,
                    "email": candidate.email,
                    "phone": candidate.phone,
                    "skills": candidate.skills,
                    "experience_years": candidate.experience_years,
                    "education": candidate.education,
                    "projects": candidate.projects,
                    "certifications": candidate.certifications,
                    "resume_text": candidate.resume_text,
                    "source": candidate.source,
                }
                for candidate in candidates
            ]

            state["current_step"] = "candidate_search_completed"

            return state

        except Exception as exc:
            state["errors"] = state.get("errors", [])
            state["errors"].append(str(exc))
            state["current_step"] = "candidate_search_failed"

            return state

    def retrieve_for_state(
        self,
        state: RecruitmentState,
        skills: List[str],
        minimum_experience_years: Optional[float] = None,
    ) -> RecruitmentState:
        """
        Convenience method for retrieval directly from
        an existing recruitment state.
        """

        return self.retrieve(
            state=state,
            skills=skills,
            minimum_experience_years=minimum_experience_years,
        )