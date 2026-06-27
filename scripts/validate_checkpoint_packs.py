"""
@meta
name: validate_checkpoint_packs
type: script
domain: docs
distribution_tier: starter_kit
responsibility:
  - Validate bounded change thread checkpoint result-pack coverage.
  - Require checkpoint packs for active and completed thread statuses.
  - Enforce the canonical result-pack section headings for discoverability.
inputs:
  - docs/intent/workstreams/threads/**/*.md
  - docs/intent/workstreams/checkpoints/**/*.md
outputs:
  - Exit status and human-readable checkpoint validation report.
tags:
  - docs
  - validation
  - planning
  - ci-safe
lifecycle:
  status: active
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

REQUIRED_SECTION_HEADINGS = (
    "## Intent",
    "## Actions",
    "## Visible Output",
    "## Status",
    "## Next Decision",
)
DEFAULT_REQUIRED_STATUSES = ("active", "completed")


@dataclass(frozen=True)
class ValidationIssue:
    category: str
    path: str
    message: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate checkpoint result-pack coverage for bounded change threads."
        )
    )
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repository root. Defaults to this script's repository.",
    )
    parser.add_argument(
        "--required-statuses",
        nargs="+",
        default=list(DEFAULT_REQUIRED_STATUSES),
        help=(
            "Thread statuses that require at least one checkpoint result pack. "
            "Defaults to: active completed"
        ),
    )
    return parser


def relative_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def parse_status(thread_text: str) -> str | None:
    match = re.search(r"^\s*status:\s*([A-Za-z_-]+)\s*$", thread_text, re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip().lower()


def find_checkpoint_packs(checkpoint_dir: Path) -> list[Path]:
    if not checkpoint_dir.exists():
        return []
    return sorted(path for path in checkpoint_dir.glob("*.md") if path.name != "README.md")


def validate_pack_file(pack_path: Path, root: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    text = pack_path.read_text(encoding="utf-8")
    rel_path = relative_path(pack_path, root)
    for heading in REQUIRED_SECTION_HEADINGS:
        if heading not in text:
            issues.append(
                ValidationIssue(
                    category="checkpoint_pack_format_error",
                    path=rel_path,
                    message=f"missing required heading `{heading}`",
                )
            )
    return issues


def validate_checkpoint_packs(root: Path, required_statuses: set[str]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    threads_root = root / "docs" / "intent" / "workstreams" / "threads"
    checkpoints_root = root / "docs" / "intent" / "workstreams" / "checkpoints"
    if not threads_root.exists():
        return issues

    for thread_file in sorted(threads_root.glob("*/*.md")):
        text = thread_file.read_text(encoding="utf-8")
        status = parse_status(text)
        if status is None:
            continue
        if status not in required_statuses:
            continue

        workstream_id = thread_file.parent.name
        thread_slug = re.sub(r"^\d+-", "", thread_file.stem)
        checkpoint_dir = checkpoints_root / workstream_id / thread_slug
        packs = find_checkpoint_packs(checkpoint_dir)
        if not packs:
            issues.append(
                ValidationIssue(
                    category="checkpoint_pack_missing",
                    path=relative_path(thread_file, root),
                    message=(
                        "thread status requires a checkpoint result pack but none were found under "
                        f"`{relative_path(checkpoint_dir, root)}`"
                    ),
                )
            )
            continue
        for pack in packs:
            issues.extend(validate_pack_file(pack, root))
    return issues


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    required_statuses = {status.strip().lower() for status in args.required_statuses}
    issues = validate_checkpoint_packs(root, required_statuses)
    if issues:
        print("Checkpoint result-pack validation failed:")
        for issue in issues:
            print(f"- [{issue.category}] {issue.path}: {issue.message}")
        return 1
    print("Checkpoint result-pack validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
