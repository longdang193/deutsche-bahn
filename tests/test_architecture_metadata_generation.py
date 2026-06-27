"""
@meta
type: test
scope: unit
domain: docs
covers:
  - Architecture metadata generation from feature source, plan metadata, and code/test markers
  - Metadata shape validation for generated feature contracts and feature-local lineage
excludes:
  - Full repository-wide migration of all feature contracts
tags:
  - fast
  - ci-safe
distribution_tier: starter_kit
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import uuid
from pathlib import Path
from shutil import rmtree

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATOR = REPO_ROOT / "tools" / "docs" / "generate_architecture_metadata.py"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_generator(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GENERATOR), "--repo-root", str(root), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def make_test_root() -> Path:
    root = REPO_ROOT / ".tmp-tests" / f"architecture-metadata-{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    return root


def test_dump_yaml_normalizes_long_mapping_keys() -> None:
    long_capability_id = (
        "pipeline-performance.shortlist-reuses-the-latest-stored-embedding-row-for-a-job-url-"
        "only-when-both-the-structured-signature-and-embedding-contract-fingerprint-still-match"
    )

    spec = importlib.util.spec_from_file_location("generate_architecture_metadata", GENERATOR)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    dumped = module.dump_yaml(
        {
            "capabilities": {
                long_capability_id: {
                    "state": "active",
                    "statement": "Long keys should stay readable in generated contracts.",
                }
            }
        }
    )

    assert "\n  ? " not in dumped
    assert f'  "{long_capability_id}":' in dumped
    assert yaml.safe_load(dumped)["capabilities"][long_capability_id]["state"] == "active"


def seed_minimal_repo(root: Path) -> None:
    write_text(
        root / "docs" / "features" / "sample-feature" / "feature.source.yaml",
        """feature_id: sample-feature
name: Sample feature
status: active
type: workflow
summary: Sample feature summary.
domains:
  - sample
depends_on: []
invariants:
  - invariant_id: sample.must-validate
    statement: Sample validation always runs first.
    state: active
capabilities:
  - capability_id: sample-feature.submit-job
    statement: Submit the sample job.
    state: active
    satisfies:
      - sample.must-validate
  - capability_id: sample-feature.audit-job
    statement: Audit the sample job.
    state: inactive
stage_participation:
  - stage_id: sample_stage
    role: primary
    capability_ids:
      - sample-feature.submit-job
""",
    )
    write_text(
        root / "sample_script.py",
        '''#!/usr/bin/env python3
"""Sample script with shebang-safe metadata.

@meta
name: sample_script
type: script
features:
  - sample-feature
capabilities:
  - sample-feature.submit-job
  - sample-feature.audit-job
"""


def submit_job() -> None:
    """
    @capability sample-feature.submit-job
    """


def audit_job() -> None:
    """
    @capability sample-feature.audit-job
    """
''',
    )
    write_text(
        root / "tests" / "test_sample_script.py",
        '''"""
@meta
type: test
scope: unit
domain: sample
"""


def test_submit_job() -> None:
    """
    @proves sample-feature.submit-job
    """


def test_audit_job() -> None:
    """
    @proves sample-feature.audit-job
    """
''',
    )
    write_text(
        root / "docs" / "superpowers" / "specs" / "2026-04-18-sample-spec.md",
        """---
feature_type: modify
feature_name: sample-feature
change_id: 2026-04-18-sample-change
created_at: 2026-04-18T10:00:00+02:00
updated_at: 2026-04-18T10:00:00+02:00
status: draft
summary: "Sample change."
affects:
  features:
    - sample-feature
  capabilities:
    - sample-feature.submit-job
dag:
  depends_on: []
  enables: []
  supersedes: []
  related: []
---

# Sample Spec
""",
    )
    write_text(
        root / "docs" / "superpowers" / "specs" / "legacy-invalid-frontmatter.md",
        """# Legacy Non-Metadata Spec

This legacy note has no frontmatter and should not participate in metadata generation.
""",
    )
    write_text(
        root / "docs" / "superpowers" / "plans" / "2026-04-18-sample-plan.md",
        """---
