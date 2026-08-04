---
name: setup-project-agents
description: Use when initializing or updating a repository with the Agents Rules, Skills, and Agents snapshot.
---

# Setup Project Agents

Create or update one target repository's managed Agent snapshot from the current canonical `main`.
This shared operational skill owns the setup session and project reconciliation workflow; it never
installs itself into the target, edits host trust or plugin caches, or upgrades external tools.

## Preconditions

- Start at the target repository root and identify the loaded Skill directory as
  `SETUP_PROJECT_AGENTS_ROOT`.
- Ask once which platforms to enable. When `.agents/config.json` is absent, default to Codex,
  Cursor, and Copilot. When it exists, use its selected platforms and asset selections unless the
  user changes them.
- Keep the selected platforms unchanged for this one session. Plugin-bundled Hooks, host
  capabilities, and external-tool maintenance are outside the project transaction.

## Workflow

1. Create one private system-temporary session using `tempfile.mkdtemp`; on POSIX confirm it is
   current-user-owned with exact mode `0700`. Keep this `SESSION` until validation is complete.
   Do not create the session inside the target repository:

   ```sh
   SESSION="$(python3 -c 'import tempfile; print(tempfile.mkdtemp(prefix="setup-project-agents-"))')"
   ```

2. Invoke the platform wrapper in `SETUP_PROJECT_AGENTS_ROOT/scripts/` with `prepare`, `--target`,
   `--session`, and each selected `--platform`. The wrapper only starts
   `bootstrap.py`. Bootstrap fetches canonical `main`, pins one commit under `SESSION/source`, and
   hands control to that pinned source. If the remote is unavailable it reports the installed-source
   fallback; if fetched content is invalid, stop before any target write. For example on POSIX:

   ```sh
   sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/setup_project_agents.sh" prepare \
     --target "$PWD" --session "$SESSION" \
     --platform codex --platform cursor --platform copilot
   ```

   On Windows, invoke `setup_project_agents.ps1` with the same arguments.

3. Read `SESSION/request.json`. It is the authority for this session's normalized target, source
   root and commit, platform choices, selected assets, model requests, and five generated
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

4. Resolve the `source_root` recorded in `request.json` as `SOURCE_ROOT`, then read the complete
   authoring contracts from
   `SOURCE_ROOT/setup-assets/skills/write-rule/SKILL.md` and
   `SOURCE_ROOT/setup-assets/skills/write-skill/SKILL.md`. Apply the first contract to the three
   requested Rule Blueprints and the second contract to the two requested Skill Blueprints. Generate
   every request output in `SESSION/generated`, not in the target project, and produce exactly these
   paths with no extra files:

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
   source commit, sorted changed paths, and `drift`. A zero check status has `drift: null`; status
   one reports a stable drift kind, message, and safely parsed path (and field when applicable)
   without writing. Read this result before reporting the pinned source commit and managed paths.

7. Delete `SESSION` only after apply and check have completed or after reporting a failure.

## Stop Conditions

Stop without project writes when the session is not private, `request.json` does not match the
invocation, `models.json` is not `SESSION/models.json`, generated outputs are incomplete or contain
an extra path, the pinned source is invalid, or the ownership planner finds unmanaged drift.

Do not use an archive fallback, a project-local setup copy, a host trust database, or a plugin cache
as an alternative path. Plugin Hooks own host capability and external-tool maintenance follow-up.

## Validation and Result

- [ ] Confirm generation, `apply`, and `check` used the same `SESSION`, source root, source commit, models file, renderer, and planner; confirm check exit status is zero.
- [ ] Confirm `.agents/lock.json` records the pinned source commit and only lock-owned paths or fields changed.
- [ ] Confirm setup-project-agents and host Hook definitions are absent from the target snapshot.

Report the pinned source commit, selected platforms, changed managed paths, and any unresolved
failure. Do not report successful setup when validation was not run.
