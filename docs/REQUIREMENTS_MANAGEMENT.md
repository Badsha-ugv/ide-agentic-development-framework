# Requirements management

## Workflow

1. Add source files to `requirements/inbox/`. Nested folders are supported.
2. Run `adt requirements ingest` from the project root.
3. Review the new immutable directory under `requirements/versions/`.
4. For version 002 and later, review the generated report under `requirements/reports/` before
   changing approved project decisions.

The inbox is never cleared, moved, or rewritten by ADF. To represent a removal in a later version,
the user removes the file from the inbox before ingesting again. Prior source copies remain in
their published version.

## Version contents

Every published version contains:

- `source-files/`: byte-for-byte copies retaining inbox-relative paths;
- `manifest.json`: source hashes, sizes, media types, extraction results, lineage, and conflicts;
- `requirements.md`: consolidated extracted text and extraction diagnostics;
- `requirements-index.json`: parsed `REQ-NNN` blocks and text hashes; and
- `traceability.json`: stable requirement IDs with extension points for SRS sections,
  architecture components, tasks, and tests.

Publication is staged in the versions directory and atomically renamed into place. A process lock
prevents concurrent ingestion. Existing version manifests and source hashes are validated before
comparison or duplicate detection. A mismatch stops processing and reports that immutable history
was modified.

“Immutable” is an application-level guarantee: ADF never changes a published version and detects
source-copy changes. Filesystem administrators can still alter files, so repositories should also
use normal access controls and Git history.

## Comparison and impact

Each non-duplicate submission after the first is compared with its immediate predecessor by
relative source path and SHA-256 hash. Requirement blocks beginning with `REQ-NNN` are compared by
normalized text hash. Reports list added, modified, removed, and unchanged source files and IDs.

If the same requirement ID occurs with different text in multiple current sources, the manifest
and impact report mark it as a conflict requiring resolution. The first source in deterministic
path order supplies the indexed text until the conflict is resolved.

Impact reports identify the changed requirement IDs and require review of documentation,
architecture, implementation tasks, tests, and approvals. Concrete dependency links will become
richer as workflow and persistence phases add approved project artifacts.

## Extraction support

UTF-8 Markdown, TXT, CSV, TSV, JSON, YAML, and reStructuredText sources are extracted directly.
An optional UTF-8 byte-order mark is accepted. Decode failures are recorded without losing the
original bytes.

Other formats are copied and hashed but marked unsupported for text extraction. This includes
PDF, DOCX, XLSX, and images until optional, format-specific extractors are introduced. Unsupported
extraction never prevents source preservation or version publication.

Symbolic links are rejected so ingestion cannot copy files from outside the explicitly managed
inbox.
