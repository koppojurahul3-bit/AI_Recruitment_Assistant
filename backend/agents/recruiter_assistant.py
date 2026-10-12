
"""Recruiter assistant agent backed by grounded resume retrieval."""

from typing import Any, Dict, Optional

from backend.repositories.candidate_repository import CandidateRepository
from backend.services.recruiter_rag_service import RecruiterRAGService


class RecruiterAssistantAgent:
    """Answer recruiter questions using retrieved candidate evidence."""

    def __init__(
        self,
        candidate_repository: Optional[CandidateRepository] = None,
        rag_service: Optional[RecruiterRAGService] = None,
    ) -> None:
        self.name = "RecruiterAssistantAgent"

        if rag_service is not None:
            self.rag_service = rag_service
        else:
            self.rag_service = RecruiterRAGService(
                candidate_repository=candidate_repository,
            )

    def answer_question(
        self,
        question: str,
        top_k: int = RecruiterRAGService.DEFAULT_TOP_K,
    ) -> Dict[str, Any]:
        """Return an answer and its supporting candidate citations."""
        return self.rag_service.answer_question(
            question=question,
            top_k=top_k,
        )

    def retrieve_evidence(
        self,
        question: str,
        top_k: int = RecruiterRAGService.DEFAULT_TOP_K,
    ) -> list[Dict[str, Any]]:
        """Return retrieved evidence without composing an answer."""
        return [
            evidence.to_dict()
            for evidence in self.rag_service.retrieve(
                question=question,
                top_k=top_k,
            )
        ]