plan_id: 2026-04-18-sample-plan
change_id: 2026-04-18-sample-change
created_at: 2026-04-18T10:05:00+02:00
updated_at: 2026-04-18T10:20:00+02:00
completed_at: 2026-04-18T10:30:00+02:00
status: complete
implements_spec: docs/superpowers/specs/2026-04-18-sample-spec.md
summary: "Add sample capability metadata."
affects:
  features:
    - sample-feature
  capabilities:
    - sample-feature.submit-job
verification:
  - pytest tests/test_sample_script.py
outcome:
  summary: Sample capability now has explicit lineage metadata.
dag:
  depends_on:
    - 2026-04-18-sample-change
  enables: []
  supersedes: []
  related: []
---

# Sample Plan
""",
    )
    write_text(root / "docs" / "features" / "sample-feature" / "history.md", "# Sample Feature History\n")
    write_text(
        root / "docs" / "sample.md",
        """---
doc_id: sample-doc
doc_type: operator-guide
explains:
  features:
    - sample-feature
  stages:
    - sample_stage
  capabilities:
    - sample-feature.submit-job
  configs:
    - configs/sample.yaml
  components:
    - aml/components/sample.yaml
---

# Sample Doc
""",
    )
    write_text(
        root / "configs" / "sample.yaml",
        """# @architecture
# owner: sample-feature
# features:
#   - sample-feature
# stages:
#   - sample_stage
# capabilities:
#   - sample-feature.submit-job
# role: config
# canonical: true
sample: true
""",
    )
    write_text(
        root / "aml" / "components" / "sample.yaml",
        """# @architecture
# owner: sample-feature
# features:
#   - sample-feature
# stages:
#   - sample_stage
# capabilities:
#   - sample-feature.submit-job
# role: component
# canonical: true
$schema: https://azuremlschemas.azureedge.net/latest/commandComponent.schema.json
name: sample
type: command
""",
    )
    write_text(
        root / "docs" / "stages" / "sample_stage.source.yaml",
        """stage_id: sample_stage
name: Sample stage
status: active
purpose: Run the sample stage.
workflow_position: sample
primary_features:
  - sample-feature
inputs:
  - Sample input
outputs:
  - Sample output
human_notes:
  - Sample stage note.
