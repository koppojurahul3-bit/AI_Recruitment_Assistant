from dataclasses import dataclass
from typing import List

from backend.models.candidate import Candidate
from backend.services.job_requirement_service import JobRequirements


@dataclass
class MatchResult:
    """
    Structured evaluation of how well a candidate matches
    a specific job.
    """

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
    """
    Evaluates candidates against structured job requirements.
    """

    SKILL_WEIGHT = 0.60
    EXPERIENCE_WEIGHT = 0.25
    EDUCATION_WEIGHT = 0.15

    def match(
        self,
        candidate: Candidate,
        requirements: JobRequirements,
    ) -> MatchResult:
        """
        Evaluate a candidate against job requirements.
        """

        matched_skills = self._matched_skills(
            candidate.skills,
            requirements.required_skills,
        )

        missing_skills = self._missing_skills(
            candidate.skills,
            requirements.required_skills,
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

        experience_gap = max(
            requirements.minimum_experience_years
            - candidate.experience_years,
            0.0,
        )

        recommendation = self._recommendation(
            overall_score
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
            recommendation=recommendation,
        )

    @staticmethod
    def _matched_skills(
        candidate_skills: List[str],
        required_skills: List[str],
    ) -> List[str]:
        """
        Return required skills present in the candidate profile.
        """

        candidate_skill_map = {
            skill.lower(): skill
            for skill in candidate_skills
        }

        matched = []

        for required_skill in required_skills:

            if required_skill.lower() in candidate_skill_map:
                matched.append(
                    required_skill
                )

        return sorted(matched)

    @staticmethod
    def _missing_skills(
        candidate_skills: List[str],
        required_skills: List[str],
    ) -> List[str]:
        """
        Return required skills missing from the candidate profile.
        """

        candidate_skill_set = {
            skill.lower()
            for skill in candidate_skills
        }

        missing = []

        for required_skill in required_skills:

            if required_skill.lower() not in candidate_skill_set:
                missing.append(required_skill)

        return sorted(missing)

    @classmethod
    def _calculate_skill_score(
        cls,
        candidate_skills: List[str],
        required_skills: List[str],
    ) -> float:
        """
        Calculate the percentage of required skills
        covered by the candidate.
        """

        if not required_skills:
            return 100.0

        candidate_skill_set = {
            skill.lower()
            for skill in candidate_skills
        }

        matched_count = sum(
            1
            for skill in required_skills
            if skill.lower() in candidate_skill_set
        )

        return (
            matched_count
            / len(required_skills)
        ) * 100

    @staticmethod
    def _calculate_experience_score(
        candidate_experience: float,
        required_experience: float,
    ) -> float:
        """
        Calculate experience fit.

        A candidate meeting or exceeding the requirement
        receives 100.

        Candidates below the requirement receive a
        proportional score.
        """

        if required_experience <= 0:
            return 100.0

        if candidate_experience >= required_experience:
            return 100.0

        return (
            candidate_experience
            / required_experience
        ) * 100

    @staticmethod
    def _calculate_education_score(
        candidate_education: List[str],
        required_education: List[str],
    ) -> float:
        """
        Calculate education fit.

        If no education requirement is specified,
        education receives a neutral full score.

        Otherwise, the candidate receives full credit
        if at least one requirement is represented
        in their education profile.
        """

        if not required_education:
            return 100.0

        candidate_education = [
            value.lower()
            for value in candidate_education
        ]

        for requirement in required_education:

            normalized_requirement = requirement.lower()

            if any(
                normalized_requirement in education
                or education in normalized_requirement
                for education in candidate_education
            ):
                return 100.0

        return 0.0

    @staticmethod
    def _recommendation(
        overall_score: float,
    ) -> str:
        """
        Convert the overall score into a recruitment
        recommendation.
        """

        if overall_score >= 85:
            return "Strong Match"

        if overall_score >= 70:
            return "Good Match"

        if overall_score >= 50:
            return "Potential Match"

        return "Low Match"