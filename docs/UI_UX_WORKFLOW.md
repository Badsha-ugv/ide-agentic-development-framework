# Frontend-first visual workflow

ADF builds the real production frontend before backend implementation. There is no disposable
design-prototype phase and no later frontend rebuild. The stable stage IDs remain `ui_ux_design`
and `design_review` so existing project state stays compatible, but they now mean complete frontend
implementation and production-frontend review.

## Three design-input modes

The frontend agent records one or more methods in `docs/frontend/design-inputs.json`:

- `figma_mcp`: a Figma URL was supplied in the requirements and inspected through an authenticated
  integration, including components, styles, variables, assets, interactions, and rendered context;
- `screenshots`: the agent opened and inspected references anywhere below
  `requirements/screenshots/`; and
- `generated_frontend`: no external design was supplied, so the agent created a cohesive modern
  visual system directly in the production frontend.

Methods may be combined. Figma claims require the original HTTPS URL, its source requirement, and
successful authenticated inspection. If access fails, the stage records a blocker. Metadata alone
never counts as visual inspection.

## Environment first

Before writing UI code, the agent inspects the architecture and existing project, identifies the
frontend root, framework, language, styling system, package manager, runtime, and commands, installs
the required dependencies, and proves the environment can produce a production build. The result is
recorded in `docs/frontend/technology-and-environment.md` and
`docs/frontend/implementation-manifest.json`.

Frontend and backend remain separate. The frontend uses typed mock data or an adapter boundary until
the integration stage; it does not wait for, implement, or directly couple itself to unfinished
backend code.

## Production frontend quality bar

The stage implements every approved page, role, journey, responsive layout, and relevant loading,
empty, success, validation, and error state. It uses reusable components and tokens, meaningful
information hierarchy, deliberate typography and spacing, coherent color and depth, realistic
content, restrained purposeful motion, and fast perceived performance.

Every visible control must work. Semantic HTML, keyboard operation, visible focus, contrast,
reduced-motion behavior, clear feedback, and responsive desktop/tablet/mobile layouts are required.
Generic template screens, placeholder controls, inconsistent one-off styling, and decorative actions
do not satisfy the stage.

When Figma or screenshots are supplied, “same” means visually faithful implementation of layout,
dimensions, spacing, typography, colors, assets, states, and interactions, allowing only necessary
responsive adaptation. Any difference must be an explicitly approved revision or a documented
technical constraint—never a silent simplification. A later revision may intentionally change the
reference decision while preserving unrelated approved work.

## Evidence and approval

`adt requirements screenshots` recursively catalogs supported images, preserves immutable revisions,
and updates `docs/ui-ux/screenshot-reference-analysis.md` without changing originals.

The frontend stage also requires a page inventory, design system, source-file manifest, reference
comparison, revision history, rendered verification screenshots, and structured browser evidence in
`docs/frontend/browser-verification.json`. Validation checks:

- the documented environment and production build passed;
- listed source files exist below the frontend root and are registered with current hashes;
- every page passed desktop, tablet, and mobile checks;
- interactions and accessibility checks passed and UI states were exercised;
- browser console errors and unapproved reference deviations are empty; and
- verification images exist below `docs/frontend/verification-screenshots/`.

`design_review` presents the actual production frontend and always stops for explicit approval.
`adt revise design_review "FEEDBACK"` preserves the reviewed snapshot, applies the requested changes
to production code, updates the revision evidence, and reruns verification. Only
`adt approve design_review` permits backend planning and implementation.

After approval, ADF plans and builds the backend without redesigning the frontend. The following
integration stage replaces mocks through the frontend adapter boundary and verifies API contracts,
authentication, validation, and loading/empty/success/error behavior end to end.