""",
    )


def test_generator_builds_feature_contract_feature_local_lineage_and_aggregate_dag(
) -> None:
    test_root = make_test_root()
    try:
        seed_minimal_repo(test_root)

        result = run_generator(test_root)

        assert result.returncode == 0, result.stderr + result.stdout
        feature_contract_path = (
            test_root / "docs" / "features" / "sample-feature" / "sample-feature.yaml"
        )
        feature_contract_text = feature_contract_path.read_text(encoding="utf-8")
        assert feature_contract_text.startswith("# GENERATED FILE - do not edit directly.")

        feature_contract = yaml.safe_load(feature_contract_text)
        assert feature_contract["feature_id"] == "sample-feature"
        assert "version" not in feature_contract
        assert feature_contract["last_updated_at"] == "2026-04-18T10:30:00+02:00"
        assert feature_contract["latest_change_id"] == "2026-04-18-sample-change"
        assert feature_contract["revision"] == 1
        assert feature_contract["capabilities"][0]["capability_id"] == "sample-feature.submit-job"
        assert feature_contract["refs"]["code"] == ["sample_script.py"]
        assert feature_contract["refs"]["tests"] == ["tests/test_sample_script.py"]
        assert feature_contract["refs"]["specs"] == [
            "docs/superpowers/specs/2026-04-18-sample-spec.md"
        ]
        assert feature_contract["refs"]["plans"] == [
            "docs/superpowers/plans/2026-04-18-sample-plan.md"
        ]
        assert feature_contract["refs"]["docs"] == ["docs/sample.md"]
        assert feature_contract["refs"]["configs"] == ["configs/sample.yaml"]
        assert feature_contract["refs"]["components"] == ["aml/components/sample.yaml"]

        feature_lineage_path = (
            test_root / "docs" / "features" / "sample-feature" / "lineage.generated.yaml"
        )
        assert feature_lineage_path.exists()
        feature_lineage_text = feature_lineage_path.read_text(encoding="utf-8")
        assert "# GENERATED FILE - do not edit directly." in feature_lineage_text
        feature_lineage = yaml.safe_load(feature_lineage_text)
        assert feature_lineage["feature_id"] == "sample-feature"
        assert feature_lineage["source"] == "docs/features/sample-feature/feature.source.yaml"
        assert set(feature_lineage) == {
            "feature_id",
            "source",
            "invariants",
            "capabilities",
            "timeline",
        }
        assert feature_lineage["invariants"]["sample.must-validate"]["satisfied_by"] == [
            "sample-feature.submit-job"
        ]
        capability_lineage = feature_lineage["capabilities"]["sample-feature.submit-job"]
        assert capability_lineage["satisfies"] == ["sample.must-validate"]
        assert capability_lineage["code"][0]["source"] == ["python_meta"]
        assert capability_lineage["code"][1]["symbols"] == ["submit_job"]
        assert capability_lineage["code"][1]["source"] == ["python_capability"]
        assert capability_lineage["tests"][0]["symbols"] == ["test_submit_job"]
        assert capability_lineage["tests"][0]["source"] == ["python_proves"]
        assert capability_lineage["docs"] == ["docs/sample.md"]
        assert capability_lineage["docs_evidence"] == [
            {
                "path": "docs/sample.md",
                "confidence": "high",
                "source": ["docs_frontmatter"],
            }
        ]
        assert capability_lineage["configs"] == ["configs/sample.yaml"]
        assert capability_lineage["config_evidence"] == [
            {
                "path": "configs/sample.yaml",
                "confidence": "high",
                "source": ["yaml_architecture"],
            }
        ]
        assert capability_lineage["components"] == ["aml/components/sample.yaml"]
        assert capability_lineage["component_evidence"] == [
            {
                "path": "aml/components/sample.yaml",
                "confidence": "high",
                "source": ["yaml_architecture"],
            }
        ]
        assert capability_lineage["specs"] == [
            "docs/superpowers/specs/2026-04-18-sample-spec.md"
        ]
        assert capability_lineage["plans"] == [
            "docs/superpowers/plans/2026-04-18-sample-plan.md"
        ]
        assert capability_lineage["evidence_gaps"] == []
        assert capability_lineage["allowed_evidence_gaps"] == []
        assert capability_lineage["lineage_exception_reason"] is None
        assert capability_lineage["unresolved_evidence_gaps"] == []
        assert capability_lineage["completeness_status"] == "complete"
        assert feature_lineage["timeline"] == [
            {
                "completed_at": "2026-04-18T10:30:00+02:00",
                "source_plan": "docs/superpowers/plans/2026-04-18-sample-plan.md",
                "change_id": "2026-04-18-sample-change",
                "summary": "Add sample capability metadata.",
                "capabilities": ["sample-feature.submit-job"],
                "verification": ["pytest tests/test_sample_script.py"],
                "outcome": "Sample capability now has explicit lineage metadata.",
            }
        ]

        aggregate_lineage = yaml.safe_load(
            (test_root / "docs" / "generated" / "capability_lineage.yaml").read_text(
                encoding="utf-8"
            )
        )
        aggregate_feature = aggregate_lineage["features"]["sample-feature"]
        assert aggregate_feature["lineage_file"] == (
            "docs/features/sample-feature/lineage.generated.yaml"
        )
        assert aggregate_feature["capability_count"] == 2
        assert {
            "capability_id": "sample-feature.submit-job",
            "state": "active",
            "code_count": 2,
            "test_count": 1,
            "config_count": 1,
            "component_count": 1,
            "spec_count": 1,
            "plan_count": 1,
            "evidence_gap_count": 0,
            "allowed_evidence_gap_count": 0,
            "unresolved_evidence_gap_count": 0,
            "completeness_status": "complete",
        } in aggregate_feature["capabilities"]

        dag = yaml.safe_load(
            (test_root / "docs" / "generated" / "architecture_dag.yaml").read_text(
                encoding="utf-8"
            )
        )
        assert {
            "from": "feature:sample-feature",
            "to": "capability:sample-feature.submit-job",
            "type": "has_capability",
        } in dag["edges"]

        stage_contract = yaml.safe_load(
            (test_root / "docs" / "stages" / "sample_stage.yaml").read_text(
                encoding="utf-8"
            )
        )
        assert stage_contract["stage_id"] == "sample_stage"
        assert stage_contract["feature_refs"] == ["sample-feature"]
        assert stage_contract["capability_refs"] == ["sample-feature.submit-job"]
        assert stage_contract["code_refs"] == ["sample_script.py"]
        assert stage_contract["test_refs"] == ["tests/test_sample_script.py"]
        assert stage_contract["doc_refs"] == ["docs/sample.md"]
        assert stage_contract["config_refs"] == ["configs/sample.yaml"]
        assert stage_contract["component_refs"] == ["aml/components/sample.yaml"]

        history = (
            test_root / "docs" / "features" / "sample-feature" / "history.md"
        ).read_text(encoding="utf-8")
        assert history.startswith("# Sample Feature History\n\n<!-- GENERATED HISTORY START -->")
        assert "## 2026-04-18" in history
        assert "### Add sample capability metadata." in history
        assert "Source plan: `docs/superpowers/plans/2026-04-18-sample-plan.md`" in history
        assert "- `sample-feature.submit-job`" in history
        assert "- `pytest tests/test_sample_script.py`" in history
        assert "Outcome:\nSample capability now has explicit lineage metadata." in history
        assert "\n## Human Notes\n" in history
        assert (
            "Add human narrative here only when operator context, rollout nuance, "
            "or meaning is needed beyond the generated plan history."
        ) in history

        idempotence_check = run_generator(test_root, "--check")
        assert idempotence_check.returncode == 0, idempotence_check.stdout
    finally:
        rmtree(test_root, ignore_errors=True)


def test_generator_preserves_existing_human_notes_below_generated_history() -> None:
    test_root = make_test_root()
    try:
        seed_minimal_repo(test_root)
        history_path = test_root / "docs" / "features" / "sample-feature" / "history.md"
        history_path.write_text(
            """# Sample Feature History

