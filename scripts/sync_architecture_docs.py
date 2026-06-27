"""
@meta
name: sync_architecture_docs
type: script
domain: docs
responsibility:
  - Run the canonical architecture metadata sync and verification workflow.
  - Provide one stable entrypoint for contributors to refresh generated architecture docs before repo-wide validation.
  - Enforce metadata-derived refs for generated feature and stage contracts.
inputs:
  - docs/features/*/feature.source.yaml
  - docs/stages/*.source.yaml
  - docs/superpowers/specs/*.md
  - docs/superpowers/plans/*.md
  - YAML # @architecture metadata in configs and AML components
  - Python @meta, @capability, and @proves markers
outputs:
  - docs/features/<feature_id>/<feature_id>.yaml
  - docs/features/<feature_id>/lineage.generated.yaml
  - docs/features/<feature_id>/history.md
  - docs/stages/<stage_id>.yaml
  - docs/generated/capability_lineage.yaml
  - docs/generated/architecture_dag.yaml
  - Awareness report for disallowed feature-source manual_refs
tags:
  - docs
  - lineage
  - sync
distribution_tier: starter_kit
lifecycle:
  status: active
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys

import yaml

from validator_policy import normalize_adoption_mode


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def pytest_basetemp(default_relative: str) -> str:
    override = os.environ.get("REPO_VALIDATOR_PYTEST_BASETEMP")
    if override:
        return override
    return f"{default_relative}-{os.getpid()}"


def has_managed_architecture_generator(root: Path) -> bool:
    adoption_mode_path = root / "repo_config" / "adoption-mode.yaml"
    if not adoption_mode_path.exists():
        return True

    payload = yaml.safe_load(adoption_mode_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return True

    adoption_mode = normalize_adoption_mode(payload.get("adoption_mode"))
    if adoption_mode == "starter_method_only":
        return False
    if payload.get("managed_architecture_metadata") is False:
        return False
    if str(payload.get("architecture_generator", "")).strip().lower() == "none":
        return False
    return True


def build_steps(*, check_only: bool, python_executable: str) -> list[list[str]]:
    root = repo_root()
    generator = str(root / "tools" / "docs" / "generate_architecture_metadata.py")
    awareness_audit = str(root / "scripts" / "audit_architecture_linkage.py")
    formatter = str(root / "scripts" / "format_contract_yaml.py")
    adoption_validator = str(root / "scripts" / "validate_adoption_shape.py")
    pytest_step = [
        python_executable,
        "-m",
        "pytest",
        "--basetemp",
        pytest_basetemp(".tmp-tests/architecture-pytest"),
        "tests/test_architecture_metadata_generation.py",
        "tests/test_architecture_linkage_audit.py",
        "tests/test_format_contract_yaml.py",
        "tests/test_validate_adoption_shape.py",
        "tests/test_setup_hooks.py",
        "-q",
    ]

    steps: list[list[str]] = [[python_executable, adoption_validator]]
    if not has_managed_architecture_generator(root):
        steps.append(pytest_step)
        return steps

    if not check_only:
        steps.append([python_executable, generator])
    steps.extend(
        [
            [python_executable, generator, "--validate-only"],
            [python_executable, generator, "--check"],
            [python_executable, awareness_audit, "--strict-awareness", "--report-awareness"],
            [python_executable, formatter, "--check"],
            pytest_step,
        ]
    )
    return steps


def run_step(command: list[str], *, cwd: Path) -> int:
    rendered = " ".join(command)
    print(f"> {rendered}")
    completed = subprocess.run(command, cwd=cwd, check=False)
    return completed.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the canonical architecture metadata sync and verification workflow."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run validation and verification without rewriting generated outputs first.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = repo_root()
    for step in build_steps(check_only=args.check, python_executable=sys.executable):
        status = run_step(step, cwd=root)
        if status != 0:
            return status
    print(
        "Architecture sync checks passed."
        if args.check
        else "Architecture sync and checks completed. Run scripts/validate_repo_contracts.py for the repo-wide contract gate."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
