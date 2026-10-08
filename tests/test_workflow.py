from backend.agents.coordinator import CoordinatorAgent
from backend.workflow import RecruitmentWorkflow


def test_workflow_starts_with_planning():
    coordinator = CoordinatorAgent()

    state = coordinator.initialize_state(
        "Find ML Engineer candidates."
    )

    state = coordinator.run(state)

    assert state["current_step"] == "planning"


def test_workflow_moves_to_next_step():
    coordinator = CoordinatorAgent()
    workflow = RecruitmentWorkflow()

    state = coordinator.initialize_state(
        "Find ML Engineer candidates."
    )

    state = coordinator.run(state)

    state = workflow.next_step(state)

    assert state["current_step"] == "job_analysis"


def test_workflow_can_move_to_specific_step():
    coordinator = CoordinatorAgent()
    workflow = RecruitmentWorkflow()

    state = coordinator.initialize_state(
        "Find ML Engineer candidates."
    )

    state = workflow.move_to(
        state,
        "candidate_ranking"
    )

    assert state["current_step"] == "candidate_ranking"


def test_invalid_workflow_step_is_rejected():
    coordinator = CoordinatorAgent()
    workflow = RecruitmentWorkflow()

    state = coordinator.initialize_state(
        "Find ML Engineer candidates."
    )

    try:
        workflow.move_to(
            state,
            "invalid_step"
        )
        assert False
    except ValueError:
        assert True


def test_workflow_can_complete():
    coordinator = CoordinatorAgent()
    workflow = RecruitmentWorkflow()

    state = coordinator.initialize_state(
        "Find ML Engineer candidates."
    )

    state = workflow.complete(state)

    assert state["current_step"] == "completed"