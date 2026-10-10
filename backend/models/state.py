
"""Typed shared state passed between recruitment agents."""

from typing import Any, Dict, List, Optional, TypedDict


class AgentTraceEvent(TypedDict, total=False):
    """One recorded agent lifecycle event."""

    agent: str
    status: str
    detail: str


class RecruitmentState(TypedDict, total=False):
    """Shared state used throughout the recruitment workflow."""

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

    # Added for Module 3 agent coordination and observability.
    agent_trace: List[AgentTraceEvent]