## 2026-04-01

- Legacy operator note.
""",
            encoding="utf-8",
        )

        result = run_generator(test_root)

        assert result.returncode == 0, result.stderr + result.stdout
        history = history_path.read_text(encoding="utf-8")
        assert history.startswith("# Sample Feature History\n\n<!-- GENERATED HISTORY START -->")
        assert "\n## Human Notes\n\n## 2026-04-01\n\n- Legacy operator note.\n" in history
    finally:
        rmtree(test_root, ignore_errors=True)


def test_generator_check_mode_detects_stale_generated_outputs() -> None:
    test_root = make_test_root()
    try:
        seed_minimal_repo(test_root)
        assert run_generator(test_root).returncode == 0

        generated_contract = (
            test_root / "docs" / "features" / "sample-feature" / "sample-feature.yaml"
        )
        generated_contract.write_text("stale: true\n", encoding="utf-8")

        result = run_generator(test_root, "--check")

        assert result.returncode == 1
        assert "stale generated output" in result.stdout.lower()
    finally:
        rmtree(test_root, ignore_errors=True)


def test_validator_rejects_invalid_metadata_shape() -> None:
    test_root = make_test_root()
    try:
        seed_minimal_repo(test_root)
        plan_path = (
            test_root / "docs" / "superpowers" / "plans" / "2026-04-18-sample-plan.md"
        )
        plan_text = plan_path.read_text(encoding="utf-8")
        plan_path.write_text(
            plan_text.replace(
                "completed_at: 2026-04-18T10:30:00+02:00",
                "completed_at: 2026-04-18",
            ),
            encoding="utf-8",
        )

        result = run_generator(test_root, "--validate-only")

        assert result.returncode == 1
        assert (
            "completed_at must be an iso 8601 timestamp with timezone"
            in result.stdout.lower()
        )
    finally:
        rmtree(test_root, ignore_errors=True)


def test_validator_rejects_literal_placeholder_feature_contract_filename() -> None:
    if os.name == "nt":
        return
    test_root = make_test_root()
    try:
        seed_minimal_repo(test_root)
        write_text(
            test_root / "docs" / "features" / "sample-feature" / "<feature_id>.yaml",
            "# placeholder should never exist\n",
        )

        result = run_generator(test_root, "--validate-only")

        assert result.returncode == 1
        assert "literal placeholder feature contract path is not allowed" in result.stdout.lower()
    finally:
        rmtree(test_root, ignore_errors=True)


def test_validator_rejects_python_files_without_meta() -> None:
    test_root = make_test_root()
    try:
        seed_minimal_repo(test_root)
        write_text(test_root / "bad_script.py", "def bad() -> None:\n    pass\n")

        result = run_generator(test_root, "--validate-only")

        assert result.returncode == 1
        assert "missing @meta" in result.stdout.lower()
    finally:
        rmtree(test_root, ignore_errors=True)


def test_validator_rejects_unknown_capability_references() -> None:
    test_root = make_test_root()
    try:
        seed_minimal_repo(test_root)
        plan_path = (
            test_root / "docs" / "superpowers" / "plans" / "2026-04-18-sample-plan.md"
        )
        plan_text = plan_path.read_text(encoding="utf-8")
        plan_path.write_text(
            plan_text.replace(
                "sample-feature.submit-job",
                "sample-feature.unknown-capability",
            ),
            encoding="utf-8",
        )

        result = run_generator(test_root, "--validate-only")

        assert result.returncode == 1
        assert "unknown capability" in result.stdout.lower()
    finally:
        rmtree(test_root, ignore_errors=True)


def test_validator_rejects_unqualified_feature_capability_ids() -> None:
    test_root = make_test_root()
    try:
        seed_minimal_repo(test_root)
        for path in test_root.rglob("*"):
            if not path.is_file() or path.suffix not in {".md", ".py", ".yaml"}:
                continue
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "sample-feature.submit-job",
                    "submit-job",
                ),
                encoding="utf-8",
            )

        result = run_generator(test_root, "--validate-only")

        assert result.returncode == 1
        assert "capability_id must start with sample-feature." in result.stdout
    finally:
        rmtree(test_root, ignore_errors=True)


def test_validator_rejects_unknown_yaml_architecture_references() -> None:
    test_root = make_test_root()
    try:
        seed_minimal_repo(test_root)
        config_path = test_root / "configs" / "sample.yaml"
        config_path.write_text(
            config_path.read_text(encoding="utf-8").replace(
                "sample-feature.submit-job",
                "sample-feature.unknown-capability",
            ),
            encoding="utf-8",
        )

        result = run_generator(test_root, "--validate-only")

        assert result.returncode == 1
        assert "unknown capability reference" in result.stdout.lower()
    finally:
        rmtree(test_root, ignore_errors=True)


def test_validator_rejects_duplicate_doc_ids() -> None:
    test_root = make_test_root()
    try:
        seed_minimal_repo(test_root)
        write_text(
            test_root / "docs" / "duplicate.md",
            """---
