# WenYue SmartKit

`WenYue SmartKit` is a cross-platform plugin for Codex, Cursor, and GitHub Copilot. Installing it
exposes only the `setup-project-agents` control plane and plugin-owned dependency-check Hooks. Shared
Rules, Skills, and agent prompts become available only after setup installs a managed snapshot into
the target repository.

## Install the plugin

Install `smartkit` once in each host you use.

Codex:

```sh
codex plugin marketplace add wenyue/agents
codex plugin add smartkit@wenyue
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
copilot plugin install smartkit@wenyue
```

To refresh a Copilot marketplace and plugin, use its native update flow, for example
`copilot plugin marketplace update wenyue` followed by `copilot plugin update smartkit`.
Confirm names with `copilot plugin list` when your marketplace differs.

## Set up each project

In every target repository, explicitly ask the installed plugin to use `setup-project-agents`.
Choose the target hosts; the default is Codex, Cursor, and Copilot. Plugin installation alone never
changes a project's tracked files.

Each setup session fetches the plugin's remote `main`, validates it, and pins one fetched commit for
the complete prepare, apply, and check sequence. Run setup again when you want a project to adopt
the current `main`. The setup control plane itself stays in the plugin and is never copied into a
target project.

The resulting snapshot owns only its lock-recorded files and configuration fields. It preserves a
target project's other files and user-owned `.agents/config.json` choices.

## Hooks, multi-agent, and tool maintenance

Hooks belong to the plugin and are declared through each host's plugin format. A host discovers them
when it installs or loads the plugin; `setup-project-agents` never writes project Hook definitions or
Hook-enable fields. Host-level trust, workspace trust, and global Hook controls remain authoritative.
The bundled SessionStart Hook runs the recommended-tool doctor for tools and required host
capabilities, including multi-agent support. It never treats Hook execution as consent and never
changes tools by itself.

When tools need installation or upgrade, the Hook asks the agent to name the affected tools and
request consent without showing the underlying commands. After consent, the plugin-private
allowlisted runner applies each supported native action; unsupported actions return official manual
guidance. This maintenance workflow remains plugin-private and is never copied into project
snapshots.

## Repository layout

```text
skills/                         Plugin-visible control plane; only setup-project-agents
hooks/                          Plugin-owned lifecycle Hook definitions
runtime/recommended-tools/      Private Hook executables; never a discoverable Skill
policies/recommended-tools/     Shared recommended-tool policies
setup-assets/catalog/           Asset, configuration, and lock contracts
setup-assets/rules/             Rules installed into target repositories
setup-assets/skills/            Skill documents installed into target repositories
setup-assets/agents/            Agent prompts installed into target repositories
setup-assets/blueprints/        Contracts for target-owned Rules and Skills
setup-assets/templates/         Host configuration and wrapper templates
docs/zh-CN/                     Simplified-Chinese documentation
.agents/rules/                  This repository's own development rules
.agents/skills/                 Thin local wrappers for write-rule and write-skill
.agents/plugins/                This repository's local plugin marketplace configuration
```

Plugin manifests expose only `skills/` and the host Hook entry points. They do not expose
`runtime/`, `policies/`, or `setup-assets/`. `docs/zh-CN/` is documentation only and is never loaded
or installed.
