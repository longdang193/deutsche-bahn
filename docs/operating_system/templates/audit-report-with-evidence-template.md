---
template_id: audit-report-with-evidence
document_type: template
target_globs:
- docs/superpowers/plans/audit/*/report.md
required_sections:
- Metadata
- Scope
- Findings
- Evidence
- Reproduction
- Root Cause And Boundary
- Fix And Verification
- Risk And Disposition
- Artifact Index
- Completion Checklist
distribution_tier: starter_kit
---

# Audit Report With Evidence Template

## Metadata

- Audit ID: `<YYYYMMDD-HHMM-<topic>>`
- Status: `open | mitigated | resolved | accepted-risk`
- Severity: `low | medium | high | critical`
- Owner: `<name>`
- Created At: `<ISO-8601>`
- Updated At: `<ISO-8601>`
- Related Thread/Plan: `<path or none>`

## Scope

- Environment: `<os/runtime/versions>`
- Commit/Branch: `<commit sha + branch>`
- Affected Surface: `<modules/stages/components>`

## Findings

### Finding `<ID>`: `<short title>`

- Classification: `regression | flaky | environment | spec-mismatch | security | data-quality | other`
- Impact: `<who/what affected>`
- Expected Behavior: `<expected>`
- Actual Behavior: `<actual>`

## Evidence

For each finding, include links to raw artifacts:

- Screenshot/Image: `evidence/images/<file>`
- Result JSON: `evidence/results/<file>.json`
- Logs/Text: `evidence/results/<file>.log`
- Trace/Telemetry export: `evidence/results/<file>`

Each evidence item should include:

- capture timestamp
- producing command/tool
- checksum (sha256) from `manifest.yaml`

## Reproduction

- Preconditions:
  - `<required env/config>`
- Steps:
  1. `<step>`
  2. `<step>`
- Commands:

```powershell
# exact reproducible commands
```

- Determinism notes: `<seed/input dataset/options>`

## Root Cause And Boundary

- Failure boundary: `<stage/component/contract>`
- Root cause summary: `<concise technical cause>`

## Fix And Verification

- Fix summary: `<bounded fix>`
- Verification commands:

```powershell
# exact verification commands
```

- Verification evidence links:
  - `<path>`

## Risk And Disposition

- Residual risk: `<none/describe>`
- Disposition decision: `<resolved | mitigated | accepted-risk>`
- Follow-ups: `<tests/specs/scenarios/docs>`

## Artifact Index

- Manifest: `manifest.yaml`
- Evidence root: `evidence/`
- Repro root: `repro/`

## Completion Checklist

- [ ] qualifying trigger documented (or explicit bypass)
- [ ] evidence bundle linked and hashed
- [ ] deterministic repro steps included
- [ ] expected vs actual included
- [ ] verification evidence attached
- [ ] final status recorded
