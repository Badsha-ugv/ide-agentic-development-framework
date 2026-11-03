# ADF Improvement: Production-Quality UI/UX Design & Final Visual Prototype System

## Objective

Redesign the UI/UX stage of the Agentic Development Framework (ADF).

The current UI/UX stage produces low-quality, overly minimal HTML prototypes that do not meet professional product-design standards.

The fundamental problem is that ADF currently treats the HTML prototype as a preliminary design concept.

This must change.

**The HTML/CSS/Tailwind prototype must be treated as the actual final visual design of the application.**

It is not a wireframe, disposable mockup, or temporary demonstration. It is the visual specification that the frontend implementation must faithfully reproduce.

ADF must support three design-input methods:

1. Figma design through MCP.
2. AI-generated HTML/CSS/Tailwind prototype.
3. User-provided screenshot references.

These methods must work independently or together.

---

# 1. Redefine the UI/UX Stage

Rename or redefine the existing stage as:

**UI/UX Design & Final Visual Prototype**

Its responsibility is to produce a complete, professional, high-fidelity and interactive application interface.

Expected deliverables:

- Complete application page layouts.
- All required user-role interfaces.
- Consistent design system.
- Responsive desktop, tablet and mobile layouts.
- Interactive components and navigation.
- Realistic sample data.
- Loading, empty, success and error states where relevant.
- Reusable frontend components.
- Browser-tested visual implementation.
- Design documentation and page inventory.

The prototype must be suitable for direct translation into the production frontend.

Do not consider the stage complete merely because HTML files have been generated.

---

# 2. Support Three Design-Input Methods

## Option A: Figma + MCP

Allow users to provide a Figma file or frame URL.

The Figma integration should:

- Connect through an available Figma MCP server.
- Retrieve the selected design context.
- Inspect frames, components, styles, variables and assets.
- Retrieve screenshots of the design as visual targets.
- Identify reusable components and design tokens.
- Implement the design in the project's frontend stack.
- Preserve the original design's visual structure and assets.

The implementation agent must follow Figma-specific design-to-code instructions and reuse suitable existing project components.

If Figma MCP is unavailable or authentication fails, report the issue clearly. Do not pretend to have inspected the design.

## Option B: Generate the Final HTML/Tailwind Prototype

This is the default design-generation method when no external design source is supplied.

Technology:

- HTML
- CSS
- Tailwind CSS
- JavaScript
- Appropriate UI libraries where beneficial

Requirements:

- Generate the complete application interface.
- Design every required page and user role.
- Establish a consistent design system before creating individual pages.
- Implement actual interactions, not decorative controls.
- Make the prototype responsive.
- Organize code into reusable components and layouts.
- Use realistic content and data.

The resulting prototype becomes the final visual reference for frontend implementation.

## Option C: Screenshot-Based Design References

Allow users to provide screenshots of existing websites, dashboards, mobile applications or individual interface components.

Screenshots must be treated as design references from which the AI reconstructs the visual system.

The agent should analyze:

- Page structure and layout.
- Section hierarchy.
- Navigation and sidebar.
- Typography and font hierarchy.
- Colors and contrast.
- Spacing and alignment.
- Card, table, form and button styles.
- Icons and visual assets.
- Desktop/mobile differences.
- Repeated component patterns.

Support multiple screenshots and multiple reference states.

The agent must identify missing design information and complete the missing pages intelligently using the available references and approved project requirements.

It must not blindly copy a screenshot into every page.

---

# 3. Screenshot Reference Folder System

Create a structured screenshot-reference directory inside the project's `requirements/` folder.

## Default folder structure

```text
requirements/
├── inbox/
│
├── screenshots/
│   ├── desktop/
│   │   ├── homepage/
│   │   ├── dashboard/
│   │   └── other/
│   │
│   ├── mobile/
│   │   ├── homepage/
│   │   ├── dashboard/
│   │   └── other/
│   │
│   ├── admin-dashboard/
│   ├── vendor-dashboard/
│   ├── customer-dashboard/
│   │
│   └── references/
│
└── versions/
```

This is a suggested initial structure, not a rigid schema.

Users must be able to create additional folders and nested directories freely.

The agent must recursively discover images regardless of their folder depth.

## Supported formats

- PNG
- JPG
- JPEG
- WEBP

## Screenshot ingestion

During requirements ingestion and UI/UX preparation:

