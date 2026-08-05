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
> SmartKit `SessionStart` Hook, then start a new Codex session or run `/clear`. Until it is trusted,
> Codex skips SmartKit's recommended-tool check. Review it again only when an update changes the
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

## Platform support

All three hosts support Windows and Linux. Setup gives every generated Agent an explicit model;
host-specific fields remain native to that host.

| Host | Windows recommended-tool Hook | Linux recommended-tool Hook | Native Agent fields |
| --- | --- | --- | --- |
| Codex | PowerShell | POSIX sh | `model_reasoning_effort`, `sandbox_mode` |
| Cursor | Polyglot dispatcher to PowerShell | Polyglot dispatcher to POSIX sh | `readonly` |
| GitHub Copilot | `powershell` handler | `bash` handler | `disable-model-invocation` |

## Set up each project

In the target repository, ask the Agent to use `setup-project-agents` to initialize the project.
Setup always configures Codex, Cursor, and Copilot.

Setup writes the rules, skills, and Agent configuration required by the project into the repository.
Run `setup-project-agents` again when you want to adopt a new version of the setup-managed snapshot.

SmartKit manages only the content it generates and preserves the project's existing files and user
configuration whenever possible. All changes can be viewed and reviewed through version control.

## Hooks, multi-agent, and tool maintenance

The plugin automatically checks recommended tools and required capabilities, such as Superpowers,
CodeGraph, Tokscale, and multi-agent support. These checks only detect issues; they never install
tools or change related configuration by themselves.

When missing or outdated tools are detected, SmartKit first lists the affected items and asks the
user. It runs maintenance actions only after explicit consent. If the user explicitly declines the
listed actions, SmartKit skips them without asking again and the original task continues. Items that
cannot be handled automatically include manual instructions. Cursor blocks affected prompts in
interactive sessions and uses the same ask-and-stop requirement as session context in headless
`--print` sessions.

## Typical workflow

```text
Install SmartKit → complete host Hook review (Codex: /hooks) → run setup-project-agents in the
project → review generated content → start working
```

If a check reports that tools need to be installed or upgraded, confirm the tool names and actions
before deciding whether to grant permission.
