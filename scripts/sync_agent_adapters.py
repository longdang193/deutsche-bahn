"""
@meta
name: sync_agent_adapters
type: script
domain: governance
distribution_tier: starter_kit
responsibility:
  - Generate runtime adapter artifacts from canonical adapter mappings.
  - Enforce role-aware source inclusion/omission during adapter sync.
  - Detect and report drift in check mode for managed generated surfaces.
inputs:
  - Adapter mapping files under adapters/*
  - Canonical source files referenced by mapping rules
  - Repo adoption mode and role configuration
outputs:
  - Updated generated runtime artifacts across adapter destinations
  - Drift/failure diagnostics when --check is used
lifecycle:
  status: active
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys

import yaml

from validator_policy import DEFAULT_REPO_ROLE, normalize_adoption_mode


@dataclass(frozen=True)
class Mapping:
    source: str
    destination: str
    mode: str
    comment_prefix: str
    include_glob: str | None


GENERATED_BY = "scripts/sync_agent_adapters.py"
MANIFEST_BEGIN = "<!-- BEGIN GENERATED: RUNTIME_MANIFEST -->"
MANIFEST_END = "<!-- END GENERATED: RUNTIME_MANIFEST -->"


def _render_json_from_yaml(text: str) -> str:
    payload = yaml.safe_load(text)
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=False)


def _provider_settings_to_codex_hooks(payload: dict) -> dict:
    hooks_payload: dict[str, list[dict[str, object]]] = {}
    events = payload.get("hooks", {}).get("events", {})
    if not isinstance(events, dict):
        return {"hooks": {}}
    for event in events.values():
        if not isinstance(event, dict) or not event.get("enabled"):
            continue
        provider_event = event.get("provider_event")
        commands = event.get("commands")
        if not isinstance(provider_event, str) or not provider_event.strip():
            continue
        if not isinstance(commands, list) or not commands:
            continue
        mapped_hooks: list[dict[str, object]] = []
        timeout_seconds = int(event.get("timeout_seconds", 60))
        for command in commands:
            if not isinstance(command, str) or not command.strip():
                continue
            mapped_hooks.append(
                {
                    "type": "command",
                    "command": command,
                    "timeout": timeout_seconds,
                    "statusMessage": "Validating repo contracts",
                }
            )
        if not mapped_hooks:
            continue
        hooks_payload.setdefault(provider_event, []).append({"hooks": mapped_hooks})
    return {"hooks": hooks_payload}


def _provider_settings_to_claude_settings(payload: dict) -> dict:
    hooks_payload: dict[str, list[dict[str, object]]] = {}
    events = payload.get("hooks", {}).get("events", {})
    if not isinstance(events, dict):
        return {"hooks": {}}
    for event in events.values():
        if not isinstance(event, dict) or not event.get("enabled"):
            continue
        provider_event = event.get("provider_event")
        commands = event.get("commands")
        if not isinstance(provider_event, str) or not provider_event.strip():
            continue
        if not isinstance(commands, list) or not commands:
            continue
        mapped_hooks: list[dict[str, object]] = []
        timeout_seconds = int(event.get("timeout_seconds", 60))
        for command in commands:
            if not isinstance(command, str) or not command.strip():
                continue
            mapped_hooks.append(
                {
                    "type": "command",
                    "command": command,
                    "timeout": timeout_seconds,
                }
            )
        if not mapped_hooks:
            continue
        hooks_payload.setdefault(provider_event, []).append({"hooks": mapped_hooks})
    return {"hooks": hooks_payload}


def _provider_settings_to_antigravity_settings(payload: dict) -> dict:
    hooks = payload.get("hooks", {})
    events = hooks.get("events", {}) if isinstance(hooks, dict) else {}
    fallback_rule = ""
    if isinstance(events, dict):
        task_end = events.get("task_end")
        if isinstance(task_end, dict):
            value = task_end.get("fallback_rule")
            if isinstance(value, str):
                fallback_rule = value
    return {
        "provider": "antigravity",
        "lifecycle_hooks_supported": False,
        "fallback": {
            "mode": "rules_workflows",
            "task_end_rule": fallback_rule,
        },
    }


def _strip_markdown_frontmatter(text: str) -> str:
    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        return normalized
    parts = normalized.split("---\n", 2)
    if len(parts) < 3:
        return normalized
    return parts[2].lstrip("\n")


def _codex_rules_filename(path: Path) -> str:
    name = path.name
    if name.endswith("-rule.md"):
        return f"{name[:-len('-rule.md')]}.rules"
    if name.endswith(".md"):
        return f"{name[:-3]}.rules"
    return f"{name}.rules"


def _strip_extension(name: str) -> str:
    return name[:-3] if name.endswith(".md") else name


def _title_from_name(name: str) -> str:
    return _strip_extension(name).replace("-", " ").replace("_", " ").strip().title()


def _extract_title_and_summary(path: Path, *, body: str | None = None) -> tuple[str, str]:
    raw = body if body is not None else path.read_text(encoding="utf-8")
    text = _strip_generated_block(raw.replace("\r\n", "\n"))
    title = ""
    summary = ""
    if text.startswith("---\n"):
        parts = text.split("---\n", 2)
        if len(parts) >= 3:
            payload = yaml.safe_load(parts[1]) or {}
            if isinstance(payload, dict):
                title = str(payload.get("name") or "").strip()
                desc = payload.get("description")
                if isinstance(desc, str):
                    summary = " ".join(desc.split())
            text = parts[2].lstrip("\n")
    if not title:
        for line in text.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
    if not summary:
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith(">"):
                continue
            summary = stripped
            break
    if not title:
        title = _title_from_name(path.name)
    if not summary:
        summary = title
    return title, summary.rstrip(".") + "."


def _workflow_skill_text(src: Path) -> str:
    raw = src.read_text(encoding="utf-8")
    normalized = raw.replace("\r\n", "\n")
    meta: dict[str, object] = {}
    body = _strip_markdown_frontmatter(raw).strip()
    if normalized.startswith("---\n"):
        parts = normalized.split("---\n", 2)
        if len(parts) >= 3:
            payload = yaml.safe_load(parts[1]) or {}
            if isinstance(payload, dict):
                meta = dict(payload)
            body = parts[2].lstrip("\n").strip()
    title, summary = _extract_title_and_summary(src, body=body)
    skill_name = _strip_extension(src.name)
    title_heading = f"# {title}"
    if body.startswith(title_heading):
        body = body[len(title_heading) :].lstrip("\n")
    meta["name"] = str(meta.get("name") or skill_name)
    meta["description"] = str(meta.get("description") or summary)
    allowed = meta.get("allowed-tools")
    if not isinstance(allowed, list):
        meta["allowed-tools"] = []
    required_reads = meta.get("required_reads")
    if not isinstance(required_reads, list):
        meta["required_reads"] = []
    required_outputs = meta.get("required_outputs")
    if not isinstance(required_outputs, list):
        meta["required_outputs"] = []
    related_skills = meta.get("related_skills")
    if related_skills is not None and not isinstance(related_skills, list):
        meta["related_skills"] = []
    tags = meta.get("tags")
    if not isinstance(tags, list):
        tags = []
    if "workflow-skill" not in tags:
        tags.append("workflow-skill")
    meta["tags"] = tags
    frontmatter = yaml.safe_dump(meta, sort_keys=False, allow_unicode=False).strip()
    heading = f"# {title}\n\n"
    return f"---\n{frontmatter}\n---\n\n{heading}{body}\n"


def _render_manifest(root: Path, platform: str) -> str:
    rules_root = root / "docs" / "operating_system" / "rules"
    workflows_root = root / "docs" / "operating_system" / "workflows"
    skills_root = root / ".agents" / "skills"
    lines = [
        MANIFEST_BEGIN,
        "## Runtime Extension Manifest (Generated)",
        "",
        "> [!IMPORTANT]",
        "> This section is generated. Do not edit manually.",
        "> Source of truth: `docs/operating_system/rules/*.md`, `docs/operating_system/workflows/*.md`, `.agents/skills/*/SKILL.md`.",
        "> Regenerate via: `scripts/sync_agent_adapters.py`.",
        "",
        "### Rules Manifest",
    ]
    for path in sorted(rules_root.glob("*.md")):
        title, summary = _extract_title_and_summary(path)
        lines.append(f"- `{path.name}` — {summary}")
        lines.append(f"  - Source: `docs/operating_system/rules/{path.name}`")
    lines.extend(["", "### Workflow-Skills Manifest"])
    for path in sorted(workflows_root.glob("*.md")):
        title, summary = _extract_title_and_summary(path)
        skill_name = _strip_extension(path.name)
        lines.append(f"- `{skill_name}` — {summary}")
        lines.append(f"  - Source: `docs/operating_system/workflows/{path.name}`")
        lines.append(f"  - Generated skill: `skills/{skill_name}/SKILL.md`")
    lines.extend(["", "### Native Skills Manifest"])
    for path in sorted(skills_root.glob("*/SKILL.md")):
        title, summary = _extract_title_and_summary(path)
        skill_name = path.parent.name
        lines.append(f"- `{skill_name}` — {summary}")
        lines.append(f"  - Source: `.agents/skills/{skill_name}/SKILL.md`")
    lines.extend(["", "### Resolution Notes"])
    if platform == "codex":
        lines.extend([
            "- `AGENTS.md` is the authoritative Codex root instruction surface.",
            "- Rules are summarized here; workflow runtime invocation flows through skill surfaces.",
        ])
    elif platform == "claude":
        lines.extend([
            "- `CLAUDE.md` complements provider-native rules and skills surfaces.",
            "- Workflows are deployed as skills for consistent invocation.",
        ])
    else:
        lines.extend([
            "- `GEMINI.md` is the primary guaranteed root instruction surface.",
            "- Skills under `antigravity/skills/*/SKILL.md` are the runtime-critical execution surface.",
        ])
    lines.extend([
        "",
        "<!-- MANIFEST_METADATA",
        "version: 1",
        f"generated_by: {GENERATED_BY}",
        "-->",
        MANIFEST_END,
        "",
    ])
    return "\n".join(lines)


def _inject_manifest(text: str, *, manifest: str) -> str:
    normalized = text.replace("\r\n", "\n").rstrip("\n")
    pattern = re.compile(r"\n?" + re.escape(MANIFEST_BEGIN) + r".*?" + re.escape(MANIFEST_END), re.S)
    if pattern.search(normalized):
        replaced = pattern.sub("\n" + manifest.rstrip("\n"), normalized, count=1)
        return replaced.strip() + "\n"
    return normalized + "\n\n" + manifest.rstrip("\n") + "\n"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync agent adapter outputs.")
    parser.add_argument("--check", action="store_true", help="Fail on drift without writing.")
    parser.add_argument(
        "--adapters-root",
        default="adapters",
        help="Adapters directory relative to repo root.",
    )
    parser.add_argument(
        "--platform",
        action="append",
        default=[],
        help="Platform to sync (repeatable). Overrides mode-driven defaults unless --all-platforms is set.",
    )
    parser.add_argument(
        "--all-platforms",
        action="store_true",
        help="Process all adapter mappings regardless of adoption-mode policy.",
    )
    return parser.parse_args()


def _load_mapping(path: Path) -> tuple[str, list[Mapping]]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid mapping yaml: {path}")
    platform = str(payload.get("platform", path.parent.name))
    mapping_items = payload.get("mappings")
    if not isinstance(mapping_items, list):
        raise ValueError(f"`mappings` must be a list in {path}")
    mappings: list[Mapping] = []
    for raw in mapping_items:
        if not isinstance(raw, dict):
            raise ValueError(f"Invalid mapping entry in {path}")
        mappings.append(
            Mapping(
                source=str(raw["source"]),
                destination=str(raw["destination"]),
                mode=str(raw.get("mode", "copy_file")),
                comment_prefix=str(raw.get("comment_prefix", "#")),
                include_glob=str(raw["include_glob"]) if "include_glob" in raw else None,
            )
        )
    return platform, mappings


def _render_generated_block(source_rel: str) -> str:
    return (
        "<!--\n"
        "GENERATED FILE - DO NOT EDIT\n\n"
        f"Source: {source_rel}\n"
        f"Generated by: {GENERATED_BY}\n"
        "To update: edit canonical source, then run sync.\n"
        "-->\n\n"
    )


def _strip_generated_block(raw: str) -> str:
    marker = "<!--\nGENERATED FILE - DO NOT EDIT\n"
    if not raw.startswith(marker):
        legacy_marker = "# GENERATED FILE - do not edit directly.\n"
        if raw.startswith(legacy_marker):
            rest = raw[len(legacy_marker) :]
            legacy_source = "# Source: `"
            if rest.startswith(legacy_source):
                line_end = rest.find("\n")
                if line_end != -1:
                    rest = rest[line_end + 1 :]
            return rest.lstrip("\n")
        return raw
    end = raw.find("-->\n")
    if end == -1:
        return raw
    return raw[end + len("-->\n") :].lstrip("\n")


def _render_with_header(text: str, *, source_rel: str, prefix: str) -> str:
    del prefix
    header = _render_generated_block(source_rel)
    normalized = _strip_generated_block(text.replace("\r\n", "\n"))
    if not normalized.startswith("---\n"):
        return header + normalized
    parts = normalized.split("---\n", 2)
    if len(parts) < 3:
        return header + normalized
    frontmatter = f"---\n{parts[1]}---\n"
    body = parts[2].lstrip("\n")
    return f"{frontmatter}\n{header}{body}"


def _inject_json_generated_metadata(payload: dict, *, source_rel: str) -> dict:
    clean_payload = dict(payload)
    clean_payload.pop("_generated", None)
    clean_payload.pop("_source", None)
    clean_payload.pop("_generated_by", None)
    clean_payload.pop("_do_not_edit", None)
    return {
        "_generated": True,
        "_source": source_rel,
        "_generated_by": GENERATED_BY,
        "_do_not_edit": "Edit canonical source and run sync.",
        **clean_payload,
    }


def _normalized(text: str) -> str:
    return text.replace("\r\n", "\n").rstrip("\n")


def _write_text_if_changed(path: Path, rendered: str) -> None:
    if path.exists():
        current = path.read_text(encoding="utf-8")
        if _normalized(current) == _normalized(rendered):
            return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")

def _iter_matching_files(root: Path, pattern: str) -> list[Path]:
    return [path for path in root.glob(pattern) if path.is_file()]

def _remove_stale_files(dst_root: Path, expected: set[Path]) -> None:
    if not dst_root.exists():
        return
    generated = {path.relative_to(dst_root) for path in dst_root.rglob("*") if path.is_file()}
    for stale in generated - expected:
        (dst_root / stale).unlink(missing_ok=True)


def _expected_tree_paths(src_root: Path, pattern: str) -> set[Path]:
    return {path.relative_to(src_root) for path in _iter_matching_files(src_root, pattern)}


def _expected_codex_rules_paths(src_root: Path, pattern: str, dst_root: Path) -> set[Path]:
    return {
        (dst_root / _codex_rules_filename(path)).relative_to(dst_root)
        for path in _iter_matching_files(src_root, pattern)
    }


def _read_adoption_config(root: Path) -> tuple[str, str]:
    mode_file = root / "repo_config" / "adoption-mode.yaml"
    if not mode_file.exists():
        return "managed_architecture_metadata", DEFAULT_REPO_ROLE
    payload = yaml.safe_load(mode_file.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return "managed_architecture_metadata", DEFAULT_REPO_ROLE
    mode = normalize_adoption_mode(payload.get("adoption_mode"))
    repo_role = payload.get("repo_role", DEFAULT_REPO_ROLE)
    normalized_mode = mode if isinstance(mode, str) and mode.strip() else "managed_architecture_metadata"
    normalized_role = repo_role if isinstance(repo_role, str) and repo_role.strip() else DEFAULT_REPO_ROLE
    return normalized_mode, normalized_role


def _read_adapter_sync_policy(root: Path) -> tuple[list[str], dict[str, dict[str, list[str]]]]:
    policy_file = root / "repo_config" / "adapter-sync-policy.yaml"
    if not policy_file.exists():
        return ["codex"], {}
    payload = yaml.safe_load(policy_file.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return ["codex"], {}
    defaults_raw = payload.get("default_platforms", ["codex"])
    defaults = [str(item).strip() for item in defaults_raw if str(item).strip()] if isinstance(defaults_raw, list) else ["codex"]
    mode_role_raw = payload.get("mode_role_platforms", {})
    mode_role: dict[str, dict[str, list[str]]] = {}
    if isinstance(mode_role_raw, dict):
        for role, by_mode in mode_role_raw.items():
            if not isinstance(by_mode, dict):
                continue
            mode_map: dict[str, list[str]] = {}
            for mode, platforms in by_mode.items():
                if not isinstance(platforms, list):
                    continue
                cleaned = [str(item).strip() for item in platforms if str(item).strip()]
                if cleaned:
                    mode_map[str(mode).strip()] = cleaned
            if mode_map:
                mode_role[str(role).strip()] = mode_map
    return defaults or ["codex"], mode_role


def _resolve_platform_selection(root: Path, args: argparse.Namespace) -> tuple[set[str], str]:
    if args.all_platforms:
        return set(), "all-platforms"
    cli_platforms = {item.strip() for item in (args.platform or []) if isinstance(item, str) and item.strip()}
    if cli_platforms:
        return cli_platforms, "cli-platform"
    adoption_mode, repo_role = _read_adoption_config(root)
    defaults, mode_role = _read_adapter_sync_policy(root)
    selected = set(mode_role.get(repo_role, {}).get(adoption_mode, []))
    if not selected:
        selected = set(defaults)
    return selected, f"mode-policy(adoption_mode={adoption_mode},repo_role={repo_role})"


def _mapping_files_for_selection(adapters_root: Path, selected_platforms: set[str]) -> list[Path]:
    all_mappings = sorted(adapters_root.glob("*/mapping.yaml"))
    if not selected_platforms:
        return all_mappings
    return [path for path in all_mappings if path.parent.name in selected_platforms]


def _has_explicit_platform_selection(args: argparse.Namespace) -> bool:
    if args.all_platforms:
        return True
    cli_platforms = [
        item.strip()
        for item in (args.platform or [])
        if isinstance(item, str) and item.strip()
    ]
    return bool(cli_platforms)



def _is_optional_provider_settings_source(root: Path, source_path: Path) -> bool:
    try:
        rel = source_path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return False
    if not rel.startswith("docs/operating_system/provider_settings/"):
        return False
    if not rel.endswith(".yaml"):
        return False
    adoption_mode, repo_role = _read_adoption_config(root)
    requires_source_owned_provider_settings = (
        adoption_mode != "starter_method_only" and repo_role == "source_owner"
    )
    return not requires_source_owned_provider_settings


def _expected_workflow_skill_paths(src_root: Path, pattern: str) -> set[Path]:
    return {
        Path(_strip_extension(path.name)) / "SKILL.md"
        for path in _iter_matching_files(src_root, pattern)
    }


def _preserve_paths_for_destination(
    destination_preserve_paths: dict[Path, set[Path]],
    dst_root: Path,
) -> set[Path]:
    preserve: set[Path] = set(destination_preserve_paths.get(dst_root, set()))
    for other_root, other_paths in destination_preserve_paths.items():
        if other_root == dst_root:
            continue
        try:
            relative_root = other_root.relative_to(dst_root)
        except ValueError:
            continue
        preserve.update(relative_root / rel_path for rel_path in other_paths)
    return preserve


def _generated_agent_destination_roots(root: Path, mappings: list[Mapping]) -> set[Path]:
    generated_root = root / "generated_agents"
    owned_roots: set[Path] = set()
    for mapping in mappings:
        destination = root / mapping.destination
        try:
            destination.relative_to(generated_root)
        except ValueError:
            continue
        owned_roots.add(destination)
    return owned_roots


def _find_orphan_generated_surfaces(root: Path, mappings: list[Mapping]) -> list[Path]:
    generated_root = root / "generated_agents"
    if not generated_root.exists():
        return []
    owned_roots = _generated_agent_destination_roots(root, mappings)
    orphans: list[Path] = []
    for path in sorted(generated_root.rglob("*")):
        if not path.is_file():
            continue
        if any(path == owned or owned in path.parents for owned in owned_roots):
            continue
        orphans.append(path)
    return orphans


def _sync_file(root: Path, mapping: Mapping, *, platform: str, check: bool) -> list[str]:
    src = root / mapping.source
    dst = root / mapping.destination
    if not src.exists():
        if _is_optional_provider_settings_source(root, src):
            print(
                "SKIP:sync_agent_adapters:provider_settings source omitted for starter_method_only or consumer_derived mode"
            )
            return []
        return [f"Missing source: {src.as_posix()}"]
    src_text = src.read_text(encoding="utf-8")
    source_rel = src.relative_to(root).as_posix()
    if mapping.mode == "render_json_from_yaml":
        payload = _inject_json_generated_metadata(yaml.safe_load(src_text) or {}, source_rel=source_rel)
        rendered = json.dumps(payload, indent=2) + "\n"
    elif mapping.mode == "render_codex_hooks_from_yaml":
        payload = _inject_json_generated_metadata(
            _provider_settings_to_codex_hooks(yaml.safe_load(src_text) or {}),
            source_rel=source_rel,
        )
        rendered = json.dumps(payload, indent=2) + "\n"
    elif mapping.mode == "render_claude_settings_from_yaml":
        payload = _inject_json_generated_metadata(
            _provider_settings_to_claude_settings(yaml.safe_load(src_text) or {}),
            source_rel=source_rel,
        )
        rendered = json.dumps(payload, indent=2) + "\n"
    elif mapping.mode == "render_antigravity_settings_from_yaml":
        payload = _inject_json_generated_metadata(
            _provider_settings_to_antigravity_settings(yaml.safe_load(src_text) or {}),
            source_rel=source_rel,
        )
        rendered = json.dumps(payload, indent=2) + "\n"
    elif mapping.mode == "render_root_doc_with_manifest":
        rendered = _inject_manifest(
            _render_with_header(src_text, source_rel=source_rel, prefix=mapping.comment_prefix),
            manifest=_render_manifest(root, platform),
        )
    elif mapping.mode == "render_codex_rule_file":
        body = _strip_markdown_frontmatter(src_text)
        rendered = _render_with_header(
            body,
            source_rel=source_rel,
            prefix=mapping.comment_prefix,
        )
    else:
        rendered = _render_with_header(
            src_text,
            source_rel=source_rel,
            prefix=mapping.comment_prefix,
        )
    if check:
        if not dst.exists():
            return [f"Missing generated file: {dst.as_posix()}"]
        actual = dst.read_text(encoding="utf-8")
        if _normalized(actual) != _normalized(rendered):
            return [f"Drift detected: {dst.as_posix()}"]
        return []
    _write_text_if_changed(dst, rendered)
    return []


def _sync_tree(
    root: Path,
    mapping: Mapping,
    *,
    check: bool,
    preserve_paths: set[Path] | None = None,
) -> list[str]:
    src_root = root / mapping.source
    dst_root = root / mapping.destination
    if not src_root.exists():
        return [f"Missing source directory: {src_root.as_posix()}"]
    pattern = mapping.include_glob or "**/*"
    issues: list[str] = []
    expected_paths = _expected_tree_paths(src_root, pattern)
    for src in _iter_matching_files(src_root, pattern):
        rel = src.relative_to(src_root)
        dst = dst_root / rel
        rendered = _render_with_header(
            src.read_text(encoding="utf-8"),
            source_rel=src.relative_to(root).as_posix(),
            prefix=mapping.comment_prefix,
        )
        if check:
            if not dst.exists():
                issues.append(f"Missing generated file: {dst.as_posix()}")
                continue
            actual = dst.read_text(encoding="utf-8")
            if _normalized(actual) != _normalized(rendered):
                issues.append(f"Drift detected: {dst.as_posix()}")
            continue
        _write_text_if_changed(dst, rendered)
    if not check:
        _remove_stale_files(dst_root, preserve_paths or expected_paths)
    return issues


def _sync_codex_rules_tree(
    root: Path,
    mapping: Mapping,
    *,
    check: bool,
    preserve_paths: set[Path] | None = None,
) -> list[str]:
    src_root = root / mapping.source
    dst_root = root / mapping.destination
    if not src_root.exists():
        return [f"Missing source directory: {src_root.as_posix()}"]
    pattern = mapping.include_glob or "*.md"
    issues: list[str] = []
    expected_paths = _expected_codex_rules_paths(src_root, pattern, dst_root)
    for src in _iter_matching_files(src_root, pattern):
        dst = dst_root / _codex_rules_filename(src)
        body = _strip_markdown_frontmatter(src.read_text(encoding="utf-8"))
        rendered = _render_with_header(
            body,
            source_rel=src.relative_to(root).as_posix(),
            prefix=mapping.comment_prefix,
        )
        if check:
            if not dst.exists():
                issues.append(f"Missing generated file: {dst.as_posix()}")
                continue
            actual = dst.read_text(encoding="utf-8")
            if _normalized(actual) != _normalized(rendered):
                issues.append(f"Drift detected: {dst.as_posix()}")
            continue
        _write_text_if_changed(dst, rendered)
    if not check:
        _remove_stale_files(dst_root, preserve_paths or expected_paths)
    return issues


def _sync_workflow_skills_tree(
    root: Path,
    mapping: Mapping,
    *,
    check: bool,
    preserve_paths: set[Path] | None = None,
) -> list[str]:
    src_root = root / mapping.source
    dst_root = root / mapping.destination
    if not src_root.exists():
        return [f"Missing source directory: {src_root.as_posix()}"]
    pattern = mapping.include_glob or "*.md"
    issues: list[str] = []
    expected_paths = _expected_workflow_skill_paths(src_root, pattern)
    for src in _iter_matching_files(src_root, pattern):
        skill_name = _strip_extension(src.name)
        dst = dst_root / skill_name / "SKILL.md"
        rendered = _render_with_header(
            _workflow_skill_text(src),
            source_rel=src.relative_to(root).as_posix(),
            prefix=mapping.comment_prefix,
        )
        if check:
            if not dst.exists():
                issues.append(f"Missing generated file: {dst.as_posix()}")
                continue
            actual = dst.read_text(encoding="utf-8")
            if _normalized(actual) != _normalized(rendered):
                issues.append(f"Drift detected: {dst.as_posix()}")
            continue
        _write_text_if_changed(dst, rendered)
    if not check:
        _remove_stale_files(dst_root, preserve_paths or expected_paths)
    return issues


def run() -> int:
    args = parse_args()
    root = repo_root()
    adapters_root = root / args.adapters_root
    selected_platforms, selector = _resolve_platform_selection(root, args)
    mapping_files = _mapping_files_for_selection(adapters_root, selected_platforms)
    if not mapping_files:
        selected_display = ",".join(sorted(selected_platforms)) if selected_platforms else "all"
        adoption_mode, repo_role = _read_adoption_config(root)
        explicit_selection = _has_explicit_platform_selection(args)
        if repo_role == "consumer_derived" and not explicit_selection:
            print(
                "SKIP:sync_agent_adapters:no mappings for consumer_derived default mode-policy selection "
                f"(selection={selected_display}, selector={selector}, adoption_mode={adoption_mode}, repo_role={repo_role})."
            )
            return 0
        print(
            f"No adapter mappings found for selection={selected_display} under {adapters_root.as_posix()} "
            f"(selector={selector}, adoption_mode={adoption_mode}, repo_role={repo_role})."
        )
        return 1
    selected_display = ",".join(sorted(selected_platforms)) if selected_platforms else "all"
    print(f"Adapter selection: {selected_display} (selector={selector})")
    issues: list[str] = []
    destination_preserve_paths: dict[Path, set[Path]] = defaultdict(set)
    loaded_mappings: list[tuple[str, list[Mapping]]] = []
    all_mappings: list[Mapping] = []
    for mapping_file in mapping_files:
        platform, mappings = _load_mapping(mapping_file)
        loaded_mappings.append((platform, mappings))
        all_mappings.extend(mappings)
    for _, mappings in loaded_mappings:
        for mapping in mappings:
            dst_root = root / mapping.destination
            if mapping.mode == "copy_tree":
                src_root = root / mapping.source
                if src_root.exists():
                    pattern = mapping.include_glob or "**/*"
                    destination_preserve_paths[dst_root].update(
                        _expected_tree_paths(src_root, pattern)
                    )
            elif mapping.mode == "render_codex_rules_tree":
                src_root = root / mapping.source
                if src_root.exists():
                    pattern = mapping.include_glob or "*.md"
                    destination_preserve_paths[dst_root].update(
                        _expected_codex_rules_paths(src_root, pattern, dst_root)
                    )
            elif mapping.mode == "render_workflow_skills_tree":
                src_root = root / mapping.source
                if src_root.exists():
                    pattern = mapping.include_glob or "*.md"
                    destination_preserve_paths[dst_root].update(
                        _expected_workflow_skill_paths(src_root, pattern)
                    )

    destination_roots = list(destination_preserve_paths.keys())
    for dst_root in destination_roots:
        for other_root in destination_roots:
            if other_root == dst_root:
                continue
            try:
                rel = other_root.relative_to(dst_root)
            except ValueError:
                continue
            destination_preserve_paths[dst_root].update(
                rel / path for path in destination_preserve_paths[other_root]
            )
    for platform, mappings in loaded_mappings:
        for mapping in mappings:
            dst_root = root / mapping.destination
            preserve_paths = _preserve_paths_for_destination(destination_preserve_paths, dst_root)
            if mapping.mode == "copy_tree":
                issues.extend(
                    _sync_tree(
                        root,
                        mapping,
                        check=args.check,
                        preserve_paths=preserve_paths,
                    )
                )
            elif mapping.mode == "render_codex_rules_tree":
                issues.extend(
                    _sync_codex_rules_tree(
                        root,
                        mapping,
                        check=args.check,
                        preserve_paths=preserve_paths,
                    )
                )
            elif mapping.mode == "render_workflow_skills_tree":
                issues.extend(
                    _sync_workflow_skills_tree(
                        root,
                        mapping,
                        check=args.check,
                        preserve_paths=preserve_paths,
                    )
                )
            else:
                issues.extend(_sync_file(root, mapping, platform=platform, check=args.check))
        print(f"Processed adapter: {platform}")
    if args.check and not selected_platforms:
        issues.extend(
            f"Orphan generated surface: {path.as_posix()}"
            for path in _find_orphan_generated_surfaces(root, all_mappings)
        )
    if issues:
        print("Agent adapter sync check failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1
    if args.check:
        print("Agent adapter outputs are up to date.")
    else:
        print("Agent adapter outputs synchronized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
