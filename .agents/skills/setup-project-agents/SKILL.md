---
name: setup-project-agents
description: Use when setting up or updating repository agent assets from the wenyue/agents public catalog, including public sync, generated project rules and skills, wrappers, retired assets, and target-owned runtime configuration.
---

# Setup Project Agents

Run the same complete reconciliation for initial setup and later updates. Reconcile public,
generated, retired, and target-owned agent assets through one idempotent workflow. Use current
target-repository evidence, review complete candidates, and accept material changes before
declaring the setup current.

## Ownership

- Always fetch the configured public GitHub archive. Do not use a local source checkout,
  cache, or stale snapshot.
- Mirror catalog-listed public assets exactly and delete only catalog-declared retired assets.
- Preserve project-local assets outside the public, generated, and retired sets. Report ownership
  collisions instead of resolving them silently.
- Regenerate managed project assets as complete candidates. Treat previous versions only as
  omission checklists and revalidate every retained fact.
- Keep target-owned model, reasoning, permission, MCP, hook, and platform settings out of the public
  catalog. Reconcile them from current platform and project evidence.

## Managed Project Assets

- `.agents/rules/20-project-tools.md`
- `.agents/rules/21-project-rules.md`
- `.agents/rules/22-project-structure.md`
- `.agents/skills/worktree-environment-setup/`
- `.agents/skills/change-set-verification/`

Accepted candidates become the target repository's runtime sources of truth.

## Shared Generation Requirements

- Write every generated or refreshed project-owned rule and skill in English.
- Use current evidence. Omit stale, speculative, unsupported, and duplicate guidance.
- Generate complete files and directories, not patch fragments.
- Make each rule conform to `.agents/rules/00-global-rule-config.md`, including title, `Strength:`,
  `Scope:`, numbering, source ownership, and thin-wrapper requirements.
- Give each generated skill frontmatter containing only `name` and `description`. Use imperative
  instructions, relative skill-owned references, and semantic target descriptions.
- Follow the target generator contracts and each target rule's generation contract for content
  specific to that asset instead of restating their policy here.
- Include a reference or script only when its owner contract and repository evidence justify it.

## Reconciliation Workflow

1. Read `AGENTS.md` and all applicable `00-*` through `09-*` rules.
2. Run `python .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py`.
3. Review every reported creation, update, deletion, retirement, and wrapper change. Confirm public
   ownership and preservation of unrelated local assets.
4. Collect current evidence for tools, runtimes, services, generated files, APIs, conventions,
   modules, dependencies, agent wrappers, and platform configuration.
5. Inventory previous managed assets as omission checklists, then revalidate each retained claim.
6. Review target-owned agent runtime and platform configuration using the boundaries below.
7. Dispatch one subagent with the shared evidence set to generate complete candidates for all
   managed project assets. If subagents are unavailable, report a blocker; do not split generation
   across inconsistent evidence sets.
8. Review every complete candidate and supporting resource. Resolve all findings before replacing
   the corresponding managed asset.
9. Apply the reviewed candidates, then run public synchronization so wrappers and entry files
   converge on the accepted sources.
10. Accept every created or materially changed rule and skill in dependency order: rules, environment
    setup, then change-set verification. Skip byte-equivalent candidates.
11. Smoke-test changed runtime fields when the installed platform exposes a safe representative
    invocation; otherwise report the result as inconclusive.
12. Run public synchronization once more, then finish with
    `python .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py --check`.

## Agent Runtime Review

- Review every catalog-listed agent during every setup or update for each installed or targeted
  platform.
- Do not store model or reasoning-effort choices in the public catalog.
- Treat existing wrapper values as previous target decisions, not public defaults. Retain them only
  after confirming they remain supported and appropriate.
- Initialize a missing target value with an explicit supported model; do not rely on inheritance.
- Require non-empty `model` and `model_reasoning_effort` in Codex wrappers, and non-empty `model` in
  Cursor and GitHub Copilot wrappers.
