# WenYue SmartKit

`WenYue SmartKit` is a cross-platform plugin for Codex, Cursor, and GitHub Copilot. It helps projects
standardize Agent rules, commonly used skills, and collaboration workflows, and checks whether
recommended tools are available when a session starts.

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

## Plugin Skills and Rules

`skills/registry.json` explicitly declares SmartKit-owned Skills and GitHub-hosted external Skills.
Maintainers update all external sources with `python scripts/update_external_skills.py --update`,
or one source with `--source owner/repository`; `--check` is read-only. Omitted refs follow the
repository default branch, while a branch, tag, or commit may be selected explicitly. Updates use
ambient Git credentials, validate licenses, and transactionally replace the aggregate lock and
snapshots.

`rules/registry.json` orders plugin Rules. `always` Rules load for every task; `file` Rules activate
for matching project-relative Git-style globs. Strength wins first (`Mandatory` > `Default` >
`Advisory`), then project ownership, then narrower file scope. Codex and Copilot CLI use Hooks;
Cursor uses native plugin Rules. Hook delivery remembers activated file Rules for the session,
restores them after compaction, and gates the first matching structured write when a Rule was not
discovered earlier. Hook dispatch writes an attempted-delivery diagnostic with the response size;
the host remains authoritative for trust, acceptance, spill, and truncation, so inspect its Hook
diagnostics when expected behavior is absent. Cursor adapter generation fails instead of publishing
a file scope the native glob format cannot represent. Copilot cloud agents are outside this
plugin-Rule contract.

## Platform support

All three hosts support Windows and Linux. Setup gives every generated Agent an explicit model;
host-specific fields remain native to that host.

| Host | Plugin Rule delivery | Recommended-tool Hook | Native Agent fields |
| --- | --- | --- | --- |
| Codex | Session, prompt, and structured-tool Hooks | PowerShell / POSIX sh | `model_reasoning_effort`, `sandbox_mode` |
| Cursor | Native plugin Rules | Polyglot dispatcher | `readonly` |
| GitHub Copilot CLI | Session, transformed-prompt, and structured-tool Hooks | `powershell` / `bash` | `disable-model-invocation` |

## Set up each project

In the target repository, ask the Agent to use `setup-project-agents` to initialize the project.
Setup always configures Codex, Cursor, and Copilot and also creates the Matt repository context in
`docs/agents/issue-tracker.md`, `docs/agents/triage-labels.md`, and `docs/agents/domain.md`.

One maintainer runs setup for a new repository, reviews the result, and commits the managed project
snapshot. Other developers receive it through clone or pull and do not run setup individually. Run
`setup-project-agents` again only when the project adopts a newer setup-managed snapshot contract.

Projects may declare GitHub Skill sources in `.agents/config.json` under
`skills.external_sources`. Setup fetches each source URL once, snapshots its selected Skills, and
writes `.agents/external-skills.lock.json`. Generated project Rules use `00–09`; module Rules use
`10–19`, domain Rules use `20–29`, and package or project-plugin Rules use `30–39`.

SmartKit manages only the content it generates and preserves the project's existing files and user
configuration whenever possible. Commit `AGENTS.md`, `.agents/`, managed host wrappers and config,
and `docs/agents/`; do not add them to `.gitignore`. Session data, caches, logs, and credentials stay
outside the repository, and generated project files must not contain secrets.

## Hooks, multi-agent, and tool maintenance

The plugin automatically checks recommended tools and required capabilities, such as CodeGraph,
Tokscale, and multi-agent support. These checks only detect issues; they never install tools or
change related configuration by themselves.

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
