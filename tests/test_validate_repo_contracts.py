"""
@meta
name: test_validate_repo_contracts
type: test
scope: unit
domain: docs
covers:
  - Repo contract validator orchestration and fast-mode success on the current starter repo
  - Partial-generated feature history boundary validation
  - Required metadata coverage rules for setup scripts and architecture-aware YAML
tags:
  - fast
  - ci-safe
lifecycle:
  status: active
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import uuid
from pathlib import Path
from shutil import rmtree


REPO_ROOT = Path(__file__).resolve().parent.parent
VALIDATOR_PATH = REPO_ROOT / "scripts" / "validate_repo_contracts.py"
POLICY_PATH = REPO_ROOT / "scripts" / "validator_policy.py"
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


VALIDATOR = load_module("validate_repo_contracts", VALIDATOR_PATH)
POLICY = load_module("validator_policy_for_tests", POLICY_PATH)
ENV_GITIGNORE_VALIDATOR = load_module(
    "validate_env_gitignore_contract",
    REPO_ROOT / "scripts" / "validate_env_gitignore_contract.py",
)


def run_validator(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def make_test_root() -> Path:
    root = REPO_ROOT / ".tmp-tests" / f"validate-repo-contracts-{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    return root


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_adoption_mode(root: Path, mode: str) -> None:
    managed = "true" if mode == "managed_architecture_metadata" else "false"
    legacy = "true" if mode == "legacy_compatibility" else "false"
    generator = "scripts/sync_architecture_docs.py" if mode == "managed_architecture_metadata" else "none"
    write_text(
        root / "repo_config" / "adoption-mode.yaml",
        f"""adoption_mode: {mode}
