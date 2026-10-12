
"""Agent interface for interview planning and answer evaluation."""

from typing import Any, Dict, List, Optional

from backend.repositories.candidate_repository import CandidateRepository
from backend.services.interview_service import InterviewService


class InterviewAgent:
    """Generate interview plans and produce structured evaluation reports."""

    def __init__(
        self,
        candidate_repository: Optional[CandidateRepository] = None,
        interview_service: Optional[InterviewService] = None,
    ) -> None:
        self.name = "InterviewAgent"

        if interview_service is not None:
            self.interview_service = interview_service
        else:
            self.interview_service = InterviewService(
                candidate_repository=candidate_repository
            )

    def generate_questions(
        self,
        job_description: str,
        candidate_id: Optional[str] = None,
        question_count: int = InterviewService.DEFAULT_QUESTION_COUNT,
    ) -> Dict[str, Any]:
        """Return a structured interview plan."""
        return self.interview_service.generate_questions(
            job_description=job_description,
            candidate_id=candidate_id,
            question_count=question_count,
        )

    def evaluate_answer(
        self,
        question: Dict[str, Any],
        answer: str,
    ) -> Dict[str, Any]:
        """Evaluate one answer using the configured rubric."""
        return self.interview_service.evaluate_answer(question, answer)

    def evaluate_interview(
        self,
        questions: List[Dict[str, Any]],
        answers: Dict[str, str],
    ) -> Dict[str, Any]:
        """Return a structured report for all submitted answers."""
        return self.interview_service.evaluate_interview(questions, answers)
