# Stage execution guide

Every initialized project receives `.agentic/execution-contracts.yaml`. Each contract contains a
stage ID and name, objective, prerequisites, required inputs, specialist role, responsibilities,
instructions, expected outputs, validation criteria, completion conditions, approval requirement,
failure behavior, and retry limit.

## IDE-agent loop

For `/start`, `/continue`, and `/adf-resume`, the agent must:

1. inspect `adt status` and prepare the current stage;
2. select that stage from `.agentic/execution-contracts.yaml`;
3. read all available required inputs and relevant source;
4. perform the responsibilities without fabricating missing facts;
5. ask questions and persist an actionable blocker when material information is absent;
6. create every expected output and run its validation criteria;
7. register every output's current bytes;
8. complete the stage, or record a failure/blocker; and
9. summarize artifacts, checks, state, and next user action.

Project discovery produces:

- `docs/discovery/project-overview.md`
- `docs/discovery/stakeholder-analysis.md`
- `docs/discovery/clarification-log.md`
- `docs/discovery/assumptions-and-risks.md`

Facts, assumptions, risks, and open questions must remain distinct. Missing product decisions go
into the clarification log; the agent must not invent answers. Requirements stages then create
stable IDs, acceptance criteria, traceability, and the SRS before the requirements approval gate.

Later contracts cover architecture; environment setup and complete production-frontend delivery
from Figma, screenshots, or a generated direction; frontend review; backend planning and
implementation; API integration; testing; review; delivery validation; documentation; and release
review. Frontend completion requires registered production sources plus structured build and browser
evidence for every page, interaction, state, and viewport. `design_review` cannot advance without
explicit approval, and backend work cannot begin early. The contract file—not conversational
memory—is the durable definition of the next work.
