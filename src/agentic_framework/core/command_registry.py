"""Central registry for chat and CLI command compatibility."""

COMMANDS = {
    "start": "Start or initialize the project workflow",
    "status": "Display persisted workflow status",
    "pause": "Pause safely and create a checkpoint",
    "resume": "Validate recovery state and resume",
    "continue": "Advance to the next eligible workflow stage",
    "stop": "Stop safely and create a checkpoint",
    "help": "Show available framework commands",
    "review": "Show deliverables waiting for approval",
    "approve": "Approve a workflow stage",
    "revise": "Record revision feedback for a stage",
    "requirements": "Show the latest requirements version",
    "tasks": "Display persisted tasks",
}
