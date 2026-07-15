---
name: setup-project-agents
description: >-
  Set up or update repository agent assets from the wenyue/agents public catalog. Use when Codex
  must reconcile public rules, skills, subagents, retired assets, wrappers, generated project
  rules and skills, or target-owned agent runtime configuration.
---

# Setup Project Agents

Run the same complete reconciliation for initial setup and later updates: synchronize public
assets, regenerate managed project assets from current evidence, review complete candidates, and
accept the result in the target repository.

## Ownership

- Treat setup and update as the same idempotent workflow.
- Always fetch the configured public GitHub archive. Do not use a local source checkout, cache, or
  stale snapshot.
- Mirror catalog-listed public assets exactly and delete only catalog-declared retired assets.
- Preserve project-local assets outside the public, generated, and retired sets. Report ownership
  collisions instead of resolving them silently.
- Regenerate managed project assets as complete candidates on every run. Read their previous
  versions only as omission checklists; they are not authoritative generation inputs.
- Revalidate every retained command, path, service, convention, and ownership claim against current
  target-repository evidence.
- Use one subagent to generate all project-owned candidates from the same evidence set. If subagents
  are unavailable, report a blocker instead of generating the files in the main agent.

## Managed Project Assets

- `.agents/rules/20-project-tools.md`
- `.agents/rules/21-project-rules.md`
- `.agents/rules/22-project-structure.md`
- `.agents/skills/worktree-environment-setup/`
- `.agents/skills/change-set-verification/`

Accepted candidates become the target repository's runtime sources of truth.

## Shared Generation Requirements

Apply only requirements shared by every generated asset here. Follow each target rule or generator
skill for its content, organization, optional resources, and workflow-specific constraints.

- Write every generated or refreshed project-owned rule and skill in English.
- Use current repository evidence. Omit unsupported, stale, speculative, and duplicate guidance.
- Generate complete files and directories, not patch fragments. Keep the result concise while
  preserving every required constraint and ownership boundary.
- Make every generated rule conform to `.agents/rules/00-global-rule-config.md`. Include a title,
  `Strength:`, `Scope:`, and rule-specific body; use its numbered location and thin wrappers as the
  source-of-truth contract requires.
- Give every generated skill YAML frontmatter containing only `name` and `description`. Use
  imperative instructions, relative references for skill-owned resources, and semantic target
  descriptions rather than machine-specific paths.
- For rule-specific or skill-specific authoring decisions, follow the target generator skill itself
  or the target rule's generation contract instead of restating that guidance here.
- Review complete candidate contents, including references and scripts, before applying or invoking
  them.

## Workflow

1. Read `AGENTS.md` and all applicable `00-*` through `09-*` rules.
2. Run `python .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py`.
3. Review every reported creation, update, and deletion. Confirm public ownership, declared
   retirements, wrapper reconciliation, and preservation of unrelated local assets.
4. Collect current evidence for tools, runtimes, services, generated files, APIs, conventions,
   modules, dependencies, wrappers, and platform configuration.
5. Inventory the previous managed assets only as omission checklists, then revalidate each retained
   fact.
6. Review agent runtime and platform configuration using the sections below.
7. Dispatch one subagent to generate complete candidates for all managed project assets from the
   generator contracts and shared evidence.
8. Review the complete candidates. Resolve all findings and repeat review before replacing any
   managed asset.
9. Run the public sync so wrappers and entry files reflect the reviewed candidates.
10. Run generated-rule acceptance for each rule that was created or materially changed. Then run
    environment-skill acceptance when `worktree-environment-setup` changed and verification-skill
    acceptance after the environment is ready when `change-set-verification` changed. Skip
    acceptance for a byte-equivalent regenerated skill or rule.
11. Smoke-test changed platform runtime fields when a safe representative invocation is available.
12. Run the public sync again, then final validation including `sync_public_agent_assets.py --check`.

## Agent Runtime Review

Review every catalog-listed agent during every setup or update for each installed or targeted
platform.

- Do not store model or reasoning-effort choices in the public catalog. Existing wrapper values are
  prior target decisions, not public defaults.
- Retain a current target value only after confirming that it remains supported and appropriate.
  Initialize missing values with an explicit supported model; do not rely on inheritance.
- Change a value only when support, responsibility, permissions, observed quality, project
  complexity, or an explicit cost/latency/quality policy justifies it.
- Codex wrappers require non-empty `model` and `model_reasoning_effort`; Cursor `model` and GitHub
  Copilot `model` must also be non-empty. Never omit these required target-owned fields.
- Preserve stable public role permissions such as writable Codex `sandbox_mode`; keep target
  permission overrides only when current platform and role evidence supports them.
- The final public sync must preserve reviewed target-owned runtime fields. Treat missing or empty
  required fields as a blocker at the strict final gate.
- When runtime fields change, run a representative smoke invocation if the installed platform has a
  safe surface; otherwise report the smoke result as inconclusive.

## Platform Configuration Review

