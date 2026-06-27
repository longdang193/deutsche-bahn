"""
@meta
# distribution_tier: starter_kit
name: test_validate_template_required_sections
type: test
scope: unit
domain: docs
covers:
  - Template metadata parsing for required-section validation
  - Required section presence and non-empty checks
  - Template/document-type matching using required frontmatter constraints
tags:
  - fast
  - ci-safe
lifecycle:
  status: active
"""

from __future__ import annotations

import importlib.util
import sys
import uuid
from pathlib import Path
from shutil import rmtree

REPO_ROOT = Path(__file__).resolve().parent.parent
VALIDATOR_PATH = REPO_ROOT / "scripts" / "validate_template_required_sections.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_module("validate_template_required_sections", VALIDATOR_PATH)


def make_test_root() -> Path:
    root = REPO_ROOT / ".tmp-tests" / f"validate-template-required-sections-{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    return root


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed_template(root: Path) -> None:
    write_text(
        root / "docs" / "operating_system" / "templates" / "implementation-plan-template.md",
        """---
template_id: implementation-plan
document_type: plan
target_globs:
  - docs/superpowers/plans/*.md
required_sections:
  - Goal
  - Key Deliverables
  - Task/Wave Breakdown
  - Verification
required_frontmatter:
  artifact_type: plan
---

# Implementation Plan Template
""",
    )


def test_missing_required_section_fails() -> None:
    root = make_test_root()
    try:
        seed_template(root)
        write_text(
            root / "docs" / "superpowers" / "plans" / "demo-plan.md",
            """---
artifact_type: plan
template_id: implementation-plan
---

# Demo Plan

## Goal
Ship safely.

## Key Deliverables
- deliverable one

## Verification
- pytest -q
""",
        )
        rules, findings = VALIDATOR.discover_template_rules(root)
        assert findings == []
        issues = VALIDATOR.validate_documents(root, rules, require_template_selection=False)
        assert any(issue.category == "template_section_missing" for issue in issues)
    finally:
        rmtree(root, ignore_errors=True)


def test_empty_goal_and_key_deliverables_fail() -> None:
    root = make_test_root()
    try:
        seed_template(root)
        write_text(
            root / "docs" / "superpowers" / "plans" / "demo-plan.md",
            """---
artifact_type: plan
template_id: implementation-plan
---

# Demo Plan

## Goal
<what this plan must deliver>

## Key Deliverables

## Task/Wave Breakdown
- task 1

## Verification
- pytest -q
""",
        )
        rules, _ = VALIDATOR.discover_template_rules(root)
        issues = VALIDATOR.validate_documents(root, rules, require_template_selection=False)
        categories = {issue.category for issue in issues}
        assert "template_section_empty" in categories
    finally:
        rmtree(root, ignore_errors=True)


def test_document_type_mismatch_fails() -> None:
    root = make_test_root()
    try:
        seed_template(root)
        write_text(
            root / "docs" / "superpowers" / "plans" / "demo-plan.md",
            """---
artifact_type: spec
template_id: implementation-plan
---

# Demo Plan

## Goal
Ship safely.

## Key Deliverables
- deliverable one

## Task/Wave Breakdown
- task 1

## Verification
- pytest -q
""",
        )
        rules, _ = VALIDATOR.discover_template_rules(root)
        issues = VALIDATOR.validate_documents(root, rules, require_template_selection=False)
        assert any(issue.category == "template_document_type_mismatch" for issue in issues)
    finally:
        rmtree(root, ignore_errors=True)


def test_master_roadmap_requires_per_phase_goal_and_deliverables() -> None:
    root = make_test_root()
    try:
        write_text(
            root / "docs" / "operating_system" / "templates" / "master-workstream-roadmap-template.md",
            """---
template_id: master-workstream-roadmap
document_type: roadmap
target_globs:
  - docs/intent/master-workstream-roadmap.md
required_sections:
  - Goal
  - Key Deliverables
  - Task/Wave Breakdown
  - Workstream Index
  - Completion Criteria
required_frontmatter:
  artifact_type: roadmap
---

# Master Workstream Roadmap Template
""",
        )
        write_text(
            root / "docs" / "intent" / "master-workstream-roadmap.md",
            """---
template_id: master-workstream-roadmap
artifact_type: roadmap
---

# Master Workstream Roadmap

## Goal
Roadmap goal.

## Key Deliverables
- one

## Task/Wave Breakdown
### Phase 1
#### Goal
Phase one goal.
#### Key Deliverables
- one
### Phase 2
#### Goal
Phase two goal.
### Phase 3
#### Goal
Phase three goal.
#### Key Deliverables
- three

## Workstream Index
- ws

## Completion Criteria
All done.
""",
        )
        rules, findings = VALIDATOR.discover_template_rules(root)
        assert findings == []
        issues = VALIDATOR.validate_documents(root, rules, require_template_selection=False)
        assert any(issue.category == "template_phase_structure_missing" for issue in issues)
    finally:
        rmtree(root, ignore_errors=True)