- Preserve evidence-backed `sandbox_mode` and other role permission fields.
- Preserve evidence-backed role permissions and target overrides. Treat missing required runtime
  fields as a final-gate blocker.
- The final public sync must preserve reviewed target-owned runtime fields.
- Run a representative smoke invocation when a reviewed runtime field changes and the installed
  platform exposes a safe surface; otherwise report the check as inconclusive.

## Platform Configuration Review

- Keep per-agent runtime fields in native wrappers and project-wide MCP, hook, concurrency, or
  permission policy in native root configuration.
- Do not create `.codex/config.toml` only to register agents, translate fields across platforms by
  name alone, write secrets, or modify user-global settings.
- Report an uncertain platform schema instead of emitting guessed fields.

## Review Gate

Review complete candidate files before acceptance.

### Generated Rules

- Confirm correct title, `Strength:`, `Scope:`, number, ownership, and evidence.
- Confirm that `20-project-tools.md`, `21-project-rules.md`, and `22-project-structure.md` keep
  distinct tooling, convention, and structure ownership.
- Confirm wrappers remain thin, point to a single source of truth, and are discoverable from
  `AGENTS.md`.

### Generated Skills

- Confirm every claim has current evidence and previous content served only as an omission checklist.
- Confirm shared requirements and the asset's own generation contract are satisfied.
- Confirm skill references and scripts are necessary, reachable, and internally consistent.
- Confirm `worktree-environment-setup` includes both host entry points.
- Confirm `change-set-verification` includes a verification matrix or executable script only when
  its generator contract and repository evidence justify one.
- Confirm no candidate absorbs worktree lifecycle, business implementation, Git integration,
  public sync, or another workflow's policy.

Do not start acceptance while any review finding remains.

## Acceptance Gate

Run only after candidate review passes.

### Generated Rules

1. Validate the complete rule against `.agents/rules/00-global-rule-config.md` and trace retained
   claims to current evidence.
2. Confirm correct ownership, numbering, discoverability from `AGENTS.md`, and synchronized thin
   wrappers.
3. Reject placeholder language, duplicated ownership, unsupported claims, and stale paths.
4. Keep the affected rule unaccepted until its static and integration checks pass.

### Generated Skills

When both generated skills changed, reuse one real temporary linked worktree. Accept the environment
skill before the verification skill.

1. Validate the complete skill and parse only the host-native setup entry point with native shell
   tooling: Bash on Linux and macOS, and PowerShell on Windows. Do not parse or invoke the other
   platform's setup script.
2. Copy uncommitted candidates into the temporary worktree when needed and verify byte equality.
3. Invoke the environment entry point and prove readiness from real project configuration.
4. Exercise the verification skill with a narrow representative change while unrelated dirty files
   remain outside its scope.
5. When an approved automatic fixer exists, exercise that path and confirm its changed files join
   the verification scope.
6. Exercise one prerequisite failure and one evidence-backed high-risk change. Confirm it avoids
   unconditional whole-project checks and does not run an expensive full suite only for acceptance.
7. Confirm scope selection, stop behavior, result classification, and that semantic diagnostics
   return to the parent implementation agent.
8. Inspect both repository and worktree state for unrelated mutations or leaked files, then remove
   the temporary worktree safely.

On failure, keep the candidate unaccepted, report exact evidence, return the complete candidate to
its generator, repeat review, and restart the affected acceptance phase.

## Validation

For public-source edits in `wenyue/agents`, run:

```bash
python .agents/skills/setup-project-agents/scripts/test_sync_public_agent_assets.py
```

For a target repository after final synchronization, run:

```bash
python .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py --check
```

## Output

List created, updated, deleted, and unchanged managed files. Report public sync, retirements,
project generation, omission review, runtime review, candidate review, acceptance, smoke checks,
and validation separately. Include exact commands and blockers; never describe a skipped or
inconclusive check as passed.