doc_id: sample-doc
doc_type: operator-guide
explains:
  features:
    - sample-feature
---

# Duplicate
""",
        )

        result = run_generator(test_root, "--validate-only")

        assert result.returncode == 1
        assert "duplicate doc_id sample-doc" in result.stdout
    finally:
        rmtree(test_root, ignore_errors=True)


def test_validator_rejects_misplaced_markdown_frontmatter() -> None:
    test_root = make_test_root()
    try:
        seed_minimal_repo(test_root)
        write_text(
            test_root / "docs" / "misplaced-frontmatter.md",
            """
---
doc_id: misplaced-frontmatter
doc_type: guide
explains:
  features:
    - sample-feature
---

# Misplaced Frontmatter
""",
        )

        result = run_generator(test_root, "--validate-only")

        assert result.returncode == 1
        assert "frontmatter must start at the first byte" in result.stdout.lower()
        assert "docs/misplaced-frontmatter.md" in result.stdout
    finally:
        rmtree(test_root, ignore_errors=True)


def test_validator_rejects_generated_fields_in_stage_source() -> None:
    test_root = make_test_root()
    try:
        seed_minimal_repo(test_root)
        stage_source = test_root / "docs" / "stages" / "sample_stage.source.yaml"
        stage_source.write_text(
            stage_source.read_text(encoding="utf-8")
            + """
