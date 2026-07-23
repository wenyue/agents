---
name: setup-project-agents
description: Use when initializing or updating a repository from the wenyue/agents public catalog.
---

# Setup Project Agents

Let the synchronization script maintain deterministic configuration. Use the LLM to choose
subagent models and generate the five repository-specific assets declared by this workflow.

Template-owned project configuration gives every developer the same repository defaults. The
script applies a partial deep merge: template fields overwrite drift, fields absent from a template
remain untouched, and normal synchronization automatically repairs missing or outdated managed
values. It never reads or modifies user configuration.

## Ownership

- The script owns deterministic configuration for every supported platform.
- Literal templates own project configuration values and native startup-hook entries; Python
  contains only generic reconciliation logic.
- The target repository owns third-party Skill declarations in `.agents/config.json`; the script
  owns fetching and reconciling each declared Skill.
- The LLM owns model selection and repository-specific Rule and Skill generation.
- Each startup hook checks only the current platform's recommended tools once per day without
  reading project or user configuration. On findings, the agent stops the current task and asks
  whether to install; any next user reply may continue.

## Managed Assets

Generate these Rules from their public blueprints:

- [`20-project-tools.md`](https://github.com/wenyue/agents/blob/master/agents/blueprints/rules/20-project-tools.md)
- [`21-project-rules.md`](https://github.com/wenyue/agents/blob/master/agents/blueprints/rules/21-project-rules.md)
- [`22-project-structure.md`](https://github.com/wenyue/agents/blob/master/agents/blueprints/rules/22-project-structure.md)

Generate these Skills from their public blueprints:

- [`worktree-environment-setup`](https://github.com/wenyue/agents/blob/master/agents/blueprints/skills/worktree-environment-setup/SKILL.md)
- [`change-set-verification`](https://github.com/wenyue/agents/blob/master/agents/blueprints/skills/change-set-verification/SKILL.md)

## Project External Skills

A repository may declare third-party Skills in `.agents/config.json`:

```json
{
  "version": 1,
  "skills": {
    "external": [
      {
        "name": "example-skill",
        "repository": "owner/repository",
        "ref": "main",
        "path": "skills/example-skill"
      }
    ]
  }
}
```

Each declaration owns the complete `.agents/skills/<name>/` directory. Synchronization replaces
that directory from the selected GitHub repository, ref, and path, including overwriting local
changes and removing files deleted upstream. Removing a declaration does not delete an installed
directory.

The script downloads and validates every declared source before writing public or external assets.
If a source fails and the target has no valid installed copy, synchronization stops without applying
changes. If a valid copy is already installed, the script keeps it, continues the remaining
synchronization, and reports a warning; `--check` reports the same warning and exits with status 1.

## Reconciliation Workflow

1. From the target repository root, resolve one model-config path in the system temporary directory
   and retain it for the complete workflow:

   ```sh
   MODEL_CONFIG="$(python -c 'import os, tempfile; print(os.path.join(tempfile.gettempdir(), "setup-project-agent-models.json"))')"
   python .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py \
     --model-request "$MODEL_CONFIG"
   ```

   The script fetches
   `https://github.com/wenyue/agents/archive/refs/heads/master.zip`, synchronizes every
   catalog-declared platform, preflights the project external Skills, and writes the model request.

2. Fill every model field in `$MODEL_CONFIG`. Use each subagent's `required_intelligence` to select
   `model` for Codex, Cursor, and GitHub, plus `model_reasoning_effort` for Codex. Existing wrappers
   are not a value source.

3. Open and execute each public blueprint enumerated under Managed Assets. Generate Rules
   at `.agents/rules/<name>.md` and Skills at `.agents/skills/<name>/`. Use current repository
   evidence; previous content may be used as a reference during generation, but it is not a source
   of truth. Each blueprint owns its generation and validation.

4. Apply the completed model configuration after all generated files exist:

   ```sh
   python .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py \
     --model-config "$MODEL_CONFIG"
   ```

   This same synchronization creates or updates the native Codex, Cursor, and Copilot project
   configuration and hook files from readable templates. Do not separately edit user-level
   configuration or remove template-external project fields.

5. When you need immediate setup feedback, run an uncached recommended-tool check only for the
   current execution platform:

   ```sh
   python .agents/skills/setup-project-agents/scripts/check_recommended_tools.py check --platform PLATFORM
   ```

   Replace `PLATFORM` with `codex`, `cursor`, or `copilot`. The native startup hook checks
   automatically. On findings, ask whether to install and wait for a reply. If the user chooses to
   install, run `check_recommended_tools.py hook --platform PLATFORM --force` afterward. Any other
   reply may continue the current task.

## Review Gate

Accept only generated assets that satisfy their public blueprint and preserve unrelated
target-owned files.

## Acceptance Gate

Every enumerated Rule and Skill must be complete, every required model field must be resolved, and
template-owned project configuration must be reconciled.

## Validation

Run the final check with the same temporary model configuration. The script checks that every
enumerated output exists and that deterministic configuration has no drift, including templates
and native hook registrations; each blueprint owns content validation. `--check` reports
drift without writing.

```sh
python .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py \
  --check --model-config "$MODEL_CONFIG"
```

Stop on any synchronization or blueprint failure. Recommended-tool checks and their internal
failures do not block validation. Do not invoke a real model for validation.

## Output

Report the changed managed files and any unresolved model or blueprint blocker.
