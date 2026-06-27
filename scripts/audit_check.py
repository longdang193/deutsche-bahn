"""
@meta
name: audit_check
type: script
domain: governance
distribution_tier: starter_kit
responsibility:
  - Validate audit bundle structure and required report sections.
  - Enforce presence of evidence, repro, and manifest artifact declarations.
inputs:
  - Path to docs/superpowers/plans/audit/<audit_id>
outputs:
  - Exit code and validation diagnostics
lifecycle:
  status: active
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REQUIRED_FILES = ["report.md", "manifest.yaml"]
REQUIRED_REPORT_TOKENS = [
    "## Metadata",
    "## Findings",
    "## Evidence",
    "## Reproduction",
    "## Fix And Verification",
    "## Completion Checklist",
]


def check_bundle(root: Path) -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_FILES:
        if not (root / name).exists():
            errors.append(f"missing required file: {name}")

    report = root / "report.md"
    if report.exists():
        text = report.read_text(encoding="utf-8", errors="replace")
        for token in REQUIRED_REPORT_TOKENS:
            if token not in text:
                errors.append(f"report missing section: {token}")

    evidence_dir = root / "evidence"
    if not evidence_dir.exists():
        errors.append("missing evidence directory")

    repro_dir = root / "repro"
    if not repro_dir.exists():
        errors.append("missing repro directory")

    manifest = root / "manifest.yaml"
    if manifest.exists():
        m = manifest.read_text(encoding="utf-8", errors="replace")
        if "artifacts:" not in m:
            errors.append("manifest missing artifacts list")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("audit_path", help="Path to docs/superpowers/plans/audit/<audit_id>")
    args = parser.parse_args()

    root = Path(args.audit_path)
    if not root.exists():
        print(f"ERROR: audit path not found: {root}")
        return 2

    errors = check_bundle(root)
    if errors:
        print("AUDIT_CHECK_FAILED")
        for err in errors:
            print(f"- {err}")
        return 1

    print("AUDIT_CHECK_PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