managed_architecture_metadata: {managed}
legacy_feature_contracts: {legacy}
architecture_generator: {generator}
""",
    )


def test_validator_fast_mode_passes_for_current_repo() -> None:
    result = run_validator("--fast")

    assert result.returncode == 0
    assert "repo contract validation passed" in result.stdout.lower()


def test_validate_history_boundaries_reports_missing_human_notes() -> None:
    test_root = make_test_root()
    try:
        write_text(
            test_root / "docs" / "features" / "demo-feature" / "feature.source.yaml",
            "feature_id: demo-feature\nname: Demo\nstatus: active\ntype: workflow\nsummary: Demo\ninvariants: []\ndomains: []\ndepends_on: []\ncapabilities: []\n",
        )
        write_text(
            test_root / "docs" / "features" / "demo-feature" / "history.md",
            (
                "# Demo History\n\n"
                f"{POLICY.GENERATED_HISTORY_START_MARKER}\n\n"
                "Nothing yet.\n\n"
                f"{POLICY.GENERATED_HISTORY_END_MARKER}\n"
            ),
        )

        issues = VALIDATOR.validate_history_boundaries(test_root)

        assert len(issues) == 1
        assert issues[0].category == "partial_generated_boundary_error"
        assert "human notes" in issues[0].message.lower()
    finally:
        rmtree(test_root, ignore_errors=True)


def test_required_metadata_coverage_allows_leading_comment_before_architecture_block() -> None:
    test_root = make_test_root()
    try:
        write_text(
            test_root / "configs" / "demo.yaml",
            (
                "# Helpful comment.\n"
                f"{POLICY.ARCHITECTURE_METADATA_MARKER_LINE}\n"
                "# owner: demo-feature\n# stages:\n#   - fixed_train\n# role: config\nvalue: 1\n"
            ),
        )
        write_text(
            test_root / "aml" / "components" / "demo.yaml",
            (
                f"{POLICY.ARCHITECTURE_METADATA_MARKER_LINE}\n"
                "# owner: demo-feature\n# stages:\n#   - fixed_train\n# role: component\ncomponent: true\n"
            ),
        )
        write_text(
            test_root / "setup" / "demo.sh",
            (
                "#!/usr/bin/env sh\n"
                f"# {POLICY.SETUP_META_MARKER}\n"
                "# type: script\n# name: demo_setup\n\necho ok\n"
            ),
        )

        issues = VALIDATOR.validate_required_metadata_coverage(test_root)

        assert issues == []
    finally:
        rmtree(test_root, ignore_errors=True)


def test_main_propagates_subprocess_failure(monkeypatch) -> None:
    monkeypatch.setattr(VALIDATOR, "validate_required_metadata_coverage", lambda root: [])
    monkeypatch.setattr(VALIDATOR, "validate_history_boundaries", lambda root: [])
    monkeypatch.setattr(
        VALIDATOR,
        "build_subprocess_steps",
        lambda *, root, python_executable, fast: [["python", "fake-step"]],
    )
    monkeypatch.setattr(VALIDATOR, "run_step", lambda command, cwd: 1)

    status = VALIDATOR.main(["--repo-root", str(REPO_ROOT), "--fast"])

    assert status == 1


def test_build_subprocess_steps_runs_adoption_shape_before_repo_config() -> None:
    steps = VALIDATOR.build_subprocess_steps(
        root=REPO_ROOT,
        python_executable="python",
        fast=True,
    )

    rendered = [" ".join(step) for step in steps]

    assert any("validate_adoption_shape.py" in step for step in rendered)
    assert any("validate_template_required_sections.py" in step for step in rendered)
    assert any("validate_prompt_ladder.py" in step for step in rendered)
    assert any("validate_prompt_metadata_schema.py" in step for step in rendered)
    assert any("validate_env_gitignore_contract.py" in step for step in rendered)
    assert any("validate_repo_config.py" in step for step in rendered)
    assert next(
        index for index, step in enumerate(rendered) if "validate_adoption_shape.py" in step
    ) < next(index for index, step in enumerate(rendered) if "validate_repo_config.py" in step)


def test_build_subprocess_steps_skips_sync_for_starter_method_only(tmp_path: Path) -> None:
    write_adoption_mode(tmp_path, "starter_method_only")

    steps = VALIDATOR.build_subprocess_steps(
        root=tmp_path,
        python_executable="python",
        fast=True,
    )

    rendered = [" ".join(step) for step in steps]

    assert any("validate_adoption_shape.py" in step for step in rendered)
    assert any("validate_repo_config.py" in step for step in rendered)
    assert not any("sync_architecture_docs.py --check" in step for step in rendered)


def test_build_subprocess_steps_keeps_sync_for_managed_mode(tmp_path: Path) -> None:
    write_adoption_mode(tmp_path, "managed_architecture_metadata")
    write_text(tmp_path / "scripts" / "sync_architecture_docs.py", "def main():\n    return 0\n")

    steps = VALIDATOR.build_subprocess_steps(
        root=tmp_path,
        python_executable="python",
        fast=True,
    )

    rendered = [" ".join(step) for step in steps]

    assert any("validate_adoption_shape.py" in step for step in rendered)
    assert any("sync_architecture_docs.py --check" in step for step in rendered)
    assert any("validate_agent_runtime_drift.py --skip-deploy-check" in step for step in rendered)
    assert any("validate_repo_config.py" in step for step in rendered)


def test_build_subprocess_steps_skips_sync_when_script_missing_in_managed_mode(tmp_path: Path) -> None:
    write_adoption_mode(tmp_path, "managed_architecture_metadata")

    steps = VALIDATOR.build_subprocess_steps(
        root=tmp_path,
        python_executable="python",
        fast=True,
    )

    rendered = [" ".join(step) for step in steps]

    assert any("validate_adoption_shape.py" in step for step in rendered)
    assert not any("sync_architecture_docs.py --check" in step for step in rendered)
    assert any("validate_agent_runtime_drift.py --skip-deploy-check" in step for step in rendered)
    assert any("validate_repo_config.py" in step for step in rendered)


def test_build_subprocess_steps_skips_runtime_drift_for_starter_method_only(tmp_path: Path) -> None:
    write_adoption_mode(tmp_path, "starter_method_only")

    steps = VALIDATOR.build_subprocess_steps(
        root=tmp_path,
        python_executable="python",
        fast=True,
    )

    rendered = [" ".join(step) for step in steps]

    assert not any("validate_agent_runtime_drift.py --skip-deploy-check" in step for step in rendered)


def test_shared_repo_contract_markers_match_expected_contract() -> None:
    assert POLICY.GENERATED_HISTORY_START_MARKER == "<!-- GENERATED HISTORY START -->"
    assert POLICY.GENERATED_HISTORY_END_MARKER == "<!-- GENERATED HISTORY END -->"
    assert POLICY.HUMAN_NOTES_HEADING == "## Human Notes"
    assert POLICY.ARCHITECTURE_METADATA_MARKER_LINE == "# @architecture"
    assert POLICY.SETUP_META_MARKER == "@meta"


def test_validate_env_gitignore_contract_passes_with_required_entries(tmp_path: Path) -> None:
    write_text(
        tmp_path / ".gitignore",
        """.env
