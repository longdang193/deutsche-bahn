"""
@meta
# distribution_tier: starter_kit
name: test_validate_prompt_ladder
type: test
scope: unit
domain: docs
covers:
  - Prompt ladder required section contract
  - Next-prompt target linkage validation
  - Allowed self-loop handling and invalid cycle detection
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
VALIDATOR_PATH = REPO_ROOT / "scripts" / "validate_prompt_ladder.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_module("validate_prompt_ladder", VALIDATOR_PATH)


def make_test_root() -> Path:
    root = REPO_ROOT / ".tmp-tests" / f"validate-prompt-ladder-{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    return root


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def prompt_doc(name: str, next_prompt: str | None) -> str:
    next_line = (
        f"- `{next_prompt}`" if next_prompt else "- terminal prompt (no further prompt required once closure-ready decision is returned)"
    )
    return f"""# {name}

## Use When

test

## Prerequisites

### Required

- one

### Optional

- none

## Next Prompts

{next_line}

## Not For

test
"""


def seed_all_prompts(root: Path) -> None:
    prompts_root = root / "docs" / "operating_system" / "prompt_templates"
    chain = list(VALIDATOR.CANONICAL_LADDER_PROMPTS)
    for idx, name in enumerate(chain):
        nxt = None
        if name == VALIDATOR.ALLOWED_SELF_LOOP:
            nxt = VALIDATOR.ALLOWED_SELF_LOOP
        elif idx + 1 < len(chain):
            nxt = chain[idx + 1]
        write_text(prompts_root / name, prompt_doc(name, nxt))


def test_prompt_ladder_passes_for_seeded_chain() -> None:
    root = make_test_root()
    try:
        seed_all_prompts(root)
        findings = VALIDATOR.validate_prompt_ladder(root)
        assert findings == []
    finally:
        rmtree(root, ignore_errors=True)


def test_prompt_ladder_fails_on_missing_section() -> None:
    root = make_test_root()
    try:
        seed_all_prompts(root)
        target = root / "docs" / "operating_system" / "prompt_templates" / "spec-prompt.md"
        text = target.read_text(encoding="utf-8").replace("## Not For", "## NotFor")
        target.write_text(text, encoding="utf-8")
        findings = VALIDATOR.validate_prompt_ladder(root)
        assert any(f.category == "prompt_ladder_missing_section" for f in findings)
    finally:
        rmtree(root, ignore_errors=True)


def test_prompt_ladder_fails_on_broken_next_prompt_link() -> None:
    root = make_test_root()
    try:
        seed_all_prompts(root)
        target = root / "docs" / "operating_system" / "prompt_templates" / "plan-prompt.md"
        text = target.read_text(encoding="utf-8").replace("`execute-prompt.md`", "`missing-next.md`")
        target.write_text(text, encoding="utf-8")
        findings = VALIDATOR.validate_prompt_ladder(root)
        assert any(f.category == "prompt_ladder_broken_link" for f in findings)
    finally:
        rmtree(root, ignore_errors=True)

