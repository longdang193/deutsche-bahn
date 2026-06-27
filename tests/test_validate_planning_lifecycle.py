"""
@meta
# distribution_tier: starter_kit
type: test
scope: unit
domain: docs
covers:
  - Planning lifecycle validation for completed-workstream thread status closure
  - Checkpoint-evidence requirements for completed threads
  - Strict-mode failure behavior for warning-level lifecycle coverage findings
tags:
  - fast
  - ci-safe
"""

from __future__ import annotations

import subprocess
import sys
import uuid
from pathlib import Path
from shutil import rmtree

REPO_ROOT = Path(__file__).resolve().parent.parent
VALIDATOR = REPO_ROOT / "scripts" / "validate_planning_lifecycle.py"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed_planning_schema(root: Path) -> None:
    source_schema = REPO_ROOT / "repo_config" / "planning_artifact_schema.yaml"
    write_text(
        root / "repo_config" / "planning_artifact_schema.yaml",
        source_schema.read_text(encoding="utf-8"),
    )


def run_validator(repo_root: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--repo-root", str(repo_root), *extra],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def make_test_root() -> Path:
    root = REPO_ROOT / ".tmp-tests" / f"validate-planning-lifecycle-{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    return root


def seed_minimum_workstream(
    root: Path,
    *,
    roadmap_status: str | None = None,
    workstream_status: str,
    thread_status: str,
) -> None:
    seed_planning_schema(root)
    if roadmap_status is None:
        write_text(root / "docs" / "intent" / "master-workstream-roadmap.md", "# Roadmap\n")
    else:
        write_text(
            root / "docs" / "intent" / "master-workstream-roadmap.md",
            f"""---
status: {roadmap_status}
---

# Roadmap
""",
        )
    write_text(
        root / "docs" / "intent" / "workstreams" / "sample-workstream.md",
        f"""---
workstream_id: sample-workstream
status: {workstream_status}
---

# Sample Workstream
""",
    )
    write_text(
        root / "docs" / "intent" / "workstreams" / "threads" / "sample-workstream" / "01-sample-thread.md",
        f"""---
thread_id: sample-workstream.sample-thread
status: {thread_status}
---

# Sample Thread
""",
    )


def test_completed_workstream_with_proposed_thread_fails() -> None:
    root = make_test_root()
    try:
        seed_minimum_workstream(root, workstream_status="completed", thread_status="proposed")
        result = run_validator(root)
        assert result.returncode == 1
        assert "non-terminal thread status" in result.stdout
    finally:
        rmtree(root, ignore_errors=True)


def test_completed_thread_without_checkpoint_evidence_fails() -> None:
    root = make_test_root()
    try:
        seed_minimum_workstream(root, workstream_status="completed", thread_status="completed")
        result = run_validator(root)
        assert result.returncode == 1
        assert "missing checkpoint evidence" in result.stdout
    finally:
        rmtree(root, ignore_errors=True)


def test_warning_only_without_strict_passes_but_strict_fails() -> None:
    root = make_test_root()
    try:
        seed_minimum_workstream(root, workstream_status="active", thread_status="proposed")
        result_normal = run_validator(root)
        result_strict = run_validator(root, "--strict")
        assert result_normal.returncode == 0
        assert result_strict.returncode == 1
    finally:
        rmtree(root, ignore_errors=True)


def test_completed_roadmap_with_non_terminal_workstream_fails() -> None:
    root = make_test_root()
    try:
        seed_minimum_workstream(
            root,
            roadmap_status="completed",
            workstream_status="active",
            thread_status="proposed",
        )
        result = run_validator(root)
        assert result.returncode == 1
        assert "completed master roadmap cannot contain non-terminal workstream status" in result.stdout
    finally:
        rmtree(root, ignore_errors=True)


def test_completed_roadmap_requires_completed_workstream_coverage() -> None:
    root = make_test_root()
    try:
        seed_minimum_workstream(
            root,
            roadmap_status="completed",
            workstream_status="completed",
            thread_status="dropped",
        )
        result = run_validator(root)
        assert result.returncode == 1
        assert "missing `complete_spec_set` execution map" in result.stdout
    finally:
        rmtree(root, ignore_errors=True)


def test_completed_workstream_requires_goal_and_key_deliverables() -> None:
    root = make_test_root()
    try:
        seed_minimum_workstream(
            root,
            roadmap_status="active",
            workstream_status="completed",
            thread_status="dropped",
        )
        result = run_validator(root)
        assert result.returncode == 1
        assert "completed workstream must have non-empty `Key Deliverables`" in result.stdout
    finally:
        rmtree(root, ignore_errors=True)


def test_thread_with_manual_linked_spec_section_warns_in_strict_mode() -> None:
    root = make_test_root()
    try:
        seed_minimum_workstream(root, workstream_status="active", thread_status="proposed")
        write_text(
            root / "docs" / "intent" / "workstreams" / "threads" / "sample-workstream" / "01-sample-thread.md",
            "---\n"
            "thread_id: sample-workstream.sample-thread\n"
            "status: proposed\n"
            "---\n\n"
            "# Sample Thread\n\n"
            "## Linked Spec\n\n"
            "docs/superpowers/specs/2026-05-08-sample-spec.md\n",
        )
        result = run_validator(root, "--strict")
        assert result.returncode == 1
        assert "manual thread linkage section is deprecated" in result.stdout.lower()
    finally:
        rmtree(root, ignore_errors=True)