- Keep per-agent runtime fields in native wrappers and project-wide MCP, hook, concurrency, or
  permission policy in native root configuration.
- Do not create `.codex/config.toml` only to register those agents; Codex discovers standalone agent
  TOML files directly.
- Do not translate fields across platforms by name alone. Model selection, sandboxing, read-only
  state, tool access, and invocation policy are different controls.
- Merge only evidence-backed project-owned keys. Preserve unrelated keys and never write secrets or
  user-global settings.
- Report uncertain platform schemas instead of emitting guessed fields.

## Review

Review complete candidate files before acceptance. Confirm that:

- every claim has current evidence and every retained previous fact was revalidated;
- all shared generation requirements and each file's own generation contract are satisfied;
- no candidate absorbs worktree lifecycle, business implementation, Git integration, public sync,
  or another workflow's policy.

### Generated Rules

- Confirm that each rule has the correct title, `Strength:`, `Scope:`, number, and rule-specific
  body required by `.agents/rules/00-global-rule-config.md`.
- Confirm that the three rules have distinct ownership, contain no placeholder language, and do not
  repeat policy already owned by another rule or skill.
- Confirm that every rule remains concise, actionable, and traceable to current repository evidence.

### Generated Skills

- Confirm that skill-owned references and scripts are necessary, internally consistent, and
  reachable from `SKILL.md`.
- Confirm that `worktree-environment-setup` contains `scripts/setup.sh` and `scripts/setup.ps1`, and
  that both entry points satisfy its generation contract.
- Confirm that `change-set-verification` uses a verification matrix or executable script only when
  its generation contract and repository evidence justify one.

Do not start acceptance while any review finding remains. Resolve findings in complete candidates,
then repeat the complete review.

## Acceptance

Run only after candidate review passes. Accept every created or materially changed managed rule or
skill; skip byte-equivalent regenerated assets.

### Generated Rules

1. Validate each complete rule source against `.agents/rules/00-global-rule-config.md`, including its
   strength, scope, numbering, source-of-truth location, and repository-root-relative references.
2. Trace every retained claim to current evidence and confirm that previous generated rules were
   used only as omission checklists.
3. Confirm that placeholder language is absent and that tooling, conventions, and structure remain
   owned by `20-project-tools.md`, `21-project-rules.md`, and `22-project-structure.md` respectively.
4. Inspect `AGENTS.md` and the synchronized Cursor and Copilot rule wrappers. Confirm that applicable
   rules are discoverable, wrappers remain thin, and each wrapper points to the rule's single source
   of truth.
5. Keep every affected rule unaccepted until all static and integration checks pass.

### Generated Skills

Run only for created or materially changed generated skills. When both skills changed, reuse one
real temporary linked worktree and accept the environment skill before the verification skill.

#### Environment Skill

1. Validate the complete skill and parse only the host entry point with native shell tooling: Bash
   on Linux and macOS for `scripts/setup.sh`, and PowerShell on Windows for `scripts/setup.ps1`. Do
   not parse or invoke the other platform's setup script.
2. Copy uncommitted candidates into the temporary worktree when needed and verify byte equality.
3. Invoke the host entry point and verify the required environment outcome using real project
   configuration rather than version-only probes.
4. Inspect repository and worktree state for primary-checkout mutation, unrelated changes, leaked
   files, or lifecycle operations outside the skill's contract.

#### Verification Skill

1. Prepare the temporary worktree with the accepted environment skill and validate the complete
   verification skill plus its verification matrix when present.
2. Exercise a narrow representative change set. Confirm minimum supported checks run once and
   unrelated dirty files remain outside the selected scope.
3. When an approved automatic fixer exists, exercise its documented normalization path and confirm
   that its changed files join the verification scope.
4. Exercise one prerequisite failure and one documented high-risk change. Confirm dependent checks
   stop after the prerequisite and broader verification is selected only for the stated risk.
5. Confirm required surfaces report `passed`, `failed`, `inconclusive`, or `not applicable`, and that
   semantic diagnostics return to the parent agent.
6. Do not run unconditional whole-project checks or an expensive full suite only to accept the
   skill unless current repository evidence requires that surface for every coherent change set.
7. Inspect repository and worktree state, then remove the temporary worktree safely.

On any acceptance failure, keep the candidate unaccepted, report the exact evidence, return the
complete candidate to its generator for revision, repeat review, and restart the affected
acceptance phase.

## Validation

For public-source edits in `wenyue/agents`, run:

```bash
python .agents/skills/setup-project-agents/scripts/test_sync_public_agent_assets.py
```

For target repository updates after final synchronization, run:

```bash
python .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py --check
```

## Output

- List created, updated, deleted, and unchanged managed files.
- Report public synchronization, retirements, project regeneration, omission review, runtime review,
  platform configuration, candidate review, acceptance, smoke checks, and validation separately.
- Include exact commands and blockers. Never describe skipped or inconclusive checks as passed.
