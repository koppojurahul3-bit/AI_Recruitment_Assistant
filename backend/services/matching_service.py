
from dataclasses import dataclass
from math import isfinite
from typing import List

from backend.models.candidate import Candidate
from backend.services.job_requirement_service import JobRequirements


@dataclass
class MatchResult:
    """Structured evaluation of a candidate for a specific job."""

    candidate_id: str
    skill_match_score: float
    experience_match_score: float
    education_match_score: float
    overall_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    experience_gap: float
    recommendation: str


class MatchingService:
    """Score candidates using skills, experience, and education."""

    SKILL_WEIGHT = 0.60
    EXPERIENCE_WEIGHT = 0.25
    EDUCATION_WEIGHT = 0.15

    def match(
        self,
        candidate: Candidate,
        requirements: JobRequirements,
    ) -> MatchResult:
        self._validate_candidate(candidate)
        self._validate_requirements(requirements)

        candidate_skills = self._normalize_skills(candidate.skills)
        required_skills = self._normalize_skills(
            requirements.required_skills
        )

        matched_skills = sorted(
            [
                display
                for key, display in required_skills.items()
                if key in candidate_skills
            ],
            key=str.casefold,
        )

        missing_skills = sorted(
            [
                display
                for key, display in required_skills.items()
                if key not in candidate_skills
            ],
            key=str.casefold,
        )

        skill_score = self._calculate_skill_score(
            candidate.skills,
            requirements.required_skills,
        )

        experience_score = self._calculate_experience_score(
            candidate.experience_years,
            requirements.minimum_experience_years,
        )

        education_score = self._calculate_education_score(
            candidate.education,
            requirements.education_requirements,
        )

        overall_score = (
            skill_score * self.SKILL_WEIGHT
            + experience_score * self.EXPERIENCE_WEIGHT
            + education_score * self.EDUCATION_WEIGHT
        )

        overall_score = min(100.0, max(0.0, overall_score))

        experience_gap = max(
            requirements.minimum_experience_years
            - candidate.experience_years,
            0.0,
        )

        return MatchResult(
            candidate_id=candidate.candidate_id,
            skill_match_score=round(skill_score, 2),
            experience_match_score=round(experience_score, 2),
            education_match_score=round(education_score, 2),
            overall_score=round(overall_score, 2),
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            experience_gap=round(experience_gap, 2),
            recommendation=self._recommendation(overall_score),
        )

    @staticmethod
    def _normalize_skills(skills: List[str]) -> dict[str, str]:
        """Normalize capitalization and whitespace and remove duplicates."""

        normalized = {}

        for skill in skills:
            if not isinstance(skill, str):
                continue

            display = " ".join(skill.split())

            if display:
                normalized.setdefault(display.casefold(), display)

        return normalized

    @classmethod
    def _matched_skills(
        cls,
        candidate_skills: List[str],
        required_skills: List[str],
    ) -> List[str]:
        candidate_keys = set(cls._normalize_skills(candidate_skills))
        required = cls._normalize_skills(required_skills)

        return sorted(
            [
                display
                for key, display in required.items()
                if key in candidate_keys
            ],
            key=str.casefold,
        )

    @classmethod
    def _missing_skills(
        cls,
        candidate_skills: List[str],
        required_skills: List[str],
    ) -> List[str]:
        candidate_keys = set(cls._normalize_skills(candidate_skills))
        required = cls._normalize_skills(required_skills)

        return sorted(
            [
                display
                for key, display in required.items()
                if key not in candidate_keys
            ],
            key=str.casefold,
        )

    @classmethod
    def _calculate_skill_score(
        cls,
        candidate_skills: List[str],
        required_skills: List[str],
    ) -> float:
        required = cls._normalize_skills(required_skills)

        if not required:
            return 100.0

        candidate_keys = set(cls._normalize_skills(candidate_skills))

        matched_count = sum(
            1 for key in required if key in candidate_keys
        )

        return matched_count / len(required) * 100.0

    @staticmethod
    def _calculate_experience_score(
        candidate_experience: float,
        required_experience: float,
    ) -> float:
        if required_experience <= 0:
            return 100.0

        if candidate_experience >= required_experience:
            return 100.0

        return max(
            0.0,
            candidate_experience / required_experience * 100.0,
        )

    @staticmethod
    def _calculate_education_score(
        candidate_education: List[str],
        required_education: List[str],
    ) -> float:
        if not required_education:
            return 100.0

        normalized_education = [
            " ".join(value.split()).casefold()
            for value in candidate_education
            if isinstance(value, str) and value.strip()
        ]

        for requirement in required_education:
            normalized_requirement = (
                " ".join(requirement.split()).casefold()
            )

            if normalized_requirement and any(
                normalized_requirement in education
                or education in normalized_requirement
                for education in normalized_education
            ):
                return 100.0

        return 0.0

    @staticmethod
    def _recommendation(overall_score: float) -> str:
        if overall_score >= 85:
            return "Strong Match"

        if overall_score >= 70:
            return "Good Match"

        if overall_score >= 50:
            return "Potential Match"

        return "Low Match"

    @staticmethod
    def _validate_candidate(candidate: Candidate) -> None:
        if not isinstance(candidate.candidate_id, str):
            raise ValueError("Candidate ID must be a non-empty string.")

        if not candidate.candidate_id.strip():
            raise ValueError("Candidate ID must be a non-empty string.")

        experience = candidate.experience_years

        if (
            isinstance(experience, bool)
            or not isinstance(experience, (int, float))
            or not isfinite(experience)
            or experience < 0
        ):
            raise ValueError(
                "Candidate experience must be finite and non-negative."
            )

    @staticmethod
    def _validate_requirements(
        requirements: JobRequirements,
    ) -> None:
        if not isinstance(requirements, JobRequirements):
            raise TypeError(
                "requirements must be a JobRequirements instance."
            )

        years = requirements.minimum_experience_years

        if (
            isinstance(years, bool)
            or not isinstance(years, (int, float))
            or not isfinite(years)
            or years < 0
        ):
            raise ValueError(
                "Required experience must be finite and non-negative."
            )