code_refs:
  - sample_script.py
""",
            encoding="utf-8",
        )

        result = run_generator(test_root, "--validate-only")

        assert result.returncode == 1
        assert "generated stage fields are not allowed" in result.stdout.lower()
    finally:
        rmtree(test_root, ignore_errors=True)


def test_validator_rejects_unknown_capability_in_feature_stage_participation() -> None:
    test_root = make_test_root()
    try:
        seed_minimal_repo(test_root)
        feature_source_path = (
            test_root / "docs" / "features" / "sample-feature" / "feature.source.yaml"
        )
        feature_source_path.write_text(
            feature_source_path.read_text(encoding="utf-8").replace(
                "      - sample-feature.submit-job",
                "      - sample-feature.missing-capability",
                1,
            ),
            encoding="utf-8",
        )

        result = run_generator(test_root, "--validate-only")

        assert result.returncode == 1
        assert "capability_ids references unknown capability" in result.stdout
    finally:
        rmtree(test_root, ignore_errors=True)


def test_validator_rejects_stage_feature_role_mismatch() -> None:
    test_root = make_test_root()
    try:
        seed_minimal_repo(test_root)
        stage_source_path = test_root / "docs" / "stages" / "sample_stage.source.yaml"
        stage_source_path.write_text(
            stage_source_path.read_text(encoding="utf-8").replace(
                "primary_features:\n  - sample-feature\n",
                "supporting_features:\n  - sample-feature\n",
                1,
            ),
            encoding="utf-8",
        )

        result = run_generator(test_root, "--validate-only")

        assert result.returncode == 1
        assert "role supporting does not match" in result.stdout
    finally:
        rmtree(test_root, ignore_errors=True)


def test_validator_rejects_manual_refs_in_feature_source() -> None:
    test_root = make_test_root()
    try:
        seed_minimal_repo(test_root)
        feature_source_path = (
            test_root / "docs" / "features" / "sample-feature" / "feature.source.yaml"
        )
        feature_source_path.write_text(
            feature_source_path.read_text(encoding="utf-8")
            + """
manual_refs:
  docs:
    - docs/sample.md
""",
            encoding="utf-8",
        )

        result = run_generator(test_root, "--validate-only")

        assert result.returncode == 1
        assert "manual_refs is no longer supported" in result.stdout
        assert "configs, or components instead" in result.stdout
    finally:
        rmtree(test_root, ignore_errors=True)


def test_validator_rejects_version_in_feature_source() -> None:
    test_root = make_test_root()
    try:
        seed_minimal_repo(test_root)
        feature_source_path = (
            test_root / "docs" / "features" / "sample-feature" / "feature.source.yaml"
        )
        feature_source_path.write_text(
            "version: 1\n" + feature_source_path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        result = run_generator(test_root, "--validate-only")

        assert result.returncode == 1
        assert "version is no longer supported" in result.stdout.lower()
    finally:
        rmtree(test_root, ignore_errors=True)


def test_feature_contract_revision_uses_latest_completed_plan() -> None:
    test_root = make_test_root()
    try:
        seed_minimal_repo(test_root)
        write_text(
            test_root / "docs" / "superpowers" / "plans" / "2026-04-18-sample-followup-plan.md",
            """---
