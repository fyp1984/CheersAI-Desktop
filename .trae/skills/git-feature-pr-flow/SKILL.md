---
name: "git-feature-pr-flow"
description: "Guides safe Git feature-branch commits and PR merges. Invoke when user wants to create a feature branch from master, commit local changes, push to GitHub, and merge via Pull Request."
---

# Git Feature PR Flow

This skill standardizes local code version control for changes that must not be committed directly to `master`.

## When to Invoke

Invoke this skill when:

- The user wants to submit local changes to GitHub safely.
- The user asks to create a feature branch from `master`.
- The user wants step-by-step Git commands for add / commit / push / PR.
- The user asks for a merge workflow that requires review and verification before updating `master`.
- The user wants a reusable release-ready branching convention for optimized or verified code.

Do not invoke when:

- The user only wants a one-line Git command.
- The user wants to commit directly to `master`.
- The repository is not a Git repository.

## Core Principles

1. Never develop directly on `master`.
2. Always sync and branch from the latest `master`.
3. Stage only intended files.
4. Commit with clear, structured messages.
5. Push the feature branch first, then merge through Pull Request.
6. Complete optimization, testing, and validation before requesting merge.

## Git Hygiene Guardrails

Treat Git as the source of durable product code, configuration templates, stable documentation, and reusable tests. Do not use Git as a dump area for local debugging residue or process-time artifacts.

### Default Exclusions

The following file classes should be excluded from version control unless the user explicitly approves them as durable repository assets:

- One-off debug scripts such as `debug_*.py`, `check_*.py`, `tmp_*.ts`, `test_manual_*`, `verify_*`
- Process documentation such as `修复总结.md`, `测试记录.md`, `立即操作.md`, `当前状态.md`, `交接说明.md`
- Local validation outputs such as screenshots, exports, archives, masked samples, `.bak`, `.tmp`, `.log`
- Local sandbox and upload artifacts such as `sandbox/uploads/*`, scratch data, copied fixtures, temporary archives
- Temporary test pages or debug routes such as `test-*.tsx`, `debug-*.tsx`, throwaway admin pages, manual inspection UIs
- Secrets or secret-like helper files such as hardcoded token scripts, local credential notes, copied `.env` variants, plaintext passwords

### What To Keep

Keep files in Git only when they are part of the maintained product surface:

- Production code and stable infrastructure code
- Reusable automated tests that protect real behavior
- Template configs such as `.env.example`
- Stable architecture, deployment, or product docs
- Long-term operational scripts that are safe, reviewed, and reusable

### Ignore Strategy

When a file is not meant for durable collaboration, keep it out of Git using the smallest safe scope:

- Use repository `.gitignore` for universal junk and generated artifacts
- Use `.git/info/exclude` for developer-local debug files that should not become team policy
- Move personal notes, experiments, and scratch outputs into ignored local directories
- Prefer deleting one-off files after use instead of creating more ignore debt

### Pre-Stage Review Rules

Before any `git add`, explicitly inspect whether changed files belong to the product or only to the process that produced the product.

Must-review questions:

- Does this file implement or protect a real user-facing or system-facing capability?
- Will another teammate need this file in six weeks?
- Does it contain secrets, temporary results, screenshots, copied data, or local-only paths?
- Is it a real automated test, or only a one-time verification script?
- Is it a stable document, or only a process log that should be summarized elsewhere?

If the answer points to temporary value only, do not stage it.

## Branch Naming Convention

Use one of the following branch prefixes:

- `feature/<scope>-<topic>` for new features
- `fix/<scope>-<topic>` for bug fixes
- `refactor/<scope>-<topic>` for code cleanup or structure changes
- `chore/<scope>-<topic>` for maintenance updates

### Naming Rules

- Use lowercase letters, numbers, and hyphens only.
- Keep names concise and descriptive.
- Prefer module or page names as scope.
- Examples:
  - `feature/chat-model-provider-link`
  - `fix/data-masking-upload-path`
  - `refactor/settings-provider-modal`

## Commit Message Format

Use Conventional Commit style:

```text
<type>(<scope>): <summary>
```

### Recommended Types

- `feat`
- `fix`
- `refactor`
- `chore`
- `docs`
- `test`

### Examples

