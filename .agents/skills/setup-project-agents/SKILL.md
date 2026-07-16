---
name: setup-project-agents
description: Use when setting up or updating repository agent assets from the wenyue/agents public catalog, including public sync, generated project rules and skills, wrappers, retired assets, and target-owned runtime configuration.
---

# Setup Project Agents

Reconcile initial setup and later updates through the same idempotent workflow. Finish only after
public assets, generated project assets, agent runtime, and every applicable native platform
configuration have been reviewed and accepted from current evidence.

## Ownership

- Fetch the configured public GitHub archive on every run. Do not substitute a local checkout,
  cache, or stale snapshot.
- Mirror catalog-listed public assets exactly and delete only catalog-declared retired assets.
- Preserve project-local assets outside the public, generated, and retired sets. Report ownership
  collisions instead of resolving them silently.
- Regenerate managed project assets as complete candidates from current target evidence. Treat
  previous versions only as omission checklists.
- Keep project-specific model, reasoning, permission, service, and platform choices out of the
  public catalog. Stable cross-target requirements may be declared as managed data.
- Use the sync script for public drift, generated wrappers, required agent runtime fields, root
  configuration reconciliation, and other requirements it can derive deterministically.
- Never edit a public-owned sync script in a target repository to encode one repository's local
  policy. Report a shared-validator gap to the public source owner instead.

## Managed Assets

The workflow owns reconciliation of:

- public rules, skills, agent prompts, wrappers, entry files, and declared retirements;
- `.agents/rules/20-project-tools.md`;
- `.agents/rules/21-project-rules.md`;
- `.agents/rules/22-project-structure.md`;
- `.agents/skills/worktree-environment-setup/`;
- `.agents/skills/change-set-verification/`;
- target-owned agent runtime values in native wrappers; and
- applicable native platform configuration.

Write every generated or refreshed project-owned rule and skill in English. Generate complete files
and directories, not fragments. Rules must conform to
`.agents/rules/00-global-rule-config.md`; generated skills must have frontmatter containing only
`name` and `description`. Follow each target asset's generator contract instead of duplicating
its policy here.

Accepted candidates become the target repository's runtime sources of truth.

## Reconciliation Workflow

1. Read `AGENTS.md` and all applicable `00-*` through `09-*` rules.
2. Run
   `python .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py`.
3. Review every reported creation, update, deletion, retirement, and wrapper change. Confirm public
   ownership and preservation of unrelated local assets.
4. Discover installed and targeted agent platforms and collect current evidence for tool versions,
   runtimes, services, generated files, APIs, conventions, modules, dependencies, and wrappers.
5. Inventory previous managed assets and settings as omission checklists. Revalidate every
   retained claim and value; do not preserve content only because it already exists.
6. Review root configuration changes reported by the sync script. Do not ask an LLM or subagent to
   reconstruct or edit script-managed values.
7. Review every catalog-listed agent for each installed or targeted platform. Resolve required
   target-owned runtime fields before generating wrappers or dispatching delegated work.
8. Dispatch one subagent with the shared evidence set to generate complete candidates for all
   managed project assets. If subagents are unavailable, report a blocker; do not split generation
   across inconsistent evidence sets.
9. Review every complete candidate and supporting resource. Resolve all findings before replacing
   the corresponding managed asset.
10. Apply accepted candidates, then run public synchronization so wrappers and entry files converge
    on their sources.
11. Accept material changes in dependency order: native platform configuration, rules, environment
    setup, then change-set verification. Skip byte-equivalent candidates.
12. Run public synchronization once more, then finish with
    `python .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py --check`.

### Agent Runtime Evidence

- Do not store target model or reasoning-effort choices in the public catalog.
- Treat existing wrapper values as previous target decisions. Retain them only after confirming
  current platform support and project suitability.
- Initialize a missing required target value with an explicitly supported model; do not rely on
  inheritance when the wrapper contract requires a value.
- Require every runtime field declared by the wrapper contract to be present and non-empty.
- Preserve evidence-backed `sandbox_mode`, role permissions, and target overrides.
- Change a runtime value only when platform support, role responsibility, permissions, observed
  quality, project complexity, or an explicit cost, latency, or quality policy justifies it.

### Root Configuration Ownership