plan_id: 2026-04-18-sample-followup-plan
change_id: 2026-04-18-sample-followup-change
created_at: 2026-04-18T11:00:00+02:00
updated_at: 2026-04-18T11:10:00+02:00
completed_at: 2026-04-18T11:15:00+02:00
status: complete
implements_spec: docs/superpowers/specs/2026-04-18-sample-spec.md
summary: "Follow up sample capability metadata."
affects:
  features:
    - sample-feature
  capabilities:
    - sample-feature.submit-job
verification:
  - pytest tests/test_sample_script.py
outcome:
  summary: Follow-up sample metadata is current.
dag:
  depends_on:
    - 2026-04-18-sample-change
  enables: []
  supersedes: []
  related: []
---

# Sample Follow-up Plan
""",
        )

        result = run_generator(test_root)

        assert result.returncode == 0, result.stderr + result.stdout
        feature_contract = yaml.safe_load(
            (
                test_root / "docs" / "features" / "sample-feature" / "sample-feature.yaml"
            ).read_text(encoding="utf-8")
        )
        assert feature_contract["revision"] == 2
        assert feature_contract["latest_change_id"] == "2026-04-18-sample-followup-change"
        assert feature_contract["last_updated_at"] == "2026-04-18T11:15:00+02:00"
    finally:
        rmtree(test_root, ignore_errors=True)


def test_feature_contract_omits_freshness_without_completed_plan() -> None:
    test_root = make_test_root()
    try:
        seed_minimal_repo(test_root)
        plan_path = test_root / "docs" / "superpowers" / "plans" / "2026-04-18-sample-plan.md"
        plan_text = plan_path.read_text(encoding="utf-8").replace(
            "status: complete\n",
            "status: building\n",
            1,
        )
        plan_text = plan_text.replace(
            "completed_at: 2026-04-18T10:30:00+02:00\n",
            "",
            1,
        )
        plan_path.write_text(plan_text, encoding="utf-8")

        result = run_generator(test_root)

        assert result.returncode == 0, result.stderr + result.stdout
        feature_contract = yaml.safe_load(
            (
                test_root / "docs" / "features" / "sample-feature" / "sample-feature.yaml"
            ).read_text(encoding="utf-8")
        )
        assert "last_updated_at" not in feature_contract
        assert "latest_change_id" not in feature_contract
        assert "revision" not in feature_contract
    finally:
        rmtree(test_root, ignore_errors=True)


def test_validator_rejects_active_capability_without_code_or_test_evidence() -> None:
    test_root = make_test_root()
    try:
        seed_minimal_repo(test_root)
        (test_root / "sample_script.py").unlink()
        (test_root / "tests" / "test_sample_script.py").unlink()

        result = run_generator(test_root, "--validate-only")

        assert result.returncode == 1
        assert "lineage completeness validation failed" in result.stdout.lower()
        assert "sample-feature.submit-job has unresolved lineage gaps" in result.stdout.lower()
        assert "missing_code_evidence" in result.stdout.lower()
        assert "missing_test_evidence" in result.stdout.lower()
    finally:
        rmtree(test_root, ignore_errors=True)


def test_validator_allows_explicit_lineage_exception_for_missing_evidence() -> None:
    test_root = make_test_root()
    try:
        seed_minimal_repo(test_root)
        (test_root / "sample_script.py").unlink()
        (test_root / "tests" / "test_sample_script.py").unlink()
        feature_source_path = (
            test_root / "docs" / "features" / "sample-feature" / "feature.source.yaml"
        )
        feature_source_path.write_text(
            feature_source_path.read_text(encoding="utf-8")
            + """
lineage_exceptions:
  capabilities:
    - reason: pending-lineage-linkage-rollout
      allowed_gaps:
        - missing_code_evidence
        - missing_test_evidence
      capability_ids:
        - sample-feature.submit-job
