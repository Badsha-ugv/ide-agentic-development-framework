"""Central registry for chat and CLI command compatibility."""

COMMANDS = {
    "start": "Start the workflow and prepare the current stage for IDE-agent execution",
    "status": "Display persisted workflow status",
    "pause": "Pause safely and create a checkpoint",
    "resume": "Validate recovery state and resume the current stage",
    "continue": "Prepare or resume the current stage without advancing it",
    "stop": "Stop safely and create a checkpoint",
    "help": "Show available framework commands",
    "review": "Show deliverables waiting for approval",
    "approve": "Approve a workflow stage",
    "revise": "Record revision feedback for a stage",
    "requirements": "Show the latest requirements version",
    "tasks": "Display persisted tasks",
    "analyze": "Inspect the project structure, stack, and completed domains",
    "plan": "Display the dynamic workflow route and task complexity plan",
    "test": "Inspect verification criteria and test readiness for the current stage",
    "docs": "List documentation deliverables and templates for the current stage",
    "agents": "List specialized agents and their instruction files",
    "design": "Modify or iterate on the application design (Figma or frontend)",
    "preferences": "View or update saved user and project design preferences",
}
