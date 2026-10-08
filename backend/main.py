from backend.agents.coordinator import CoordinatorAgent
from backend.workflow import RecruitmentWorkflow


def create_recruitment_agent():
    """
    Create the main recruitment coordinator.
    """

    return CoordinatorAgent()


if __name__ == "__main__":

    coordinator = create_recruitment_agent()
    workflow = RecruitmentWorkflow()

    state = coordinator.initialize_state(
        "Find the strongest candidates for an ML Engineer role."
    )

    state = coordinator.run(state)

    print("Recruitment Agent initialized.")
    print("Current step:", state["current_step"])

    print("\nWorkflow steps:")

    for step in workflow.WORKFLOW_STEPS:
        print("-", step)

    print("\nAdvancing workflow...")

    state = workflow.next_step(state)

    print("Current step:", state["current_step"])

    state = workflow.next_step(state)

    print("Current step:", state["current_step"])

    print("\nWorkflow foundation is working.")