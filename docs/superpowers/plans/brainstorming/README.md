# Brainstorming Report Storage

Canonical path for each brainstorming report:

- `docs/superpowers/plans/brainstorming/<report_id>/`

Recommended structure:

```text
docs/superpowers/plans/brainstorming/<report_id>/
  report.md
  manifest.yaml
  context/
    summary.md
  evidence/
    inputs/
```

## Rules

1. `report.md` should follow:
   - `docs/operating_system/templates/brainstorming-detailed-report-template.md`
2. `manifest.yaml` tracks report path, optional supporting artifacts, timestamp, checksum.
3. Use repo-relative paths in report links.
4. Redact secrets before storage.
5. Generate report bundle only after user explicitly asks for detailed report.

## Operator Quickstart

1. Create scaffold:

```powershell
.\scripts\new_brainstorming_report.ps1 -ReportId <report_id>
```

2. Optional supporting artifact capture:

```powershell
.\scripts\brainstorming_capture.ps1 -ReportId <report_id> -SourceFile <path> -Type input
```

3. Fill `report.md` using:
   - `docs/operating_system/templates/brainstorming-detailed-report-template.md`
