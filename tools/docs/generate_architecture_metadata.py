"""
@meta
name: generate_architecture_metadata
type: script
domain: docs
responsibility:
  - Generate feature contracts and discovery indexes from feature source metadata.
  - Validate architecture metadata shape for feature, spec, plan, code, and test lineage.
  - Generate canonical feature-local lineage evidence and aggregate architecture indexes.
inputs:
  - docs/features/*/feature.source.yaml
  - docs/superpowers/specs/*.md
  - docs/superpowers/plans/*.md
  - Markdown docs frontmatter with doc_id/explains metadata
  - YAML # @architecture metadata in configs and AML components
  - Python @meta, @capability, and @proves markers
  - Setup-script @meta ownership blocks in setup/*.ps1 and setup/*.sh
outputs:
  - docs/features/<feature_id>/<feature_id>.yaml
  - docs/features/<feature_id>/lineage.generated.yaml
  - docs/features/<feature_id>/history.md
  - docs/stages/<stage_id>.yaml
  - docs/generated/capability_lineage.yaml
  - docs/generated/architecture_dag.yaml
tags:
  - docs
  - lineage
  - metadata
distribution_tier: starter_kit
lifecycle:
  status: active
"""

# Canonical generated lineage contract:
# - docs/features/<feature_id>/lineage.generated.yaml is the feature-local evidence surface
# - it is capability-keyed and evidence-oriented
# - it is not a summary contract, naming-policy dump, or refs inventory

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import fnmatch
import os
from pathlib import Path
import re
import sys
from typing import Iterable, Mapping

import yaml


SCRIPTS_ROOT = Path(__file__).resolve().parents[2] / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from validator_policy import (  # noqa: E402
    FORBIDDEN_MANUAL_REFS_FIELD,
    feature_source_has_forbidden_manual_refs,
    format_manual_refs_forbidden_message,
)


GENERATED_HEADER = "# GENERATED FILE - do not edit directly.\n"
GENERATED_HISTORY_START = "<!-- GENERATED HISTORY START -->"
GENERATED_HISTORY_END = "<!-- GENERATED HISTORY END -->"
HUMAN_HISTORY_HEADING = "## Human Notes"
MAX_LINE_WIDTH = 10_000
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*(?:\.[a-z0-9]+(?:-[a-z0-9]+)*)?$")
STAGE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
TIMESTAMP_FIELDS = ("created_at", "updated_at", "completed_at")
ALLOWED_EVIDENCE_GAPS = {"missing_code_evidence", "missing_test_evidence"}
ALLOWED_LINEAGE_EXCEPTION_REASONS = {
    "pending-lineage-linkage-rollout",
    "docs-only-concept",
    "cloud-proof-deferred",
    "split-capability-needed",
}
ALLOWED_AFFECTS_KEYS = {
    "features",
    "capabilities",
    "invariants",
    "stages",
    "code",
    "tests",
    "docs",
    "operating_system",
    "generated",
}
ALLOWED_DAG_KEYS = {"depends_on", "enables", "supersedes", "related", "produces", "blocks"}
ALLOWED_EXPLAINS_KEYS = {"features", "capabilities", "stages", "configs", "components"}
ALLOWED_YAML_ARCHITECTURE_KEYS = {
    "owner",
    "features",
    "stages",
    "capabilities",
    "invariants",
    "role",
    "canonical",
}
ALLOWED_YAML_ARCHITECTURE_ROLES = {"config", "component", "fixture", "contract"}
ALLOWED_STAGE_SOURCE_FIELDS = {
    "stage_id",
    "name",
    "status",
    "purpose",
    "workflow_position",
    "primary_features",
    "supporting_features",
    "depends_on",
    "hands_off_to",
    "inputs",
    "outputs",
    "invariants",
    "human_notes",
    "docs_only",
}
GENERATED_STAGE_SOURCE_FIELDS = {
    "feature_refs",
    "capability_refs",
    "code_refs",
    "test_refs",
    "doc_refs",
    "config_refs",
    "component_refs",
}
STAGE_SOURCE_FEATURE_ROLE_FIELDS = {
    "primary_features": "primary",
    "supporting_features": "supporting",
}
ALLOWED_STAGE_FEATURE_ROLES = set(STAGE_SOURCE_FEATURE_ROLE_FIELDS.values())
ALLOWED_STAGE_PARTICIPATION_FIELDS = {"stage_id", "role", "capability_ids"}
IGNORED_PARTS = {
    ".git",
    ".venv",
    ".uv-python",
    ".worktrees",
    ".tmp-tests",
    "__pycache__",
    ".agents",
    ".claude",
    ".codex",
    "agent-core",
}


class IndentedSafeDumper(yaml.SafeDumper):
    def increase_indent(self, flow: bool = False, indentless: bool = False) -> object:
        return super().increase_indent(flow, False)


def quote_yaml_key(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def normalize_explicit_string_keys(yaml_text: str) -> str:
    lines = yaml_text.splitlines()
    normalized: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        stripped = line.lstrip(" ")
        indent = line[: len(line) - len(stripped)]

        if stripped.startswith("? ") and index + 1 < len(lines):
            next_line = lines[index + 1]
            next_stripped = next_line.lstrip(" ")
            next_indent = next_line[: len(next_line) - len(next_stripped)]
            if next_indent == indent and next_stripped.startswith(": "):
                normalized.append(f"{indent}{quote_yaml_key(stripped[2:])}:")
                normalized.append(f"{indent}  {next_stripped[2:]}")
                index += 2
                continue

        normalized.append(line)
        index += 1

    trailing_newline = "\n" if yaml_text.endswith("\n") else ""
    return "\n".join(normalized) + trailing_newline


@dataclass(frozen=True)
class MetadataDocument:
    path: Path
    relative_path: str
    frontmatter: dict[str, object]


@dataclass(frozen=True)
class EvidenceNode:
    path: str
    symbols: tuple[str, ...]
    confidence: str
    source: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "path": self.path,
            "confidence": self.confidence,
            "source": list(self.source),
        }
        if self.symbols:
            payload["symbols"] = list(self.symbols)
        return payload


@dataclass(frozen=True)
class CodeMetadata:
    path: str
    metadata: dict[str, object]
    marker_kind: str


@dataclass(frozen=True)
class YamlArchitectureMetadata:
    path: str
    metadata: dict[str, object]
    artifact_kind: str


@dataclass(frozen=True)
class CapabilityLineageException:
    reason: str
    allowed_gaps: tuple[str, ...]


@dataclass(frozen=True)
class ArchitectureBuildResult:
    outputs: dict[Path, str]
    completeness_failures: tuple[str, ...]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def relative_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def dump_yaml(payload: object) -> str:
    dumped = yaml.dump(
        payload,
        Dumper=IndentedSafeDumper,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=False,
        width=MAX_LINE_WIDTH,
    )
    return normalize_explicit_string_keys(dumped)


def load_yaml_mapping(path: Path) -> dict[str, object]:
    parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError(f"{path}: expected a top-level mapping")
    return parsed


def parse_frontmatter(path: Path, root: Path) -> MetadataDocument | None:
    text = path.read_text(encoding="utf-8")
    if text.startswith("\ufeff"):
        text = text.removeprefix("\ufeff")
    if not text.startswith("---"):
        if text.lstrip().startswith("---"):
            raise ValueError(f"{relative_path(path, root)}: frontmatter must start at the first byte")
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{relative_path(path, root)}: frontmatter block is not properly closed")
    try:
        parsed = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        raise ValueError(f"{relative_path(path, root)}: could not parse frontmatter: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{relative_path(path, root)}: frontmatter must be a top-level mapping")
    return MetadataDocument(path=path, relative_path=relative_path(path, root), frontmatter=parsed)


def parse_python_metadata(path: Path, root: Path) -> CodeMetadata:
    text = path.read_text(encoding="utf-8")
    rel_path = relative_path(path, root)
    docstring_match = re.match(
        r"\A(?:#![^\r\n]*(?:\r?\n))?\s*([\"']{3})(.*?)\1",
        text,
        flags=re.DOTALL,
    )
    if docstring_match is None:
        raise ValueError(f"{rel_path}: missing @meta top-of-file metadata")

    body = docstring_match.group(2)
    lines = body.splitlines()
    meta_line_index = next(
        (index for index, line in enumerate(lines) if line.strip() == "@meta"),
        None,
    )
    if meta_line_index is None:
        raise ValueError(f"{rel_path}: missing @meta top-of-file metadata")

    meta_text = "\n".join(lines[meta_line_index + 1 :]).strip()
    parsed = yaml.safe_load(meta_text) if meta_text else {}
    if not isinstance(parsed, dict):
        raise ValueError(f"{rel_path}: @meta must be a YAML mapping")
    if not isinstance(parsed.get("type"), str):
        raise ValueError(f"{rel_path}: @meta.type must be a string")
    return CodeMetadata(path=rel_path, metadata=parsed, marker_kind="python_meta")


