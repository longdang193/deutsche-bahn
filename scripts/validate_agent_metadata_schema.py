"""
@meta
name: validate_agent_metadata_schema
type: script
domain: validation
distribution_tier: starter_kit
responsibility:
  - Validate canonical metadata schema for skills, rules, and workflows.
  - Enforce frontmatter shape and reference integrity for agent metadata surfaces.
inputs:
  - Skill, rule, and workflow markdown files with YAML frontmatter
outputs:
  - Exit status and schema validation findings
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


@dataclass(frozen=True)
class Finding:
    category: str
    path: str
    message: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate skills/rules/workflows metadata schema.")
    parser.add_argument("--repo-root", default=str(repo_root()))
    return parser.parse_args()


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

def _extract_body_without_frontmatter(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return text
    return parts[2]


def _require_list(meta: dict[str, Any], key: str, findings: list[Finding], rel: str) -> None:
    value = meta.get(key)
    if not isinstance(value, list):
        findings.append(Finding("agent_metadata_schema_error", rel, f"`{key}` must be a list."))


def _require_string(meta: dict[str, Any], key: str, findings: list[Finding], rel: str) -> None:
    value = meta.get(key)
    if not isinstance(value, str) or not value.strip():
        findings.append(Finding("agent_metadata_schema_error", rel, f"`{key}` must be a non-empty string."))


def _require_resolved_skill_refs(
    meta: dict[str, Any],
    key: str,
    findings: list[Finding],
    rel: str,
    known_skills: set[str],
) -> None:
    value = meta.get(key)
    if not isinstance(value, list):
        return
    for item in value:
        if not isinstance(item, str) or not item.strip():
            findings.append(Finding("agent_metadata_schema_error", rel, f"`{key}` entries must be non-empty strings."))
            continue
        if item not in known_skills:
            findings.append(Finding("agent_metadata_schema_error", rel, f"`{key}` references unknown skill `{item}`."))


def validate(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    known_skills = {path.parent.name for path in sorted((root / ".agents" / "skills").glob("*/SKILL.md"))}

    # Skills
    for path in sorted((root / ".agents" / "skills").glob("*/SKILL.md")):
        rel = path.relative_to(root).as_posix()
        meta = _extract_frontmatter(path)
        if meta is None:
            findings.append(Finding("agent_metadata_schema_error", rel, "missing YAML frontmatter."))
            continue
        for key in ("name", "description"):
            _require_string(meta, key, findings, rel)
        name = meta.get("name")
        if isinstance(name, str) and name != path.parent.name:
            findings.append(Finding("agent_metadata_schema_error", rel, f"`name` must match skill folder name `{path.parent.name}`."))
        _require_list(meta, "allowed-tools", findings, rel)
        hooks = meta.get("hooks")
        if not isinstance(hooks, dict):
            findings.append(Finding("agent_metadata_schema_error", rel, "`hooks` must be an object with `pre` and `post` lists."))
        else:
            if not isinstance(hooks.get("pre"), list):
                findings.append(Finding("agent_metadata_schema_error", rel, "`hooks.pre` must be a list."))
            if not isinstance(hooks.get("post"), list):
                findings.append(Finding("agent_metadata_schema_error", rel, "`hooks.post` must be a list."))
        _require_list(meta, "required_reads", findings, rel)
        _require_list(meta, "required_outputs", findings, rel)
        _require_list(meta, "tags", findings, rel)
        _require_resolved_skill_refs(meta, "related_skills", findings, rel, known_skills)
        if path.parent.name == "skill-creating-learning-materials":
            body_lines = _extract_body_without_frontmatter(path).splitlines()
            for idx, line in enumerate(body_lines):
                if not line.startswith("## "):
                    continue
                if idx == 0 or body_lines[idx - 1].strip():
                    findings.append(
                        Finding(
                            "agent_metadata_schema_error",
                            rel,
                            "each `##` heading must have an empty line before it.",
                        )
                    )
                    break

    # Rules
    rules_root = root / "docs" / "operating_system" / "rules"
    for path in sorted(rules_root.glob("*.md")):
        rel = path.relative_to(root).as_posix()
        meta = _extract_frontmatter(path)
        if meta is None:
            findings.append(Finding("agent_metadata_schema_error", rel, "missing YAML frontmatter."))
            continue
        for key in ("name", "description"):
            _require_string(meta, key, findings, rel)
        if not isinstance(meta.get("alwaysApply"), bool):
            findings.append(Finding("agent_metadata_schema_error", rel, "`alwaysApply` must be boolean."))
        _require_list(meta, "required_reads", findings, rel)
        _require_list(meta, "tags", findings, rel)

    # Workflows
    workflows_root = root / "docs" / "operating_system" / "workflows"
    for path in sorted(workflows_root.glob("*.md")):
        rel = path.relative_to(root).as_posix()
        meta = _extract_frontmatter(path)
        if meta is None:
            findings.append(Finding("agent_metadata_schema_error", rel, "missing YAML frontmatter."))
            continue
        for key in ("name", "description"):
            _require_string(meta, key, findings, rel)
        name = meta.get("name")
        if isinstance(name, str) and name != path.stem:
            findings.append(Finding("agent_metadata_schema_error", rel, f"`name` must match workflow filename stem `{path.stem}`."))
        _require_list(meta, "allowed-tools", findings, rel)
        _require_list(meta, "required_reads", findings, rel)
        _require_list(meta, "required_outputs", findings, rel)
        _require_list(meta, "related_skills", findings, rel)
        _require_resolved_skill_refs(meta, "related_skills", findings, rel, known_skills)
        _require_list(meta, "tags", findings, rel)

    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.repo_root).resolve()
    findings = validate(root)
    if findings:
        print("Agent metadata schema validation failed:")
        for finding in findings:
            print(f"- {finding.category}: {finding.path} - {finding.message}")
        return 1
    print("Agent metadata schema validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

