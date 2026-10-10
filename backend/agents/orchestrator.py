
"""Coordinate recruitment agents through a traceable workflow."""

from typing import Any, Dict, List, Optional

from backend.agents.coordinator import CoordinatorAgent
from backend.agents.evaluation import CandidateEvaluationAgent
from backend.agents.retrieval import ResumeRetrievalAgent
from backend.models.state import RecruitmentState
from backend.repositories.candidate_repository import CandidateRepository
from backend.workflow import RecruitmentWorkflow


class RecruitmentOrchestrator:
    """Coordinate candidate retrieval and evaluation."""

    def __init__(
        self,
        candidate_repository: Optional[CandidateRepository] = None,
        coordinator: Optional[Any] = None,
        retrieval_agent: Optional[Any] = None,
        evaluation_agent: Optional[Any] = None,
        workflow: Optional[RecruitmentWorkflow] = None,
    ) -> None:
        self.name = "RecruitmentOrchestrator"

        self.candidate_repository = (
            candidate_repository
            if candidate_repository is not None
            else CandidateRepository()
        )

        self.coordinator = (
            coordinator if coordinator is not None else CoordinatorAgent()
        )
        self.workflow = (
            workflow if workflow is not None else RecruitmentWorkflow()
        )
        self.retrieval_agent = (
            retrieval_agent
            if retrieval_agent is not None
            else ResumeRetrievalAgent(
                candidate_repository=self.candidate_repository
            )
        )
        self.evaluation_agent = (
            evaluation_agent
            if evaluation_agent is not None
            else CandidateEvaluationAgent(
                candidate_repository=self.candidate_repository
            )
        )

        for name, agent in (
            ("retrieval", self.retrieval_agent),
            ("evaluation", self.evaluation_agent),
        ):
            agent_repository = getattr(agent, "candidate_repository", None)

            if (
                agent_repository is not None
                and agent_repository is not self.candidate_repository
            ):
                raise ValueError(
                    f"The {name} agent must use the orchestrator's "
                    "candidate repository."
                )

    def initialize(
        self,
        recruiter_goal: str,
        job_description: str,
    ) -> RecruitmentState:
        """Create and validate the initial recruitment state."""

        if not isinstance(recruiter_goal, str):
            raise TypeError("Recruiter goal must be a string.")

        if not recruiter_goal.strip():
            raise ValueError("Recruiter goal cannot be empty.")

        if not isinstance(job_description, str):
            raise TypeError("Job description must be a string.")

        if not job_description.strip():
            raise ValueError("Job description cannot be empty.")

        state = self.coordinator.initialize_state(recruiter_goal.strip())
        state["job_description"] = job_description.strip()
        state.setdefault("errors", [])
        state.setdefault("agent_trace", [])

        return state

    @staticmethod
    def _record(
        state: RecruitmentState,
        agent: str,
        status: str,
        detail: Optional[str] = None,
    ) -> None:
        """Append an agent lifecycle event to the shared state."""

        trace = state.setdefault("agent_trace", [])
        event: Dict[str, str] = {
            "agent": agent,
            "status": status,
        }

        if detail:
            event["detail"] = detail

        trace.append(event)

    def run(
        self,
        state: RecruitmentState,
        skills: Optional[List[str]] = None,
        minimum_experience_years: Optional[float] = None,
    ) -> RecruitmentState:
        """Execute the agents in sequence and record their outcomes."""

        state.setdefault("errors", [])
        state.setdefault("agent_trace", [])

        try:
            self._record(state, "coordinator", "started")
            state = self.coordinator.run(state)
            self._record(state, "coordinator", "completed")

            state = self.workflow.start(state)

            self._record(state, "retrieval", "started")
            state = self.retrieval_agent.retrieve(
                state=state,
                skills=skills,
                minimum_experience_years=minimum_experience_years,
            )

            if state.get("current_step") == "candidate_search_failed":
                self._record(
                    state,
                    "retrieval",
                    "failed",
                    "Candidate retrieval failed.",
                )
                return state

            if not state.get("candidate_ids"):
                state["current_step"] = "candidate_search_failed"
                message = "No candidates matched the retrieval criteria."

                if message not in state["errors"]:
                    state["errors"].append(message)

                self._record(state, "retrieval", "failed", message)
                return state

            self._record(state, "retrieval", "completed")

            self._record(state, "evaluation", "started")
            state = self.evaluation_agent.evaluate(state)

            if state.get("current_step") == "candidate_evaluation_failed":
                self._record(
                    state,
                    "evaluation",
                    "failed",
                    "Candidate evaluation failed.",
                )
                return state

            if state.get("errors") and not state.get("rankings"):
                self._record(
                    state,
                    "evaluation",
                    "failed",
                    "Evaluation produced no rankings.",
                )
                return state

            self._record(state, "evaluation", "completed")
            state = self.workflow.complete(state)

            return state

        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"

            if message not in state["errors"]:
                state["errors"].append(message)

            state["current_step"] = "orchestration_failed"
            self._record(state, "orchestrator", "failed", message)

            return state