1. Recursively scan `requirements/screenshots/`.
2. Discover supported image files.
3. Preserve original files without modification.
4. Record relative paths, file names and image dimensions.
5. Identify folder names and nested directory names as contextual metadata.
6. Generate or update a screenshot manifest.
7. Make screenshots available to the UI/UX analysis agent.

Do not require users to register screenshots manually.

Folder names are contextual hints, not guaranteed descriptions of image contents. The agent must inspect the actual images.

## Screenshot analysis document

Generate:

`docs/ui-ux/screenshot-reference-analysis.md`

Include:

- Screenshot inventory.
- Original file paths.
- Identified page and user role.
- Desktop/mobile classification.
- Extracted design patterns.
- Reusable component observations.
- Missing page and responsive-state analysis.
- Assumptions and inferred design decisions.
- Links between references and generated pages.

## Completing missing screens

When screenshots cover only part of the application, the agent must:

1. Identify which pages have direct references.
2. Identify which required pages are missing.
3. Analyze common visual patterns across the references.
4. Use approved requirements to understand missing functionality.
5. Reconstruct missing layouts consistently.
6. Adapt layouts for other device sizes.
7. Document important assumptions.
8. Ask questions if a missing design decision materially affects functionality or usability.

Screenshots are design references, not replacements for functional requirements.

Do not assume screenshots reveal hidden interactions.

Never modify or delete original screenshot files.

Preserve references across requirements versioning and revision cycles. Support new screenshots being added during revisions.

---

# 4. Design-System-First Workflow

Before generating the complete prototype, the agent must establish a coherent visual system.

## Step 1: Analyze requirements

Identify:

- All user roles.
- Required pages.
- Navigation hierarchy.
- User journeys.
- Major features.
- Data-heavy interfaces.
- Forms and user interactions.

## Step 2: Analyze design inputs

Inspect available Figma files, screenshots and existing project design assets.

Identify reusable patterns and missing information.

## Step 3: Establish the design system

Define:

- Primary, secondary and neutral colors.
- Typography and font hierarchy.
- Spacing scale.
- Grid and layout rules.
- Border and radius conventions.
- Shadows and elevation.
- Icon style.
- Button variants.
- Input and form styles.
- Cards, tables and navigation components.
- Responsive breakpoints.

## Step 4: Present the design direction

When generating a design from scratch, present the proposed visual direction and design system for human review before generating all pages.

When implementing an existing Figma design, preserve its established design system instead of unnecessarily inventing a new one.

## Step 5: Build the complete prototype

Generate all required pages using the approved design system and the available references.

Maintain consistent components and visual language throughout the application.

---

# 5. Professional Design Quality Standards

The generated interface must resemble a professionally designed commercial product, not a generic AI-generated dashboard.

Required standards:

### Layout and information architecture
- Strong page hierarchy.
- Clear navigation.
- Organized content sections.
- Consistent grid and alignment.
- Appropriate content density.
- Meaningful visual grouping.

### Visual design
- Professional typography.
- Refined color palette.
- Clear visual hierarchy.
- Appropriate contrast.
- Consistent spacing.
- Well-designed surfaces and borders.
- Purposeful use of shadows and elevation.

### Components
- Professional cards.
- Data tables.
- Forms and input controls.
- Charts and analytics.
- Filters and search.
- Modals and dropdowns.
- Notifications and status indicators.
- Pagination and navigation.

### User experience
- Clear interaction feedback.
- Useful empty states.
- Loading indicators.
- Error and validation states.
- Responsive navigation.
- Accessible controls.
- Consistent behavior.

Avoid:

- Excessive whitespace.
- Unnecessary rounded containers.
- Excessive card nesting.
- Arbitrary gradients.
- Generic dashboard templates.
- Decorative elements without purpose.
- Oversimplified page layouts.
- Inconsistent typography or spacing.

Do not interpret professional design as simply adding more colors, shadows or decorative elements. Visual quality must come from good information architecture, composition, consistency and usability.

---

# 6. Interactive Prototype Requirements

The prototype must demonstrate actual interface behavior.

Implement relevant interactions, including:

- Navigation between pages.
- Sidebar collapse and expansion.
- Dropdown menus.
- Tabs.
- Search and filtering.
- Sorting and pagination.
- Modals and dialogs.
- Form validation.
- Toggles and switches.
- Notifications.
- Responsive navigation.
- Relevant dashboard interactions.