```text
fix(chat): replace deprecated model provider route
feat(settings): add provider modal entry from chat
refactor(data-masking): simplify sandbox transfer flow
```

## Standard Workflow

### 1) Confirm Repository Status

Run:

```bash
git status --short
git branch --show-current
git remote -v
```

Verify:

- Working directory is the expected repository.
- Remote points to the correct GitHub repository.
- You understand which files are modified before staging.

### 2) Update Local Master

Run:

```bash
git checkout master
git pull origin master
```

Verify:

```bash
git branch --show-current
git log --oneline -n 3
```

Success criteria:

- Current branch is `master`
- Pull succeeds without conflict
- Latest commits match remote expectations

### 3) Create a New Feature Branch

Run:

```bash
git checkout -b feature/<scope>-<topic>
```

Example:

```bash
git checkout -b feature/chat-model-provider-link
```

Verify:

```bash
git branch --show-current
```

Success criteria:

- Branch name matches convention
- Current branch is not `master`

### 4) Review Changes Before Staging

Run:

```bash
git status --short
git diff --stat
git diff
```

Verify:

- Only intended files are modified
- No secrets, temporary files, or unrelated edits are included
- Test, debug, and process files are explicitly filtered out unless approved as durable assets

Then perform a classification pass:

- `product` - stage normally
- `reusable-test` - stage only if it protects real behavior
- `process` - summarize into stable docs if needed, otherwise exclude
- `temporary` - delete or ignore locally, never stage

### 5) Stage Intended Files

Prefer explicit file paths:

```bash
git add path/to/file1 path/to/file2
```

If all current changes are intended:

```bash
git add .
```

Verify:

```bash
git status
git diff --cached --stat
git diff --cached
```

Success criteria:

- Intended files are in `Changes to be committed`
- Nothing unexpected is staged
- No temporary debug files, process docs, local outputs, or secret-bearing helpers are staged

### 6) Complete Optimization and Validation Before Commit

Run the project-appropriate checks, such as:

```bash
npm run lint
npm run test
npm run build
```

Or use repository-specific commands if different.

Verify:

- Lint passes
- Tests pass
- Build passes
- Manual critical path verification passes

If any check fails:

- Fix issues on the same feature branch
- Re-run checks before committing

### 6.1) Cleanup Sweep Before Commit

Before committing, do a lightweight cleanup sweep:

```bash
git status --short
git diff --stat
git ls-files --others --exclude-standard
```

Review and act on:

- stray debug or validation files
- process notes that should not live in Git
- generated outputs or copied data files
- files with names that suggest temporary intent such as `test-`, `debug-`, `output`, `backup`, `final`, `v2`, `done`

Preferred actions:

- delete the file if it is temporary
- move it into an ignored local path if it is still useful personally
- convert it into a stable test or stable doc if it has long-term value

### 7) Commit to the Feature Branch

Run:

```bash
git commit -m "fix(chat): replace deprecated model provider route"
```

Verify:

```bash
git log --oneline -n 1
git status
```

Success criteria:

- Commit appears at HEAD
- Working tree is clean or only contains intentionally unstaged files

### 8) Push the Feature Branch to GitHub

First push:

```bash
git push -u origin feature/<scope>-<topic>
```

Subsequent pushes:

```bash
git push
```

Verify:

```bash
git branch -vv
```

Success criteria:

- Local branch tracks `origin/feature/<scope>-<topic>`
- Push completes without rejection

### 9) Open Pull Request Instead of Updating Master Directly

After push, open a Pull Request from:

```text
feature/<scope>-<topic> -> master
```

PR title should usually match the main commit summary:

```text
fix(chat): replace deprecated model provider route
```

PR description should include:

- Change summary
- Why the change is needed
- Validation results
- Risk and rollback notes

### Pull Request Title Templates

Use one of the following PR title formats:

```text
<type>(<scope>): <summary>
```

```text
[<scope>] <summary>
```

Examples:

```text
fix(chat): replace deprecated model provider route
feat(docker): switch local stack to source-backed images
[settings] open provider configuration from chat selector
```

### Pull Request Description Template

