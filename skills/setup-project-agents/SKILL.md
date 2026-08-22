---
name: setup-project-agents
description: Use when initializing or reconciling a repository's Rules, Skills, Agents, or MCP across Codex, Cursor, and Copilot.
---

# Setup Project Agents

This Hybrid Skill reconciles one repository's Rules, Skills, Agents, and MCP. The Agent decides the
accepted capability intent; the public workflow owns deterministic discovery, rendering,
validation, transaction, and cleanup.

## Judgment Frame

Treat the four capability families as peers. Before `start`, inspect their canonical inputs and
change one only when the user requests that change.

| Capability | Canonical project input | Setup responsibility |
| --- | --- | --- |
| Rules | Project-owned sources under `.agents/rules/` and requested generated Rule targets | Preserve project Rules and deliver setup-managed Rules to each host. |
| Skills | Project-owned directories under `.agents/skills/`, requested generated Skill targets, and `.agents/config.json` `skills` declarations | Preserve project Skills and install requested generated or external Skills. |
| Agents | Project-owned sources under `.agents/agents/` and `.agents/config.json` `agents` declarations | Preserve Agent sources, render the declared host adapters, and install catalog-declared Codex Plugin Agent defaults. |
| MCP | `.agents/config.json` `mcp` declarations | Render the declared host-native MCP entries without storing secret values. |

Use the shipped `.agents/config.json` schema. A configured Agent source is its matching
`.agents/agents/<id>.md`; each MCP entry declares exactly one of `url` or `command`. Ordered
`when`/`set` overrides may select Harnesses and Platforms, and optional MCP readiness may scope or
replace inferred static checks.

Project-owned canonical inputs remain editable project content. Files and structured fields
produced by setup are setup-owned. Plugin Rules, Skills, MCP, and native Cursor and Copilot Plugin
Agents stay outside this project workflow. Setup installs only catalog-declared Codex Plugin Agent
defaults as managed assets; they never become Project Agent declarations.

Matt repository context is a separate project-owned prerequisite. This workflow neither generates
nor owns `docs/agents/issue-tracker.md`, `docs/agents/triage-labels.md`,
`docs/agents/domain.md`, or the `## Agent skills` block that points to them.

## Transactional Workflow

1. From the target repository root, verify that Matt repository setup is complete: the three
   `docs/agents/` context files exist and either `AGENTS.md` or `CLAUDE.md` contains the matching
   `## Agent skills` block. If any part is missing, stop before `start` and tell the user to
   explicitly invoke `setup-matt-pocock-skills` in this repository. Do not reproduce that Skill's
   questions or choose an issue tracker on its behalf. Resume by invoking `setup-project-agents`
   again only after Matt setup reports completion.

2. Establish that Rules, Skills, Agents, and MCP each represent the accepted project intent.

3. Identify the loaded Skill directory as `SETUP_PROJECT_AGENTS_ROOT`, then start the public
   workflow:

   ```sh
   sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/setup_project_agents.sh" start \
     --target "$PWD"
   ```

   On Windows, invoke `setup_project_agents.ps1` with the same arguments. Stop on a nonzero result.
   Record the returned `session` as `SESSION`, `generated` as `GENERATED`, and the `request` and
   `source_root` paths. Continue only when one private session exists and the target remains
   unchanged.

4. Read the request and confirm it captured the accepted Rules, Skills, Agents, and MCP intent. If
   any captured choice is wrong, cancel the session, correct the canonical project input, and start
   again. Keep the request unchanged after start.

5. Fulfil every `generation_requests` entry under `GENERATED/<target>`, preserving the complete
   target path. Resolve each request's blueprint from `source_root` and use the matching authoring
   contract:

   - apply the Rule branch of `write-rules-and-skills` to Rule targets; and
   - apply the Skill branch of `write-rules-and-skills` to Skill targets.

   The request contains exactly five generated targets:

   - `.agents/rules/00-project-tools.md`
   - `.agents/rules/01-project-contracts.md`
   - `.agents/rules/02-project-structure.md`
   - `.agents/skills/change-set-verification/SKILL.md`
   - `.agents/skills/worktree-environment-setup/SKILL.md`

   Matt context is never a generation request.

   Use current repository evidence and preserve complete project-owned content unless the user
   requests reconfiguration. Continue only when `GENERATED` contains exactly the requested targets
   and no undeclared path.

6. Pass the Review Gate, then finish the same session exactly once:

   ```sh
   sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/setup_project_agents.sh" finish \
     --session "$SESSION"
   ```

   On Windows, invoke `setup_project_agents.ps1`. Completion requires a zero exit and JSON containing
   `phase: finish` and `check: clean`.

7. If work must stop after `start` and before `finish`, cancel the session:

   ```sh
   sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/setup_project_agents.sh" cancel \
     --session "$SESSION"
   ```

   Do not cancel after `finish`; finish owns cleanup on success and failure.

## Review Gate

- [ ] Rules, Skills, Agents, and MCP all match the accepted project intent.
- [ ] Matt repository setup completed before `start` and remains project-owned.
- [ ] Every configured Agent points to a complete matching project-owned source.
- [ ] Every generated Rule and Skill follows its authoring contract and current repository evidence.
- [ ] The request is unchanged and every requested target exists under the generated root.
- [ ] Generated project content contains no credential or secret.

## Stop and Recovery

Stop and report the exact error when `start`, `finish`, or `cancel` fails. After a `finish` failure,
discard that session and restart after resolving the cause. Stop before `finish` when a capability
declaration, ownership conflict, or generated output remains unresolved.
Use only `start`, `finish`, and `cancel`; their implementation owns selection, rendering, deletion,
validation, transaction, checking, and session cleanup.

## Result

Report the finish result: pinned source commit, enabled hosts, changed paths, external Skills,
preserved project-owned paths, and clean check status. Ask the maintainer to review and commit the
reported project snapshot; other developers receive it through clone or pull.
