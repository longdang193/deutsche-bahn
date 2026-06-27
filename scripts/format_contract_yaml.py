"""
@meta
name: format_contract_yaml
type: script
domain: docs
responsibility:
  - Normalize human-authored YAML contracts under docs/features and docs/stages.
  - Provide explicit check and rewrite modes for contract formatting drift.
inputs:
  - docs/features/*/*.yaml
  - docs/stages/*.yaml
outputs:
  - Formatting-only rewrites for the targeted YAML contract files.
tags:
  - yaml
  - docs
  - formatting
distribution_tier: starter_kit
lifecycle:
  status: active
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import yaml


MAX_LINE_WIDTH = 10_000
GENERATED_FILE_PREFIX = "# GENERATED FILE - do not edit directly."


class IndentedSafeDumper(yaml.SafeDumper):
    def increase_indent(self, flow: bool = False, indentless: bool = False) -> object:
        return super().increase_indent(flow, False)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def is_supported_contract_path(path: Path) -> bool:
    parts = path.resolve().parts
    if "docs" not in parts:
        return False

    docs_index = parts.index("docs")
    tail = parts[docs_index:]

    if len(tail) >= 4 and tail[1] == "features":
        return path.suffix == ".yaml"
    if len(tail) == 3 and tail[1] == "stages":
        return path.suffix == ".yaml"
    return False


def default_targets() -> list[Path]:
    root = repo_root()
    feature_files = sorted((root / "docs" / "features").glob("*/*.yaml"))
    stage_files = sorted((root / "docs" / "stages").glob("*.yaml"))
    return [*feature_files, *stage_files]


def resolve_targets(raw_targets: Iterable[str]) -> list[Path]:
    targets = [Path(target) for target in raw_targets]
    if not targets:
        return default_targets()
    return targets


def normalize_yaml_text(raw_text: str) -> str:
    parsed = yaml.safe_load(raw_text)
    dumped = yaml.dump(
        parsed,
        Dumper=IndentedSafeDumper,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=False,
        width=MAX_LINE_WIDTH,
    )
    return dumped


def is_generated_contract(raw_text: str) -> bool:
    return raw_text.startswith(GENERATED_FILE_PREFIX)


def process_file(path: Path, check_only: bool) -> tuple[bool, str]:
    original = path.read_text(encoding="utf-8")
    if is_generated_contract(original):
        return False, f"Skipped generated: {path}"

    normalized = normalize_yaml_text(original)
    changed = normalized != original

    if changed and not check_only:
        path.write_text(normalized, encoding="utf-8")

    if changed:
        return True, f"Would reformat: {path}" if check_only else f"Reformatted: {path}"
    return False, f"Already normalized: {path}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Normalize or check formatting for human-authored YAML contracts under "
            "docs/features/*/*.yaml and docs/stages/*.yaml."
        )
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help="Optional YAML contract paths. Defaults to docs/features/*/*.yaml and docs/stages/*.yaml.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report formatting drift without rewriting files.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    targets = resolve_targets(args.targets)
    if not targets:
        print("No YAML contract files found; nothing to format.")
        return 0

    invalid_targets = [path for path in targets if not is_supported_contract_path(path)]
    if invalid_targets:
        parser.error(
            "Unsupported target path(s): "
            + ", ".join(str(path) for path in invalid_targets)
            + ". Only docs/features/*/*.yaml and docs/stages/*.yaml are supported."
        )

    drift_found = False
    for path in targets:
        changed, message = process_file(path, check_only=args.check)
        print(message)
        drift_found = drift_found or changed

    if args.check and drift_found:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
