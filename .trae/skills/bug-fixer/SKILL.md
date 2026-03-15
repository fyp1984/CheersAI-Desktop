---
name: "bug-fixer"
description: "Diagnoses and fixes bugs with reproducible validation. Invoke when users report runtime errors, type/lint/build failures, regressions, or unexpected behavior."
---

# Bug Fixer Skill

This skill provides a best-practice workflow for fast and safe bug fixing in engineering projects.

## When to Invoke

Invoke this skill when:

- A user reports an exception, crash, wrong output, or inconsistent behavior.
- Build, lint, or type-check fails.
- A regression appears after recent changes.
- The user asks for “全面排查 / 彻底修复 / 修复到可发布”.

Do not invoke for pure feature implementation without an existing defect signal.

## Core Principles

1. Reproduce first, then modify.
2. Fix root cause, not symptoms.
3. Keep changes minimal and localized.
4. Verify with automated checks before release.
5. Preserve security and never expose secrets in logs.

## Standard Workflow

### 1) Triage

- Capture exact error text, stack, file path, and line.
- Classify severity: blocker, high, medium, low.
- Define impact scope: API, UI, data, deployment, or cross-module.

### 2) Reproduce

- Run the smallest command that reproduces the issue.
- Prefer file-scoped validation first, then project-level validation.
- Record deterministic steps and inputs.

### 3) Locate Root Cause

- Trace call chain from failing line to data source.
- Check type definitions, API contracts, and null/undefined boundaries.
- Validate assumptions against existing code patterns in nearby modules.

### 4) Implement Fix

- Prefer type-safe fixes over broad casting.
- Follow existing project conventions for naming, imports, and architecture.
- Avoid introducing new dependencies unless already used in repo.
- Keep backward compatibility unless explicitly approved.

### 5) Validate

- Run targeted checks for changed files.
- Run required global checks (type-check, lint, tests, build) when relevant.
- Confirm no new diagnostics introduced.

### 6) Deploy Readiness

- Ensure fix is reproducibly verified.
- Provide concise release notes: cause, fix, verification result, risk.
- If deployment is requested, execute standard sync/build/restart workflow.

## Validation Checklist

- [ ] Original issue can be reproduced (or evidence captured).
- [ ] Root cause identified and documented.
- [ ] Code fix applied with minimal scope.
- [ ] Targeted checks passed.
- [ ] Project-level required checks passed.
- [ ] No unrelated files changed.
- [ ] Deployment steps and rollback path are clear.

## Output Template

Use this summary format when finishing:

1. Issue Summary
2. Root Cause
3. Files Changed
4. Verification Commands and Results
5. Deployment Status
6. Risk and Follow-up
