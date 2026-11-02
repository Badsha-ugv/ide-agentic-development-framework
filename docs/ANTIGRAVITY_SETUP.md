# Antigravity setup

Run these commands in the target project:

```bash
adt init
adt requirements ingest
```

Then open the project root in Antigravity. ADF generates:

- root `AGENTS.md` project guidance;
- `.agents/rules/adf.md` command interpretation rules;
- `.agents/skills/<command>/SKILL.md` files that register commands such as `/continue`;
- `.agents/skills/agentic-commands/SKILL.md` with the shared execution loop;
- `.agents/skills/adf/SKILL.md` for state-aware custom requests;
- `.agents/skills/adf-resume/SKILL.md` for ADF checkpoint recovery; and
- `.agentic/execution-contracts.yaml` with stage-specific responsibilities and outputs.

Start a new conversation and type `/continue`. Antigravity should interpret it as an ADF request,
run `adt start` when the workflow is not active or `adt continue` when it is active, execute the
reported stage, and persist its artifacts. ADF does not install a proprietary slash-command
extension. Modern Antigravity directly indexes workspace skills and invokes a skill named
`continue` as `/continue`. Legacy `.agents/workflows/` files are intentionally not generated,
because Antigravity stopped indexing them on October 19, 2026.

Running `adt continue` in an ordinary terminal does **not** call the Antigravity model. It only
prepares and persists the current stage. Invoking `/continue` in Antigravity loads the generated
skill, so the IDE agent calls the CLI, reads the contract, reasons about the project, writes and
registers artifacts, and completes or blocks the stage.

For an ad hoc request tied to durable state, type `/adf <request>`. To add a reusable custom slash
command:

```bash
adt command create verify-api "Run API verification relevant to the current stage"
```

Antigravity then exposes `/verify-api`. The wrapper always reads status and the current contract,
persists its task with `adt stage task`, and refuses to skip prerequisites or approval gates.
Existing skill files are preserved and cannot be overwritten by this command.

Antigravity already owns `/resume` for conversation recovery. Use `/adf-resume` when you mean ADF
checkpoint recovery.

If the agent only prints CLI state, ask it to re-read the generated `agentic-commands` skill and
execution contract. Confirm the installed framework version contains the current skill, then rerun
`adt init`. Existing customized generated files are never overwritten; inspect corresponding
`.agentic/proposals/**/*.proposed` files and merge the update deliberately.

After creating or upgrading skills, reopen the project or start a new Antigravity chat if the
slash-command autocomplete has not refreshed.

Use `adt status`, `adt artifact list`, and `adt stage show` to verify durable state independently of
the IDE conversation.

References: [Antigravity workflows-to-skills migration](https://antigravity.google/docs/migration/workflows-to-skills/)
and [Antigravity workflow documentation](https://antigravity.google/docs/ide/workflows/).
