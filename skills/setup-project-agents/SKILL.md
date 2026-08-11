---
name: setup-project-agents
description: Use when initializing or reconciling a repository's Rules, Skills, Agents, or MCP across Codex, Cursor, and Copilot.
---

# Setup Project Agents

Reconcile one repository's Rules, Skills, Agents, and MCP through the script-backed setup workflow.
Treat the four capability families as peers: each has its own canonical project input and native
delivery form; none is an appendix to another.

## Capability Inputs

Establish the requested project intent before `start`. Change a canonical input only when the user
requests that change.

| Capability | Canonical project input | Setup responsibility |
| --- | --- | --- |
| Rules | Project-owned sources under `.agents/rules/` and requested generated Rule targets | Preserve project Rules and deliver setup-managed Rules to each host. |
| Skills | Project-owned directories under `.agents/skills/`, requested generated Skill targets, and `.agents/config.json` `skills` declarations | Preserve project Skills and install requested generated or external Skills. |
| Agents | Project-owned sources under `.agents/agents/` and `.agents/config.json` `agents` declarations | Preserve Agent sources and render the declared host adapters. |
| MCP | `.agents/config.json` `mcp` declarations | Render the declared host-native MCP entries without storing secret values. |

Use the version 1 schema declared by `.agents/config.json`. A configured Agent source must be the
matching `.agents/agents/<id>.md` file. MCP entries declare exactly one of `url` or `command`; ordered
`when`/`set` overrides may select host platforms and operating systems.

Project-owned canonical inputs remain editable project content. Files and structured fields
produced by setup are setup-owned. Plugin Rules, Skills, Agents, and MCP are installed with
SmartKit and are outside this project workflow.

## Workflow

1. From the target repository root, inspect all four capability inputs. Apply any user-requested
   canonical-input changes before starting. This step is complete when Rules, Skills, Agents, and
   MCP each represent the accepted project intent.

2. Identify the loaded Skill directory as `SETUP_PROJECT_AGENTS_ROOT`, then start the public
   workflow:

   ```sh
   sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/setup_project_agents.sh" start \
     --target "$PWD"
   ```

   On Windows, invoke `setup_project_agents.ps1` with the same arguments. Stop on a nonzero result.
   Record the returned `session` as `SESSION` and `generated` as `GENERATED`, plus the `request` and
   `source_root` paths. This step is complete when one private session exists and the target
   repository remains unchanged by start.

3. Read the request and confirm it captured the accepted Rules, Skills, Agents, and MCP intent. If
   any captured choice is wrong, cancel the session, correct the canonical project input, and start
   again. Keep the request unchanged after start.

4. Fulfil every `generation_requests` entry under `GENERATED/<target>`, preserving the complete
   target path. Resolve each request's blueprint from `source_root` and use the matching authoring
   contract:

   - apply `write-agent-rule` to Rule targets;
   - apply `write-agent-skill` to Skill targets; and
   - read `setup-matt-pocock-skills` from `source_root` and execute its contract within this workflow
     for the requested `docs/agents/` targets; do not invoke it as a separate Skill.

   Use the current repository as evidence and preserve complete project-owned content unless the
   user requests reconfiguration. For Matt context, default an absent tracker to Local Markdown,
   preserve an existing triage mapping, and use a single domain context unless repository evidence
   establishes materially separate contexts. This step is complete when the generated directory
   contains exactly the requested targets and no undeclared path.

5. Pass the Review Gate, then finish the same session:

   ```sh
   sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/setup_project_agents.sh" finish \
     --session "$SESSION"
   ```

   On Windows, invoke `setup_project_agents.ps1`. Invoke `finish` once. Completion requires a zero
   exit and JSON containing `phase: finish` and `check: clean`.

6. If work must stop after `start` and before `finish`, cancel the session:

   ```sh
   sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/setup_project_agents.sh" cancel \
     --session "$SESSION"
   ```

   Do not cancel after `finish`; finish owns cleanup on success and failure.

## Review Gate

- [ ] Rules, Skills, Agents, and MCP all match the accepted project intent.
- [ ] Every configured Agent points to a complete matching project-owned source.
- [ ] Every generated Rule and Skill follows its authoring contract and current repository evidence.
- [ ] Matt context matches the accepted tracker, triage, and domain decisions.
- [ ] The request is unchanged and every requested target exists under the generated root.
- [ ] Generated project content contains no credential or secret.

## Stop Conditions

Stop and report the exact error when `start`, `finish`, or `cancel` fails. After a `finish` failure,
discard that session and restart after resolving the cause. Stop before `finish` when a tracker,
domain-layout, capability declaration, ownership conflict, or generated output remains unresolved.
Use only the public `start`, `finish`, and `cancel` commands; the workflow owns selection,
rendering, deletion, validation, transaction, checking, and session cleanup.

## Result

Report the finish result: pinned source commit, enabled hosts, changed paths, external Skills,
preserved project-owned paths, and clean check status. Ask the maintainer to review and commit the
reported project snapshot; other developers receive it through clone or pull.
