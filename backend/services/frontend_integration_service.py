
"""Integration layer between the Streamlit UI and recruitment services."""

from hashlib import sha256
from typing import Any, Dict, List, Sequence, Tuple

from backend.repositories.repository_factory import (
    create_candidate_repository,
)
from backend.services.candidate_intake_service import CandidateIntakeService
from backend.services.job_requirement_service import JobRequirementService
from backend.services.matching_service import MatchingService
from backend.services.ranking_service import RankingService


class FrontendIntegrationService:
    """Expose resume intake, matching, and ranking to the frontend."""

    def __init__(
        self,
        storage_backend: str = "sqlite",
        database_path: str = "data/candidates.sqlite3",
    ) -> None:
        self.repository = create_candidate_repository(
            storage_backend=storage_backend,
            database_path=database_path,
        )

        self.intake_service = CandidateIntakeService(
            candidate_repository=self.repository,
        )
        self.job_requirement_service = JobRequirementService()
        self.matching_service = MatchingService()
        self.ranking_service = RankingService()

    def ingest_resumes(
        self,
        uploads: Sequence[Tuple[str, bytes]],
    ) -> List[Any]:
        """Validate and store uploaded PDF resumes."""
        if not uploads:
            raise ValueError("Upload at least one resume.")

        candidates = []
        seen_ids = set()

        for filename, file_bytes in uploads:
            if not isinstance(filename, str) or not filename.strip():
                raise ValueError("Every resume must have a filename.")

            if not isinstance(file_bytes, bytes):
                raise TypeError("Resume content must be bytes.")

            # Stable IDs avoid duplicate insertion when the same file
            # is processed again after a Streamlit rerun.
            digest = sha256(
                filename.strip().lower().encode("utf-8") + b"\0" + file_bytes
            ).hexdigest()
            candidate_id = f"upload-{digest[:24]}"

            if candidate_id in seen_ids:
                continue
            seen_ids.add(candidate_id)

            existing = self.repository.get_by_id(candidate_id)

            if existing is not None:
                candidates.append(existing)
                continue

            candidate = self.intake_service.ingest_pdf(
                filename=filename,
                file_bytes=file_bytes,
                candidate_id=candidate_id,
            )
            candidates.append(candidate)

        if not candidates:
            raise ValueError("No usable resumes were supplied.")

        return candidates

    def analyze_candidates(
        self,
        candidates: Sequence[Any],
        job_description: str,
    ) -> Dict[str, Any]:
        """Match candidates against a job description and rank them."""
        if not isinstance(job_description, str) or not job_description.strip():
            raise ValueError("Job description cannot be empty.")

        if not candidates:
            raise ValueError("At least one candidate is required.")

        requirements = self.job_requirement_service.extract(
            job_description.strip()
        )

        match_results = [
            self.matching_service.match(candidate, requirements)
            for candidate in candidates
        ]

        rankings = self.ranking_service.rank(match_results)
        matches_by_id = {
            result.candidate_id: result for result in match_results
        }

        candidate_by_id = {
            candidate.candidate_id: candidate for candidate in candidates
        }

        results = []

        for ranked in rankings:
            candidate = candidate_by_id[ranked.candidate_id]
            match = matches_by_id[ranked.candidate_id]

            results.append({
                "candidate_id": candidate.candidate_id,
                "name": candidate.name,
                "filename": candidate.source,
                "email": candidate.email,
                "phone": candidate.phone,
                "skills": list(candidate.skills),
                "experience_years": candidate.experience_years,
                "education": list(candidate.education),
                "projects": list(candidate.projects),
                "certifications": list(candidate.certifications),
                "matched_skills": list(match.matched_skills),
                "missing_skills": list(match.missing_skills),
                "skill_match_score": match.skill_match_score,
                "experience_match_score": match.experience_match_score,
                "education_match_score": match.education_match_score,
                "overall_score": match.overall_score,
                "experience_gap": match.experience_gap,
                "recommendation": match.recommendation,
                "rank": ranked.rank,
            })

        return {
            "requirements": {
                "required_skills": list(requirements.required_skills),
                "minimum_experience_years": (
                    requirements.minimum_experience_years
                ),
                "education_requirements": (
                    list(requirements.education_requirements)
                ),
                "categories": list(requirements.categories),
            },
            "results": results,
            "total_candidates": len(results),
        }

    def close(self) -> None:
        """Release repository resources when supported."""
        close = getattr(self.repository, "close", None)
        if callable(close):
            close()
