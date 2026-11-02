"""Requirement-ID extraction and initial traceability records."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

_REQUIREMENT_HEADING = re.compile(r"(?m)^\s*(REQ-\d+)\b[^\n]*")


@dataclass(frozen=True, slots=True)
class RequirementRecord:
    """One identified requirement and its source location."""

    requirement_id: str
    source: str
    text: str

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()


def extract_requirement_records(
    extracted_sources: dict[str, str],
) -> tuple[dict[str, RequirementRecord], tuple[str, ...]]:
    """Extract requirement blocks and report duplicate IDs with conflicting text."""

    records: dict[str, RequirementRecord] = {}
    conflicts: set[str] = set()
    for source, text in sorted(extracted_sources.items()):
        matches = list(_REQUIREMENT_HEADING.finditer(text))
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            block = text[match.start() : end].strip().splitlines()
            normalized = "\n".join(line.rstrip() for line in block)
            requirement_id = match.group(1).upper()
            record = RequirementRecord(requirement_id, source, normalized)
            existing = records.get(requirement_id)
            if existing is None:
                records[requirement_id] = record
            elif existing.text != record.text:
                conflicts.add(requirement_id)
    return records, tuple(sorted(conflicts))


def traceability_document(records: dict[str, RequirementRecord]) -> dict[str, object]:
    """Create the initial traceability shape extended by later workflow phases."""

    return {
        "schema_version": 1,
        "requirements": [
            {
                "id": record.requirement_id,
                "source": record.source,
                "text_sha256": record.sha256,
                "srs_sections": [],
                "architecture_components": [],
                "tasks": [],
                "tests": [],
            }
            for record in sorted(records.values(), key=lambda item: item.requirement_id)
        ],
    }
