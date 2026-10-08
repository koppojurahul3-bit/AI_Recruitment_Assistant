from backend.models.state import RecruitmentState
from backend.workflow import RecruitmentWorkflow


class CoordinatorAgent:
    """
    Main agent responsible for coordinating the recruitment workflow.
    """

    def __init__(self):
        self.name = "CoordinatorAgent"
        self.workflow = RecruitmentWorkflow()

    def initialize_state(
        self,
        recruiter_goal: str
    ) -> RecruitmentState:

        return {
            "recruiter_goal": recruiter_goal,
            "job_description": "",
            "job_requirements": [],
            "candidate_ids": [],
            "candidates": [],
            "evaluations": [],
            "rankings": [],
            "requested_actions": [],
            "approved_actions": [],
            "completed_actions": [],
            "requires_approval": False,
            "approval_reason": None,
            "final_response": None,
            "current_step": "initialized",
            "errors": []
        }

    def run(
        self,
        state: RecruitmentState
    ) -> RecruitmentState:
        """
        Start the recruitment workflow.
        """

        state = self.workflow.start(state)

        return state