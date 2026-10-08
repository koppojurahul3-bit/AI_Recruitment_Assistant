from typing import Any, Dict, List, Optional, TypedDict


class RecruitmentState(TypedDict, total=False):
    """
    Shared state passed between recruitment agents.
    """

    recruiter_goal: str
    job_description: str
    job_requirements: List[str]

    candidate_ids: List[str]
    candidates: List[Dict[str, Any]]
    evaluations: List[Dict[str, Any]]
    rankings: List[Dict[str, Any]]

    requested_actions: List[Dict[str, Any]]
    approved_actions: List[Dict[str, Any]]
    completed_actions: List[Dict[str, Any]]

    requires_approval: bool
    approval_reason: Optional[str]

    final_response: Optional[str]
    current_step: str

    errors: List[str]