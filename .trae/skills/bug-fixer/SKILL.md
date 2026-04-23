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
6. Keep the repair strictly inside the reported defect boundary unless the user explicitly expands scope.

## Historical Failure Modes To Strictly Forbid

The following recurring failure modes are now prohibited in future bug-fixing tasks:

- **Over-cleaning**: do not mix repo-wide formatting, import sorting, logging style changes, or broad cleanup into a targeted bug fix unless the user explicitly asked for cleanup.
- **Debug-stage residue**: do not leave behind temporary probes, test scripts, throwaway routes, process notes, screenshots, or helper outputs after diagnosis.
- **Requirement-boundary drift**: do not convert a bug fix into opportunistic refactoring, architecture reshaping, or adjacent feature work without user approval.
- **Automation-induced churn**: do not accept formatter, linter, or code-action rewrites as part of the fix unless they are directly necessary for the touched bug path or required validation.

If a potentially useful experiment or exploratory patch appears promising but is not needed for the current fix, keep it out of the production diff and record it as a separate follow-up rather than shipping it implicitly.

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

Before editing, prune any change that only serves cleanup aesthetics or tool output. The bug-fix diff should stay explainable in terms of the reported failure and its direct validation path.

- Prefer type-safe fixes over broad casting.
- Follow existing project conventions for naming, imports, and architecture.
- Avoid introducing new dependencies unless already used in repo.
- Keep backward compatibility unless explicitly approved.

### 5) Validate

- Run targeted checks for changed files.
- Run required global checks (type-check, lint, tests, build) when relevant.
- Confirm no new diagnostics introduced.
- If a tool reports unrelated historical or generated noise, record it separately instead of expanding the bug-fix scope to clean the whole repository.

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