.env.*
!.env.example
*.private.*
*.local.*
""",
    )
    write_text(tmp_path / ".env.example", "API_KEY=placeholder\n")

    issues = ENV_GITIGNORE_VALIDATOR.validate_env_gitignore_contract(tmp_path)

    assert issues == []


def test_validate_env_gitignore_contract_reports_missing_entries(tmp_path: Path) -> None:
    write_text(tmp_path / ".gitignore", "node_modules/\n")
    write_text(tmp_path / ".env.example", "API_KEY=placeholder\n")

    issues = ENV_GITIGNORE_VALIDATOR.validate_env_gitignore_contract(tmp_path)

    assert "missing required .gitignore entry: .env" in issues
    assert "missing required .gitignore entry: .env.*" in issues
    assert "missing required .gitignore entry: *.private.*" in issues
    assert "missing required .gitignore entry: *.local.*" in issues
    assert "missing required .gitignore entry when .env.example exists: !.env.example" in issues


def test_starter_kit_classification_detects_missing_distribution_tier(tmp_path: Path) -> None:
    write_text(
        tmp_path / "repo_config" / "starter-kit-manifest.json",
        """{
  "copyPaths": ["scripts"]
}
""",
    )
    write_text(
        tmp_path / "scripts" / "demo.py",
        """\"\"\"
@meta
name: demo
type: script
\"\"\"
""",
    )

    issues = VALIDATOR.validate_starter_kit_classification(tmp_path)

    assert any("missing `distribution_tier: starter_kit`" in issue.message for issue in issues)


def test_starter_kit_classification_detects_out_of_manifest_tier(tmp_path: Path) -> None:
    write_text(
        tmp_path / "repo_config" / "starter-kit-manifest.json",
        """{
  "copyPaths": ["docs"]
}
""",
    )
    write_text(
        tmp_path / "scripts" / "demo.py",
        """\"\"\"
@meta
name: demo
type: script
distribution_tier: starter_kit
\"\"\"
""",
    )

    issues = VALIDATOR.validate_starter_kit_classification(tmp_path)

    assert any("not included in starter-kit manifest" in issue.message for issue in issues)


def test_starter_kit_classification_ignores_tmp_tests_tree(tmp_path: Path) -> None:
    write_text(
        tmp_path / "repo_config" / "starter-kit-manifest.json",
        """{
  "copyPaths": ["docs"]
}
""",
    )
    write_text(
        tmp_path / ".tmp-tests" / "scratch.py",
        """\"\"\"
@meta
name: scratch
type: script
distribution_tier: starter_kit
\"\"\"
""",
    )

    issues = VALIDATOR.validate_starter_kit_classification(tmp_path)

    assert issues == []
