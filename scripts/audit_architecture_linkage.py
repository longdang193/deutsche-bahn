"""
@meta
name: audit_architecture_linkage
type: script
domain: docs
responsibility:
  - Audit feature sources for removed manual reference bridges.
  - Confirm architecture refs are owned by metadata instead of feature-local manual lists.
inputs:
  - docs/features/*/feature.source.yaml
  - Python @meta blocks
outputs:
  - Human-readable report for disallowed feature-source manual_refs
tags:
  - docs
  - lineage
  - metadata
  - audit
distribution_tier: starter_kit
lifecycle:
  status: active
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys
from typing import TYPE_CHECKING, Any

import yaml
from validator_policy import (
    FORBIDDEN_MANUAL_REFS_FIELD,
    feature_source_has_forbidden_manual_refs,
    format_manual_refs_forbidden_message,
)


if TYPE_CHECKING:
    from tools.docs.generate_architecture_metadata import CodeMetadata  # pragma: no cover


def script_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_generator_module() -> Any:
    generator_path = script_root() / "tools" / "docs" / "generate_architecture_metadata.py"
    spec = importlib.util.spec_from_file_location("architecture_generator", generator_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load architecture generator from {generator_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def find_manual_ref_sources(root: Path) -> list[str]:
    findings: list[str] = []
    features_root = root / "docs" / "features"
    for source_path in sorted(features_root.glob("*/feature.source.yaml")):
        parsed = yaml.safe_load(source_path.read_text(encoding="utf-8"))
        if not feature_source_has_forbidden_manual_refs(parsed):
            continue
        findings.append(str(source_path.relative_to(root).as_posix()))
    return sorted(findings)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Audit architecture linkage policy that requires metadata-derived refs "
            f"instead of feature-source {FORBIDDEN_MANUAL_REFS_FIELD}."
        )
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=script_root(),
        help="Repository root to audit. Defaults to the current repository root.",
    )
    parser.add_argument(
        "--strict-awareness",
        action="store_true",
        help=f"Exit non-zero when disallowed {FORBIDDEN_MANUAL_REFS_FIELD} are found.",
    )
    parser.add_argument(
        "--report-awareness",
        action="store_true",
        help="Print the awareness report even when no candidates are found.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.repo_root.resolve()
    manual_ref_sources = find_manual_ref_sources(root)
    if manual_ref_sources:
        print(f"Architecture linkage policy failed: {format_manual_refs_forbidden_message()}")
        for source_path in manual_ref_sources:
            print(f"- {source_path}")
        return 1

    generator = load_generator_module()
    generator.load_feature_sources(root)
    generator.load_code_metadata(root)

    if args.report_awareness:
        print(
            "Architecture linkage awareness audit passed: "
            f"no feature-source {FORBIDDEN_MANUAL_REFS_FIELD} found."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
