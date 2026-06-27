"""
@meta
name: planning_lineage_support
type: utility
domain: docs
distribution_tier: starter_kit
responsibility:
  - Assemble the planning-lineage graph from roadmap, workstream, thread, spec, and plan surfaces.
  - Provide stable derived planning-lineage output for validation and generation workflows.
inputs:
  - docs/intent/master-workstream-roadmap.md
  - docs/intent/workstreams/*.md
  - docs/intent/workstreams/threads/**/*.md
  - docs/superpowers/specs/*.md
  - docs/superpowers/plans/*.md
outputs:
  - In-memory planning-lineage graph
  - Stable YAML text for docs/generated/planning_lineage.yaml
tags:
  - docs
  - lineage
  - validation
  - generation
lifecycle:
  status: active
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml

from planning_artifact_schema import get_artifact_schema, get_required_values


@dataclass(frozen=True)
class WorkstreamRecord:
    workstream_id: str
    status: str
    path: str


@dataclass(frozen=True)
class ThreadRecord:
    thread_id: str
    status: str
    path: str
    workstream_id: str


@dataclass(frozen=True)
class ArtifactRecord:
    artifact_type: str
    layer: str | None
    status: str | None
    path: str
    parent_thread: str | None
    parent_spec: str | None


FRONTMATTER_RE = re.compile(r"\A---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|$)", re.DOTALL)


def relpath(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def extract_frontmatter(text: str) -> dict[str, Any] | None:
    if text.startswith("\ufeff"):
        text = text.removeprefix("\ufeff")
    match = FRONTMATTER_RE.match(text)
    if match is None:
        return None
    payload = yaml.safe_load(match.group(1))
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        return None
    return payload


def read_frontmatter(path: Path) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    return extract_frontmatter(text)


def iter_workstream_docs(root: Path) -> list[Path]:
    registry = root / "docs" / "intent" / "workstreams"
    if not registry.exists():
        return []
    return sorted(path for path in registry.glob("*.md") if path.name != "README.md")


def iter_thread_docs(root: Path) -> list[Path]:
    threads_root = root / "docs" / "intent" / "workstreams" / "threads"
    if not threads_root.exists():
        return []
    return sorted(
        path
        for path in threads_root.glob("*/*.md")
        if path.name != "README.md"
    )


def iter_superpowers_docs(root: Path, folder_name: str) -> list[Path]:
    folder = root / "docs" / "superpowers" / folder_name
    if not folder.exists():
        return []
    return sorted(path for path in folder.glob("*.md") if path.name != "README.md")


def _resolve_identity(payload: dict[str, Any], root: Path, artifact_type: str) -> str | None:
    artifact_schema = get_artifact_schema(root, artifact_type)
    identity = artifact_schema.get("identity", {})
    if not isinstance(identity, dict):
        return None
    canonical_field = identity.get("canonical_field")
    legacy_field = identity.get("legacy_field")
    for field_name in (canonical_field, legacy_field):
        if not isinstance(field_name, str) or field_name == "none":
            continue
        value = payload.get(field_name)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def discover_workstreams(root: Path) -> dict[str, WorkstreamRecord]:
    records: dict[str, WorkstreamRecord] = {}
    for path in iter_workstream_docs(root):
        payload = read_frontmatter(path)
        if not isinstance(payload, dict):
            continue
        workstream_name = _resolve_identity(payload, root, "workstream")
        status = payload.get("status")
        if isinstance(workstream_name, str) and isinstance(status, str):
            records[workstream_name] = WorkstreamRecord(
                workstream_id=workstream_name,
                status=status,
                path=relpath(path, root),
            )
    return records


def discover_threads(root: Path) -> dict[str, ThreadRecord]:
    records: dict[str, ThreadRecord] = {}
    threads_root = root / "docs" / "intent" / "workstreams" / "threads"
    for path in iter_thread_docs(root):
        payload = read_frontmatter(path)
        if not isinstance(payload, dict):
            continue
        thread_name = _resolve_identity(payload, root, "bounded_change_thread")
        status = payload.get("status")
        if not isinstance(thread_name, str) or not isinstance(status, str):
            continue
        try:
            workstream_id = path.relative_to(threads_root).parts[0]
        except (ValueError, IndexError):
            continue
        records[thread_name] = ThreadRecord(
            thread_id=thread_name,
            status=status,
            path=relpath(path, root),
            workstream_id=workstream_id,
        )
    return records


def discover_superpowers_artifacts(root: Path, folder_name: str) -> list[ArtifactRecord]:
    artifact_type = folder_name.removesuffix("s")
    expected_artifact_type = get_required_values(root, artifact_type).get("artifact_type", artifact_type)
    records: list[ArtifactRecord] = []
    for path in iter_superpowers_docs(root, folder_name):
        payload = read_frontmatter(path)
        if not isinstance(payload, dict):
            continue
        actual_artifact_type = payload.get("artifact_type")
        if isinstance(actual_artifact_type, str) and actual_artifact_type != expected_artifact_type:
            continue
        records.append(
            ArtifactRecord(
                artifact_type=expected_artifact_type,
                layer=payload.get("layer") if isinstance(payload.get("layer"), str) else None,
                status=payload.get("status") if isinstance(payload.get("status"), str) else None,
                path=relpath(path, root),
                parent_thread=payload.get("parent_thread")
                if isinstance(payload.get("parent_thread"), str)
                else None,
                parent_spec=payload.get("parent_spec")
                if isinstance(payload.get("parent_spec"), str)
                else None,
            )
        )
    return records


def _thread_derived_completion(
    thread: ThreadRecord,
    linked_specs: list[ArtifactRecord],
    linked_plans: list[ArtifactRecord],
) -> str:
    if thread.status == "completed":
        return "completed"
    if linked_plans and all(plan.status == "completed" for plan in linked_plans):
        return "completed"
    if linked_specs or linked_plans:
        return "in_progress"
    return "not_started"


def _workstream_derived_completion(thread_nodes: list[dict[str, Any]]) -> str:
    if not thread_nodes:
        return "not_started"
    statuses = {node["derived_completion"] for node in thread_nodes}
    if statuses == {"completed"}:
        return "completed"
    if "in_progress" in statuses or "completed" in statuses:
        return "in_progress"
    return "not_started"


def build_planning_lineage(root: Path) -> dict[str, Any]:
    workstreams = discover_workstreams(root)
    threads = discover_threads(root)
    specs = discover_superpowers_artifacts(root, "specs")
    plans = discover_superpowers_artifacts(root, "plans")

    specs_by_thread: dict[str, list[ArtifactRecord]] = {}
    for spec in specs:
        if spec.parent_thread is not None:
            specs_by_thread.setdefault(spec.parent_thread, []).append(spec)

    plans_by_thread: dict[str, list[ArtifactRecord]] = {}
    for plan in plans:
        if plan.parent_thread is not None:
            plans_by_thread.setdefault(plan.parent_thread, []).append(plan)

    workstream_nodes: list[dict[str, Any]] = []
    for workstream_id in sorted(workstreams):
        workstream = workstreams[workstream_id]
        thread_nodes: list[dict[str, Any]] = []
        for thread in sorted(
            (record for record in threads.values() if record.workstream_id == workstream_id),
            key=lambda record: record.path,
        ):
            linked_specs = sorted(specs_by_thread.get(thread.thread_id, []), key=lambda record: record.path)
            linked_plans = sorted(plans_by_thread.get(thread.thread_id, []), key=lambda record: record.path)
            thread_nodes.append(
                {
                    "thread_id": thread.thread_id,
                    "status": thread.status,
                    "path": thread.path,
                    "specs": [record.path for record in linked_specs],
                    "plans": [record.path for record in linked_plans],
                    "derived_completion": _thread_derived_completion(thread, linked_specs, linked_plans),
                }
            )

        workstream_nodes.append(
            {
                "workstream_id": workstream.workstream_id,
                "status": workstream.status,
                "path": workstream.path,
                "thread_count": len(thread_nodes),
                "completed_thread_count": sum(
                    1 for node in thread_nodes if node["derived_completion"] == "completed"
                ),
                "derived_completion": _workstream_derived_completion(thread_nodes),
                "threads": thread_nodes,
            }
        )

    return {
        "roadmap": {
            "path": "docs/intent/master-workstream-roadmap.md",
            "workstream_count": len(workstream_nodes),
            "completed_workstream_count": sum(
                1 for node in workstream_nodes if node["derived_completion"] == "completed"
            ),
        },
        "workstreams": workstream_nodes,
    }


def render_planning_lineage_yaml(root: Path) -> str:
    payload = build_planning_lineage(root)
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=False)
