---
name: setup-project-agents
description: Use when initializing or updating a repository with the Agents Rules, Skills, Agents, and Matt repository-context snapshot.
---

# Setup Project Agents

Run the script-backed setup workflow for one target repository. The workflow always enables Codex,
Cursor, and Copilot, authors the project-owned snapshot, configures the bundled Matt Skills, and
applies everything in one reviewed transaction. Scripts own deterministic setup behavior; the Agent
owns only the requested authoring decisions.

## Ownership

Do not reconstruct source selection, discovery, overwrite, deletion, validation, transaction,
checking, summary, or cleanup behavior. Invoke the public workflow and treat its result as
authoritative. Host trust, plugin caches, bundled Hooks, and external-tool installation are outside
this workflow.

## Managed Assets

The Agent may edit only these workflow inputs:

- requested model values the user explicitly changes and empty values that remain in the reported
  `models.json`;
- the eight targets listed by `generation_requests`: three Rules, two Skills, and
  `docs/agents/issue-tracker.md`, `docs/agents/triage-labels.md`, and
  `docs/agents/domain.md`.

Write every repository-relative `target` unchanged under the reported `generated` directory. For
example, `.agents/rules/20-project-tools.md` belongs at
`GENERATED/.agents/rules/20-project-tools.md`, and `docs/agents/domain.md` belongs at
`GENERATED/docs/agents/domain.md`. Do not edit `request.json` or create another models or generated
root.

The three `docs/agents/` files and the `AGENTS.md` pointers are shared, human-editable repository
configuration. Preserve complete existing documents unless the user explicitly confirms a
reconfiguration; they are not disposable generated cache files.

## Preconditions

- Start at the target repository root and identify the loaded Skill directory as
  `SETUP_PROJECT_AGENTS_ROOT`.
- Enable Codex, Cursor, and Copilot on every run.

## Reconciliation Workflow

1. Invoke the platform wrapper with `start` and the target:

   ```sh
   sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/setup_project_agents.sh" start \
     --target "$PWD"
   ```

   On Windows, invoke `setup_project_agents.ps1` with the same arguments. Stop on a nonzero result.
   From the single JSON result, record `session` as `SESSION` and use its reported request, models,
   generated, and source paths; record the reported generated path as `GENERATED`.

2. Read `SESSION/request.json` and the reported `models.json`. Start preserves model settings from
   existing platform Agent configurations. Keep every prefilled value unless the user explicitly
   changes it, and fill each remaining empty required `model` at the requested Agent and
   `model_key`. Codex optional `model_reasoning_effort` and `sandbox_mode` values are strings;
   Cursor optional `readonly` is Boolean.

3. Resolve the reported `source_root` as `SOURCE_ROOT`. Read the complete authoring contracts at
   `SOURCE_ROOT/setup-assets/skills/write-rule/SKILL.md`,
   `SOURCE_ROOT/setup-assets/skills/write-skill/SKILL.md`, and
   `SOURCE_ROOT/skills/setup-matt-pocock-skills/SKILL.md`. Apply the Rule and Skill Blueprints, then
   configure the three Matt documents inside this same setup workflow; do not invoke
   `setup-matt-pocock-skills` as a second Skill.

4. Explore the target using the Matt setup contract. Preserve any complete existing
   `docs/agents/*.md` document unless the user requests a change. Otherwise:

   - select the GitHub, GitLab, or local issue-tracker seed that matches the unambiguous Git remote;
     when remotes disagree or an existing document conflicts with the remote, present the evidence
     and wait for confirmation;
   - use the existing triage-label mapping when present, or the bundled five-role default when it is
     absent;
   - use the single-context domain layout when no monorepo signal exists; when workspace files or
     multiple source packages indicate materially separate contexts, present single- and
     multi-context choices and wait for confirmation.

   Write exactly all eight `generation_requests` targets to `GENERATED/<target>`, preserving every
   target path segment. The issue-tracker request names the GitHub seed as its catalog blueprint;
   when confirmed evidence selects GitLab or local markdown, read the corresponding sibling seed
   from the vendored Matt setup Skill and write the same requested target.

5. After the Review Gate passes, invoke the same wrapper with `finish` and only the session path:

   ```sh
   sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/setup_project_agents.sh" finish \
     --session "$SESSION"
   ```

   Do not invoke the internal prepare/apply/check commands directly.

6. If the workflow must stop after a successful start but before invoking finish, invoke `cancel`
   with only `--session "$SESSION"`. Do not invoke cancel after finish returns: finish owns session
   cleanup on both success and failure.

## Stop Conditions

Stop on any start, finish, or cancel error and report it exactly. After a finish error, do not invoke
cancel or reuse that session; resolve the reported cause and restart with start. Stop for unresolved
tracker conflicts or monorepo layout choices before finish. Do not repair script-owned state, choose
per-file coverage, change the request, pass unrequested paths to finish, or manually remove the
session.

## Review Gate

- [ ] Read each complete generated Rule and Skill; confirm it follows its authoring contract and
      uses current target evidence.
- [ ] Read all three Matt documents; confirm they match confirmed tracker, label, and domain-layout
      decisions and preserve existing user-owned content.
- [ ] Confirm `AGENTS.md` will contain one `## Agent skills` block pointing to all three documents.
- [ ] Read the completed models file; confirm every requested Agent/platform has a non-empty model.
- [ ] Confirm the request is unchanged and `GENERATED` contains exactly the eight requested target
      paths with no undeclared directories.
- [ ] Confirm no requested target is ignored by Git and no generated project file contains a
      credential or secret.

## Acceptance Gate

- [ ] Run finish once; accept setup only when its JSON reports `phase: finish` and `check: clean`.

## Validation and Result

Report the fields returned by finish: pinned source commit, enabled platforms, changed paths,
external Skills, preserved project-owned paths, and check status. Tell the repository maintainer to
review and commit the reported changed paths; other developers obtain the shared snapshot by clone
or pull and do not run setup individually. Session files, caches, logs, and credentials remain
outside the repository. On failure, report the exact script error; do not infer a successful or
partially successful setup without a clean finish result.
