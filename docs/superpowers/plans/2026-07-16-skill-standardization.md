# Skill Standardization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite all eight runtime skills and their Simplified Chinese mirrors to follow one role-aware authoring standard while preserving each skill's original purpose and safety boundaries.

**Architecture:** Keep `.agents/skills/` as the only runtime source of truth and update each `agents-zh/skills/` mirror in the same task as its English source. Apply one shared metadata and prose standard, but use role-specific body structures for generator contracts, operational workflows, orchestration, and writing guidance. Validate structure, public-asset ownership, mirror parity, trigger boundaries, and safety behavior without adding persistent evaluation infrastructure.

**Tech Stack:** Markdown, YAML frontmatter, Python `unittest`, Git, Codex skill validation and forward-testing.

---

### Task 1: Capture Baseline Behavior

**Files:**
- Read: `.agents/skills/*/SKILL.md`
- Temporary: `.tmp/skill-standardization/baseline/`

- [ ] **Step 1: Create three independent baseline evaluation assignments**

Use the current committed skills before editing:

1. Generator contracts: `change-set-verification`, `worktree-environment-setup`.
2. Operational guidance: `debug-mode`, `refactor-code`, `rename`, `write-comment`.
3. Orchestration and transfer safety: `setup-project-agents`, `worktree-integrate`.

Each assignment must receive only the relevant committed `SKILL.md` files and realistic prompts. Ask the evaluator to report the action sequence, stop conditions, ambiguous instructions, and likely unnecessary work without proposing a rewrite.

- [ ] **Step 2: Exercise the known edge cases**

Include these prompts:

- Generate a verification skill for a small multi-package repository with no existing selector.
- Prepare an already-created Windows worktree whose setup script fails halfway through.
- Enter debug mode for an intermittent browser bug and stop at the reproduction gate.
- Refactor a private function for readability without changing behavior.
- Rename a public method when compatibility requirements are not stated.
- Add a useful comment to Python code in a project whose local rules choose the comment language.
- Update public and generated project-agent assets while preserving target-owned runtime fields.
- Return verified task work to a dirty base checkout with an overlapping text file.

- [ ] **Step 3: Record baseline findings outside tracked paths**

Save concise evaluator outputs under `.tmp/skill-standardization/baseline/`. Confirm the findings cover the known design issues: author/generated-contract mixing, repeated safety text, unnecessary clarification, unconditional compatibility behavior, project-specific comment assumptions, and long orchestration steps.

### Task 2: Rewrite the Generator Contracts

**Files:**
- Modify: `.agents/skills/change-set-verification/SKILL.md`
- Modify: `agents-zh/skills/change-set-verification/SKILL.md`
- Modify: `.agents/skills/worktree-environment-setup/SKILL.md`
- Modify: `agents-zh/skills/worktree-environment-setup/SKILL.md`

- [ ] **Step 1: Rewrite `change-set-verification`**

Use this section order: `Evidence`, `Authoring Workflow`, `Generated Skill Contract`, `Normalization and Repair`, `Result Contract`, `Optional Resources`, `Review and Handoff`. Keep minimum-sufficient scope, risk-based broadening, one formatter/fixer pass, semantic-fix handoff, four result states, and evidence-backed optional resources.

- [ ] **Step 2: Synchronize the Chinese mirror**

Translate the revised prose while preserving `name`, commands, paths, result identifiers, section order, and requirement strength.

- [ ] **Step 3: Rewrite `worktree-environment-setup`**

Use this section order: `Evidence`, `Authoring Workflow`, `Generated Skill Contract`, `Failure Recovery`, `Review and Handoff`. Keep the already-created linked-worktree precondition, primary-checkout rejection, host-native entry point, idempotency, readiness boundary, and strict failure stop.

- [ ] **Step 4: Synchronize the Chinese mirror**

Translate the revised prose with the same structural and literal-preservation requirements as Step 2.

- [ ] **Step 5: Validate and commit the generator-contract pair**

Run `quick_validate.py` for both English skill directories, compare English/Chinese headings and code blocks, then commit all four files with `refactor(skills): standardize generator contracts`.

### Task 3: Rewrite the Operational Skills

**Files:**
- Modify: `.agents/skills/debug-mode/SKILL.md`
- Modify: `agents-zh/skills/debug-mode/SKILL.md`
- Modify: `.agents/skills/refactor-code/SKILL.md`
- Modify: `agents-zh/skills/refactor-code/SKILL.md`
- Modify: `.agents/skills/rename/SKILL.md`
- Modify: `agents-zh/skills/rename/SKILL.md`
- Modify: `.agents/skills/write-comment/SKILL.md`
- Modify: `agents-zh/skills/write-comment/SKILL.md`

- [ ] **Step 1: Rewrite `debug-mode`**

Keep explicit-only activation and six phases. Give each phase a purpose, action, output, and wait condition. Consolidate instrumentation invariants into one contract and keep absolute paths, file-only logging, hypothesis IDs, region markers, log clearing, filtered reading, human verification, and cleanup-after-confirmation.

- [ ] **Step 2: Rewrite `refactor-code`**

Add a mode-selection table for format, logic, and deep refactors. Infer the mode when the requested scope is unambiguous; ask only when the choice changes observable behavior or public compatibility. Move shared context, scope, cleanup, and verification requirements into a common workflow, then keep only mode-specific permissions and gates.

- [ ] **Step 3: Rewrite `rename`**

Remove `user-invocable`. Prefer semantic reference discovery when available and whole-word search as fallback. Separate code symbols, mirrored text, filenames, generated sources, serialization keys, and external contracts. Require a compatibility decision for public surfaces instead of always adding a deprecated alias.

- [ ] **Step 4: Rewrite `write-comment`**