def parse_setup_script_metadata(path: Path, root: Path) -> CodeMetadata | None:
    text = path.read_text(encoding="utf-8")
    rel_path = relative_path(path, root)
    lines = text.splitlines()

    if path.suffix == ".sh" and lines and lines[0].startswith("#!"):
        lines = lines[1:]

    comment_lines: list[str] = []
    meta_started = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if meta_started:
                break
            continue
        if not stripped.startswith("#"):
            break
        comment_body = stripped[1:].lstrip()
        if comment_body == "@meta":
            meta_started = True
            continue
        if meta_started:
            if comment_body == "":
                break
            comment_lines.append(comment_body)

    if not meta_started:
        return None

    meta_text = "\n".join(comment_lines).strip()
    parsed = yaml.safe_load(meta_text) if meta_text else {}
    if not isinstance(parsed, dict):
        raise ValueError(f"{rel_path}: @meta must be a YAML mapping")
    if not isinstance(parsed.get("type"), str):
        raise ValueError(f"{rel_path}: @meta.type must be a string")
    return CodeMetadata(path=rel_path, metadata=parsed, marker_kind="shell_meta")


def parse_yaml_architecture_metadata(
    path: Path,
    root: Path,
    artifact_kind: str,
) -> YamlArchitectureMetadata | None:
    text = path.read_text(encoding="utf-8")
    rel_path = relative_path(path, root)
    comment_lines: list[str] = []
    meta_started = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if meta_started:
                break
            continue
        if not stripped.startswith("#"):
            break
        comment_body = stripped[1:].lstrip()
        if comment_body == "@architecture":
            meta_started = True
            continue
        if meta_started:
            if ":" not in comment_body and not comment_body.lstrip().startswith("-"):
                break
            comment_lines.append(comment_body)

    if not meta_started:
        return None

    meta_text = "\n".join(comment_lines).strip()
    parsed = yaml.safe_load(meta_text) if meta_text else {}
    if not isinstance(parsed, dict):
        raise ValueError(f"{rel_path}: @architecture must be a YAML mapping")
    validate_yaml_architecture_metadata(parsed, rel_path)
    return YamlArchitectureMetadata(
        path=rel_path,
        metadata=parsed,
        artifact_kind=artifact_kind,
    )


def iter_files(root: Path, pattern: str) -> Iterable[Path]:
    matched_paths: list[Path] = []
    for current_root, dirnames, filenames in os.walk(root, topdown=True):
        dirnames[:] = sorted(
            dirname for dirname in dirnames if dirname not in IGNORED_PARTS
        )
        current_root_path = Path(current_root)
        for filename in sorted(filenames):
            if not fnmatch.fnmatch(filename, pattern):
                continue
            path = current_root_path / filename
            if path.is_file():
                matched_paths.append(path)
    yield from matched_paths


def require_string(mapping: Mapping[str, object], key: str, owner: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{owner}: {key} must be a non-empty string")
    return value


def validate_id(value: str, field_name: str, owner: str) -> None:
    if not ID_PATTERN.match(value):
        raise ValueError(f"{owner}: {field_name} has invalid id format: {value}")


def validate_stage_id(value: str, field_name: str, owner: str) -> None:
    if not STAGE_ID_PATTERN.match(value):
        raise ValueError(f"{owner}: {field_name} has invalid stage id format: {value}")


def validate_timestamp(value: object, field_name: str, owner: str) -> None:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError(
                f"{owner}: {field_name} must be an ISO 8601 timestamp with timezone"
            )
        return
    if not isinstance(value, str):
        raise ValueError(f"{owner}: {field_name} must be an ISO 8601 timestamp with timezone")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{owner}: {field_name} must be an ISO 8601 timestamp with timezone"
        ) from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{owner}: {field_name} must be an ISO 8601 timestamp with timezone")


def validate_string_list(value: object, owner: str, field_name: str) -> None:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{owner}: {field_name} must be a list of strings")


def optional_string_list(value: object, owner: str, field_name: str) -> list[str]:
    if value is None:
        return []
    validate_string_list(value, owner, field_name)
    return list(value)


