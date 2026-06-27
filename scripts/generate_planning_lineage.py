"""
@meta
name: generate_planning_lineage
type: script
domain: docs
responsibility:
  - Generate the derived planning-lineage roll-up from roadmap, workstream, thread, spec, and plan metadata.
inputs:
  - docs/intent/master-workstream-roadmap.md
  - docs/intent/workstreams/*.md
  - docs/intent/workstreams/threads/**/*.md
  - docs/superpowers/specs/*.md
  - docs/superpowers/plans/*.md
outputs:
  - docs/generated/planning_lineage.yaml
tags:
  - docs
  - lineage
  - generation
  - ci-safe
distribution_tier: starter_kit
lifecycle:
  status: active
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from planning_lineage_support import render_planning_lineage_yaml


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate docs/generated/planning_lineage.yaml.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root to operate on.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    output_path = repo_root / "docs" / "generated" / "planning_lineage.yaml"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_planning_lineage_yaml(repo_root), encoding="utf-8")
    print(f"Generated {output_path.relative_to(repo_root).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
