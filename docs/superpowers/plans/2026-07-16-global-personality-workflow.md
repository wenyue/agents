# Global Personality and Workflow Rules Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Separate the global agent personality from the engineering workflow and renumber the skill configuration from `03` to `04` across every owned surface.

**Architecture:** Keep four distinct always-loaded global contracts: personality (`01`), response format (`02`), engineering workflow (`03`), and workflow/skill configuration (`04`). The English public catalog owns distributed rules, the Chinese tree mirrors their meaning, and `.agents/` independently adopts the same contracts for this repository runtime.

**Tech Stack:** Markdown rules, JSON public manifest, Python 3.11 standard-library contract tests.

## Global Constraints

- Preserve unrelated staged and unstaged work.
- Keep `Strength: Default` for personality and engineering workflow.
- Keep `Strength: Mandatory` and all existing behavior for the renumbered skill configuration.
- Update English sources, the Simplified-Chinese mirror, and the curated local runtime coherently.
- Verify with `python agents/skills/setup-project-agents/scripts/test_sync_public_agent_assets.py` and `git diff --check`.

---

### Task 1: Declare the global rule-family contract

**Files:**
- Modify: `agents/skills/setup-project-agents/scripts/test_sync_public_agent_assets.py`

**Interfaces:**
- Consumes: The repository-local curated rule set and public global-rule files.
- Produces: A failing contract for the new `03`/`04` filenames and separated responsibilities.

- [x] **Step 1: Update the curated asset expectation and add semantic rule-family assertions.**
- [x] **Step 2: Run the repository contract test and confirm it fails because the new rule files do not exist.**

### Task 2: Rewrite and redistribute the global rules

**Files:**
- Modify: `agents/rules/01-global-personality.md`
- Create: `agents/rules/03-global-engineering-workflow.md`
- Rename: `agents/rules/03-global-skill-config.md` to `agents/rules/04-global-skill-config.md`
- Modify/Create/Rename: Matching files under `agents-zh/rules/` and `.agents/rules/`

**Interfaces:**
- Consumes: The rule-family contract from Task 1 and the existing engineering/workflow configuration policies.
- Produces: Four non-overlapping global rule contracts in English, Chinese, and local-runtime form.

- [x] **Step 1: Rewrite `01` around reasoning posture, judgment, collaboration, and temperament.**
- [x] **Step 2: Move preparation, change discipline, verification, and engineering handoff behavior into `03`.**
- [x] **Step 3: Renumber the unchanged mandatory workflow configuration to `04`.**
- [x] **Step 4: Review each complete rule against the `write-rule` anti-degradation gate.**

### Task 3: Update discovery and distribution surfaces

**Files:**
- Modify: `AGENTS.md`
- Modify: `agents/skills/setup-project-agents/references/public_assets.json`
- Modify: `agents/skills/setup-project-agents/scripts/test_sync_public_agent_assets.py`

**Interfaces:**
- Consumes: The final four-file global rule family.
- Produces: Correct load order, public metadata, wrapper-generation names, and test paths.

- [x] **Step 1: Add the `03` workflow row and move the skill row to `04` in `AGENTS.md`.**
- [x] **Step 2: Insert the workflow manifest entry and renumber the skill manifest entry.**
- [x] **Step 3: Point the worktree-policy contract test at `04-global-skill-config.md`.**

### Task 4: Verify the coherent change set

**Files:**
- Verify: All files changed by Tasks 1-3 without modifying unrelated work.

**Interfaces:**
- Consumes: The complete rule, mirror, manifest, discovery, and test changes.
- Produces: Evidence that repository contracts and diff integrity pass.

- [x] **Step 1: Run `python agents/skills/setup-project-agents/scripts/test_sync_public_agent_assets.py` and expect all tests to pass.**
- [x] **Step 2: Run `git diff --check` and expect no output.**
- [x] **Step 3: Inspect the scoped diff and confirm unrelated user changes remain intact.**
