---
name: agentic-commands
description: Interpret ADF workflow commands such as /start, /status, /pause, /resume, /continue, /stop, /review, /approve, /revise, /requirements, and /tasks in an initialized project.
---

# ADF command interpretation

When the user sends an ADF slash command, run the matching `adt` command from the project root so
the operation is persisted outside the conversation. Show the command result without claiming
work occurred that the CLI did not record.

Use these mappings:

- `/start`, `/status`, `/pause`, `/resume`, `/continue`, `/stop`, `/review`, `/requirements`, and
  `/tasks` map directly to the same `adt` subcommand.
- `/approve <stage>` maps to `adt approve <stage>`.
- `/revise <stage> <feedback>` maps to `adt revise <stage> <feedback>`.
- `/help` maps to `adt help`.

Do not advance through an approval gate without an explicit recorded approval. If the CLI reports
invalid state or checkpoint corruption, stop and present that error rather than reconstructing or
overwriting state from conversation memory.