- The sync script reconciles catalog-declared root configuration during every setup and update,
  creating or updating locked values while preserving unrelated project-owned values.
- Root configuration declarations and conditions belong in `references/public_assets.json`; parsing,
  mutation, and validation belong in the sync script.
- Do not edit managed root configuration manually or ask the generation subagent to do so. Review
  the script's reported changes and treat unresolved reconciliation errors as blockers.

## Review Gate

Review complete candidates before acceptance. Do not start acceptance while any finding remains.

### Platform Configuration

- Confirm the sync script reported each managed root configuration as created, updated, unchanged,
  or not applicable.
- Confirm locked values were reconciled without replacing unrelated project-owned values.
- Treat invalid files, unsupported declarations, missing references, or unresolved locks as blockers.

### Agent Runtime

- Confirm every catalog-listed agent has the required native wrapper and reviewed runtime fields for
  each installed or targeted platform.
- Confirm every wrapper remains eligible for its intended manual or model-driven invocation mode.
- Confirm model, reasoning, sandbox, tool, and permission choices remain supported and appropriate.
- Treat missing required runtime fields, disabled required delegation, or stale retired wrappers as
  blockers.

### Generated Rules

- Confirm correct title, `Strength:`, `Scope:`, number, ownership, and current evidence.
- Keep `20-project-tools.md`, `21-project-rules.md`, and `22-project-structure.md` limited to
  distinct tooling, convention, and structure ownership.
- Confirm wrappers remain thin, point to one source of truth, and are discoverable from
  `AGENTS.md`.

### Generated Skills

- Confirm every claim has current evidence and previous content served only as an omission
  checklist.
- Confirm the shared requirements and each asset's own generator contract are satisfied.
- Confirm references and scripts are necessary, reachable, and internally consistent.
- Confirm `worktree-environment-setup` includes both host entry points.
- Confirm `change-set-verification` contains a verification matrix or executable script only when
  its generator contract and repository evidence justify one.
- Confirm no candidate absorbs worktree lifecycle, business implementation, Git integration,
  public sync, or another workflow's policy.

## Acceptance Gate

Run only after the review gate passes.

### Platform Configuration and Agent Runtime

1. Run the final sync check to validate public assets, wrappers, references, retirements, root
   configuration locks, and other deterministic requirements.
2. Confirm a second non-check sync would be byte-idempotent for every managed root file.
3. Run a safe representative invocation for each changed runtime behavior when the installed
   platform exposes one.
4. Record unavailable smoke surfaces as inconclusive with the exact limitation.
5. Keep the affected platform unaccepted while reconciliation fails, a required reference is
   missing, or the platform lacks a result.

### Generated Rules

1. Validate the complete rule against `.agents/rules/00-global-rule-config.md` and trace retained
   claims to current evidence.
2. Confirm ownership, numbering, `AGENTS.md` discovery, and synchronized thin wrappers.
3. Reject placeholder language, duplicated ownership, unsupported claims, and stale paths.
4. Keep the rule unaccepted until its static and integration checks pass.

### Generated Skills

When both generated skills change, reuse one real temporary linked worktree. Accept the environment
skill before the verification skill.

1. Validate the complete skill and parse only the host-native setup entry point: Bash on Linux and
   macOS, and PowerShell on Windows.
2. Copy uncommitted candidates into the temporary worktree when needed and verify byte equality.
3. Invoke the environment entry point and prove readiness from real project configuration.
4. Exercise the verification skill with a narrow representative change while unrelated dirty files
   remain outside its scope.
5. Exercise an approved automatic fixer when available and confirm its changes join the verification
   scope.
6. Exercise one prerequisite failure and one evidence-backed high-risk change. Confirm the skill
   avoids unconditional whole-project checks and acceptance-only expensive full suites.
7. Confirm scope selection, stop behavior, result classification, and that semantic diagnostics
   return to the parent implementation agent.
8. Inspect repository and worktree state for unrelated mutations or leaked files, then remove the
   temporary worktree safely.

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

Never describe a skipped or inconclusive check as passed.

## Output

List created, updated, deleted, and unchanged managed files. Report public sync, retirements,
project generation, omission review, agent runtime, platform configuration, candidate review,
acceptance, smoke checks, and validation separately. Include exact commands, evidence-backed
not-applicable decisions, inconclusive checks, and blockers.
