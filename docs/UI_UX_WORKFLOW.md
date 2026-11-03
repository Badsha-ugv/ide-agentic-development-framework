# UI/UX Design & Final Visual Prototype

ADF treats the interactive prototype as the final visual specification for frontend
implementation. It is not a wireframe or disposable mockup. The stable workflow stage IDs remain
`ui_ux_design` and `design_review`, so existing runtime state remains compatible.

## Design inputs

The UI/UX agent records one or more methods in `docs/ui-ux/design-inputs.json`:

- `figma_mcp`: an authenticated Figma MCP connection was used to inspect the supplied file or
  frame, including its components, styles, variables, assets, and visual screenshots;
- `generated_prototype`: the agent established a design system and generated the final visual
  direction from approved requirements; and
- `screenshots`: the agent visually inspected references discovered below
  `requirements/screenshots/`.

Methods may be combined. Selecting Figma without recording successful authenticated inspection
blocks completion. An unavailable MCP server or failed authentication must be reported as a
blocker; generated claims cannot substitute for design context.

## Screenshot references

`adt init` creates suggested desktop, mobile, role, and general reference folders. These are
conveniences, not a schema. Any additional nesting is supported. PNG, JPG, JPEG, and WEBP files
are discovered recursively with:

```bash
adt requirements screenshots
```

ADF reads image dimensions, hashes original bytes, records contextual folder hints, writes
`requirements/screenshots/manifest.json`, and maintains immutable copies under the hidden
`requirements/screenshots/.versions/` history. It never modifies or deletes originals. A changed
reference creates a new revision; unchanged references do not.

The generated inventory block in `docs/ui-ux/screenshot-reference-analysis.md` is updated without
overwriting the agent-authored analysis below it. Folder names are only hints. The agent must open
and inspect the images, record visual patterns and missing screens, and trace references to
generated pages.

Requirements ingestion also synchronizes screenshot references. Preparing `ui_ux_design` or
`design_review` performs the same synchronization, so newly added references enter the current
design cycle automatically.

## Required final-design evidence

The design contract requires:

- a page and role inventory;
- the complete design system;
- screenshot analysis and missing-screen decisions;
- the high-fidelity interactive prototype;
- at least one immutable prototype version;
- revision history;
- rendered verification screenshots; and
- structured browser evidence in `docs/ui-ux/browser-verification.json`.

Browser evidence must mark the run as passed and list every page with desktop, tablet, and mobile
coverage, passing interactions, and project-relative rendered screenshot paths below
`design-prototype/verification-screenshots/`. `adt stage complete` validates this evidence instead
of accepting file existence alone.

Visible controls must perform meaningful actions. Browser verification covers navigation,
responsive behavior, states, forms, filters, dialogs, and other interactions relevant to the
approved requirements.

## Review, revisions, and frontend handoff

`design_review` presents the complete page inventory, preview instructions, design system,
responsive and interaction evidence, issues, and revision history. It always stops at
`awaiting_approval`. Only explicit `adt approve design_review` advances the workflow.

`adt revise design_review "FEEDBACK"` preserves the reviewed artifact snapshot. The agent updates
affected screens without discarding unrelated approved decisions, creates a new prototype version,
reruns browser verification, registers the new bytes, and submits the same review stage again.

The implementation stage consumes the approved prototype and requires
`docs/reports/frontend-design-traceability.md`. Production frontend work must preserve approved
layouts, components, visual hierarchy, interactions, and responsive behavior, then compare its
rendering with the approved prototype rather than independently redesigning it.
