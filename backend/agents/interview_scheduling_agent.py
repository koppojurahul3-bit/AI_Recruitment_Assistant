
"""Agent interface for interview scheduling and communication drafts."""

from typing import Any, Dict, List, Optional

from backend.services.interview_scheduling_service import (
    InterviewSchedulingService,
)


class InterviewSchedulingAgent:
    """Coordinate interview records, lifecycle changes, and draft messages."""

    def __init__(
        self,
        service: Optional[InterviewSchedulingService] = None,
    ) -> None:
        self.name = "InterviewSchedulingAgent"
        self.service = (
            service if service is not None
            else InterviewSchedulingService()
        )

    def schedule_interview(self, **kwargs: Any) -> Dict[str, Any]:
        return self.service.schedule_interview(**kwargs)

    def get_interview(self, interview_id: str) -> Optional[Dict[str, Any]]:
        return self.service.get_interview(interview_id)

    def list_interviews(
        self,
        candidate_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        return self.service.list_interviews(candidate_id, status)

    def confirm_interview(
        self, interview_id: str, actor: str = "Recruiter"
    ) -> Dict[str, Any]:
        return self.service.confirm_interview(interview_id, actor)

    def cancel_interview(
        self, interview_id: str, actor: str = "Recruiter"
    ) -> Dict[str, Any]:
        return self.service.cancel_interview(interview_id, actor)

    def complete_interview(
        self, interview_id: str, actor: str = "Recruiter"
    ) -> Dict[str, Any]:
        return self.service.complete_interview(interview_id, actor)

    def reschedule_interview(self, interview_id: str, **kwargs: Any) -> Dict[str, Any]:
        return self.service.reschedule_interview(interview_id, **kwargs)

    def draft_communication(
        self,
        interview_id: str,
        communication_type: str,
        sender_name: str = "Recruitment Team",
    ) -> Dict[str, Any]:
        return self.service.draft_communication(
            interview_id,
            communication_type,
            sender_name=sender_name,
        )

    def get_audit_history(self, interview_id: str) -> List[Dict[str, Any]]:
        return self.service.get_audit_history(interview_id)

    def list_communications(self, interview_id: str) -> List[Dict[str, Any]]:
        return self.service.list_communications(interview_id)
