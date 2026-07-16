# Curate Project Agents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep `.agents/` limited to this repository's runtime configuration and remove the real-model smoke-test requirement from the shared `setup-project-agents` skill.

**Architecture:** `agents/` remains the complete public catalog and implementation source. `.agents/` becomes a curated target-local runtime containing only applicable rules, the verifier prompt, and the project workflows required by this repository. Project-local rules and verification are synthesized from current repository evidence instead of copied from shared generation contracts.

**Tech Stack:** Markdown agent contracts, Python 3.11 standard library, `unittest`, Git.

## Global Constraints

- Preserve all existing user edits, especially both `change-set-verifier.md` files.
- Do not change target installation paths away from `.agents/`.
- Do not invoke a real model during `setup-project-agents` acceptance.
- Do not commit, push, or create a pull request.

---

### Task 1: Remove the real-model smoke-test requirement

**Files:**
- Modify: `agents/skills/setup-project-agents/scripts/test_sync_public_agent_assets.py`
- Modify: `agents/skills/setup-project-agents/SKILL.md`
- Modify: `agents-zh/skills/setup-project-agents/SKILL.md`

**Interfaces:**
- Consumes: the shared setup skill and its Chinese mirror.
- Produces: an acceptance contract that validates configuration and local deterministic behavior without a real-model invocation.

- [x] Add a contract test requiring the English prohibition `Do not invoke a real model` and the Chinese equivalent `不得调用真实模型`, while rejecting `safe representative invocation` and smoke-check reporting.
- [x] Run the focused test and confirm it fails against the current skill.
- [x] Rewrite the Agent Runtime acceptance and output sections in both language versions so static/runtime-field checks remain, but real-model smoke tests are explicitly out of scope.
- [x] Run the focused test and then the complete public-source test suite.

### Task 2: Generate complete project-local candidates

**Files:**
- Rewrite: `.agents/rules/20-project-tools.md`
- Rewrite: `.agents/rules/21-project-rules.md`
- Rewrite: `.agents/rules/22-project-structure.md`
- Rewrite: `.agents/skills/change-set-verification/SKILL.md`

**Interfaces:**
- Consumes: repository layout, public manifest, sync/test scripts, README ownership statements, and applicable shared generation contracts.
- Produces: three direct project rules and one executable project-local verification skill.

- [x] Generate one coherent candidate set from the shared evidence: Python 3.11, no declared package installation/formatter/linter/service, the public `unittest` suite, `agents/` public ownership, `agents-zh/` Markdown mirror ownership, and curated `.agents/` runtime ownership.
- [x] Review each candidate as a complete artifact for exact paths, commands, boundaries, frontmatter, and absence of generator-only wording.
- [x] Apply the accepted candidates without modifying their public generation contracts under `agents/`.

### Task 3: Prune `.agents/` and repair discovery

**Files:**
- Modify: `AGENTS.md`
- Modify: `README.md`
- Delete from `.agents/rules/`: `11-base-cpp.md`, `11-base-flutter.md`, `11-base-go.md`, `12-base-arb.md`
- Delete from `.agents/skills/`: `debug-mode/`, `refactor-code/`, `rename/`, `setup-project-agents/`, `worktree-environment-setup/`, `write-comment/`
- Keep in `.agents/skills/`: `change-set-verification/`, `track-worktree-time/`, `worktree-integrate/`, `write-rule/`, `write-skill/`

**Interfaces:**
- Consumes: the accepted project-local candidates.
- Produces: a self-consistent project runtime whose discovery files reference only existing assets.

- [x] Remove the listed unrelated language rules and nonessential shared workflows from `.agents/` only; leave `agents/` and `agents-zh/` public sources intact.
- [x] Remove obsolete language rows from `AGENTS.md` and describe `.agents/` in `README.md` as curated rather than mirrored.
- [x] Update public-source tests that previously required a duplicate `.agents/skills/setup-project-agents/` installation.
- [x] Verify every `AGENTS.md` and verifier-prompt reference resolves, `.agents/` contains only the declared keep set, public tests pass, and `git diff --check` is clean.