Use mock data where backend functionality is not yet available.

Every visible interactive control must have a meaningful behavior. Do not create decorative controls that appear functional but do nothing.

---

# 7. Browser-Based Visual Verification

Visual verification is mandatory.

The agent must:

1. Run the prototype locally.
2. Open it in a browser.
3. Inspect every required page.
4. Capture rendered screenshots.
5. Check layout, spacing, alignment and typography.
6. Verify desktop, tablet and mobile layouts.
7. Test interactive components.
8. Identify visual inconsistencies.
9. Fix defects.
10. Repeat the inspection.

When Figma is the source, compare the rendered implementation against the retrieved Figma screenshot.

When screenshots are the source, compare the implementation against the relevant reference images while respecting the inferred missing sections.

Do not mark the stage complete just because the code builds or the browser opens successfully.

---

# 8. Iterative Revision and Version History

Users must be able to revise the prototype through natural-language conversation or `/revise`.

Example requests:

- Redesign the dashboard layout.
- Make the sidebar more compact.
- Improve the table design.
- Change the color palette.
- Make the cards less rounded.
- Improve mobile responsiveness.
- Add a missing page.
- Follow the newly provided screenshot more closely.

The agent must:

- Understand the specific feedback.
- Identify affected pages and components.
- Preserve unrelated approved design decisions.
- Update affected screens consistently.
- Re-run visual verification.
- Preserve previous prototype versions.
- Maintain revision history.
- Explain what changed.

Do not overwrite the only approved version.

Support multiple revision cycles until the user is satisfied.

---

# 9. Final Human Approval

The complete prototype must be presented for human review.

The review should include:

- Page inventory.
- Prototype preview or local access instructions.
- Design-system documentation.
- Responsive verification summary.
- Interaction verification summary.
- Outstanding issues.
- Revision history.

The user must explicitly approve the final visual prototype.

Do not automatically approve the UI/UX stage.

Do not advance to frontend implementation until approval is recorded.

---

# 10. Frontend Implementation Must Follow the Approved Design

The approved prototype becomes the visual source of truth for frontend development.

During React or another frontend implementation:

- Reuse the approved design system.
- Preserve page layouts and visual hierarchy.
- Reproduce approved components and interactions.
- Reuse appropriate assets.
- Maintain responsive behavior.
- Avoid independently redesigning or simplifying screens.
- Compare actual frontend rendering against the approved prototype.
- Report and fix visual deviations.

The frontend implementation should reproduce the approved visual design while adapting the prototype's structure to the production application's architecture and component system.

---

# 11. ADF Architecture and Compatibility

Before implementing changes, audit the existing ADF architecture.

Update existing:

- UI/UX stage contracts.
- Agent responsibilities.
- Skills and instructions.
- Templates.
- Requirements ingestion.
- Screenshot discovery and manifest generation.
- Artifact management.
- Workflow state and approval handling.
- Revision and version management.
- Validation rules.
- Documentation.
- Automated tests.

Do not create a disconnected second UI/UX workflow.

Preserve compatibility with existing projects and workflow states.

Do not automatically publish a new PyPI version.

Add tests covering:

- Screenshot folder initialization.
- Recursive image discovery.
- Supported image formats.
- Manifest generation.
- Preservation of original files.
- Multiple design-input methods.
- Missing-screen analysis.
- Artifact generation.
- Revision history.
- Approval gates.
- Browser verification requirements.
- Frontend design-reference traceability.

---

# 12. Definition of Done

A fresh ADF project must be able to:

1. Supply an existing Figma design, screenshot references or no external design input.
2. Combine multiple design-input methods.
3. Store screenshots in an organized, flexible folder system inside `requirements/screenshots/`.
4. Automatically discover and analyze the supplied references.
5. Identify missing screens and infer consistent layouts.
6. Establish a professional design system.
7. Generate a complete, high-fidelity and interactive prototype.
8. Verify the actual browser rendering.
9. Support iterative human revisions.
10. Preserve prototype versions and reference traceability.
11. Wait for explicit human approval.
12. Use the approved design as the visual source of truth for frontend development.

**Final principle: ADF must not treat UI/UX as a preliminary design exercise. It must deliver a complete, professionally designed and approved visual product that the frontend implementation faithfully reproduces.**