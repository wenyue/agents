---
name: setup-project-agents
description: Use when initializing or updating a repository with the Agents Rules, Skills, Agents, and explicitly enabled Hooks snapshot.
---

# Setup Project Agents

Create or update one target repository's managed Agent snapshot from the current canonical `main`.
This shared operational skill owns the setup session and project reconciliation workflow; it never
installs itself into the target, edits host trust or plugin caches, or upgrades external tools.

## Preconditions

- Start at the target repository root and identify the loaded Skill directory as
  `SETUP_PROJECT_AGENTS_ROOT`.
- Ask once which platforms to enable and whether to enable Hooks. When
  `.agents/config.json` is absent, default to Codex, Cursor, and Copilot with Hooks disabled.
  When it exists, use its selected platforms, asset selections, and Hook choice unless the user
  changes them.
- Keep the selected platforms and Hook decision unchanged for this one session. Hooks require an
  explicit enabled choice; multi-agent capability is checked from effective host state and is not
  written as a replacement default.

## Workflow

1. Create one private system-temporary session using `tempfile.mkdtemp`; on POSIX confirm it is
   current-user-owned with exact mode `0700`. Keep this `SESSION` until validation is complete.
   Do not create the session inside the target repository:

   ```sh
   SESSION="$(python3 -c 'import tempfile; print(tempfile.mkdtemp(prefix="setup-project-agents-"))')"
   ```

2. Invoke the platform wrapper in `SETUP_PROJECT_AGENTS_ROOT/scripts/` with `prepare`, `--target`,
   `--session`, each selected `--platform`, and `--hooks enabled|disabled`. The wrapper only starts
   `bootstrap.py`. Bootstrap fetches canonical `main`, pins one commit under `SESSION/source`, and
   hands control to that pinned source. If the remote is unavailable it reports the installed-source
   fallback; if fetched content is invalid, stop before any target write. For example on POSIX:

   ```sh
   sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/setup_project_agents.sh" prepare \
     --target "$PWD" --session "$SESSION" \
     --platform codex --platform cursor --platform copilot --hooks disabled
   ```

   On Windows, invoke `setup_project_agents.ps1` with the same arguments.

3. Read `SESSION/request.json`. It is the authority for this session's normalized target, source
   root and commit, platform and Hook choices, selected assets, model requests, and five generated
   outputs. Write one JSON-object `SESSION/models.json` that satisfies every listed agent/platform
   request at its requested `model_key`: Codex and Cursor use `codex` and `cursor`, while Copilot
   uses `github`. Each platform object needs a non-empty `model`; Codex optional
   `model_reasoning_effort` and `sandbox_mode` are strings when present, and Cursor optional
   `readonly` is Boolean when present. Do not use a models file outside `SESSION` or change the
   request after preparation.

   ```json
   {
     "agents": {
       "change-set-verifier": {
         "codex": {"model": "codex-model"},
         "cursor": {"model": "cursor-model"},
         "github": {"model": "copilot-model"}
       }
     }
   }
   ```

4. Generate every request output in `SESSION/generated`, not in the target project. Use `write-rule`
   for the three requested Rule Blueprints and `write-skill` for the two requested Skill Blueprints.
   Produce exactly these paths and no extra files:

   - `.agents/rules/20-project-tools.md`
   - `.agents/rules/21-project-rules.md`
   - `.agents/rules/22-project-structure.md`
   - `.agents/skills/change-set-verification/SKILL.md`
   - `.agents/skills/worktree-environment-setup/SKILL.md`

5. Read the source root and commit from `request.json`; use `offline` as the CLI commit argument
   when its recorded commit is `null`. Run the pinned
   `skills/setup-project-agents/scripts/setup_project_agents.py apply` with the same target,
   session, `SESSION/models.json`, source root, source commit, and `--no-bootstrap`. Apply validates
   the session request, generated tree, rendered state, and ownership plan before its single project
   transaction:

   ```sh
   python3 "$SOURCE_ROOT/skills/setup-project-agents/scripts/setup_project_agents.py" apply \
     --target "$TARGET" --session "$SESSION" --models "$SESSION/models.json" \
     --source-root "$SOURCE_ROOT" --source-commit "$SOURCE_COMMIT" --no-bootstrap
   ```

6. Run the same pinned entry point with `check` and the identical arguments, replacing only `apply`
   with `check`. Apply and check each write exactly one JSON result to stdout with the phase, pinned
   source commit, sorted changed paths, per-platform capability state, candidate refresh commands,
   and `needs_restart`. A zero check status means the project is unchanged; status one reports drift
   without writing. Read this result before reporting the pinned source commit and managed paths.

7. Present candidate refresh commands or an official UI action from the JSON result. Do not execute
   a candidate command during setup; execute it only after the user separately approves it. Report a
   host `needs_restart` or Cursor Hook-trust requirement separately; neither is part of the
   project-file transaction.

8. Delete `SESSION` only after apply and check have completed or after reporting a failure.

## Stop Conditions

Stop without project writes when the session is not private, `request.json` does not match the
invocation, `models.json` is not `SESSION/models.json`, generated outputs are incomplete or contain
an extra path, the pinned source is invalid, or the ownership planner finds unmanaged drift.

Do not use an archive fallback, a project-local setup copy, a host trust database, or a plugin cache
as an alternative path. Use `manage-agent-tools` only for a separately approved external-tool
diagnosis or upgrade.

## Validation and Result

- [ ] Confirm `check` used the same `SESSION`, source root, source commit, models file, renderer, and planner as `apply`; confirm exit status is zero.
- [ ] Confirm `.agents/lock.json` records the pinned source commit and only lock-owned paths or fields changed.
- [ ] Confirm setup-project-agents is absent from the target snapshot; confirm Hooks are present only when explicitly enabled.

Report the pinned source commit, selected platforms, Hook choice, changed managed paths, capability
or trust follow-up, and any unresolved failure. Do not report successful setup when validation was
not run.
