from backend.agents.coordinator import CoordinatorAgent


def create_recruitment_agent():
    """
    Create the main recruitment coordinator.
    """

    return CoordinatorAgent()


if __name__ == "__main__":

    coordinator = create_recruitment_agent()

    state = coordinator.initialize_state(
        "Find the strongest candidates for an ML Engineer role."
    )

    state = coordinator.run(state)

    print("Recruitment Agent initialized.")
    print("Current step:", state["current_step"])