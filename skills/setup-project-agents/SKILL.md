---
name: setup-project-agents
description: Use when initializing or updating a repository from the wenyue/agents public catalog.
---

# Setup Project Agents

Let the synchronization script maintain deterministic configuration. Use the LLM to choose
subagent models and generate the five repository-specific assets declared by this workflow.

Start from the active Skill supplied by the installed plugin. A previously installed project-local
copy remains a supported legacy entry point when that is the Skill the host loaded.

Template-owned project configuration gives every developer the same repository defaults. The
script applies a partial deep merge: template fields overwrite drift, fields absent from a template
remain untouched, and normal synchronization automatically repairs missing or outdated managed
values. User configuration remains outside this workflow.

## Ownership

- The script owns deterministic configuration for every supported platform.
- Literal templates own project configuration values and native startup-hook entries; Python
  contains only generic reconciliation logic.
- The public manifest owns bundle-required third-party Skill declarations.
- The public manifest owns the catalog identity and version recorded in `.agents/config.json`.
- The target repository owns optional third-party Skill declarations in `.agents/config.json`; the
  script owns fetching and reconciling every public and project declaration.
- The LLM owns model selection and repository-specific Rule and Skill generation.
- `manage-agent-tools` owns interactive tool diagnosis and user-approved installation or upgrade;
  project startup hooks only report drift and never mutate tools.
- Each startup hook checks the current platform's recommended tools and policy-declared effective
  runtime values once per project per local date. It evaluates declared detector output instead of
  parsing raw project or user configuration. On findings, the agent stops the current task and asks
  whether to use `manage-agent-tools`; any next user reply may continue.

## Remote Bootstrap Security Boundary

The remote `main` bootstrap accepts an external `--session` path. It safely creates missing session
path components without following symlinks, then always requires the final `SESSION` to be owned by
the current effective user with exact mode `0700`; bootstrap never blindly trusts the supplied path.
Normal orchestration must create its session with `tempfile.mkdtemp` (or an equivalent
system-temporary secure creator) before passing it to bootstrap. Bootstrap creates a random 128-bit
candidate directory, writes and validates through a held directory descriptor, and publishes it to
`SESSION/source` with no-replace rename. Failed pre-publication candidates remain for session-end
cleanup; bootstrap never removes or renames the current `SESSION/source` pathname after publication.

This protects against pathname races from other users who cannot write the private session. A process
running as the same user that actively alters the session, traces the bootstrap, or injects code into
it is already within the trusted execution boundary and is not defended by the filesystem protocol.

## Managed Assets

Generate these Rules from their public blueprints:

- [`20-project-tools.md`](https://github.com/wenyue/agents/blob/master/agents/blueprints/rules/20-project-tools.md)
- [`21-project-rules.md`](https://github.com/wenyue/agents/blob/master/agents/blueprints/rules/21-project-rules.md)
- [`22-project-structure.md`](https://github.com/wenyue/agents/blob/master/agents/blueprints/rules/22-project-structure.md)

Generate these Skills from their public blueprints:

- [`worktree-environment-setup`](https://github.com/wenyue/agents/blob/master/agents/blueprints/skills/worktree-environment-setup/SKILL.md)
- [`change-set-verification`](https://github.com/wenyue/agents/blob/master/agents/blueprints/skills/change-set-verification/SKILL.md)

## Project External Skills

Public bundle external Skills are installed automatically. A repository may declare only additional
project-selected Skills in `.agents/config.json`; do not repeat public bundle declarations:

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

Each public or project declaration owns the complete `.agents/skills/<name>/` directory.
Synchronization replaces that directory from the selected GitHub repository, ref, and path,
including overwriting local changes and removing files deleted upstream. Removing a project
declaration does not delete an installed directory.

The script downloads and validates every public and project source before writing public or external
assets. If a source fails and the target has no valid installed copy, synchronization stops without
applying changes. If a valid copy is already installed, the script keeps it, continues the remaining
synchronization, and reports a warning; `--check` reports the same warning and exits with status 1.

## Reconciliation Workflow

1. From the target repository root, resolve the directory containing the active
   `setup-project-agents` `SKILL.md` as `SETUP_PROJECT_AGENTS_ROOT`. Derive it from the Skill file the
   host loaded; do not assume a repository-local `.agents/` path or persist a machine-specific path.
   On POSIX run its `scripts/sync_public_agent_assets.sh` entry point; on Windows run
   `scripts/sync_public_agent_assets.ps1`. Resolve one model-config path in the system temporary
   directory and retain it for both stages:

   ```sh
   MODEL_CONFIG="$(python -c 'import os, tempfile; print(os.path.join(tempfile.gettempdir(), "setup-project-agent-models.json"))')"
   sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/sync_public_agent_assets.sh" \
     --model-request "$MODEL_CONFIG"
   ```

   The entry point uses the installed plugin or repository catalog containing the active Skill. A
   project-local legacy copy fetches its pinned catalog source. It synchronizes every
   catalog-declared platform and writes the model request.

2. Fill every model field in `$MODEL_CONFIG`. Use each subagent's `required_intelligence` to select
   `model` for Codex, Cursor, and GitHub, plus `model_reasoning_effort` for Codex. Existing wrappers
   are not a value source.

3. Open and execute each public blueprint enumerated under Managed Assets. Generate Rules
   at `.agents/rules/<name>.md` and Skills at `.agents/skills/<name>/`. Apply `write-rule` when
   generating each Rule and `write-skill` when generating each Skill. Use current repository
   evidence; previous content may be used as a reference during generation, but it is not a source
   of truth. Each blueprint owns its generation and validation.

4. Apply the completed model configuration after all generated files exist:

   ```sh
   sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/sync_public_agent_assets.sh" \
     --model-config "$MODEL_CONFIG"
   ```

   This same synchronization creates or updates the native Codex, Cursor, and Copilot project
   configuration and hook files from readable templates. Let synchronization own those managed
   fields, including the recorded catalog version, while preserving user-level configuration and
   template-external project fields.

## Review Gate

- [ ] Review every generated Rule and Skill against its public blueprint.
- [ ] Confirm unrelated target-owned files remain unchanged.

## Acceptance Gate

- [ ] Confirm every enumerated Rule and Skill is complete.
- [ ] Confirm every required model field is resolved.
- [ ] Confirm template-owned project configuration is reconciled.
- [ ] Confirm `.agents/config.json` records the installed catalog identity and version.

## Validation

Run the final check with the same temporary model configuration. The script checks that every
enumerated output exists and that deterministic configuration has no drift, including templates
and native hook registrations; each blueprint owns content validation. `--check` reports
drift without writing.

```sh
sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/sync_public_agent_assets.sh" \
  --check --model-config "$MODEL_CONFIG"
```

Stop on any synchronization or blueprint failure. Startup project-health checks and their internal
failures do not block validation. Perform validation without invoking a real model.

## Output

Report the changed managed files and any unresolved model or blueprint blocker.