```markdown
## Summary
- What changed
- Which modules or pages were affected

## Why
- Why the change is needed
- Which issue, defect, or requirement it addresses

## Changes
- Key implementation points
- Files or subsystems touched

## Validation
- [ ] Lint passed
- [ ] Tests passed
- [ ] Build passed
- [ ] Manual verification passed

Validation commands:
~~~bash
<commands here>
~~~

## Risk
- Known side effects
- Compatibility or deployment considerations

## Rollback
- Revert PR
- Re-deploy previous stable version if needed
- Restore configuration or data only if impacted
```

### 10) Merge Only After Review and Verification

Before merge:

- Ensure code optimization is complete
- Ensure feature behavior is manually verified
- Ensure lint, tests, and build are green
- Ensure no unresolved review comments remain

Preferred merge path:

- Merge via GitHub Pull Request UI
- Use repository policy: merge commit, squash, or rebase as required

After merge:

```bash
git checkout master
git pull origin master
git branch -d feature/<scope>-<topic>
git push origin --delete feature/<scope>-<topic>
```

Verify:

```bash
git branch
git branch -r
git log --oneline -n 5
```

## Rollback Strategy

If the merged change must be rolled back, prefer the following order:

### 1) Revert the Pull Request Commit

If the PR was merged as a merge commit:

```bash
git checkout master
git pull origin master
git revert -m 1 <merge_commit_sha>
git push origin master
```

If the PR was squash merged or rebased:

```bash
git checkout master
git pull origin master
git revert <commit_sha>
git push origin master
```

Verify:

```bash
git log --oneline -n 5
git status
```

### 2) Restore a Hotfix Branch if Further Repair Is Needed

```bash
git checkout -b fix/<scope>-rollback-followup
```

Use this branch when revert alone is insufficient and a follow-up correction is required.

### 3) Revalidate After Rollback

Run the same checks used before merge:

```bash
<lint command>
<test command>
<build command>
```

Confirm:

- The failing behavior is gone
- No new build or runtime issue is introduced
- Production or staging returns to the expected stable state

## Quick Command Template

```bash
git status --short
git checkout master
git pull origin master
git checkout -b feature/<scope>-<topic>
git status --short
git diff --stat
git add <files>
git diff --cached --stat
<run lint/test/build commands>
git commit -m "<type>(<scope>): <summary>"
git push -u origin feature/<scope>-<topic>
```

## Step Verification Checklist

- [ ] Current branch is not `master` during development
- [ ] Feature branch name follows convention
- [ ] Only intended files are staged
- [ ] Lint passed
- [ ] Tests passed
- [ ] Build passed
- [ ] Commit message follows Conventional Commit format
- [ ] Branch pushed to GitHub successfully
- [ ] Pull Request targets `master`
- [ ] Merge happens only after review and validation

## Common Mistakes to Prevent

- Committing directly on `master`
- Branching from an outdated local `master`
- Using `git add .` without reviewing file changes
- Pushing unverified code
- Opening a PR before optimization and validation complete
- Including secrets, logs, or generated local files in the commit
- Keeping one-off debug scripts and process documents under version control
- Letting temporary files accumulate until they look "normal" and get staged by habit

## Periodic Cleanup Mechanism

Use the following maintenance rhythm to keep the repository clean over time:

### Before Every Commit

- review `git status --short`
- review unstaged and staged diffs
- remove or ignore temporary debug, test, and process files

### Weekly Or Before Release

- scan for new `.bak`, `.tmp`, `output*`, `test-*`, `debug-*`, and upload artifacts
- review docs directories for process summaries that should be collapsed or removed
- review helper scripts for hardcoded credentials, local hosts, and one-time repair logic
- update `.gitignore` or `.git/info/exclude` when the same local residue pattern repeats

### Monthly Hygiene Review

- prune obsolete utility scripts that are no longer part of the maintained workflow
- remove process-time documents after their stable conclusions are merged into durable docs
- check whether temporary tests can be replaced by real automated tests or deleted
- confirm that Git history still reflects product evolution rather than troubleshooting residue

## Output Template

When assisting a user with this workflow, summarize using:

1. Current Branch Status
2. Planned Feature Branch Name
3. Files to Stage
4. Validation Commands
5. Commit Message
6. Push Status
7. Pull Request Target
8. Merge Readiness
9. Rollback Plan
