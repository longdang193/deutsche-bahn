---
name: execution-context-pack-template
template_id: execution-context-pack-template
document_type: template
description: Template for resumable execution handoff during long-running implementation work.
type: template
stage: execution
target_globs:
- artifacts/execution_context_pack.md
required_sections:
- Objective
- Canonical Inputs (Source of Truth)
- Current Task State
- Files Changed This Session
- Verification State
- Open Blockers / Risks
- Next Exact Action
- Resume Prompt (Copy/Paste)
- Optional Deep Context (Consult Only)
- Source-Truth Rule
tags:
- handoff
- execution
- context-pack
distribution_tier: starter_kit
---

# Execution Context Pack

Use this artifact as primary handoff packet between sessions.
Keep concise, source-linked, and current as progress lands.

## 1) Objective

- **Workstream / Plan:**
- **Goal:**
- **Bounded Scope (in-scope only):**
- **Out of Scope (explicit):**

## 2) Canonical Inputs (Source of Truth)

List only files that currently govern execution.

- **Primary plan:**
- **Specs / maps / thread docs:**
- **Governance / workflow rules used:**

## 3) Current Task State

- **Completed:**
- **In Progress:**
- **Deferred / Dropped:**
- **Known divergence from plan (if any):**

## 4) Files Changed This Session

- `path/to/file` — short reason
- `path/to/file` — short reason

## 5) Verification State

- **Last commands run:**
- **Result summary:**
- **Failing checks (if any):**
- **Gaps still unverified:**

## 6) Open Blockers / Risks

- blocker or risk
- required unblock input / dependency / approval

## 7) Next Exact Action

Single smallest concrete action to run first in next session.

- **Action type:** (edit / command / verification / docs sync)
- **Target:**
- **Exact command or edit intent:**
- **Why this is next:**

## 8) Resume Prompt (Copy/Paste)

```text
Read this execution context pack first. Verify its state against listed source files. Then execute the Next Exact Action immediately. Do not re-plan unless blocker is found.
```

## 9) Optional Deep Context (Consult Only)

Use only when ambiguity remains after checking source files.

- **conversation_id:**
- **overview_log:** `.gemini/antigravity/brain/<conversation-id>/.system_generated/logs/overview.txt`
- **consult_if:** (what ambiguity requires this)
- **notes_from_log (optional, concise):**

## Source-Truth Rule

If context pack, source files, and raw log disagree:
1. source files and current tests/checks win
2. then context pack
3. raw log is fallback evidence only
