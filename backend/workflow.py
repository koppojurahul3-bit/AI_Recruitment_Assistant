from typing import List

from backend.models.state import RecruitmentState


class RecruitmentWorkflow:
    """
    Controls the high-level execution flow of the recruitment platform.
    """

    WORKFLOW_STEPS: List[str] = [
        "initialized",
        "planning",
        "job_analysis",
        "candidate_search",
        "candidate_evaluation",
        "candidate_ranking",
        "action_decision",
        "human_approval",
        "action_execution",
        "verification",
        "completed",
    ]

    def start(
        self,
        state: RecruitmentState
    ) -> RecruitmentState:
        """
        Start the recruitment workflow.
        """

        state["current_step"] = "planning"

        return state

    def move_to(
        self,
        state: RecruitmentState,
        step: str
    ) -> RecruitmentState:
        """
        Move the workflow to a valid step.
        """

        if step not in self.WORKFLOW_STEPS:
            raise ValueError(
                f"Invalid workflow step: {step}"
            )

        state["current_step"] = step

        return state

    def next_step(
        self,
        state: RecruitmentState
    ) -> RecruitmentState:
        """
        Move the workflow to the next defined step.
        """

        current_step = state.get(
            "current_step",
            "initialized"
        )

        try:
            current_index = self.WORKFLOW_STEPS.index(
                current_step
            )
        except ValueError as exc:
            raise ValueError(
                f"Unknown current workflow step: {current_step}"
            ) from exc

        if current_index >= len(self.WORKFLOW_STEPS) - 1:
            state["current_step"] = "completed"
            return state

        state["current_step"] = self.WORKFLOW_STEPS[
            current_index + 1
        ]

        return state

    def requires_human_approval(
        self,
        state: RecruitmentState
    ) -> bool:
        """
        Determine whether the workflow currently requires
        human approval.
        """

        return state.get(
            "requires_approval",
            False
        )

    def complete(
        self,
        state: RecruitmentState
    ) -> RecruitmentState:
        """
        Mark the recruitment workflow as completed.
        """

        state["current_step"] = "completed"

        return state