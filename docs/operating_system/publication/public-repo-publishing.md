# Public Repo Publishing

This document is execution runbook for publishing curated public mirror output.

Normative boundary rules are defined in:

- [Public Repo Publication Policy](./public-repo-publication-policy.md)

Doc sanitization patterns are defined in:

- [Public-Safe Doc Rewrite Guide](./public-safe-doc-rewrite-guide.md)

## Remote Roles

- `origin`
  - private source repo
  - primary development remote
- `public`
  - public curated repo
  - downstream publication target

## Operator Workflow

1. ensure private repo state is ready for export
2. run curated export workflow
3. run boundary validation gates
4. inspect export content from external-reader perspective
5. publish to `public` remote

## Commands

Prepare export without pushing:

```powershell
.\scripts\publish_public_repo.ps1
```

Prepare and publish:

```powershell
.\scripts\publish_public_repo.ps1 -Push
```

## Expected Script Gates

Publish workflow should enforce:

1. copy approved public paths
2. assert deny-policy paths are absent
3. assert required public paths exist
4. block private references/absolute local links
5. block forbidden metadata markers configured in publication policy config
6. block forbidden filename markers configured in publication policy config
7. do not treat `distribution_tier: starter_kit` as deny marker

## Pre-Publish Review Checklist

- policy constraints reviewed in publication policy doc
- export tree checked for external-reader clarity
- README and linked docs are public-safe
- no private-only workflow/process dependency remains in published docs

## Failure Handling

If any gate fails:

1. stop publish
2. fix source content or boundary config
3. rerun export and validation
4. publish only after clean pass

## Maintenance Notes

- keep procedural steps here; do not duplicate normative policy lists
- update this runbook only when script workflow changes
- update policy doc when boundary rules change
