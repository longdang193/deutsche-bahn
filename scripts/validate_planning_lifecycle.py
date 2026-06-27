"""
@meta
name: validate_planning_lifecycle
type: script
domain: docs
distribution_tier: starter_kit
responsibility:
  - Validate planning lifecycle integrity across workstreams, threads, specs, execution maps, and plans.
  - Enforce execution-map metadata and cross-reference integrity.
  - Warn when active/completed workstreams are missing expected lifecycle artifacts.
inputs:
  - docs/intent/master-workstream-roadmap.md
  - docs/intent/workstreams/*.md
  - docs/intent/workstreams/threads/**/*.md
  - docs/superpowers/specs/*.md
  - docs/superpowers/plans/*.md
  - docs/superpowers/execution_maps/*.md
outputs:
  - Exit status and human-readable planning lifecycle validation report.
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
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from typing import Any

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from planning_artifact_schema import get_allowed_values, get_required_values

ACTIVE_STATUSES = {"active", "completed"}
TERMINAL_THREAD_STATUSES = {"completed", "dropped"}
TERMINAL_WORKSTREAM_STATUSES = {"completed", "dropped"}


@dataclass(frozen=True)
class Finding:
    level: str
    category: str
    path: str
    message: str


@dataclass(frozen=True)
class WorkstreamRecord:
    workstream_id: str
    status: str
    path: Path


@dataclass(frozen=True)
class ThreadRecord:
    thread_id: str
    status: str
    workstream_id: str
    path: Path


@dataclass(frozen=True)
class SpecRecord:
    path: Path
    parent_thread: str | None


@dataclass(frozen=True)
class PlanRecord:
    path: Path
    parent_thread: str | None


@dataclass(frozen=True)
class ExecutionMapRecord:
    path: Path
    artifact_type: str | None
    map_type: str | None
    parent_workstream: str | None
    threads: list[str]
    specs: list[str]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate planning lifecycle integrity and coverage."
    )
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repository root. Defaults to this script's repository.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when warning-level lifecycle coverage issues are present.",
    )
    return parser


def relative_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def extract_frontmatter(path: Path) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if text.startswith("\ufeff"):
        text = text.removeprefix("\ufeff")
    if not text.startswith("---"):
        return None
    marker_end = text.find("\n---", 3)
    if marker_end == -1:
        return None
    yaml_blob = text[3:marker_end]
    payload = yaml.safe_load(yaml_blob)
    if not isinstance(payload, dict):
        return None
    return payload


def extract_body(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if text.startswith("\ufeff"):
        text = text.removeprefix("\ufeff")
    if not text.startswith("---"):
        return text
    marker_end = text.find("\n---", 3)
    if marker_end == -1:
        return text
    return text[marker_end + 4 :]


def extract_h2_section(body: str, section_name: str) -> str | None:
    pattern = re.compile(rf"^##\s+{re.escape(section_name)}\s*$", re.MULTILINE)
    match = pattern.search(body)
    if match is None:
        return None
    next_heading = re.search(r"^##\s+.+$", body[match.end() :], re.MULTILINE)
    if next_heading is None:
        return body[match.end() :].strip()
    return body[match.end() : match.end() + next_heading.start()].strip()


def is_effectively_empty(section_text: str) -> bool:
    if not section_text.strip():
        return True
    lines = [line.strip() for line in section_text.splitlines() if line.strip()]
    if not lines:
        return True
    return all(re.fullmatch(r"(<[^>]+>|\[[^\]]+\]|\([^)]*\))", line) for line in lines)


def has_unchecked_checklist(section_text: str) -> bool:
    return bool(re.search(r"^\s*-\s*\[\s\]\s+", section_text, re.MULTILINE))


def discover_workstreams(root: Path) -> dict[str, WorkstreamRecord]:
    registry = root / "docs" / "intent" / "workstreams"
    records: dict[str, WorkstreamRecord] = {}
    if not registry.exists():
        return records
    for path in sorted(p for p in registry.glob("*.md") if p.name != "README.md"):
        payload = extract_frontmatter(path)
        if not isinstance(payload, dict):
            continue
        workstream_id = payload.get("workstream_id")
        status = payload.get("status")
        if isinstance(workstream_id, str) and isinstance(status, str):
            records[workstream_id] = WorkstreamRecord(
                workstream_id=workstream_id,
                status=status.strip().lower(),
                path=path,
            )
    return records


def discover_threads(root: Path) -> dict[str, ThreadRecord]:
    threads_root = root / "docs" / "intent" / "workstreams" / "threads"
    records: dict[str, ThreadRecord] = {}
    if not threads_root.exists():
        return records
    for path in sorted(p for p in threads_root.glob("*/*.md") if p.name != "README.md"):
        payload = extract_frontmatter(path)
        if not isinstance(payload, dict):
            continue
        thread_id = payload.get("thread_id")
        status = payload.get("status")
        if not isinstance(thread_id, str) or not isinstance(status, str):
            continue
        workstream_id = path.parent.name
        records[thread_id] = ThreadRecord(
            thread_id=thread_id,
            status=status.strip().lower(),
            workstream_id=workstream_id,
            path=path,
        )
    return records


def discover_specs(root: Path) -> list[SpecRecord]:
    folder = root / "docs" / "superpowers" / "specs"
    records: list[SpecRecord] = []
    if not folder.exists():
        return records
    for path in sorted(p for p in folder.glob("*.md") if p.name != "README.md"):
        payload = extract_frontmatter(path) or {}
        parent_thread = payload.get("parent_thread") if isinstance(payload.get("parent_thread"), str) else None
        records.append(SpecRecord(path=path, parent_thread=parent_thread))
    return records


def discover_plans(root: Path) -> list[PlanRecord]:
    folder = root / "docs" / "superpowers" / "plans"
    records: list[PlanRecord] = []
    if not folder.exists():
        return records
    for path in sorted(p for p in folder.glob("*.md") if p.name != "README.md"):
        payload = extract_frontmatter(path) or {}
        parent_thread = payload.get("parent_thread") if isinstance(payload.get("parent_thread"), str) else None
        records.append(PlanRecord(path=path, parent_thread=parent_thread))
    return records


def discover_execution_maps(root: Path) -> list[ExecutionMapRecord]:
    folder = root / "docs" / "superpowers" / "execution_maps"
    records: list[ExecutionMapRecord] = []
    if not folder.exists():
        return records
    for path in sorted(p for p in folder.glob("*.md") if p.name != "README.md"):
        payload = extract_frontmatter(path) or {}
        threads = payload.get("threads")
        specs = payload.get("specs")
        records.append(
            ExecutionMapRecord(
                path=path,
                artifact_type=payload.get("artifact_type") if isinstance(payload.get("artifact_type"), str) else None,
                map_type=payload.get("map_type") if isinstance(payload.get("map_type"), str) else None,
                parent_workstream=payload.get("parent_workstream")
                if isinstance(payload.get("parent_workstream"), str)
                else None,
                threads=threads if isinstance(threads, list) and all(isinstance(item, str) for item in threads) else [],
                specs=specs if isinstance(specs, list) and all(isinstance(item, str) for item in specs) else [],
            )
        )
    return records


def validate_execution_map_integrity(
    root: Path,
    workstreams: dict[str, WorkstreamRecord],
    threads: dict[str, ThreadRecord],
    specs: list[SpecRecord],
    maps: list[ExecutionMapRecord],
) -> list[Finding]:
    findings: list[Finding] = []
    spec_paths = {relative_path(spec.path, root): spec for spec in specs}
    expected_artifact_type = get_required_values(root, "execution_map").get(
        "artifact_type", "execution_map"
    )
    allowed_map_types = set(get_allowed_values(root, "map_type", "execution_map"))
    for record in maps:
        rel = relative_path(record.path, root)
        if record.artifact_type != expected_artifact_type:
            findings.append(
                Finding(
                    level="ERROR",
                    category="execution_map_format_error",
                    path=rel,
                    message=(
                        "execution map must use "
                        f"`artifact_type: {expected_artifact_type}`."
                    ),
                )
            )
        if record.map_type not in allowed_map_types:
            findings.append(
                Finding(
                    level="ERROR",
                    category="execution_map_format_error",
                    path=rel,
                    message=(
                        "execution map must use `map_type` in "
                        f"{sorted(allowed_map_types)}."
                    ),
                )
            )
        if not record.parent_workstream:
            findings.append(
                Finding(
                    level="ERROR",
                    category="execution_map_format_error",
                    path=rel,
                    message="execution map must define `parent_workstream`.",
                )
            )
            continue
        if record.parent_workstream != "none" and record.parent_workstream not in workstreams:
            findings.append(
                Finding(
                    level="ERROR",
                    category="execution_map_reference_error",
                    path=rel,
                    message="execution map parent_workstream must resolve to a registered workstream.",
                )
            )
        if not record.threads:
            findings.append(
                Finding(
                    level="ERROR",
                    category="execution_map_format_error",
                    path=rel,
                    message="execution map must provide a non-empty `threads` list.",
                )
            )
        for thread_id in record.threads:
            thread = threads.get(thread_id)
            if thread is None:
                findings.append(
                    Finding(
                        level="ERROR",
                        category="execution_map_reference_error",
                        path=rel,
                        message=f"execution map thread `{thread_id}` does not resolve to a registered thread.",
                    )
                )
                continue
            if record.parent_workstream not in {"none", thread.workstream_id}:
                findings.append(
                    Finding(
                        level="ERROR",
                        category="execution_map_reference_error",
                        path=rel,
                        message=(
                            f"execution map thread `{thread_id}` does not belong to "
                            f"`{record.parent_workstream}`."
                        ),
                    )
                )
        if record.map_type in {"spec_authoring", "implementation_execution"} and not record.specs:
            findings.append(
                Finding(
                    level="WARN",
                    category="execution_map_coverage_warning",
                    path=rel,
                    message=f"{record.map_type} map should include a non-empty `specs` list.",
                )
            )
        for spec_path in record.specs:
            spec_record = spec_paths.get(spec_path)
            if spec_record is None:
                findings.append(
                    Finding(
                        level="ERROR",
                        category="execution_map_reference_error",
                        path=rel,
                        message=f"execution map spec `{spec_path}` does not resolve to a real spec file.",
                    )
                )
                continue
            if spec_record.parent_thread and spec_record.parent_thread not in record.threads:
                findings.append(
                    Finding(
                        level="WARN",
                        category="execution_map_coverage_warning",
                        path=rel,
                        message=(
                            f"spec `{spec_path}` parent_thread `{spec_record.parent_thread}` "
                            "is not listed in this map's threads."
                        ),
                    )
                )
    return findings


def validate_lifecycle_coverage(
    root: Path,
    workstreams: dict[str, WorkstreamRecord],
    threads: dict[str, ThreadRecord],
    specs: list[SpecRecord],
    plans: list[PlanRecord],
    maps: list[ExecutionMapRecord],
) -> list[Finding]:
    findings: list[Finding] = []
    roadmap_path = root / "docs" / "intent" / "master-workstream-roadmap.md"
    if not roadmap_path.exists():
        findings.append(
            Finding(
                level="ERROR",
                category="planning_lifecycle_error",
                path="docs/intent/master-workstream-roadmap.md",
                message="master workstream roadmap is missing.",
            )
        )
        return findings
    roadmap_payload = extract_frontmatter(roadmap_path) or {}
    roadmap_status = (
        roadmap_payload.get("status").strip().lower()
        if isinstance(roadmap_payload.get("status"), str)
        else None
    )
    roadmap_completed = roadmap_status == "completed"
    if roadmap_completed:
        roadmap_body = extract_body(roadmap_path)
        roadmap_goal = extract_h2_section(roadmap_body, "Goal")
        roadmap_deliverables = extract_h2_section(roadmap_body, "Key Deliverables")
        if roadmap_goal is None or is_effectively_empty(roadmap_goal):
            findings.append(
                Finding(
                    level="ERROR",
                    category="planning_lifecycle_error",
                    path=relative_path(roadmap_path, root),
                    message="completed roadmap must have a non-empty `Goal` section.",
                )
            )
        if roadmap_deliverables is None or is_effectively_empty(roadmap_deliverables):
            findings.append(
                Finding(
                    level="ERROR",
                    category="planning_lifecycle_error",
                    path=relative_path(roadmap_path, root),
                    message="completed roadmap must have non-empty `Key Deliverables`.",
                )
            )
        elif has_unchecked_checklist(roadmap_deliverables):
            findings.append(
                Finding(
                    level="ERROR",
                    category="planning_lifecycle_error",
                    path=relative_path(roadmap_path, root),
                    message="completed roadmap cannot contain unchecked Key Deliverables checklist items.",
                )
            )
        non_terminal_workstreams = [
            workstream
            for workstream in workstreams.values()
            if workstream.status not in TERMINAL_WORKSTREAM_STATUSES
        ]
        for workstream in non_terminal_workstreams:
            findings.append(
                Finding(
                    level="ERROR",
                    category="planning_lifecycle_error",
                    path=relative_path(workstream.path, root),
                    message=(
                        "completed master roadmap cannot contain non-terminal workstream status "
                        f"`{workstream.status}`; use `completed` or `dropped`."
                    ),
                )
            )

    specs_by_thread = {spec.parent_thread for spec in specs if spec.parent_thread}
    plans_by_thread = {plan.parent_thread for plan in plans if plan.parent_thread}

    for workstream_id, workstream in sorted(workstreams.items()):
        if workstream.status not in ACTIVE_STATUSES:
            continue
        ws_threads = [thread for thread in threads.values() if thread.workstream_id == workstream_id]
        thread_folder = root / "docs" / "intent" / "workstreams" / "threads" / workstream_id
        if not thread_folder.exists():
            findings.append(
                Finding(
                    level="WARN",
                    category="planning_lifecycle_warning",
                    path=relative_path(workstream.path, root),
                    message=(
                        "active/completed workstream should have a thread folder at "
                        f"`docs/intent/workstreams/threads/{workstream_id}/`."
                    ),
                )
            )
        elif not ws_threads:
            findings.append(
                Finding(
                    level="WARN",
                    category="planning_lifecycle_warning",
                    path=relative_path(workstream.path, root),
                    message="active/completed workstream should have at least one bounded change thread file.",
                )
            )

        ws_thread_ids = {thread.thread_id for thread in ws_threads}
        has_specs = any(thread_id in specs_by_thread for thread_id in ws_thread_ids)
        has_plans = any(thread_id in plans_by_thread for thread_id in ws_thread_ids)
        ws_maps = [record for record in maps if record.parent_workstream == workstream_id]
        has_complete_spec_set = any(record.map_type == "complete_spec_set" for record in ws_maps)
        has_spec_authoring_map = any(record.map_type == "spec_authoring" for record in ws_maps)
        has_implementation_map = any(record.map_type == "implementation_execution" for record in ws_maps)

        coverage_level = (
            "ERROR"
            if roadmap_completed and workstream.status == "completed"
            else "WARN"
        )

        if not has_complete_spec_set:
            findings.append(
                Finding(
                    level=coverage_level,
                    category=(
                        "planning_lifecycle_error"
                        if coverage_level == "ERROR"
                        else "planning_lifecycle_warning"
                    ),
                    path=relative_path(workstream.path, root),
                    message="missing `complete_spec_set` execution map for active/completed workstream.",
                )
            )
        if not has_spec_authoring_map:
            findings.append(
                Finding(
                    level=coverage_level,
                    category=(
                        "planning_lifecycle_error"
                        if coverage_level == "ERROR"
                        else "planning_lifecycle_warning"
                    ),
                    path=relative_path(workstream.path, root),
                    message="missing `spec_authoring` execution map for active/completed workstream.",
                )
            )
        if not has_implementation_map:
            findings.append(
                Finding(
                    level=coverage_level,
                    category=(
                        "planning_lifecycle_error"
                        if coverage_level == "ERROR"
                        else "planning_lifecycle_warning"
                    ),
                    path=relative_path(workstream.path, root),
                    message="missing `implementation_execution` execution map for active/completed workstream.",
                )
            )
        if not has_specs:
            findings.append(
                Finding(
                    level=coverage_level,
                    category=(
                        "planning_lifecycle_error"
                        if coverage_level == "ERROR"
                        else "planning_lifecycle_warning"
                    ),
                    path=relative_path(workstream.path, root),
                    message="no detailed specs linked to this workstream's bounded threads.",
                )
            )
        if not has_plans:
            findings.append(
                Finding(
                    level=coverage_level,
                    category=(
                        "planning_lifecycle_error"
                        if coverage_level == "ERROR"
                        else "planning_lifecycle_warning"
                    ),
                    path=relative_path(workstream.path, root),
                    message="no implementation plans linked to this workstream's bounded threads.",
                )
            )
        for thread in ws_threads:
            thread_body = extract_body(thread.path)
            if any(section in thread_body.lower() for section in ("## linked spec", "## linked plan")):
                findings.append(
                    Finding(
                        level="WARN",
                        category="planning_lifecycle_warning",
                        path=relative_path(thread.path, root),
                        message="manual thread linkage section is deprecated; use generated planning lineage instead.",
                    )
                )

        if workstream.status == "completed":
            workstream_body = extract_body(workstream.path)
            ws_goal = extract_h2_section(workstream_body, "Goal")
            ws_deliverables = extract_h2_section(workstream_body, "Key Deliverables")
            if ws_goal is None or is_effectively_empty(ws_goal):
                findings.append(
                    Finding(
                        level="ERROR",
                        category="planning_lifecycle_error",
                        path=relative_path(workstream.path, root),
                        message="completed workstream must have a non-empty `Goal` section.",
                    )
                )
            if ws_deliverables is None or is_effectively_empty(ws_deliverables):
                findings.append(
                    Finding(
                        level="ERROR",
                        category="planning_lifecycle_error",
                        path=relative_path(workstream.path, root),
                        message="completed workstream must have non-empty `Key Deliverables`.",
                    )
                )
            elif has_unchecked_checklist(ws_deliverables):
                findings.append(
                    Finding(
                        level="ERROR",
                        category="planning_lifecycle_error",
                        path=relative_path(workstream.path, root),
                        message="completed workstream cannot contain unchecked Key Deliverables checklist items.",
                    )
                )
            non_terminal_threads = [
                thread for thread in ws_threads if thread.status not in TERMINAL_THREAD_STATUSES
            ]
            for thread in non_terminal_threads:
                findings.append(
                    Finding(
                        level="ERROR",
                        category="planning_lifecycle_error",
                        path=relative_path(thread.path, root),
                        message=(
                            "completed workstream cannot contain non-terminal thread status "
                            f"`{thread.status}`; use `completed` or `dropped`."
                        ),
                    )
                )
            for thread in ws_threads:
                if thread.status != "completed":
                    continue
                thread_body = extract_body(thread.path)
                thread_goal = extract_h2_section(thread_body, "Goal")
                thread_deliverables = extract_h2_section(thread_body, "Key Deliverables")
                if thread_goal is None or is_effectively_empty(thread_goal):
                    findings.append(
                        Finding(
                            level="ERROR",
                            category="planning_lifecycle_error",
                            path=relative_path(thread.path, root),
                            message="completed thread must have a non-empty `Goal` section.",
                        )
                    )
                if thread_deliverables is None or is_effectively_empty(thread_deliverables):
                    findings.append(
                        Finding(
                            level="ERROR",
                            category="planning_lifecycle_error",
                            path=relative_path(thread.path, root),
                            message="completed thread must have non-empty `Key Deliverables`.",
                        )
                    )
                elif has_unchecked_checklist(thread_deliverables):
                    findings.append(
                        Finding(
                            level="ERROR",
                            category="planning_lifecycle_error",
                            path=relative_path(thread.path, root),
                            message="completed thread cannot contain unchecked Key Deliverables checklist items.",
                        )
                    )
                thread_slug = thread.path.stem
                if "-" in thread_slug:
                    maybe_number, remainder = thread_slug.split("-", 1)
                    if maybe_number.isdigit() and remainder:
                        thread_slug = remainder
                checkpoint_dir = (
                    root
                    / "docs"
                    / "intent"
                    / "workstreams"
                    / "checkpoints"
                    / workstream_id
                    / thread_slug
                )
                has_checkpoint = checkpoint_dir.exists() and any(
                    child.is_file() and child.suffix.lower() == ".md" and child.name != "README.md"
                    for child in checkpoint_dir.iterdir()
                )
                if not has_checkpoint:
                    findings.append(
                        Finding(
                            level="ERROR",
                            category="planning_lifecycle_error",
                            path=relative_path(thread.path, root),
                            message=(
                                "completed thread under completed workstream is missing checkpoint evidence at "
                                f"`docs/intent/workstreams/checkpoints/{workstream_id}/{thread_slug}/`."
                            ),
                        )
                    )
    return findings


def main() -> int:
    args = build_parser().parse_args()
    root = Path(args.repo_root).resolve()
    workstreams = discover_workstreams(root)
    threads = discover_threads(root)
    specs = discover_specs(root)
    plans = discover_plans(root)
    maps = discover_execution_maps(root)

    adoption_mode_path = root / "repo_config" / "adoption-mode.yaml"
    adoption_mode = None
    if adoption_mode_path.exists():
        payload = yaml.safe_load(adoption_mode_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            value = payload.get("adoption_mode")
            if isinstance(value, str):
                adoption_mode = value.strip().lower()

    lifecycle_findings: list[Finding] = []
    if adoption_mode != "starter_method_only":
        lifecycle_findings = validate_lifecycle_coverage(
            root, workstreams, threads, specs, plans, maps
        )

    findings = [
        *validate_execution_map_integrity(root, workstreams, threads, specs, maps),
        *lifecycle_findings,
    ]
    if findings:
        print("Planning lifecycle validation findings:")
        for finding in findings:
            print(f"- [{finding.level}] {finding.category}: {finding.path} - {finding.message}")
    errors = [finding for finding in findings if finding.level == "ERROR"]
    warnings = [finding for finding in findings if finding.level == "WARN"]
    if errors:
        return 1
    if warnings and args.strict:
        return 1
    print("Planning lifecycle validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
