from typing import List, Optional

from backend.agents.coordinator import CoordinatorAgent
from backend.agents.evaluation import CandidateEvaluationAgent
from backend.agents.retrieval import ResumeRetrievalAgent
from backend.models.state import RecruitmentState
from backend.repositories.candidate_repository import CandidateRepository
from backend.workflow import RecruitmentWorkflow


class RecruitmentOrchestrator:
    """
    Orchestrates the recruitment workflow by connecting the
    coordinator, retrieval agent, and evaluation agent.

    Responsibilities:
    1. Initialize recruitment state.
    2. Start the recruitment workflow.
    3. Retrieve relevant candidates.
    4. Evaluate retrieved candidates.
    5. Produce the final recruitment state.
    """

    def __init__(
        self,
        candidate_repository: Optional[CandidateRepository] = None,
    ):
        self.name = "RecruitmentOrchestrator"

        self.candidate_repository = (
            candidate_repository
            if candidate_repository is not None
            else CandidateRepository()
        )

        self.coordinator = CoordinatorAgent()

        self.workflow = RecruitmentWorkflow()

        self.retrieval_agent = ResumeRetrievalAgent(
            candidate_repository=self.candidate_repository
        )

        self.evaluation_agent = CandidateEvaluationAgent(
            candidate_repository=self.candidate_repository
        )

    def initialize(
        self,
        recruiter_goal: str,
        job_description: str,
    ) -> RecruitmentState:
        """
        Create the initial recruitment state.
        """

        if not isinstance(recruiter_goal, str):
            raise TypeError("Recruiter goal must be a string.")

        if not recruiter_goal.strip():
            raise ValueError("Recruiter goal cannot be empty.")

        if not isinstance(job_description, str):
            raise TypeError("Job description must be a string.")

        if not job_description.strip():
            raise ValueError("Job description cannot be empty.")

        state = self.coordinator.initialize_state(
            recruiter_goal.strip()
        )

        state["job_description"] = job_description.strip()

        return state

    def run(
        self,
        state: RecruitmentState,
        skills: Optional[List[str]] = None,
        minimum_experience_years: Optional[float] = None,
    ) -> RecruitmentState:
        """
        Execute the recruitment workflow.

        Flow:

        Coordinator
            ↓
        Candidate Retrieval
            ↓
        Candidate Evaluation
            ↓
        Candidate Ranking
            ↓
        Completed
        """

        try:
            state = self.coordinator.run(state)

            state = self.workflow.start(state)

            state = self.retrieval_agent.retrieve(
                state=state,
                skills=skills,
                minimum_experience_years=minimum_experience_years,
            )

            if state.get("current_step") == "candidate_search_failed":
                return state

            if not state.get("candidate_ids"):
                state["current_step"] = "candidate_search_failed"
                state["errors"] = state.get("errors", [])
                state["errors"].append(
                    "No candidates matched the retrieval criteria."
                )
                return state

            state = self.evaluation_agent.evaluate(
                state
            )

            if state.get("current_step") == "candidate_evaluation_failed":
                return state

            state = self.workflow.complete(state)

            return state

        except Exception as exc:
            state["errors"] = state.get("errors", [])
            state["errors"].append(str(exc))
            state["current_step"] = "orchestration_failed"

            return state