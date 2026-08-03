# wenyue/agents

Shared runtime assets live under `agents/rules/`, `agents/skills/`, and `agents/agents/`. Generative
Rule and Skill blueprints live under `agents/blueprints/`. Runtime assets are installed into target
repositories under `.agents/`, while blueprints guide creation of target-owned `.agents/` content;
this repository keeps a curated local runtime configuration in `.agents/` rather than mirroring the
public catalog.

## Install the Plugin

Install `agents` once for the host you use.

Codex:

```sh
codex plugin marketplace add wenyue/agents
codex plugin add agents@wenyue-agents
```

Cursor: add `https://github.com/wenyue/agents` as a plugin source, then install `agents`.

GitHub Copilot CLI:

```sh
copilot plugin marketplace add wenyue/agents
copilot plugin install agents@wenyue-agents
```

Installing the plugin only makes its Skills available; it does not modify repositories. Open each
target repository and ask the installed plugin to use `setup-project-agents`. Run that Skill again
whenever you want to synchronize the repository with the installed catalog version.

## Review Project Hooks

`setup-project-agents` installs a project-health `sessionStart` Hook for each supported host. The
Hook checks recommended tools and effective runtime requirements at most once per project per day;
it reports drift but never installs, upgrades, or trusts tools. Review the command using the host's
normal trust flow before allowing it to run.

| Agent | Project Hook | Required user action |
| --- | --- | --- |
| Codex | `.codex/hooks.json` | Start `codex`, enter `/hooks`, inspect the project Hook, and trust its exact definition. |
| Cursor | `.cursor/hooks.json` | Open the repository as a trusted workspace and inspect the Hook under `Cursor Settings > Hooks`. |
| GitHub Copilot | `.github/hooks/*.json` | Start `copilot` in the repository and accept the prompt to trust the current directory. |

Hook support is enabled explicitly for all three hosts. Multi-agent support is not force-enabled by
project configuration; the health check validates each host's effective default state and reports
when it has been disabled.

## Boundaries

- Edit the public catalog under `agents/`; treat `.agents/` as this repository's curated local
  runtime configuration.
- Keep project-specific facts in the target repository, not here.
- Do not locally adapt public rules or public skills for one project.
- Use skillshare only for third-party skills that should remain independently upgradable:

```bash
skillshare update --all -p
skillshare sync -p
```
