# Checkpoint Result Pack Template

Use this template for each bounded change thread checkpoint execution.

```md
# Checkpoint Result Pack

## Metadata

- Checkpoint ID: `<workstream-id>.<thread-slug>.<YYYYMMDD-HHMM>`
- Workstream ID: `<workstream-id>`
- Thread ID: `<workstream-id>.<thread-slug>`
- Thread file: `docs/intent/workstreams/threads/<workstream-id>/<nn-thread-slug>.md`
- Timestamp (UTC): `<YYYY-MM-DDTHH:MM:SSZ>`
- Owner: `<person-or-agent>`

## Intent

<what this checkpoint execution aimed to do>

## Actions

- <commands run, files changed, or workflow steps executed>

## Visible Output

- Artifacts:
  - `<path or URL>`
- Verification output:
  - `<summary of test/lint/validation results>`
- Diff summary:
  - `<high-level file or behavior deltas>`

## Status

`pass | partial | fail`

## Next Decision

<continue | fix-forward | rollback | pause and re-scope>
```