Start with target project and language rules. Use a decision workflow: decide whether a comment adds information, identify its role, write the missing intent or constraint, apply project syntax and language, then run the project check. Keep information-density tests and concise examples, but remove universal English, Dart `///`, and Dart parameter-reference requirements.

- [ ] **Step 5: Synchronize all four Chinese mirrors**

Update each mirror immediately after its English source. Preserve commands, paths, code samples, phase numbers, mode names, and safety strength.

- [ ] **Step 6: Validate and commit the operational group**

Run `quick_validate.py` for all four English skills, compare mirror structure, and commit the eight files with `refactor(skills): standardize operational workflows`.

### Task 4: Rewrite Orchestration and Integration

**Files:**
- Modify: `.agents/skills/setup-project-agents/SKILL.md`
- Modify: `agents-zh/skills/setup-project-agents/SKILL.md`
- Modify: `.agents/skills/worktree-integrate/SKILL.md`
- Modify: `agents-zh/skills/worktree-integrate/SKILL.md`

- [ ] **Step 1: Rewrite `setup-project-agents`**

Keep `Ownership`, then use a checkpointed `Reconciliation Workflow`, one `Candidate Contract`, separate `Review` and `Acceptance` gates, focused runtime/platform subsections, `Validation`, and `Output`. Preserve archive-only public sync, declared retirements, complete candidate generation by one subagent, current-evidence regeneration, runtime-field ownership, real linked-worktree acceptance, smoke testing, and final `--check`.

- [ ] **Step 2: Rewrite `worktree-integrate`**

Use `Mode Selection`, `Task Branch Preparation`, `Base Snapshot`, `Review Mode Transfer`, `Commit Mode`, `Verification and Recovery`, and `Prohibited Operations`. Preserve review-first transfer, exactly one business commit, rebase-to-current-base, external backup, three-way text merge, unchanged base HEAD/index proof, explicit commit mode, and creation-owned cleanup.

- [ ] **Step 3: Synchronize both Chinese mirrors**

Keep section order, Git commands, mode names, paths, result states, and safety requirements equivalent.

- [ ] **Step 4: Validate and commit the orchestration pair**

Run `quick_validate.py` for both English skills and the focused public-sync tests, compare mirror structure, then commit the four files with `refactor(skills): standardize orchestration workflows`.

### Task 5: Run Automated Repository Verification

**Files:**
- Verify: `.agents/skills/*/SKILL.md`
- Verify: `.agents/skills/setup-project-agents/references/public_assets.json`
- Verify: `.agents/skills/setup-project-agents/scripts/test_sync_public_agent_assets.py`

- [ ] **Step 1: Validate every English skill**

Run the bundled `quick_validate.py` once for each of the eight directories. Expected: every command exits successfully with `Skill is valid!`.

- [ ] **Step 2: Verify public asset ownership and synchronization behavior**

Run `python .agents/skills/setup-project-agents/scripts/test_sync_public_agent_assets.py`. Expected: all tests pass with no unexpected public asset additions, removals, or wrapper changes.

- [ ] **Step 3: Verify repository text integrity**

Run `git diff --check`. Expected: no output and exit code 0.

- [ ] **Step 4: Check frontmatter and mirror structure**

Confirm all English frontmatter mappings contain only `name` and `description`; each name matches its directory. Compare English and Chinese heading counts, fenced-code-block counts, inline paths, commands, and result identifiers. Resolve every mismatch before forward-testing.

### Task 6: Forward-Test the Rewritten Skills

**Files:**
- Read: `.agents/skills/*/SKILL.md`
- Compare: `.tmp/skill-standardization/baseline/`
- Temporary: `.tmp/skill-standardization/rewrite/`

- [ ] **Step 1: Repeat the three independent evaluation assignments**

Use the same prompts and grouping from Task 1, but point evaluators at the rewritten skills. Do not provide the design diagnosis or expected fixes.

- [ ] **Step 2: Compare behavior against the baseline**

Confirm the rewrite preserves each original direction, removes the identified ambiguity or redundancy, and still stops at the original safety gates. Treat any loss of archive-only sync, primary-checkout protection, file-only debug logs, review-first integration, semantic-fix handoff, or explicit public-contract confirmation as a regression.

- [ ] **Step 3: Apply only evidence-backed corrections**

If a rewritten skill creates a new ambiguity or misses an original invariant, patch that skill and its Chinese mirror together. Re-run its `quick_validate.py` check and the affected evaluation prompt.

- [ ] **Step 4: Remove temporary evaluation artifacts**

Delete `.tmp/skill-standardization/` after recording the final comparison in the task handoff. Confirm `git status --short` shows no evaluation artifacts.

### Task 7: Final Change-Set Verification

**Files:**
- Verify: all modified English and Chinese skill files
- Verify: `docs/superpowers/specs/2026-07-16-skill-standardization-design.md`
- Verify: `docs/superpowers/plans/2026-07-16-skill-standardization.md`

- [ ] **Step 1: Inspect the complete diff**

Check that only the intended skill pairs and planning artifacts changed. Confirm scripts, manifests, wrappers, and unrelated rules remain untouched.

- [ ] **Step 2: Re-run the full validation set**

Repeat all eight `quick_validate.py` commands, the public-sync test file, mirror checks, and `git diff --check` from Task 5.

- [ ] **Step 3: Report behavior changes explicitly**

List the deliberate corrections: inferred refactor mode when unambiguous, compatibility decision for public renames, project-owned comment conventions, role-separated generator contracts, consolidated orchestration checkpoints, and deduplicated safety rules.

- [ ] **Step 4: Commit any final evidence-backed corrections**

If Task 6 required corrections, commit only those paired English/Chinese changes with `fix(skills): address forward-test findings`. Do not push.

