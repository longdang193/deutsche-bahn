---
layer: operating_system
artifact_type: plan
status: completed
template_id: implementation-plan
name: single-field-dag-publication-resolver
parent_workstream: none
targets:
  - repo_config/publication-config.json
  - scripts/publish_public_repo.ps1
  - scripts/validate_repo_config.py
  - scripts/validate_repo_contracts.py
  - docs/operating_system/procedures/publication-workflow.md
related_features: []
related_stages: []
distribution_tier: starter_kit
---

# Implementation Plan: Single-Field DAG Publication Resolver

## Goal

Enable `publicPaths` to accept both file and directory seeds while preserving strict publication boundary guarantees by resolving deterministic file-only effective export set before copy/validation.

## Key Deliverables

### DAG resolution contract for publication path expansion

Define and implement deterministic seed expansion rules where `publicPaths` may include directories, but effective export set is always normalized file paths with explicit precedence for excludes and fail-fast missing-path checks.

### Publication pipeline hardening with auditable decisions

Update publication script flow to compute and log include/exclude decisions before copy, preserving required-path and marker enforcement order while eliminating silent file deletion behavior.

### Validation and documentation alignment

Align repo-config validator and publication workflow documentation with new mixed-seed contract, including guardrails, precedence rules, and operator usage examples.

## Task/Wave Breakdown

### Task 1: Define resolver contract and config semantics

**Purpose:**
- Lock exact mixed-seed behavior and precedence before script changes.

**Files:**
- Inspect: `repo_config/publication-config.json`
- Inspect: `scripts/publish_public_repo.ps1`
- Modify: `docs/operating_system/procedures/publication-workflow.md`
- Verify: `scripts/validate_repo_config.py`

**Preconditions:**
- Current file-only enforcement behavior is confirmed.
- Current required/forbidden/marker validation order is confirmed.

**Steps:**
- [x] Step 1: Define canonical resolution stages: seed collect -> expand directories -> normalize/de-dup -> apply excludes -> assert file-only effective set -> copy -> validate markers/paths.
- [x] Step 2: Define precedence table for `publicPaths`, `forbiddenPaths`, and new exclude controls.
- [x] Step 3: Document fail-fast rules for missing seed paths and unresolved required paths.

**Verification:**
- [x] Precedence and stage order documented in `publication-workflow.md` with no ambiguity.

**Exit Criteria:**
- Resolver contract documented and ready for implementation without policy gaps.

### Task 2: Implement single-field DAG resolver in publish script

**Purpose:**
- Add deterministic mixed-seed resolution in `publish_public_repo.ps1` while preserving boundary checks.

**Files:**
- Inspect: `scripts/publish_public_repo.ps1`
- Modify: `scripts/publish_public_repo.ps1`
- Verify: `scripts/publish_public_repo.ps1`

**Preconditions:**
- Task 1 resolver contract approved.

**Steps:**
- [x] Step 1: Add resolver helpers to expand directory seeds into file paths and normalize to repo-relative canonical strings.
- [x] Step 2: Add optional exclude processing (`publicExcludeGlobs` and/or explicit excludes) with deterministic ordering and reason capture.
- [x] Step 3: Replace direct foreach-copy over raw `publicPaths` with foreach-copy over resolved effective file set.
- [x] Step 4: Keep required-path checks and forbidden marker assertions in fail-fast mode; do not reintroduce pre-validation deletion.

**Verification:**
- [x] Dry-run/controlled run confirms directory seed expansion produces file-only effective set.
- [x] Publish run fails fast on missing seeds or forbidden marker leaks.

**Exit Criteria:**
- Script supports mixed seeds via one field and enforces file-only effective export boundary.

### Task 3: Update validators for new config contract

**Purpose:**
- Ensure config validators accept and enforce new DAG semantics consistently.

**Files:**
- Inspect: `scripts/validate_repo_config.py`
- Inspect: `scripts/validate_repo_contracts.py`
- Modify: `scripts/validate_repo_config.py`
- Modify: `scripts/validate_repo_contracts.py` (only if contract checks require cross-validator alignment)
- Verify: `tests/` (existing validator tests)

**Preconditions:**
- Task 2 implementation complete.

**Steps:**
- [x] Step 1: Extend repo-config schema checks to allow directory seeds in `publicPaths` while prohibiting invalid/missing path types.
- [x] Step 2: Validate exclude-field shape and defaults.
- [x] Step 3: Add/adjust tests for mixed seeds, exclusion precedence, and failure cases.

**Verification:**
- [x] `py -3 scripts/validate_repo_config.py`
- [x] `py -3 scripts/validate_repo_contracts.py --fast`
- [x] `py -3 -m pytest tests/test_validate_repo_config.py -q`

**Exit Criteria:**
- Validator layer enforces new contract and catches malformed publication config early.

### Task 4: Capture boundary evidence and rollout guidance

**Purpose:**
- Provide reproducible proof that DAG resolver preserves publication boundary integrity.

**Files:**
- Inspect: `repo_config/publication-config.json`
- Modify: `docs/operating_system/procedures/publication-workflow.md`
- Modify: `docs/superpowers/plans/audit/<new-audit-id>/...` (if audit bundle required by lane policy)
- Verify: `scripts/publish_public_repo.ps1`

**Preconditions:**
- Tasks 2 and 3 complete and passing.

**Steps:**
- [x] Step 1: Run positive publish scenario with mixed seeds including at least one directory.
- [x] Step 2: Run negative scenario where expanded file triggers forbidden marker assertion.
- [x] Step 3: Record evidence outputs and migration notes for repos currently using directory-only assumptions.

**Verification:**
- [x] `powershell -ExecutionPolicy Bypass -File scripts/publish_public_repo.ps1`
- [x] Evidence runs executed via temporary config scenarios (`scratch/publication_evidence.py`, `scratch/publication_evidence_refined.py`, `scratch/publication_evidence_final.py`, `scratch/publication_evidence_policysafe.py`).
- [x] Policy-safe closure evidence confirmed: positive pass (`RC=0`) with optional non-matching exclude and negative fail-fast (`RC=1`) via forbidden metadata marker assertion.

**Exit Criteria:**
- Evidence-backed rollout guidance available; boundary guarantees demonstrated.

### Rollout / Migration Notes

- Current baseline policy restricts `publicPaths` to `README.md`; directory-seed evidence beyond this baseline requires temporary policy override and is not part of closure proof.
- Resolver now supports optional `publicExcludeGlobs`; under README-only baseline this behaves as no-op when patterns do not match.
- For repos migrating from directory-seed assumptions, first align `forbiddenPaths` policy with intended allowed directory roots, then enable directory seeds and targeted exclude globs.

## Verification

- `py -3 scripts/validate_repo_config.py`
- `py -3 scripts/validate_repo_contracts.py --fast`
- `powershell -ExecutionPolicy Bypass -File scripts/publish_public_repo.ps1`
- `py -3 -m pytest tests/test_validate_repo_config.py -q`
- `py -3 scripts/validate_planning_lifecycle.py --strict`
- `py -3 scripts/validate_checkpoint_packs.py`

## Closure

- Lane status: closed
- Closure commit: `4944f11`
- Push status: `origin/main` updated
- Closure validators: pass


## Completion Criteria

1. all Key Deliverables satisfied
2. mixed-seed `publicPaths` resolves to deterministic file-only effective export set
3. boundary validations (required paths, forbidden paths, forbidden markers, private references) remain fail-fast and evidence-backed

Canonical source-of-truth:

<LINK>
- `docs/operating_system/governance/repo-governance.md`
- `scripts/validate_planning_lifecycle.py`
</LINK>