def validate_affects(value: object, owner: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{owner}: affects must be a mapping")
    unknown_keys = set(value) - ALLOWED_AFFECTS_KEYS
    if unknown_keys:
        raise ValueError(f"{owner}: affects has unknown keys: {', '.join(sorted(unknown_keys))}")
    for key, item in value.items():
        validate_string_list(item, owner, f"affects.{key}")


def validate_dag(value: object, owner: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{owner}: dag must be a mapping")
    unknown_keys = set(value) - ALLOWED_DAG_KEYS
    if unknown_keys:
        raise ValueError(f"{owner}: dag has unknown keys: {', '.join(sorted(unknown_keys))}")
    for key, item in value.items():
        validate_string_list(item, owner, f"dag.{key}")


def validate_explains(value: object, owner: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{owner}: explains must be a mapping")
    unknown_keys = set(value) - ALLOWED_EXPLAINS_KEYS
    if unknown_keys:
        raise ValueError(f"{owner}: explains has unknown keys: {', '.join(sorted(unknown_keys))}")
    for key, item in value.items():
        validate_string_list(item, owner, f"explains.{key}")


def validate_yaml_architecture_metadata(metadata: Mapping[str, object], owner: str) -> None:
    unknown_keys = set(metadata) - ALLOWED_YAML_ARCHITECTURE_KEYS
    if unknown_keys:
        raise ValueError(
            f"{owner}: @architecture has unknown keys: {', '.join(sorted(unknown_keys))}"
        )
    require_string(metadata, "owner", owner)
    for field_name in ("features", "stages", "capabilities", "invariants"):
        if field_name in metadata:
            validate_string_list(metadata[field_name], owner, field_name)
    if "features" not in metadata:
        raise ValueError(f"{owner}: @architecture.features is required")
    if "stages" not in metadata:
        raise ValueError(f"{owner}: @architecture.stages is required")
    role = metadata.get("role")
    if role is not None and role not in ALLOWED_YAML_ARCHITECTURE_ROLES:
        raise ValueError(
            f"{owner}: @architecture.role must be one of "
            + ", ".join(sorted(ALLOWED_YAML_ARCHITECTURE_ROLES))
        )
    canonical = metadata.get("canonical")
    if canonical is not None and not isinstance(canonical, bool):
        raise ValueError(f"{owner}: @architecture.canonical must be a boolean")


def validate_feature_capability_id(
    *,
    feature_id: str,
    capability_id: str,
    owner: str,
) -> None:
    expected_prefix = f"{feature_id}."
    if not capability_id.startswith(expected_prefix):
        raise ValueError(f"{owner}: capability_id must start with {expected_prefix}")


def validate_feature_source(source: Mapping[str, object], owner: str) -> None:
    feature_id = require_string(source, "feature_id", owner)
    validate_id(feature_id, "feature_id", owner)
    for key in ("name", "status", "type", "summary"):
        require_string(source, key, owner)
    if "version" in source:
        raise ValueError(
            f"{owner}: version is no longer supported; feature freshness is "
            "generated from completed plan metadata"
        )

    declared_capability_ids: set[str] = set()
    for item_key, id_key in (("invariants", "invariant_id"), ("capabilities", "capability_id")):
        items = source.get(item_key, [])
        if not isinstance(items, list):
            raise ValueError(f"{owner}: {item_key} must be a list")
        for item in items:
            if not isinstance(item, dict):
                raise ValueError(f"{owner}: {item_key} entries must be mappings")
            item_id = require_string(item, id_key, owner)
            validate_id(item_id, id_key, owner)
            require_string(item, "statement", owner)
            require_string(item, "state", owner)
            if item_key == "capabilities":
                validate_feature_capability_id(
                    feature_id=feature_id,
                    capability_id=item_id,
                    owner=owner,
                )
                declared_capability_ids.add(item_id)
    if feature_source_has_forbidden_manual_refs(source):
        raise ValueError(format_manual_refs_forbidden_message(owner=owner))
    validate_stage_participation(
        source=source,
        owner=owner,
        declared_capability_ids=declared_capability_ids,
    )
    validate_lineage_exceptions(
        source=source,
        owner=owner,
        declared_capability_ids=declared_capability_ids,
    )


def validate_stage_participation(
    *,
    source: Mapping[str, object],
    owner: str,
    declared_capability_ids: set[str],
) -> None:
    stage_participation = source.get("stage_participation")
    if stage_participation is None:
        return
    if not isinstance(stage_participation, list):
        raise ValueError(f"{owner}: stage_participation must be a list")
    seen_stage_ids: set[str] = set()
    for index, participation in enumerate(stage_participation):
        participation_owner = f"{owner}: stage_participation[{index}]"
        if not isinstance(participation, dict):
            raise ValueError(f"{participation_owner} must be a mapping")
        unknown_keys = set(participation) - ALLOWED_STAGE_PARTICIPATION_FIELDS
        if unknown_keys:
            raise ValueError(
                f"{participation_owner}: unknown keys: {', '.join(sorted(unknown_keys))}"
            )
        stage_id = require_string(participation, "stage_id", participation_owner)
        validate_stage_id(stage_id, "stage_id", participation_owner)
        if stage_id in seen_stage_ids:
            raise ValueError(
                f"{participation_owner}: duplicate stage_participation entry for {stage_id}"
            )
        seen_stage_ids.add(stage_id)
        role = require_string(participation, "role", participation_owner)
        if role not in ALLOWED_STAGE_FEATURE_ROLES:
            raise ValueError(
                f"{participation_owner}: role must be one of "
                + ", ".join(sorted(ALLOWED_STAGE_FEATURE_ROLES))
            )
        capability_ids = participation.get("capability_ids", [])
        validate_string_list(capability_ids, participation_owner, "capability_ids")
        seen_capability_ids: set[str] = set()
        for capability_id in capability_ids:
            if capability_id not in declared_capability_ids:
                raise ValueError(
                    f"{participation_owner}: capability_ids references unknown capability: "
                    f"{capability_id}"
                )
            if capability_id in seen_capability_ids:
                raise ValueError(
                    f"{participation_owner}: duplicate capability_ids entry: {capability_id}"
                )
            seen_capability_ids.add(capability_id)


def feature_stage_participation_map(source: Mapping[str, object]) -> dict[str, dict[str, object]]:
    participation_map: dict[str, dict[str, object]] = {}
    stage_participation = source.get("stage_participation", [])
    if not isinstance(stage_participation, list):
        return participation_map
    for participation in stage_participation:
        if not isinstance(participation, dict):
            continue
        stage_id = participation.get("stage_id")
        role = participation.get("role")
        capability_ids = participation.get("capability_ids", [])
        if not isinstance(stage_id, str) or not isinstance(role, str):
            continue
        if not isinstance(capability_ids, list) or not all(
            isinstance(item, str) for item in capability_ids
        ):
            continue
        participation_map[stage_id] = {
            "role": role,
            "capability_ids": list(capability_ids),
        }
    return participation_map


def validate_lineage_exceptions(
    *,
    source: Mapping[str, object],
    owner: str,
    declared_capability_ids: set[str],
) -> None:
    lineage_exceptions = source.get("lineage_exceptions")
    if lineage_exceptions is None:
        return
    if not isinstance(lineage_exceptions, dict):
        raise ValueError(f"{owner}: lineage_exceptions must be a mapping")
    capability_exceptions = lineage_exceptions.get("capabilities", [])
    if not isinstance(capability_exceptions, list):
        raise ValueError(f"{owner}: lineage_exceptions.capabilities must be a list")
    seen_capability_ids: set[str] = set()
    for index, exception in enumerate(capability_exceptions):
        exception_owner = f"{owner}: lineage_exceptions.capabilities[{index}]"
        if not isinstance(exception, dict):
            raise ValueError(f"{exception_owner} must be a mapping")
        reason = require_string(exception, "reason", exception_owner)
        if reason not in ALLOWED_LINEAGE_EXCEPTION_REASONS:
            raise ValueError(
                f"{exception_owner}: reason must be one of "
                + ", ".join(sorted(ALLOWED_LINEAGE_EXCEPTION_REASONS))
            )
        allowed_gaps = exception.get("allowed_gaps")
        validate_string_list(allowed_gaps, exception_owner, "allowed_gaps")
        unknown_gaps = set(allowed_gaps) - ALLOWED_EVIDENCE_GAPS
        if unknown_gaps:
            raise ValueError(
                f"{exception_owner}: allowed_gaps has unknown values: "
                + ", ".join(sorted(unknown_gaps))
            )
        capability_ids = exception.get("capability_ids")
        validate_string_list(capability_ids, exception_owner, "capability_ids")
        for capability_id in capability_ids:
            if capability_id not in declared_capability_ids:
                raise ValueError(
                    f"{exception_owner}: capability_ids references unknown capability: "
                    f"{capability_id}"
                )
            if capability_id in seen_capability_ids:
                raise ValueError(
                    f"{exception_owner}: duplicate lineage exception for capability: "
                    f"{capability_id}"
                )
            seen_capability_ids.add(capability_id)


def capability_lineage_exceptions(
    source: Mapping[str, object],
) -> dict[str, CapabilityLineageException]:
    lineage_exceptions = source.get("lineage_exceptions", {})
    if not isinstance(lineage_exceptions, dict):
        return {}
    capability_exceptions = lineage_exceptions.get("capabilities", [])
    if not isinstance(capability_exceptions, list):
        return {}
    exception_map: dict[str, CapabilityLineageException] = {}
    for exception in capability_exceptions:
        if not isinstance(exception, dict):
            continue
        reason = exception.get("reason")
        allowed_gaps = exception.get("allowed_gaps")
        capability_ids = exception.get("capability_ids")
        if not isinstance(reason, str):
            continue
        if not isinstance(allowed_gaps, list) or not all(isinstance(item, str) for item in allowed_gaps):
            continue
        if not isinstance(capability_ids, list) or not all(isinstance(item, str) for item in capability_ids):
            continue
        payload = CapabilityLineageException(
            reason=reason,
            allowed_gaps=tuple(sorted(allowed_gaps)),
        )
        for capability_id in capability_ids:
            exception_map[capability_id] = payload
    return exception_map


def feature_directories(root: Path) -> list[Path]:
    features_root = root / "docs" / "features"
    if not features_root.exists():
        return []
    return sorted(path for path in features_root.iterdir() if path.is_dir())


def extract_history_heading(text: str) -> str | None:
    stripped = text.lstrip()
    if not stripped.startswith("# "):
        return None
    heading, _, _ = stripped.partition("\n")
    return heading.strip()


def extract_existing_human_history(history_path: Path) -> tuple[str | None, str]:
    if not history_path.exists():
        return None, ""

    text = history_path.read_text(encoding="utf-8")
    heading = extract_history_heading(text)
    if GENERATED_HISTORY_START in text and GENERATED_HISTORY_END in text:
        after_end = text.split(GENERATED_HISTORY_END, 1)[1].lstrip("\n")
        if after_end.startswith(HUMAN_HISTORY_HEADING):
            body = after_end[len(HUMAN_HISTORY_HEADING) :].lstrip()
        else:
            body = after_end.strip()
        return heading, body.rstrip()

    legacy_body = text
    if heading is not None:
        legacy_body = legacy_body.split("\n", 1)[1] if "\n" in legacy_body else ""
    return heading, legacy_body.strip()


def validate_feature_folder_sources(root: Path) -> None:
    missing_sources: list[str] = []
    missing_histories: list[str] = []
    literal_placeholder_contracts: list[str] = []
    for folder in feature_directories(root):
        source_path = folder / "feature.source.yaml"
        if not source_path.exists():
            missing_sources.append(relative_path(source_path, root))
        history_path = folder / "history.md"
        if not history_path.exists():
            missing_histories.append(relative_path(history_path, root))
        literal_placeholder_path = folder / "<feature_id>.yaml"
        if literal_placeholder_path.exists():
            literal_placeholder_contracts.append(relative_path(literal_placeholder_path, root))
    if missing_sources:
        raise ValueError("Missing feature.source.yaml: " + ", ".join(missing_sources))
    if missing_histories:
        raise ValueError("Missing history.md: " + ", ".join(missing_histories))
    if literal_placeholder_contracts:
        raise ValueError(
            "Literal placeholder feature contract path is not allowed: "
            + ", ".join(literal_placeholder_contracts)
        )


def validate_metadata_document(document: MetadataDocument) -> None:
    metadata = document.frontmatter
    owner = document.relative_path
    for field_name in TIMESTAMP_FIELDS:
        if field_name in metadata:
            validate_timestamp(metadata[field_name], field_name, owner)

    for field_name in ("change_id", "plan_id", "feature_name"):
        value = metadata.get(field_name)
        if isinstance(value, str):
            validate_id(value, field_name, owner)

    if "affects" in metadata:
        validate_affects(metadata["affects"], owner)
    if "dag" in metadata:
        validate_dag(metadata["dag"], owner)

    if metadata.get("status") == "complete":
        if "completed_at" not in metadata:
            raise ValueError(f"{owner}: complete plans must include completed_at")
        outcome = metadata.get("outcome")
        if not isinstance(outcome, dict) or not isinstance(outcome.get("summary"), str):
            raise ValueError(f"{owner}: complete plans must include outcome.summary")

    if "explains" in metadata:
        validate_explains(metadata["explains"], owner)


def validate_stage_source(source: Mapping[str, object], owner: str) -> None:
    forbidden_keys = set(source) & GENERATED_STAGE_SOURCE_FIELDS
    if forbidden_keys:
        raise ValueError(
            f"{owner}: generated stage fields are not allowed in source: "
            + ", ".join(sorted(forbidden_keys))
        )
    unknown_keys = set(source) - ALLOWED_STAGE_SOURCE_FIELDS
    if unknown_keys:
        raise ValueError(f"{owner}: stage source has unknown keys: {', '.join(sorted(unknown_keys))}")
    stage_id = require_string(source, "stage_id", owner)
    validate_stage_id(stage_id, "stage_id", owner)
    for key in ("name", "status", "purpose"):
        require_string(source, key, owner)
    for key in (
        "primary_features",
        "supporting_features",
        "depends_on",
        "hands_off_to",
        "inputs",
        "outputs",
        "human_notes",
    ):
        if key in source:
            validate_string_list(source[key], owner, key)
    stage_source_feature_roles(source, owner)
    if "invariants" in source:
        invariants = source["invariants"]
        if not isinstance(invariants, list) or not all(isinstance(item, str) for item in invariants):
            raise ValueError(f"{owner}: invariants must be a list of strings")
    if "docs_only" in source and not isinstance(source["docs_only"], bool):
        raise ValueError(f"{owner}: docs_only must be a boolean")


def stage_source_feature_roles(
    stage_source: Mapping[str, object],
    owner: str,
) -> dict[str, str]:
    roles: dict[str, str] = {}
    for field_name, role in STAGE_SOURCE_FEATURE_ROLE_FIELDS.items():
        feature_ids = optional_string_list(stage_source.get(field_name), owner, field_name)
        seen_in_field: set[str] = set()
        for feature_id in feature_ids:
            validate_id(feature_id, field_name, owner)
            if feature_id in seen_in_field:
                raise ValueError(f"{owner}: duplicate {field_name} entry: {feature_id}")
            if feature_id in roles:
                raise ValueError(
                    f"{owner}: feature {feature_id} cannot appear in multiple stage role lists"
                )
            seen_in_field.add(feature_id)
            roles[feature_id] = role
    return roles


def validate_stage_feature_linkage(
    *,
    feature_sources: Iterable[Mapping[str, object]],
    stage_sources: Iterable[Mapping[str, object]],
) -> None:
    source_by_feature = {
        require_string(source, "feature_id", "feature source"): source for source in feature_sources
    }
    stage_source_by_id = {
        require_string(stage_source, "stage_id", "stage source"): stage_source
        for stage_source in stage_sources
    }
    for stage_id, stage_source in stage_source_by_id.items():
        stage_owner = f"docs/stages/{stage_id}.source.yaml"
        feature_roles = stage_source_feature_roles(stage_source, stage_owner)
        for feature_id, stage_role in feature_roles.items():
            source = source_by_feature.get(feature_id)
            if source is None:
                raise ValueError(f"{stage_owner}: unknown feature reference: {feature_id}")
            feature_participation = feature_stage_participation_map(source).get(stage_id)
            if feature_participation is None:
                raise ValueError(
                    f"{stage_owner}: feature {feature_id} is missing matching "
                    f"stage_participation in docs/features/{feature_id}/feature.source.yaml"
                )
            feature_role = feature_participation.get("role")
            if feature_role != stage_role:
                raise ValueError(
                    f"{stage_owner}: feature {feature_id} role {stage_role} does not match "
                    f"docs/features/{feature_id}/feature.source.yaml role {feature_role}"
                )
    for feature_id, source in source_by_feature.items():
        source_owner = f"docs/features/{feature_id}/feature.source.yaml"
        for stage_id, participation in feature_stage_participation_map(source).items():
            stage_source = stage_source_by_id.get(stage_id)
            if stage_source is None:
                raise ValueError(
                    f"{source_owner}: stage_participation references unknown stage: {stage_id}"
                )
            stage_roles = stage_source_feature_roles(
                stage_source,
                f"docs/stages/{stage_id}.source.yaml",
            )
            stage_role = stage_roles.get(feature_id)
            if stage_role is None:
                raise ValueError(
                    f"{source_owner}: stage_participation references {stage_id} but "
                    f"docs/stages/{stage_id}.source.yaml does not list {feature_id}"
                )
            feature_role = participation.get("role")
            if feature_role != stage_role:
                raise ValueError(
                    f"{source_owner}: stage_participation role {feature_role} for {stage_id} "
                    f"does not match docs/stages/{stage_id}.source.yaml role {stage_role}"
                )


def load_feature_sources(root: Path) -> list[dict[str, object]]:
    validate_feature_folder_sources(root)
    sources: list[dict[str, object]] = []
    for path in sorted((root / "docs" / "features").glob("*/feature.source.yaml")):
        source = load_yaml_mapping(path)
        validate_feature_source(source, relative_path(path, root))
        sources.append(source)
    return sources


def load_stage_sources(root: Path) -> list[dict[str, object]]:
    stages_root = root / "docs" / "stages"
    if not stages_root.exists():
        return []
    sources: list[dict[str, object]] = []
    for path in sorted(stages_root.glob("*.source.yaml")):
        source = load_yaml_mapping(path)
        validate_stage_source(source, relative_path(path, root))
        sources.append(source)
    return sources


def stage_ids_from_sources_or_contracts(root: Path, stage_sources: Iterable[Mapping[str, object]]) -> set[str]:
    source_ids = {
        require_string(source, "stage_id", "stage source") for source in stage_sources
    }
    if source_ids:
        return source_ids
    stages_root = root / "docs" / "stages"
    if not stages_root.exists():
        return set()
    return {
        path.stem
        for path in stages_root.glob("*.yaml")
        if path.is_file() and not path.name.endswith(".source.yaml")
    }


def load_code_metadata(root: Path) -> list[CodeMetadata]:
    metadata: list[CodeMetadata] = [
        parse_python_metadata(path, root) for path in iter_files(root, "*.py")
    ]
    for pattern in ("setup/*.ps1", "setup/*.sh"):
        for path in sorted(root.glob(pattern)):
            if not path.is_file():
                continue
            parsed = parse_setup_script_metadata(path, root)
            if parsed is not None:
                metadata.append(parsed)
    return metadata


def load_yaml_architecture_metadata(root: Path) -> list[YamlArchitectureMetadata]:
    metadata: list[YamlArchitectureMetadata] = []
    for folder, artifact_kind in (("aml/components", "component"), ("configs", "config")):
        for path in sorted((root / folder).glob("*.yaml")):
            parsed = parse_yaml_architecture_metadata(path, root, artifact_kind)
            if parsed is not None:
                metadata.append(parsed)
    return metadata


def load_metadata_documents(root: Path, folder: str) -> list[MetadataDocument]:
    docs_folder = root / "docs" / "superpowers" / folder
    if not docs_folder.exists():
        return []
    documents: list[MetadataDocument] = []
    for path in sorted(docs_folder.glob("*.md")):
        document = parse_frontmatter(path, root)
        if document is None:
            continue
        validate_metadata_document(document)
        documents.append(document)
    return documents


def load_explanation_documents(root: Path) -> list[MetadataDocument]:
    documents: list[MetadataDocument] = []
    docs_root = root / "docs"
    if not docs_root.exists():
        return documents
    for path in sorted(docs_root.rglob("*.md")):
        if "superpowers" in path.relative_to(root).parts:
            continue
        document = parse_frontmatter(path, root)
        if document is not None:
            validate_metadata_document(document)
            documents.append(document)
    validate_unique_doc_ids(documents)
    return documents


def validate_unique_doc_ids(documents: Iterable[MetadataDocument]) -> None:
    seen: dict[str, str] = {}
    for document in documents:
        doc_id = document.frontmatter.get("doc_id")
        if not isinstance(doc_id, str):
            continue
        validate_id(doc_id, "doc_id", document.relative_path)
        previous = seen.get(doc_id)
        if previous is not None:
            raise ValueError(
                f"{document.relative_path}: duplicate doc_id {doc_id}; first seen in {previous}"
            )
        seen[doc_id] = document.relative_path


def metadata_mentions_feature(document: MetadataDocument, feature_id: str) -> bool:
    affects = document.frontmatter.get("affects")
    if not isinstance(affects, dict):
        return False
    features = affects.get("features", [])
    return isinstance(features, list) and feature_id in features


def metadata_mentions_capability(document: MetadataDocument, capability_id: str) -> bool:
    affects = document.frontmatter.get("affects")
    if not isinstance(affects, dict):
        return False
    capabilities = affects.get("capabilities", [])
    return isinstance(capabilities, list) and capability_id in capabilities


def metadata_explains_capability(document: MetadataDocument, capability_id: str) -> bool:
    explains = document.frontmatter.get("explains")
    if not isinstance(explains, dict):
        return False
    capabilities = explains.get("capabilities", [])
    return isinstance(capabilities, list) and capability_id in capabilities


def metadata_explains_feature(document: MetadataDocument, feature_id: str) -> bool:
    explains = document.frontmatter.get("explains")
    if not isinstance(explains, dict):
        return False
    features = explains.get("features", [])
    return isinstance(features, list) and feature_id in features


def metadata_explains_stage(document: MetadataDocument, stage_id: str) -> bool:
    explains = document.frontmatter.get("explains")
    if not isinstance(explains, dict):
        return False
    stages = explains.get("stages", [])
    return isinstance(stages, list) and stage_id in stages


def metadata_explains_path(document: MetadataDocument, key: str, path: str) -> bool:
    explains = document.frontmatter.get("explains")
    if not isinstance(explains, dict):
        return False
    values = explains.get(key, [])
    return isinstance(values, list) and path in values


def validate_known_references(
    *,
    documents: Iterable[MetadataDocument],
    feature_ids: set[str],
    capability_ids: set[str],
    invariant_ids: set[str],
    stage_ids: set[str],
    config_paths: set[str],
    component_paths: set[str],
) -> None:
    allowed_empty = {"none"}
    for document in documents:
        for block_name in ("affects", "explains"):
            references = document.frontmatter.get(block_name)
            if not isinstance(references, dict):
                continue

            reference_sets = {
                "features": feature_ids,
                "capabilities": capability_ids,
                "invariants": invariant_ids,
                "stages": stage_ids,
                "configs": config_paths,
                "components": component_paths,
            }
            for key, known_values in reference_sets.items():
                values = references.get(key, [])
                if not isinstance(values, list):
                    continue
                for value in values:
                    if value in allowed_empty:
                        continue
                    if isinstance(value, str) and value not in known_values:
                        singular = {
                            "features": "feature",
                            "capabilities": "capability",
                            "invariants": "invariant",
                            "stages": "stage",
                            "configs": "config",
                            "components": "component",
                        }[key]
                        raise ValueError(
                            f"{document.relative_path}: unknown {singular} reference: {value}"
                        )


def validate_yaml_architecture_references(
    *,
    yaml_metadata: Iterable[YamlArchitectureMetadata],
    feature_ids: set[str],
    capability_ids: set[str],
    invariant_ids: set[str],
    stage_ids: set[str],
) -> None:
    for artifact in yaml_metadata:
        owner = artifact.path
        owner_feature = artifact.metadata.get("owner")
        if isinstance(owner_feature, str) and owner_feature not in feature_ids:
            raise ValueError(f"{owner}: unknown owner feature reference: {owner_feature}")
        for key, known_values, singular in (
            ("features", feature_ids, "feature"),
            ("capabilities", capability_ids, "capability"),
            ("invariants", invariant_ids, "invariant"),
            ("stages", stage_ids, "stage"),
        ):
            values = artifact.metadata.get(key, [])
            if not isinstance(values, list):
                continue
            for value in values:
                if isinstance(value, str) and value not in known_values:
                    raise ValueError(f"{owner}: unknown {singular} reference: {value}")


def timestamp_to_string(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def extract_symbols_for_marker(text: str, marker: str, prefix: str) -> tuple[str, ...]:
    symbols: list[str] = []
    current_symbol: str | None = None
    for line in text.splitlines():
        function_match = re.match(r"\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", line)
        if function_match:
            current_symbol = function_match.group(1)
        if marker in line and current_symbol:
            symbols.append(current_symbol)
        if marker in line and current_symbol is None and prefix:
            symbols.append(prefix)
    return tuple(dict.fromkeys(symbols))


def is_test_path(path: str) -> bool:
    return path.startswith("tests/") or Path(path).name.startswith("test_")


def artifact_mentions_feature(artifact: YamlArchitectureMetadata, feature_id: str) -> bool:
    features = artifact.metadata.get("features", [])
    return isinstance(features, list) and feature_id in features


def artifact_mentions_capability(artifact: YamlArchitectureMetadata, capability_id: str) -> bool:
    capabilities = artifact.metadata.get("capabilities", [])
    return isinstance(capabilities, list) and capability_id in capabilities


def artifact_mentions_stage(artifact: YamlArchitectureMetadata, stage_id: str) -> bool:
    stages = artifact.metadata.get("stages", [])
    return isinstance(stages, list) and stage_id in stages


def artifact_paths_for_feature(
    artifacts: Iterable[YamlArchitectureMetadata],
    feature_id: str,
    artifact_kind: str,
) -> list[str]:
    return sorted(
        artifact.path
        for artifact in artifacts
        if artifact.artifact_kind == artifact_kind and artifact_mentions_feature(artifact, feature_id)
    )


def artifact_paths_for_capability(
    artifacts: Iterable[YamlArchitectureMetadata],
    capability_id: str,
    artifact_kind: str,
) -> list[str]:
    return sorted(
        artifact.path
        for artifact in artifacts
        if artifact.artifact_kind == artifact_kind
        and artifact_mentions_capability(artifact, capability_id)
    )


def artifact_evidence_for_capability(
    artifacts: Iterable[YamlArchitectureMetadata],
    capability_id: str,
    artifact_kind: str,
) -> list[dict[str, object]]:
    return [
        EvidenceNode(
            path=artifact.path,
            symbols=(),
            confidence="high",
            source=("yaml_architecture",),
        ).as_dict()
        for artifact in sorted(artifacts, key=lambda item: item.path)
        if artifact.artifact_kind == artifact_kind
        and artifact_mentions_capability(artifact, capability_id)
    ]


def scan_code_evidence(
    code_metadata: Iterable[CodeMetadata],
    root: Path,
    capability_id: str,
) -> tuple[list[EvidenceNode], list[EvidenceNode]]:
    code_nodes: list[EvidenceNode] = []
    test_nodes: list[EvidenceNode] = []
    for metadata in code_metadata:
        path = root / metadata.path
        text = path.read_text(encoding="utf-8")
        rel_path = metadata.path
        capability_marker = f"@capability {capability_id}"
        proves_marker = f"@proves {capability_id}"
        meta_capabilities = metadata.metadata.get("capabilities", [])
        meta_mentions_capability = (
            isinstance(meta_capabilities, list) and capability_id in meta_capabilities
        )

        if meta_mentions_capability and not is_test_path(rel_path):
            code_nodes.append(
                EvidenceNode(
                    path=rel_path,
                    symbols=(),
                    confidence="high",
                    source=(metadata.marker_kind,),
                )
            )
        if capability_marker in text and not is_test_path(rel_path):
            code_nodes.append(
                EvidenceNode(
                    path=rel_path,
                    symbols=extract_symbols_for_marker(text, capability_marker, ""),
                    confidence="high",
                    source=("python_capability",),
                )
            )
        if proves_marker in text:
            test_nodes.append(
                EvidenceNode(
                    path=rel_path,
                    symbols=extract_symbols_for_marker(text, proves_marker, ""),
                    confidence="high",
                    source=("python_proves",),
                )
            )
    return sorted(code_nodes, key=lambda node: node.path), sorted(test_nodes, key=lambda node: node.path)


def canonical_code_paths(nodes: Iterable[EvidenceNode]) -> list[str]:
    canonical_sources = {"python_capability", "shell_meta"}
    return sorted(
        {
            node.path
            for node in nodes
            if any(source in canonical_sources for source in node.source)
        }
    )


def collect_feature_refs(
    *,
    source: Mapping[str, object],
    specs: list[MetadataDocument],
    plans: list[MetadataDocument],
    docs: list[MetadataDocument],
    yaml_metadata: list[YamlArchitectureMetadata],
    capability_evidence: Mapping[str, dict[str, list[EvidenceNode]]],
) -> dict[str, list[str]]:
    feature_id = require_string(source, "feature_id", "feature source")
    code_paths: set[str] = set()
    test_paths: set[str] = set()
    docs_paths: set[str] = set()
    specs_paths: set[str] = set()
    plans_paths: set[str] = set()
    for evidence in capability_evidence.values():
        code_paths.update(canonical_code_paths(evidence["code"]))
        test_paths.update(node.path for node in evidence["tests"])
    specs_paths.update(
        document.relative_path for document in specs if metadata_mentions_feature(document, feature_id)
    )
    plans_paths.update(
        document.relative_path for document in plans if metadata_mentions_feature(document, feature_id)
    )
    docs_paths.update(document.relative_path for document in docs if metadata_explains_feature(document, feature_id))

    return {
        "code": sorted(code_paths),
        "tests": sorted(test_paths),
        "docs": sorted(docs_paths),
        "configs": artifact_paths_for_feature(yaml_metadata, feature_id, "config"),
        "components": artifact_paths_for_feature(yaml_metadata, feature_id, "component"),
        "specs": sorted(specs_paths),
        "plans": sorted(plans_paths),
    }


def build_feature_contract(
    *,
    source: Mapping[str, object],
    refs: Mapping[str, list[str]],
    plans: Iterable[MetadataDocument],
) -> str:
    feature_id = require_string(source, "feature_id", "feature source")
    payload: dict[str, object] = {
        "feature_id": source["feature_id"],
        "name": source["name"],
        "status": source["status"],
        "type": source["type"],
        "summary": source["summary"],
        "invariants": source.get("invariants", []),
        "domains": source.get("domains", []),
        "depends_on": source.get("depends_on", []),
        "capabilities": source.get("capabilities", []),
        "refs": dict(refs),
    }
    payload.update(feature_freshness_metadata(plans=plans, feature_id=feature_id))
    header = GENERATED_HEADER + f"# Source: docs/features/{feature_id}/feature.source.yaml\n"
    return header + dump_yaml(payload)


def feature_capability_ids(
    source_by_feature: Mapping[str, Mapping[str, object]],
    feature_ids: Iterable[str],
) -> list[str]:
    capability_ids: set[str] = set()
    for feature_id in feature_ids:
        source = source_by_feature.get(feature_id)
        if source is None:
            continue
        capabilities = source.get("capabilities", [])
        if not isinstance(capabilities, list):
            continue
        for capability in capabilities:
            if isinstance(capability, dict):
                capability_ids.add(require_string(capability, "capability_id", feature_id))
    return sorted(capability_ids)


def stage_feature_refs(stage_source: Mapping[str, object]) -> list[str]:
    stage_id = require_string(stage_source, "stage_id", "stage source")
    return list(
        stage_source_feature_roles(stage_source, f"docs/stages/{stage_id}.source.yaml").keys()
    )


def stage_capability_refs(
    *,
    stage_source: Mapping[str, object],
    feature_refs: Iterable[str],
    source_by_feature: Mapping[str, Mapping[str, object]],
    yaml_metadata: Iterable[YamlArchitectureMetadata],
) -> list[str]:
    stage_id = require_string(stage_source, "stage_id", "stage source")
    capability_refs: set[str] = set()
    for feature_id in feature_refs:
        source = source_by_feature.get(feature_id)
        if source is None:
            continue
        feature_stage_participation = feature_stage_participation_map(source).get(stage_id)
        if feature_stage_participation is None:
            continue
        capability_ids = feature_stage_participation.get("capability_ids", [])
        if isinstance(capability_ids, list):
            capability_refs.update(
                capability_id
                for capability_id in capability_ids
                if isinstance(capability_id, str)
            )
    for artifact in yaml_metadata:
        if artifact_mentions_stage(artifact, stage_id):
            capabilities = artifact.metadata.get("capabilities", [])
            if isinstance(capabilities, list):
                capability_refs.update(item for item in capabilities if isinstance(item, str))
    return sorted(capability_refs)


def code_refs_for_capabilities(
    capability_refs: Iterable[str],
    capability_evidence_by_id: Mapping[str, Mapping[str, list[EvidenceNode]]],
) -> list[str]:
    refs: set[str] = set()
    for capability_id in capability_refs:
        evidence = capability_evidence_by_id.get(capability_id)
        if evidence is None:
            continue
        refs.update(canonical_code_paths(evidence["code"]))
    return sorted(refs)


def test_refs_for_capabilities(
    capability_refs: Iterable[str],
    capability_evidence_by_id: Mapping[str, Mapping[str, list[EvidenceNode]]],
) -> list[str]:
    refs: set[str] = set()
    for capability_id in capability_refs:
        evidence = capability_evidence_by_id.get(capability_id)
        if evidence is None:
            continue
        refs.update(node.path for node in evidence["tests"])
    return sorted(refs)


def artifact_paths_for_stage(
    yaml_metadata: Iterable[YamlArchitectureMetadata],
    stage_id: str,
    artifact_kind: str,
) -> list[str]:
    return sorted(
        artifact.path
        for artifact in yaml_metadata
        if artifact.artifact_kind == artifact_kind and artifact_mentions_stage(artifact, stage_id)
    )


def build_stage_contract(
    *,
    stage_source: Mapping[str, object],
    source_by_feature: Mapping[str, Mapping[str, object]],
    yaml_metadata: list[YamlArchitectureMetadata],
    docs: list[MetadataDocument],
    capability_evidence_by_id: Mapping[str, Mapping[str, list[EvidenceNode]]],
) -> str:
    stage_id = require_string(stage_source, "stage_id", "stage source")
    feature_refs = stage_feature_refs(stage_source)
    capability_refs = stage_capability_refs(
        stage_source=stage_source,
        feature_refs=feature_refs,
        source_by_feature=source_by_feature,
        yaml_metadata=yaml_metadata,
    )
    payload: dict[str, object] = {
        "stage_id": stage_id,
        "name": stage_source["name"],
        "status": stage_source["status"],
        "purpose": stage_source["purpose"],
    }
    for key in ("workflow_position", "depends_on", "hands_off_to", "inputs", "outputs", "invariants"):
        if key in stage_source:
            payload[key] = stage_source[key]
    payload.update(
        {
            "feature_refs": feature_refs,
            "capability_refs": capability_refs,
            "code_refs": code_refs_for_capabilities(capability_refs, capability_evidence_by_id),
            "test_refs": test_refs_for_capabilities(capability_refs, capability_evidence_by_id),
            "doc_refs": sorted(
                document.relative_path for document in docs if metadata_explains_stage(document, stage_id)
            ),
            "config_refs": artifact_paths_for_stage(yaml_metadata, stage_id, "config"),
            "component_refs": artifact_paths_for_stage(yaml_metadata, stage_id, "component"),
        }
    )
    if "human_notes" in stage_source:
        payload["human_notes"] = stage_source["human_notes"]
    header = GENERATED_HEADER + f"# Source: docs/stages/{stage_id}.source.yaml\n"
    return header + dump_yaml(payload)


def evidence_gaps_for_capability(
    *,
    capability: Mapping[str, object],
    evidence: Mapping[str, list[EvidenceNode]],
) -> list[str]:
    if capability.get("state", "active") != "active":
        return []

    gaps: list[str] = []
    if not evidence["code"]:
        gaps.append("missing_code_evidence")
    if not evidence["tests"]:
        gaps.append("missing_test_evidence")
    return gaps


def unresolved_evidence_gaps_for_capability(
    *,
    evidence_gaps: list[str],
    allowed_gaps: tuple[str, ...],
) -> list[str]:
    return [gap for gap in evidence_gaps if gap not in allowed_gaps]


def docs_for_capability(
    docs: Iterable[MetadataDocument],
    capability_id: str,
) -> list[str]:
    docs_paths: set[str] = set()
    docs_paths.update(
        document.relative_path for document in docs if metadata_explains_capability(document, capability_id)
    )
    return sorted(docs_paths)


def docs_evidence_for_capability(
    docs: Iterable[MetadataDocument],
    capability_id: str,
) -> list[dict[str, object]]:
    return [
        EvidenceNode(
            path=document.relative_path,
            symbols=(),
            confidence="high",
            source=("docs_frontmatter",),
        ).as_dict()
        for document in docs
        if metadata_explains_capability(document, capability_id)
    ]


def build_invariant_lineage(source: Mapping[str, object]) -> dict[str, object]:
    invariants = source.get("invariants", [])
    capabilities = source.get("capabilities", [])
    invariant_payload: dict[str, object] = {}
    if not isinstance(invariants, list) or not isinstance(capabilities, list):
        return invariant_payload

    for invariant in invariants:
        if not isinstance(invariant, dict):
            continue
        invariant_id = require_string(invariant, "invariant_id", "feature source")
        satisfied_by: list[str] = []
        for capability in capabilities:
            if not isinstance(capability, dict):
                continue
            satisfies = capability.get("satisfies", [])
            if isinstance(satisfies, list) and invariant_id in satisfies:
                satisfied_by.append(require_string(capability, "capability_id", invariant_id))
        invariant_payload[invariant_id] = {
            "state": invariant.get("state", "active"),
            "statement": invariant.get("statement", ""),
            "satisfied_by": sorted(satisfied_by),
        }
    return invariant_payload


def build_timeline(
    *,
    plans: Iterable[MetadataDocument],
    feature_id: str,
) -> list[dict[str, object]]:
    timeline: list[dict[str, object]] = []
    for plan in plans_for_feature(plans, feature_id):
        metadata = plan.frontmatter
        affects = metadata.get("affects", {})
        outcome = metadata.get("outcome", {})
        capabilities = affects.get("capabilities", []) if isinstance(affects, dict) else []
        verification = metadata.get("verification", [])
        timeline.append(
            {
                "completed_at": timestamp_to_string(metadata["completed_at"]),
                "source_plan": plan.relative_path,
                "change_id": metadata.get("change_id", ""),
                "summary": plan_title(plan),
                "capabilities": capabilities if isinstance(capabilities, list) else [],
                "verification": verification if isinstance(verification, list) else [],
                "outcome": outcome.get("summary", "") if isinstance(outcome, dict) else "",
            }
        )
    return timeline


def feature_freshness_metadata(
    *,
    plans: Iterable[MetadataDocument],
    feature_id: str,
) -> dict[str, object]:
    relevant_plans = plans_for_feature(plans, feature_id)
    if not relevant_plans:
        return {}
    latest_plan = relevant_plans[-1]
    latest_completed_at = latest_plan.frontmatter.get("completed_at")
    metadata: dict[str, object] = {
        "revision": len(relevant_plans),
        "latest_change_id": str(latest_plan.frontmatter.get("change_id", "")),
    }
    if latest_completed_at is not None:
        metadata["last_updated_at"] = timestamp_to_string(latest_completed_at)
    return metadata


def build_generated_history_section(
    *,
    timeline: Iterable[Mapping[str, object]],
) -> str:
    timeline_items = list(timeline)
    if not timeline_items:
        return (
            f"{GENERATED_HISTORY_START}\n\n"
            "No completed implementation-plan metadata currently targets this feature.\n\n"
            f"{GENERATED_HISTORY_END}"
        )

    lines = [GENERATED_HISTORY_START, ""]
    current_date: str | None = None
    for item in timeline_items:
        completed_at = str(item.get("completed_at", ""))
        completed_date = completed_at.split("T", 1)[0] if completed_at else "unknown-date"
        if completed_date != current_date:
            if current_date is not None:
                lines.append("")
            lines.append(f"## {completed_date}")
            lines.append("")
            current_date = completed_date

        lines.append(f"### {str(item.get('summary', 'Completed change'))}")
        lines.append("")
        lines.append(f"Source plan: `{str(item.get('source_plan', ''))}`")
        lines.append("")
        capabilities = item.get("capabilities", [])
        lines.append("Affected capabilities:")
        if isinstance(capabilities, list) and capabilities:
            lines.extend(f"- `{capability}`" for capability in capabilities)
        else:
            lines.append("- none recorded")
        lines.append("")
        verification = item.get("verification", [])
        lines.append("Verification:")
        if isinstance(verification, list) and verification:
            lines.extend(f"- `{entry}`" for entry in verification)
        else:
            lines.append("- none recorded")
        lines.append("")
        outcome = str(item.get("outcome", "")).strip()
        lines.append("Outcome:")
        lines.append(outcome if outcome else "No outcome summary recorded.")
        lines.append("")

    if lines[-1] == "":
        lines.pop()
    lines.append("")
    lines.append(GENERATED_HISTORY_END)
    return "\n".join(lines)


def build_feature_history(
    *,
    source: Mapping[str, object],
    plans: Iterable[MetadataDocument],
    existing_heading: str | None,
    existing_human_body: str,
) -> str:
    feature_id = require_string(source, "feature_id", "feature source")
    default_heading = f"# {require_string(source, 'name', feature_id)} History"
    heading = existing_heading or default_heading
    timeline = build_timeline(plans=plans, feature_id=feature_id)
    generated_section = build_generated_history_section(timeline=timeline)
    human_body = existing_human_body.strip()
    if not human_body:
        human_body = (
            "Add human narrative here only when operator context, rollout nuance, "
            "or meaning is needed beyond the generated plan history."
        )
    return (
        f"{heading}\n\n"
        f"{generated_section}\n\n"
        f"{HUMAN_HISTORY_HEADING}\n\n"
        f"{human_body.rstrip()}\n"
    )


def build_feature_lineage(
    *,
    source: Mapping[str, object],
    specs: list[MetadataDocument],
    plans: list[MetadataDocument],
    docs: list[MetadataDocument],
    yaml_metadata: list[YamlArchitectureMetadata],
    capability_evidence: Mapping[str, dict[str, list[EvidenceNode]]],
) -> str:
    feature_id = require_string(source, "feature_id", "feature source")
    exception_map = capability_lineage_exceptions(source)
    capabilities: dict[str, object] = {}
    source_capabilities = source.get("capabilities", [])
    if isinstance(source_capabilities, list):
        for capability in source_capabilities:
            if not isinstance(capability, dict):
                continue
            capability_id = require_string(capability, "capability_id", feature_id)
            evidence = capability_evidence[capability_id]
            exception = exception_map.get(capability_id)
            capability_specs = [
                doc.relative_path for doc in specs if metadata_mentions_capability(doc, capability_id)
            ]
            capability_plans = [
                doc.relative_path for doc in plans if metadata_mentions_capability(doc, capability_id)
            ]
            satisfies = capability.get("satisfies", [])
            evidence_gaps = evidence_gaps_for_capability(
                capability=capability,
                evidence=evidence,
            )
            allowed_gaps = list(exception.allowed_gaps) if exception else []
            unresolved_gaps = unresolved_evidence_gaps_for_capability(
                evidence_gaps=evidence_gaps,
                allowed_gaps=tuple(allowed_gaps),
            )
            completeness_status = "complete"
            if unresolved_gaps:
                completeness_status = "incomplete"
            elif evidence_gaps:
                completeness_status = "excepted"
            capabilities[capability_id] = {
                "state": capability.get("state", "active"),
                "statement": capability.get("statement", ""),
                "satisfies": satisfies if isinstance(satisfies, list) else [],
                "code": [node.as_dict() for node in evidence["code"]],
                "tests": [node.as_dict() for node in evidence["tests"]],
                "docs": docs_for_capability(docs, capability_id),
                "docs_evidence": docs_evidence_for_capability(docs, capability_id),
                "configs": artifact_paths_for_capability(yaml_metadata, capability_id, "config"),
                "config_evidence": artifact_evidence_for_capability(
                    yaml_metadata,
                    capability_id,
                    "config",
                ),
                "components": artifact_paths_for_capability(yaml_metadata, capability_id, "component"),
                "component_evidence": artifact_evidence_for_capability(
                    yaml_metadata,
                    capability_id,
                    "component",
                ),
                "specs": capability_specs,
                "plans": capability_plans,
                "evidence_gaps": evidence_gaps,
                "allowed_evidence_gaps": allowed_gaps,
                "lineage_exception_reason": exception.reason if exception else None,
                "unresolved_evidence_gaps": unresolved_gaps,
                "completeness_status": completeness_status,
            }

    payload = {
        "feature_id": feature_id,
        "source": f"docs/features/{feature_id}/feature.source.yaml",
        "invariants": build_invariant_lineage(source),
        "capabilities": capabilities,
        "timeline": build_timeline(plans=plans, feature_id=feature_id),
    }
    header = (
        GENERATED_HEADER
        + "# Source:\n"
        + f"#   - docs/features/{feature_id}/feature.source.yaml\n"
        + "#   - docs/superpowers/specs/*.md\n"
        + "#   - docs/superpowers/plans/*.md\n"
        + "#   - Python and setup-script @meta, @capability, and @proves markers\n"
        + "#   - YAML # @architecture metadata in configs and AML components\n"
    )
    return header + dump_yaml(payload)


def build_aggregate_lineage(
    *,
    sources: Iterable[Mapping[str, object]],
    feature_lineages: Mapping[str, Mapping[str, object]],
) -> str:
    features: dict[str, object] = {}
    for source in sources:
        feature_id = require_string(source, "feature_id", "feature source")
        lineage = feature_lineages[feature_id]
        capabilities = lineage.get("capabilities", {})
        capability_summaries: list[dict[str, object]] = []
        if isinstance(capabilities, dict):
            for capability_id, capability in capabilities.items():
                if not isinstance(capability, dict):
                    continue
                capability_summaries.append(
                    {
                        "capability_id": str(capability_id),
                        "state": capability.get("state", "active"),
                        "code_count": len(capability.get("code", [])),
                        "test_count": len(capability.get("tests", [])),
                        "config_count": len(capability.get("configs", [])),
                        "component_count": len(capability.get("components", [])),
                        "spec_count": len(capability.get("specs", [])),
                        "plan_count": len(capability.get("plans", [])),
                        "evidence_gap_count": len(capability.get("evidence_gaps", [])),
                        "allowed_evidence_gap_count": len(capability.get("allowed_evidence_gaps", [])),
                        "unresolved_evidence_gap_count": len(
                            capability.get("unresolved_evidence_gaps", [])
                        ),
                        "completeness_status": capability.get("completeness_status", "complete"),
                    }
                )
        features[feature_id] = {
            "lineage_file": f"docs/features/{feature_id}/lineage.generated.yaml",
            "capability_count": len(capability_summaries),
            "capabilities": capability_summaries,
        }
    return GENERATED_HEADER + dump_yaml({"features": features})


def build_architecture_dag(
    *,
    sources: Iterable[Mapping[str, object]],
    stage_sources: Iterable[Mapping[str, object]],
    yaml_metadata: Iterable[YamlArchitectureMetadata],
    docs: Iterable[MetadataDocument],
) -> str:
    nodes: list[dict[str, str]] = []
    edges: list[dict[str, str]] = []
    seen_nodes: set[str] = set()

    def add_node(node_id: str, node_type: str) -> None:
        if node_id in seen_nodes:
            return
        seen_nodes.add(node_id)
        nodes.append({"id": node_id, "type": node_type})

    for source in sources:
        feature_id = require_string(source, "feature_id", "feature source")
        add_node(f"feature:{feature_id}", "feature")
        capabilities = source.get("capabilities", [])
        if isinstance(capabilities, list):
            for capability in capabilities:
                if not isinstance(capability, dict):
                    continue
                capability_id = require_string(capability, "capability_id", feature_id)
                add_node(f"capability:{capability_id}", "capability")
                edges.append(
                    {
                        "from": f"feature:{feature_id}",
                        "to": f"capability:{capability_id}",
                        "type": "has_capability",
                    }
                )
        invariants = source.get("invariants", [])
        if isinstance(invariants, list):
            for invariant in invariants:
                if not isinstance(invariant, dict):
                    continue
                invariant_id = require_string(invariant, "invariant_id", feature_id)
                add_node(f"invariant:{invariant_id}", "invariant")
                edges.append(
                    {
                        "from": f"feature:{feature_id}",
                        "to": f"invariant:{invariant_id}",
                        "type": "has_invariant",
                    }
                )
    for stage_source in stage_sources:
        stage_id = require_string(stage_source, "stage_id", "stage source")
        add_node(f"stage:{stage_id}", "stage")
        feature_roles = stage_source_feature_roles(
            stage_source,
            f"docs/stages/{stage_id}.source.yaml",
        )
        for feature_id, role in feature_roles.items():
            add_node(f"feature:{feature_id}", "feature")
            edges.append(
                {
                    "from": f"stage:{stage_id}",
                    "to": f"feature:{feature_id}",
                    "type": "contains_feature",
                    "role": role,
                }
            )
    for artifact in yaml_metadata:
        node_type = artifact.artifact_kind
        add_node(f"{node_type}:{artifact.path}", node_type)
        for feature_id in optional_string_list(artifact.metadata.get("features"), artifact.path, "features"):
            add_node(f"feature:{feature_id}", "feature")
            edges.append(
                {
                    "from": f"{node_type}:{artifact.path}",
                    "to": f"feature:{feature_id}",
                    "type": "metadata_feature",
                }
            )
        for stage_id in optional_string_list(artifact.metadata.get("stages"), artifact.path, "stages"):
            add_node(f"stage:{stage_id}", "stage")
            edges.append(
                {
                    "from": f"{node_type}:{artifact.path}",
                    "to": f"stage:{stage_id}",
                    "type": "metadata_stage",
                }
            )
        for capability_id in optional_string_list(
            artifact.metadata.get("capabilities"),
            artifact.path,
            "capabilities",
        ):
            add_node(f"capability:{capability_id}", "capability")
            edges.append(
                {
                    "from": f"{node_type}:{artifact.path}",
                    "to": f"capability:{capability_id}",
                    "type": "metadata_capability",
                }
            )
    for document in docs:
        add_node(f"doc:{document.relative_path}", "doc")
        explains = document.frontmatter.get("explains", {})
        if not isinstance(explains, dict):
            continue
        for feature_id in optional_string_list(explains.get("features"), document.relative_path, "explains.features"):
            add_node(f"feature:{feature_id}", "feature")
            edges.append(
                {
                    "from": f"doc:{document.relative_path}",
                    "to": f"feature:{feature_id}",
                    "type": "explains_feature",
                }
            )
        for stage_id in optional_string_list(explains.get("stages"), document.relative_path, "explains.stages"):
            add_node(f"stage:{stage_id}", "stage")
            edges.append(
                {
                    "from": f"doc:{document.relative_path}",
                    "to": f"stage:{stage_id}",
                    "type": "explains_stage",
                }
            )
    return GENERATED_HEADER + dump_yaml({"nodes": nodes, "edges": edges})


def plan_title(plan: MetadataDocument) -> str:
    summary = plan.frontmatter.get("summary")
    if isinstance(summary, str) and summary:
        return summary
    outcome = plan.frontmatter.get("outcome")
    if isinstance(outcome, dict) and isinstance(outcome.get("summary"), str):
        return str(outcome["summary"])
    return Path(plan.relative_path).stem


def plans_for_feature(plans: Iterable[MetadataDocument], feature_id: str) -> list[MetadataDocument]:
    relevant = [
        plan
        for plan in plans
        if plan.frontmatter.get("status") == "complete" and metadata_mentions_feature(plan, feature_id)
    ]
    return sorted(relevant, key=lambda plan: str(plan.frontmatter.get("completed_at", "")))


def collect_lineage_completeness_failures(
    feature_lineages: Mapping[str, Mapping[str, object]],
) -> tuple[str, ...]:
    failures: list[str] = []
    for feature_id, lineage in sorted(feature_lineages.items()):
        capabilities = lineage.get("capabilities", {})
        if not isinstance(capabilities, dict):
            continue
        for capability_id, capability_payload in sorted(capabilities.items()):
            if not isinstance(capability_payload, dict):
                continue
            unresolved = capability_payload.get("unresolved_evidence_gaps", [])
            if not isinstance(unresolved, list) or not unresolved:
                continue
            failures.append(
                f"{feature_id}: {capability_id} has unresolved lineage gaps: "
                + ", ".join(str(gap) for gap in unresolved)
            )
    return tuple(failures)


def format_completeness_failures(failures: tuple[str, ...]) -> str:
    lines = ["Lineage completeness validation failed:"]
    lines.extend(f"- {failure}" for failure in failures)
    return "\n".join(lines)


def build_outputs(root: Path) -> ArchitectureBuildResult:
    sources = load_feature_sources(root)
    stage_sources = load_stage_sources(root)
    specs = load_metadata_documents(root, "specs")
    plans = load_metadata_documents(root, "plans")
    docs = load_explanation_documents(root)
    code_metadata = load_code_metadata(root)
    yaml_metadata = load_yaml_architecture_metadata(root)

    feature_ids = {require_string(source, "feature_id", "feature source") for source in sources}
    capability_ids: set[str] = set()
    invariant_ids: set[str] = set()
    for source in sources:
        capabilities = source.get("capabilities", [])
        if isinstance(capabilities, list):
            for capability in capabilities:
                if isinstance(capability, dict):
                    capability_ids.add(require_string(capability, "capability_id", "feature source"))
        invariants = source.get("invariants", [])
        if isinstance(invariants, list):
            for invariant in invariants:
                if isinstance(invariant, dict):
                    invariant_ids.add(require_string(invariant, "invariant_id", "feature source"))
    stage_ids = stage_ids_from_sources_or_contracts(root, stage_sources)
    validate_stage_feature_linkage(feature_sources=sources, stage_sources=stage_sources)
    config_paths = {relative_path(path, root) for path in (root / "configs").glob("*.yaml")}
    component_paths = {
        relative_path(path, root) for path in (root / "aml" / "components").glob("*.yaml")
    }
    validate_known_references(
        documents=[*specs, *plans, *docs],
        feature_ids=feature_ids,
        capability_ids=capability_ids,
        invariant_ids=invariant_ids,
        stage_ids=stage_ids,
        config_paths=config_paths,
        component_paths=component_paths,
    )
    validate_yaml_architecture_references(
        yaml_metadata=yaml_metadata,
        feature_ids=feature_ids,
        capability_ids=capability_ids,
        invariant_ids=invariant_ids,
        stage_ids=stage_ids,
    )

    evidence_by_feature: dict[str, dict[str, dict[str, list[EvidenceNode]]]] = {}
    evidence_by_capability: dict[str, dict[str, list[EvidenceNode]]] = {}
    feature_lineages: dict[str, dict[str, object]] = {}
    outputs: dict[Path, str] = {}
    for source in sources:
        feature_id = require_string(source, "feature_id", "feature source")
        evidence_by_feature[feature_id] = {}
        capabilities = source.get("capabilities", [])
        if not isinstance(capabilities, list):
            continue
        for capability in capabilities:
            if not isinstance(capability, dict):
                continue
            capability_id = require_string(capability, "capability_id", feature_id)
            code_nodes, test_nodes = scan_code_evidence(code_metadata, root, capability_id)
            evidence_by_feature[feature_id][capability_id] = {
                "code": code_nodes,
                "tests": test_nodes,
            }
            evidence_by_capability[capability_id] = {
                "code": code_nodes,
                "tests": test_nodes,
            }

        refs = collect_feature_refs(
            source=source,
            specs=specs,
            plans=plans,
            docs=docs,
            yaml_metadata=yaml_metadata,
            capability_evidence=evidence_by_feature[feature_id],
        )
        feature_contract_path = root / "docs" / "features" / feature_id / f"{feature_id}.yaml"
        outputs[feature_contract_path] = build_feature_contract(
            source=source,
            refs=refs,
            plans=plans,
        )
        lineage_path = root / "docs" / "features" / feature_id / "lineage.generated.yaml"
        lineage_text = build_feature_lineage(
            source=source,
            specs=specs,
            plans=plans,
            docs=docs,
            yaml_metadata=yaml_metadata,
            capability_evidence=evidence_by_feature[feature_id],
        )
        outputs[lineage_path] = lineage_text
        parsed_lineage = yaml.safe_load(lineage_text)
        if not isinstance(parsed_lineage, dict):
            raise ValueError(f"Generated lineage for {feature_id} did not parse as a mapping")
        feature_lineages[feature_id] = parsed_lineage

        history_path = root / "docs" / "features" / feature_id / "history.md"
        existing_heading, existing_human_body = extract_existing_human_history(history_path)
        outputs[history_path] = build_feature_history(
            source=source,
            plans=plans,
            existing_heading=existing_heading,
            existing_human_body=existing_human_body,
        )

    source_by_feature = {
        require_string(source, "feature_id", "feature source"): source for source in sources
    }
    for stage_source in stage_sources:
        stage_id = require_string(stage_source, "stage_id", "stage source")
        stage_contract_path = root / "docs" / "stages" / f"{stage_id}.yaml"
        outputs[stage_contract_path] = build_stage_contract(
            stage_source=stage_source,
            source_by_feature=source_by_feature,
            yaml_metadata=yaml_metadata,
            docs=docs,
            capability_evidence_by_id=evidence_by_capability,
        )

    outputs[root / "docs" / "generated" / "capability_lineage.yaml"] = build_aggregate_lineage(
        sources=sources,
        feature_lineages=feature_lineages,
    )
    outputs[root / "docs" / "generated" / "architecture_dag.yaml"] = build_architecture_dag(
        sources=sources,
        stage_sources=stage_sources,
        yaml_metadata=yaml_metadata,
        docs=docs,
    )
    return ArchitectureBuildResult(
        outputs=outputs,
        completeness_failures=collect_lineage_completeness_failures(feature_lineages),
    )


def write_or_check_outputs(outputs: Mapping[Path, str], check_only: bool) -> int:
    status = 0
    for path, expected in sorted(outputs.items()):
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if current == expected:
            continue
        if check_only:
            print(f"Stale generated output: {path}")
            status = 1
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(expected, encoding="utf-8")
        print(f"Generated: {path}")
    return status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate and validate architecture metadata discovery surfaces."
    )
    parser.add_argument(
        "--repo-root",
        default=str(repo_root()),
        help="Repository root. Defaults to the current script's repository.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check generated outputs without rewriting them.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate metadata shape without writing generated outputs.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve()
    try:
        build_result = build_outputs(root)
    except ValueError as exc:
        print(str(exc))
        return 1
    if build_result.completeness_failures and args.validate_only:
        print(format_completeness_failures(build_result.completeness_failures))
        return 1
    if args.validate_only:
        print("Architecture metadata validation passed.")
        return 0
    status = write_or_check_outputs(build_result.outputs, check_only=args.check)
    if build_result.completeness_failures:
        print(format_completeness_failures(build_result.completeness_failures))
        return 1 if status == 0 else status
    if status == 0:
        print("Architecture metadata generated." if not args.check else "Generated outputs are current.")
    return status


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

