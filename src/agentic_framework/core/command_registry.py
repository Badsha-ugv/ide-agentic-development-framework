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
}
