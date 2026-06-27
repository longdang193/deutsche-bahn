"""
@meta
name: test_sync_architecture_docs
type: test
scope: unit
domain: docs
covers:
  - Starter-mode sync skips managed architecture generation and check steps.
  - Managed-mode sync preserves generator, formatter, audit, and focused test lanes.
  - Architecture sync pytest basetemp is unique per process unless explicitly overridden.
tags:
  - fast
  - ci-safe
lifecycle:
  status: active
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SYNC_SCRIPT_PATH = REPO_ROOT / "scripts" / "sync_architecture_docs.py"
SCRIPTS_ROOT = str(REPO_ROOT / "scripts")

if SCRIPTS_ROOT not in sys.path:
    sys.path.insert(0, SCRIPTS_ROOT)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SYNC = load_module("sync_architecture_docs", SYNC_SCRIPT_PATH)


def test_build_steps_skips_managed_architecture_lanes_in_starter_mode(monkeypatch) -> None:
    monkeypatch.setattr(SYNC, "repo_root", lambda: REPO_ROOT)

    steps = SYNC.build_steps(check_only=True, python_executable="python")
    rendered = [" ".join(step) for step in steps]

    assert any("validate_adoption_shape.py" in step for step in rendered)
    assert not any(step[1:] == [str(REPO_ROOT / "tools" / "docs" / "generate_architecture_metadata.py"), "--validate-only"] for step in steps)
    assert not any(step[1:] == [str(REPO_ROOT / "tools" / "docs" / "generate_architecture_metadata.py"), "--check"] for step in steps)
    assert not any(step[1:] == [str(REPO_ROOT / "scripts" / "audit_architecture_linkage.py"), "--strict-awareness", "--report-awareness"] for step in steps)
    assert not any(step[1:] == [str(REPO_ROOT / "scripts" / "format_contract_yaml.py"), "--check"] for step in steps)
    assert any("tests/test_architecture_metadata_generation.py" in step for step in rendered)
    assert any("tests/test_setup_hooks.py" in step for step in rendered)


def test_build_steps_keeps_managed_architecture_lanes_when_enabled(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "repo_config").mkdir(parents=True)
    (tmp_path / "repo_config" / "adoption-mode.yaml").write_text(
        """adoption_mode: managed_architecture_metadata
repo_role: source_owner
managed_architecture_metadata: true
legacy_feature_contracts: false
architecture_generator: scripts/sync_architecture_docs.py
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(SYNC, "repo_root", lambda: tmp_path)

    steps = SYNC.build_steps(check_only=True, python_executable="python")
    rendered = [" ".join(step) for step in steps]

    assert any("validate_adoption_shape.py" in step for step in rendered)
    assert any("generate_architecture_metadata.py --validate-only" in step for step in rendered)
    assert any("generate_architecture_metadata.py --check" in step for step in rendered)
    assert any("audit_architecture_linkage.py --strict-awareness --report-awareness" in step for step in rendered)
    assert any("format_contract_yaml.py --check" in step for step in rendered)
    assert any("tests/test_architecture_metadata_generation.py" in step for step in rendered)


def test_pytest_basetemp_is_unique_per_process_by_default(monkeypatch) -> None:
    monkeypatch.delenv("REPO_VALIDATOR_PYTEST_BASETEMP", raising=False)
    monkeypatch.setattr(os, "getpid", lambda: 4242)

    assert SYNC.pytest_basetemp(".tmp-tests/architecture-pytest") == ".tmp-tests/architecture-pytest-4242"


def test_pytest_basetemp_respects_override(monkeypatch) -> None:
    monkeypatch.setenv("REPO_VALIDATOR_PYTEST_BASETEMP", "custom-basetemp")

    assert SYNC.pytest_basetemp(".tmp-tests/architecture-pytest") == "custom-basetemp"
