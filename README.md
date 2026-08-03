# wenyue/agents

`agents` is a cross-platform plugin for Codex, Cursor, and GitHub Copilot. It maintains shared
Rules, Skills, agent prompts, templates, and optional project Hooks. Installing the plugin makes
those capabilities available to a host; every repository is configured separately and explicitly.

## Install the plugin

Install `agents` once in each host you use.

Codex:

```sh
codex plugin marketplace add wenyue/agents
codex plugin add agents@wenyue-agents
```

You can also use `/plugins` in Codex to browse the configured marketplace. Start a new Codex
session after installation.

Cursor: use Cursor's Plugin Marketplace or `/add-plugin` flow. For an unpublished plugin, import
this repository through your team or private marketplace UI, or clone it locally for development
installation. Cursor's UI changes independently, so follow the current in-product flow rather than
an unsupported repository CLI command.

GitHub Copilot CLI:

```sh
copilot plugin marketplace add wenyue/agents
copilot plugin install agents@wenyue-agents
```

To refresh a Copilot marketplace and plugin, use its native update flow, for example
`copilot plugin marketplace update wenyue-agents` followed by `copilot plugin update agents`.
Confirm names with `copilot plugin list` when your marketplace differs.

## Set up each project

In every target repository, explicitly ask the installed plugin to use `setup-project-agents`.
Choose the target hosts and whether to enable Hooks; the default is Codex, Cursor, and Copilot with
Hooks disabled. Plugin installation alone never changes a project.

Each setup session fetches the plugin's remote `main`, validates it, and pins one fetched commit for
the complete prepare, apply, and check sequence. Run setup again when you want a project to adopt
the current `main`. The setup control plane itself stays in the plugin and is never copied into a
target project.

The resulting snapshot owns only its lock-recorded files and configuration fields. It preserves a
target project's other files and user-owned `.agents/config.json` choices.

## Hooks, multi-agent, and tool maintenance

Hooks are an explicit opt-in. When enabled, setup writes the host Hook definitions but never edits
host trust storage, workspace trust, plugin caches, or editor UI state. Review and trust each Hook
in the relevant host UI before allowing it to run. A Hook only performs project-health diagnosis;
it does not install or upgrade tools.

Multi-agent capability is checked from effective host state or the host's documented default. Setup
does not write a replacement multi-agent setting: Codex reads the effective `multi_agent` status,
while Cursor and GitHub Copilot report whether the host version supports its default capability.

Use `manage-agent-tools` separately for tool maintenance. Its `doctor` operation is read-only. An
`upgrade` is proposed one native command at a time and runs only after the user approves that exact
command; doctor runs again afterwards.

## Repository layout

```text
rules/                 Shared runtime Rules
skills/                Shared operational Skills, including setup-project-agents
agents/                Shared agent prompts
blueprints/            Contracts for target-owned Rules and Skills
catalog/               Asset and lock contracts
templates/project/     Host configuration and wrapper templates
config/                Recommended-tool policies
docs/zh-CN/             Simplified-Chinese documentation
.agents/rules/         This repository's own development rules
.agents/plugins/       This repository's local plugin marketplace configuration
```

The root runtime directories are the English plugin source of truth. `docs/zh-CN/` is documentation
only and is never loaded, installed, or synchronized into a project.