""",
            encoding="utf-8",
        )

        validate_result = run_generator(test_root, "--validate-only")
        assert validate_result.returncode == 0, validate_result.stdout + validate_result.stderr

        generate_result = run_generator(test_root)
        assert generate_result.returncode == 0, generate_result.stdout + generate_result.stderr

        feature_lineage = yaml.safe_load(
            (
                test_root
                / "docs"
                / "features"
                / "sample-feature"
                / "lineage.generated.yaml"
            ).read_text(encoding="utf-8")
        )
        capability_lineage = feature_lineage["capabilities"]["sample-feature.submit-job"]
        assert capability_lineage["evidence_gaps"] == [
            "missing_code_evidence",
            "missing_test_evidence",
        ]
        assert capability_lineage["allowed_evidence_gaps"] == [
            "missing_code_evidence",
            "missing_test_evidence",
        ]
        assert capability_lineage["lineage_exception_reason"] == "pending-lineage-linkage-rollout"
        assert capability_lineage["unresolved_evidence_gaps"] == []
        assert capability_lineage["completeness_status"] == "excepted"
    finally:
        rmtree(test_root, ignore_errors=True)


def test_generator_uses_setup_script_meta_for_code_evidence() -> None:
    test_root = make_test_root()
    try:
        seed_minimal_repo(test_root)
        (test_root / "sample_script.py").unlink()
        write_text(
            test_root / "setup" / "setup.sh",
            """#!/bin/bash
# @meta
# name: sample_setup
# type: script
# features:
#   - sample-feature
# capabilities:
#   - sample-feature.submit-job
# lifecycle:
#   status: active

echo "sample"
""",
        )
        write_text(
            test_root / "setup" / "setup.ps1",
            """# @meta
# name: sample_setup_ps1
# type: script
# features:
#   - sample-feature
# capabilities:
#   - sample-feature.submit-job
# lifecycle:
#   status: active

Write-Host "sample"
""",
        )

        validate_result = run_generator(test_root, "--validate-only")
        assert validate_result.returncode == 0, validate_result.stdout + validate_result.stderr

        generate_result = run_generator(test_root)
        assert generate_result.returncode == 0, generate_result.stdout + generate_result.stderr

        feature_lineage = yaml.safe_load(
            (
                test_root
                / "docs"
                / "features"
                / "sample-feature"
                / "lineage.generated.yaml"
            ).read_text(encoding="utf-8")
        )
        capability_lineage = feature_lineage["capabilities"]["sample-feature.submit-job"]
        code_paths = [entry["path"] for entry in capability_lineage["code"]]
        evidence_sources = [tuple(entry["source"]) for entry in capability_lineage["code"]]
        assert "setup/setup.sh" in code_paths
        assert "setup/setup.ps1" in code_paths
        assert ("shell_meta",) in evidence_sources
        assert capability_lineage["completeness_status"] == "complete"
    finally:
        rmtree(test_root, ignore_errors=True)


def test_validator_rejects_unknown_capability_in_lineage_exception() -> None:
    test_root = make_test_root()
    try:
        seed_minimal_repo(test_root)
        feature_source_path = (
            test_root / "docs" / "features" / "sample-feature" / "feature.source.yaml"
        )
        feature_source_path.write_text(
            feature_source_path.read_text(encoding="utf-8")
            + """
lineage_exceptions:
  capabilities:
    - reason: pending-lineage-linkage-rollout
      allowed_gaps:
        - missing_code_evidence
      capability_ids:
        - sample-feature.unknown-capability
""",
            encoding="utf-8",
        )

        result = run_generator(test_root, "--validate-only")

        assert result.returncode == 1
        assert "lineage_exceptions.capabilities[0]: capability_ids references unknown capability" in result.stdout.lower()
    finally:
        rmtree(test_root, ignore_errors=True)

def test_validator_allows_repo_without_managed_features_yet(tmp_path: Path) -> None:
    write_text(tmp_path / "README.md", "# starter\n")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "features").mkdir()
    (tmp_path / "docs" / "stages").mkdir()
    (tmp_path / "docs" / "generated").mkdir()
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "docs").mkdir()

    script_path = REPO_ROOT / "tools" / "docs" / "generate_architecture_metadata.py"
    result = subprocess.run(
        [sys.executable, str(script_path), "--repo-root", str(tmp_path), "--validate-only"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr

