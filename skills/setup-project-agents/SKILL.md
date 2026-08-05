---
name: setup-project-agents
description: Use when initializing or updating a repository with the Agents Rules, Skills, and Agents snapshot.
---

# Setup Project Agents

Run the script-backed setup workflow for one target repository. The workflow always enables Codex,
Cursor, and Copilot. The agent chooses any models that the target does not already define, authors
the requested project-specific content, reviews it, and consumes the structured result; the scripts
own every deterministic setup operation.

## Ownership

Do not reconstruct source selection, discovery, overwrite, deletion, validation, transaction,
checking, summary, or cleanup behavior. Invoke the public workflow and treat its result as
authoritative. Host trust, plugin caches, bundled Hooks, and external-tool installation are outside
this workflow.

## Managed Assets

The agent may edit only these workflow inputs:

- any requested model values the user explicitly changes and empty values that remain in the
  reported `models.json`;
- the three Rule and two Skill targets listed by `generation_requests` under the reported
  `generated` directory.

Do not edit `request.json` or create another models or generated root.

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
   generated, and source paths.

2. Read `SESSION/request.json` and the reported `models.json`. Start preserves model settings from
   existing platform Agent configurations. Keep every prefilled value unless the user explicitly
   changes it, and fill each remaining empty required `model` at the requested agent and
   `model_key`. Codex optional `model_reasoning_effort` and `sandbox_mode` values are strings;
   Cursor optional `readonly` is Boolean.

3. Resolve the reported `source_root` as `SOURCE_ROOT`. Read the complete authoring contracts at
   `SOURCE_ROOT/setup-assets/skills/write-rule/SKILL.md` and
   `SOURCE_ROOT/setup-assets/skills/write-skill/SKILL.md`. Apply the listed Blueprints and write
   exactly the five `generation_requests` targets under the reported generated directory.

4. After the Review Gate passes, invoke the same wrapper with `finish` and only the session path:

   ```sh
   sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/setup_project_agents.sh" finish \
     --session "$SESSION"
   ```

   Do not invoke the internal prepare/apply/check commands directly.

5. If the workflow cannot reach finish after a successful start, invoke `cancel` with only
   `--session "$SESSION"`.

## Stop Conditions

Stop on any start, finish, or cancel error and report it exactly. Do not repair script-owned state,
choose per-file coverage, change the request, pass unrequested paths to finish, or manually remove
the session; restart with start after resolving the reported cause.

## Review Gate

- [ ] Read each complete generated Rule and Skill; confirm it follows its authoring contract and
      uses current target evidence.
- [ ] Read the completed models file; confirm every requested agent/platform has a non-empty model.
- [ ] Confirm the request is unchanged and the generated directory contains exactly the five
      requested files.

## Acceptance Gate

- [ ] Run finish once; accept setup only when its JSON reports `phase: finish` and `check: clean`.

## Validation and Result

Report the fields returned by finish: pinned source commit, enabled platforms, changed paths,
external Skills, preserved project-owned paths, and check status. On failure, report the exact
script error; do not infer a successful or partially successful setup without a clean finish result.
