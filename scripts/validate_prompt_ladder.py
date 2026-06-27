"""
@meta
name: validate_prompt_ladder
type: script
domain: docs
distribution_tier: starter_kit
responsibility:
  - Validate prompt ladder metadata sections and next-prompt linkage integrity.
  - Enforce non-standalone prompt routing for canonical ladder prompts.
inputs:
  - docs/operating_system/prompt_templates/*.md
outputs:
  - Exit status and human-readable prompt ladder validation report.
tags:
  - docs
  - validation
  - prompts
  - ci-safe
lifecycle:
  status: active
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml


REQUIRED_SECTIONS = (
    "Use When",
    "Prerequisites",
    "Next Prompts",
    "Not For",
)

REQUIRED_PREREQ_SUBSECTIONS = ("Required", "Optional")

CANONICAL_LADDER_PROMPTS = (
    "intent-prompt.md",
    "master-workstream-roadmap-build-prompt.md",
    "registered-workstream-set-build-prompt.md",
    "bounded-change-thread-build-prompt.md",
    "thread-set-to-spec-set-prompt.md",
    "spec-set-to-spec-authoring-map-prompt.md",
    "spec-prompt.md",
    "spec-set-execution-map-prompt.md",
    "plan-prompt.md",
    "execute-prompt.md",
    "implementation-next-action-gate-prompt.md",
    "thread-closeout-readiness-prompt.md",
    "workstream-closeout-readiness-prompt.md",
    "roadmap-closeout-readiness-prompt.md",
)

ALLOWED_SELF_LOOP = "implementation-next-action-gate-prompt.md"
TERMINAL_PROMPTS = {"roadmap-closeout-readiness-prompt.md"}


@dataclass(frozen=True)
class Finding:
    category: str
    path: str
    message: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate prompt ladder section contract and next-prompt link integrity."
    )
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repository root. Defaults to this script's repository.",
    )
    return parser


def _extract_section(text: str, heading: str) -> str | None:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(text)
    if match is None:
        return None
    next_heading = re.search(r"^##\s+.+$", text[match.end() :], re.MULTILINE)
    if next_heading is None:
        return text[match.end() :].strip()
    return text[match.end() : match.end() + next_heading.start()].strip()


def _extract_prereq_subsection(prereq_text: str, heading: str) -> str | None:
    pattern = re.compile(rf"^###\s+{re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(prereq_text)
    if match is None:
        return None
    next_heading = re.search(r"^###\s+.+$", prereq_text[match.end() :], re.MULTILINE)
    if next_heading is None:
        return prereq_text[match.end() :].strip()
    return prereq_text[match.end() : match.end() + next_heading.start()].strip()


def _extract_next_prompt_targets(section_text: str) -> list[str]:
    targets: list[str] = []
    for line in section_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        item = stripped[2:].strip().strip("`")
        if item.endswith(".md"):
            targets.append(item)
    return targets


def _extract_frontmatter(path: Path) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    payload = yaml.safe_load(parts[1]) if parts[1].strip() else {}
    if not isinstance(payload, dict):
        return None
    return payload


def _metadata_contract_present(meta: dict[str, Any] | None) -> bool:
    if not isinstance(meta, dict):
        return False
    return (
        isinstance(meta.get("entry_points"), list)
        and isinstance(meta.get("prerequisites"), list)
        and isinstance(meta.get("next_steps"), list)
    )


def _extract_next_targets_from_metadata(meta: dict[str, Any]) -> list[str]:
    targets: list[str] = []
    values = meta.get("next_steps")
    if not isinstance(values, list):
        return targets
    for value in values:
        if not isinstance(value, str):
            continue
        item = value.strip().strip("`")
        if not item:
            continue
        if item.endswith(".md"):
            targets.append(Path(item).name)
    return targets


def _find_cycles(
    graph: dict[str, list[str]],
    *,
    allowed_self_loop: str,
) -> list[list[str]]:
    visited: set[str] = set()
    stack: list[str] = []
    active: set[str] = set()
    cycles: list[list[str]] = []

    def dfs(node: str) -> None:
        visited.add(node)
        active.add(node)
        stack.append(node)
        for nxt in graph.get(node, []):
            if node == nxt == allowed_self_loop:
                continue
            if nxt not in visited:
                dfs(nxt)
            elif nxt in active:
                idx = stack.index(nxt)
                cycles.append(stack[idx:] + [nxt])
        active.remove(node)
        stack.pop()

    for node in graph:
        if node not in visited:
            dfs(node)
    return cycles


def validate_prompt_ladder(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    prompts_root = root / "docs" / "operating_system" / "prompt_templates"
    existing = {p.name for p in prompts_root.glob("*.md")}

    graph: dict[str, list[str]] = {}

    for name in CANONICAL_LADDER_PROMPTS:
        path = prompts_root / name
        if not path.exists():
            findings.append(
                Finding(
                    category="prompt_ladder_missing_file",
                    path=str(path.relative_to(root)).replace("\\", "/"),
                    message="canonical ladder prompt file is missing.",
                )
            )
            continue

        rel = str(path.relative_to(root)).replace("\\", "/")
        text = path.read_text(encoding="utf-8", errors="ignore")

        meta = _extract_frontmatter(path)
        uses_metadata_contract = _metadata_contract_present(meta)

        targets: list[str] = []
        if uses_metadata_contract and isinstance(meta, dict):
            targets = _extract_next_targets_from_metadata(meta)
            if not targets and name not in TERMINAL_PROMPTS:
                findings.append(
                    Finding(
                        category="prompt_ladder_dead_end",
                        path=rel,
                        message="non-terminal prompt has no next-prompt targets (metadata `next_steps`).",
                    )
                )
        else:
            missing_sections = [section for section in REQUIRED_SECTIONS if _extract_section(text, section) is None]
            for section in missing_sections:
                findings.append(
                    Finding(
                        category="prompt_ladder_missing_section",
                        path=rel,
                        message=f"missing required section `## {section}`.",
                    )
                )

            prereq_text = _extract_section(text, "Prerequisites")
            if prereq_text is not None:
                for subsection in REQUIRED_PREREQ_SUBSECTIONS:
                    if _extract_prereq_subsection(prereq_text, subsection) is None:
                        findings.append(
                            Finding(
                                category="prompt_ladder_missing_section",
                                path=rel,
                                message=f"`## Prerequisites` is missing `### {subsection}`.",
                            )
                        )

            next_text = _extract_section(text, "Next Prompts")
            if next_text is not None:
                targets = _extract_next_prompt_targets(next_text)
                if not targets and name not in TERMINAL_PROMPTS:
                    findings.append(
                        Finding(
                            category="prompt_ladder_dead_end",
                            path=rel,
                            message="non-terminal prompt has no next-prompt targets.",
                        )
                    )

        for target in targets:
            if target not in existing:
                findings.append(
                    Finding(
                        category="prompt_ladder_broken_link",
                        path=rel,
                        message=f"next prompt target `{target}` does not exist.",
                    )
                )
        graph[name] = targets

    cycles = _find_cycles(graph, allowed_self_loop=ALLOWED_SELF_LOOP)
    for cycle in cycles:
        findings.append(
            Finding(
                category="prompt_ladder_cycle_error",
                path="docs/operating_system/prompt_templates",
                message=f"invalid prompt cycle detected: {' -> '.join(cycle)}",
            )
        )

    return findings


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.repo_root).resolve()
    findings = validate_prompt_ladder(root)
    if findings:
        print("Prompt ladder validation failed:")
        for finding in findings:
            print(f"- {finding.category}: {finding.path} - {finding.message}")
        return 1
    print("Prompt ladder validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
