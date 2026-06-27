"""
@meta
# distribution_tier: starter_kit
type: test
scope: unit
domain: metadata
covers:
  - Agent metadata schema validation for skills, rules, and workflows
excludes:
  - End-to-end adapter generation and publish flows
tags:
  - fast
  - ci-safe
"""

from __future__ import annotations

import importlib.util
import sys
import uuid
from pathlib import Path
from shutil import rmtree


REPO_ROOT = Path(__file__).resolve().parent.parent
VALIDATOR_PATH = REPO_ROOT / "scripts" / "validate_agent_metadata_schema.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_module("validate_agent_metadata_schema", VALIDATOR_PATH)


def _mkroot() -> Path:
    root = REPO_ROOT / ".tmp-tests" / f"agent-meta-{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    return root


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_schema_passes_for_minimal_valid_surfaces() -> None:
    root = _mkroot()
    try:
        _write(
            root / ".agents/skills/demo/SKILL.md",
            """---
name: demo
description: demo
allowed-tools: []
hooks:
  pre: []
  post: []
required_reads: []
required_outputs: []
tags: []
---
# Demo
""",
        )
        _write(
            root / "docs/operating_system/rules/demo.md",
            """---
name: demo
description: demo
alwaysApply: true
required_reads: []
required_outputs: []
tags: []
---
# Demo
""",
        )
        _write(
            root / "docs/operating_system/workflows/demo.md",
            """---
name: demo
description: demo
allowed-tools: []
required_reads: []
required_outputs: []
related_skills: []
tags: []
---
# Demo
""",
        )
        findings = VALIDATOR.validate(root)
        assert findings == []
    finally:
        rmtree(root, ignore_errors=True)


def test_schema_fails_when_required_fields_missing() -> None:
    root = _mkroot()
    try:
        _write(root / ".agents/skills/demo/SKILL.md", "---\nname: demo\n---\n# Demo\n")
        findings = VALIDATOR.validate(root)
        assert any("allowed-tools" in f.message for f in findings)
    finally:
        rmtree(root, ignore_errors=True)

def test_learning_materials_skill_requires_blank_line_before_h2() -> None:
    root = _mkroot()
    try:
        _write(
            root / ".agents/skills/skill-creating-learning-materials/SKILL.md",
            """---
name: skill-creating-learning-materials
description: demo
allowed-tools: []
hooks:
  pre: []
  post: []
required_reads: []
required_outputs: []
tags: []
---
# Creating Learning Materials
## No Blank Before This Heading
body
""",
        )
        findings = VALIDATOR.validate(root)
        assert any("empty line before" in f.message for f in findings)
    finally:
        rmtree(root, ignore_errors=True)

def test_learning_materials_skill_allows_blank_line_before_h2() -> None:
    root = _mkroot()
    try:
        _write(
            root / ".agents/skills/skill-creating-learning-materials/SKILL.md",
            """---
name: skill-creating-learning-materials
description: demo
allowed-tools: []
hooks:
  pre: []
  post: []
required_reads: []
required_outputs: []
tags: []
---
# Creating Learning Materials

## Blank Before This Heading
body
""",
        )
        findings = VALIDATOR.validate(root)
        assert not any("empty line before" in f.message for f in findings)
    finally:
        rmtree(root, ignore_errors=True)

