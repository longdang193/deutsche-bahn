"""
@meta
name: validate_execution_context_pack_references
type: script
domain: docs
distribution_tier: starter_kit
responsibility:
  - Validate canonical execution context-pack policy references across execution surfaces.
inputs:
  - .agents/skills/skill-executing-plans/SKILL.md
  - docs/operating_system/prompt_templates/execute-prompt.md
  - docs/operating_system/prompt_templates/implementation-next-action-gate-prompt.md
  - docs/operating_system/governance/execution-context-pack-governance.md
outputs:
  - Exit status and human-readable validation results.
tags:
  - docs
  - validation
  - execution
lifecycle:
  status: active
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys


@dataclass(frozen=True)
class Issue:
    path: str
    message: str


REQUIRED_DOCS = {
    ".agents/skills/skill-executing-plans/SKILL.md": [
        "docs/superpowers/execution_context_packs/<lane-id>/latest.md",
        "docs/operating_system/governance/execution-context-pack-governance.md",
    ],
    "docs/operating_system/prompt_templates/execute-prompt.md": [
        "docs/superpowers/execution_context_packs/<lane-id>/latest.md",
        "docs/operating_system/governance/execution-context-pack-governance.md",
    ],
    "docs/operating_system/prompt_templates/implementation-next-action-gate-prompt.md": [
        "docs/superpowers/execution_context_packs/<lane-id>/latest.md",
        "docs/operating_system/governance/execution-context-pack-governance.md",
    ],
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def validate(root: Path) -> list[Issue]:
    issues: list[Issue] = []

    governance_path = root / "docs/operating_system/governance/execution-context-pack-governance.md"
    if not governance_path.exists():
        issues.append(Issue(path=governance_path.as_posix(), message="missing required governance doc"))

    for relative, needles in REQUIRED_DOCS.items():
        path = root / relative
        if not path.exists():
            issues.append(Issue(path=relative, message="required file missing"))
            continue
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                issues.append(Issue(path=relative, message=f"missing canonical reference: `{needle}`"))

    return issues


def main(argv: list[str] | None = None) -> int:
    root = repo_root()
    issues = validate(root)
    if issues:
        print("Execution context-pack reference validation failed:")
        for issue in issues:
            print(f"- {issue.path}: {issue.message}")
        return 1
    print("Execution context-pack reference validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
