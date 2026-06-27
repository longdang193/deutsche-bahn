"""
@meta
name: validate_prompt_metadata_schema
type: script
domain: validation
distribution_tier: starter_kit
responsibility:
  - Validate prompt-template metadata schema for operating-system prompt templates.
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

VALID_STAGES = {"planning", "execution", "closeout", "drift", "maintenance"}
NAME_PATTERN = re.compile(r"^[a-z0-9-]+$")


@dataclass(frozen=True)
class Finding:
    category: str
    path: str
    message: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate prompt template metadata schema.")
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


def _require_string(meta: dict[str, Any], key: str, findings: list[Finding], rel: str) -> None:
    value = meta.get(key)
    if not isinstance(value, str) or not value.strip():
        findings.append(Finding("prompt_metadata_schema_error", rel, f"`{key}` must be a non-empty string."))


def _require_list_non_empty(meta: dict[str, Any], key: str, findings: list[Finding], rel: str) -> None:
    value = meta.get(key)
    if not isinstance(value, list):
        findings.append(Finding("prompt_metadata_schema_error", rel, f"`{key}` must be a list."))
        return
    if len(value) == 0:
        findings.append(Finding("prompt_metadata_schema_error", rel, f"`{key}` must not be empty."))


def validate(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    names_seen: dict[str, str] = {}
    prompts_root = root / "docs" / "operating_system" / "prompt_templates"
    for path in sorted(prompts_root.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        rel = path.relative_to(root).as_posix()
        meta = _extract_frontmatter(path)
        if meta is None:
            findings.append(Finding("prompt_metadata_schema_error", rel, "missing YAML frontmatter."))
            continue

        for key in ("name", "description", "type", "stage"):
            _require_string(meta, key, findings, rel)
        for key in ("entry_points", "prerequisites", "next_steps", "related_skills", "required_reads", "tags"):
            _require_list_non_empty(meta, key, findings, rel)

        name = meta.get("name")
        if isinstance(name, str) and name.strip():
            if not NAME_PATTERN.fullmatch(name):
                findings.append(Finding("prompt_metadata_schema_error", rel, "`name` must match ^[a-z0-9-]+$."))
            previous = names_seen.get(name)
            if previous is not None:
                findings.append(Finding("prompt_metadata_schema_error", rel, f"duplicate `name` already used in {previous}."))
            else:
                names_seen[name] = rel

        prompt_type = meta.get("type")
        if isinstance(prompt_type, str) and prompt_type != "prompt":
            findings.append(Finding("prompt_metadata_schema_error", rel, "`type` must be `prompt`."))

        stage = meta.get("stage")
        if isinstance(stage, str) and stage not in VALID_STAGES:
            findings.append(
                Finding(
                    "prompt_metadata_schema_error",
                    rel,
                    f"`stage` must be one of {sorted(VALID_STAGES)}.",
                )
            )

    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.repo_root).resolve()
    findings = validate(root)
    if findings:
        print("Prompt metadata schema validation failed:")
        for finding in findings:
            print(f"- {finding.category}: {finding.path} - {finding.message}")
        return 1
    print("Prompt metadata schema validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

