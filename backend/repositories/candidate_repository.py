from typing import List, Optional

from backend.models.candidate import Candidate


class CandidateRepository:
    """
    Repository responsible for storing and retrieving candidates.
    """

    def __init__(self):
        self._candidates: List[Candidate] = []

    def add(
        self,
        candidate: Candidate
    ) -> Candidate:
        """
        Add a candidate to the repository.

        Raises:
            ValueError: If the candidate ID already exists.
        """

        if self.get_by_id(candidate.candidate_id) is not None:
            raise ValueError(
                f"Candidate already exists: {candidate.candidate_id}"
            )

        self._candidates.append(candidate)

        return candidate

    def get_by_id(
        self,
        candidate_id: str
    ) -> Optional[Candidate]:
        """
        Retrieve a candidate by candidate ID.
        """

        for candidate in self._candidates:
            if candidate.candidate_id == candidate_id:
                return candidate

        return None

    def get_all(self) -> List[Candidate]:
        """
        Return all candidates.
        """

        return list(self._candidates)

    def search_by_skill(
        self,
        skill: str
    ) -> List[Candidate]:
        """
        Find candidates who have a specific skill.
        """

        normalized_skill = skill.lower()

        return [
            candidate
            for candidate in self._candidates
            if any(
                candidate_skill.lower() == normalized_skill
                for candidate_skill in candidate.skills
            )
        ]

    def search_by_skills(
        self,
        skills: List[str]
    ) -> List[Candidate]:
        """
        Find candidates who have at least one of the requested skills.
        """

        normalized_skills = {
            skill.lower()
            for skill in skills
        }

        return [
            candidate
            for candidate in self._candidates
            if any(
                candidate_skill.lower() in normalized_skills
                for candidate_skill in candidate.skills
            )
        ]

    def search_by_experience(
        self,
        minimum_years: float
    ) -> List[Candidate]:
        """
        Find candidates with at least the requested experience.
        """

        return [
            candidate
            for candidate in self._candidates
            if candidate.experience_years >= minimum_years
        ]

    def count(self) -> int:
        """
        Return the number of candidates in the repository.
        """

        return len(self._candidates)

    def clear(self) -> None:
        """
        Clear all candidates from the repository.
        """

        self._candidates.clear()