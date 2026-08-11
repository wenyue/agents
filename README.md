# WenYue SmartKit

`WenYue SmartKit` is a cross-platform plugin for Codex, Cursor, and GitHub Copilot. It provides
Rules, Skills, Agents, and MCP as peer capabilities, then checks whether recommended tools and
configured MCP prerequisites are available when a session starts.

## Install the plugin

Install `smartkit` once in each host you use.

Codex:

```sh
codex plugin marketplace add wenyue/agents
codex plugin add smartkit@wenyue
```

You can also use `/plugins` in Codex to install it.

> **Required Codex Hook review:** Installing or enabling SmartKit does not automatically trust its
> bundled Hook. After installation, open a Codex CLI session, run `/hooks`, review and trust the
> SmartKit Hooks, then start a new Codex session or run `/clear`. Until they are trusted,
> Codex skips SmartKit's recommended-tool check and Rule delivery. Review again only when an update changes a
> Hook definition and Codex marks it for review.

Cursor: install it through the Plugin Marketplace or `/add-plugin`; import private versions through
a team marketplace or as a local plugin.

GitHub Copilot CLI:

```sh
copilot plugin marketplace add wenyue/agents
copilot plugin install smartkit@wenyue
```

To update the Copilot plugin, run `copilot plugin marketplace update wenyue`, followed by
`copilot plugin update smartkit`.

## Plugin Rules, Skills, Agents, and MCP

| Capability | What SmartKit provides |
| --- | --- |
| Rules | Always-on and file-scoped instructions. Strength wins first (`Mandatory` > `Default` > `Advisory`), followed by project ownership and narrower file scope. |
| Skills | SmartKit workflows plus reviewed, licensed, version-pinned third-party workflows. |
| Agents | `change-set-verifier` on all three hosts. It uses the project's change-set-verification Skill, reports `inconclusive` when setup has not installed that Skill, and inherits the host-selected model. |
| MCP | Playwright in isolated headless mode on all three hosts, subject to normal host approval. |

Codex and Copilot CLI receive Rules through Hooks; Cursor uses native plugin Rules. Inspect the
host's Hook diagnostics when an expected Rule is absent. Copilot cloud agents are outside this
plugin-Rule contract.

## Platform support

All three hosts support Windows and Linux.

| Host | Rules | Skills | Agents | MCP |
| --- | --- | --- | --- | --- |
| Codex | Session, prompt, and structured-tool Hooks | Plugin Skill catalog | `change-set-verifier` | Playwright |
| Cursor | Native plugin Rules | Plugin Skill catalog | `change-set-verifier` | Playwright |
| GitHub Copilot CLI | Session, transformed-prompt, and structured-tool Hooks | Plugin Skill catalog | `change-set-verifier` | Playwright |

## Set up each project

In the target repository, ask the Agent to use `setup-project-agents` to initialize the project.
Setup always configures Codex, Cursor, and Copilot and also creates the Matt repository context in
`docs/agents/issue-tracker.md`, `docs/agents/triage-labels.md`, and `docs/agents/domain.md`.

New projects default to a Local Markdown issue tracker under `.scratch/`, regardless of their Git
remote. Setup preserves a complete existing tracker configuration. Ask explicitly for GitHub,
GitLab, or another tracker when that project should publish work remotely.

One maintainer runs setup for a new repository, reviews the result, and commits the managed project
snapshot. Other developers receive it through clone or pull and do not run setup individually. Run
`setup-project-agents` again only when the project adopts a newer setup-managed snapshot contract.

| Capability | Project configuration |
| --- | --- |
| Rules | Keep project-owned sources under `.agents/rules/`; setup preserves them and installs requested generated Rules. |
| Skills | Keep project-owned Skills under `.agents/skills/`, or declare GitHub `source`, optional `ref`, and non-empty `include` entries in `.agents/config.json` `skills`. |
| Agents | Keep canonical sources under `.agents/agents/` and declare matching `id`, `source`, `description`, and host `platforms` in `.agents/config.json` `agents`; edit these inputs rather than generated adapters. |
| MCP | Declare each server in `.agents/config.json` `mcp` with a stable ID and exactly one of `url` or `command`; environment variables are referenced by name, never stored as secret values. |

Setup preserves unmanaged host configuration and stops before writes when a setup-managed entry
conflicts or was modified locally.

### MCP overrides

Each override has a `when` selector and a `set` object. Omit `when.platforms` to match every host
enabled for the server, or omit `when.operatingSystems` to match every supported operating system
(`windows` and `linux`). When both are present, both must match. Matching rules apply in array order,
and a later rule wins only for fields it declares:

```json
{
  "id": "inspector",
  "command": "python3",
  "overrides": [
    {
      "when": {"operatingSystems": ["windows"]},
      "set": {"command": "py"}
    },
    {
      "when": {"platforms": ["cursor", "copilot"]},
      "set": {"cwd": "tools/inspector"}
    }
  ]
}
```

SmartKit manages only the content it generates and preserves the project's existing files and user
configuration whenever possible. Commit `AGENTS.md`, `.agents/`, managed host wrappers and config,
and `docs/agents/`; do not add them to `.gitignore`. Session data, caches, logs, and credentials stay
outside the repository, and generated project files must not contain secrets.

## Hooks, multi-agent, MCP readiness, and tool maintenance

The plugin runs one automatic readiness pipeline per canonical project, active host, and local
calendar day. Its first step is the daily gate; policy changes do not bypass it, while an explicit
`--force` run does. The current checks are:

- recommended-tool installation and version, including CodeGraph and Tokscale;
- required effective values, including Codex multi-agent support;
- Plugin MCP static prerequisites, currently Node 18 or newer and `npx` for Playwright;
- Project MCP inferred prerequisites: bare-command availability, an executable workspace-relative
  command path, and declared environment-variable names.

These checks never install tools, mutate MCP configuration, start an MCP server, probe a network or
application port, trigger OAuth, or require a live debug session. Project HTTP MCP declarations
therefore produce no connectivity check.

When missing or outdated tools are detected, SmartKit first lists the affected items and asks the
user. It runs maintenance actions only after explicit consent. If the user explicitly declines the
listed actions, SmartKit skips them without asking again and the original task continues. Items that
cannot be handled automatically include manual instructions. Cursor blocks affected prompts in
interactive sessions and uses the same ask-and-stop requirement as session context in headless
`--print` sessions.

## Typical workflow

```text
Install or update SmartKit → start a new host session → complete host Hook review (Codex: /hooks)
→ a maintainer runs setup-project-agents → review and commit the generated snapshot → other
developers pull → start working
```

If a check reports that tools need to be installed or upgraded, confirm the tool names and actions
before deciding whether to grant permission.
