# Template-Driven Project Agent Setup Design

## Objective

`setup-project-agents` gives every developer the same repository-level agent defaults without
requiring them to understand or maintain native Codex, Cursor, or GitHub Copilot configuration.
All managed configuration is expressed as readable templates. The sync engine contains only
generic template reconciliation logic and no platform configuration values.

Startup hooks have one narrower responsibility: once per day and per platform, verify that the
recommended platform tools exist and are newer than the configured target versions. Hooks never
inspect or modify user configuration and never block the agent.

## Ownership Boundaries

The setup workflow owns these repository assets:

- public rules, skills, agent definitions, and wrappers;
- project-native configuration fields declared by configuration templates;
- platform-native startup-hook registrations;
- declarative recommended-tool policies and version thresholds.

The setup workflow does not inspect, compare, or modify user-level configuration. It does not
classify any repository field as personal, remove template-external fields, or provide a separate
configuration repair command. Normal synchronization is the repair mechanism for template-owned
project settings.

## Template-Driven Configuration

The public manifest maps a target path to a literal template and format. It contains no individual
configuration values:

```json
{
  "path": ".codex/config.toml",
  "template": "project-config/codex.config.toml",
  "format": "toml",
  "merge": "deep-overwrite"
}
```

Templates live under `agents/skills/setup-project-agents/assets/templates/project-config/` and are
valid native TOML, JSON/JSONC, or plain text. They are the only source of managed values, so a
reviewer can understand the team baseline by reading the templates without reading Python.

The generic reconciliation contract is:

- recursively merge objects and tables;
- overwrite scalar leaves declared by the template;
- replace arrays declared by the template as complete values;
- preserve every target field absent from the template;
- create a missing target file from the template;
- validate the merged native format before atomic replacement;
- leave malformed existing files byte-identical and report an error;
- make `--check` report drift without writing;
- make normal setup reconcile drift automatically and idempotently.

The engine accepts target path, template path, format, merge strategy, and optional declarative
conditions from the manifest. It has no Codex-, Cursor-, Copilot-, MCP-, model-, approval-, sandbox-,
or token-setting constants. Platform-specific reference validation may be declared as a generic
validation rule in the manifest; it must not inject configuration values.

## Platform Baselines

### Codex

The Codex project template is a balanced team baseline:

```toml
model = "gpt-5.6"
model_reasoning_effort = "medium"
plan_mode_reasoning_effort = "medium"
model_verbosity = "low"

approval_policy = "on-request"
approvals_reviewer = "auto_review"
sandbox_mode = "workspace-write"

model_auto_compact_token_limit = 64000
tool_output_token_limit = 12000

[features]
multi_agent = true
hooks = true

[agents]
max_threads = 2
max_depth = 1
interrupt_message = false
```

The cost controls deliberately avoid high reasoning by default, compact long sessions before they
grow without bound, cap retained tool output, limit concurrent subagents, prevent recursive
delegation beyond direct children, and avoid injecting interruption messages into model context.
Runtime flags and trusted-project rules retain their normal higher precedence.

### GitHub Copilot

The repository template uses only settings documented for
`.github/copilot/settings.json`:

```json
{
  "model": "gpt-5.4",
  "effortLevel": "medium",
  "contextTier": "default",
  "extraKnownMarketplaces": {
    "superpowers-marketplace": {
      "source": {
        "source": "github",
        "repo": "obra/superpowers-marketplace"
      }
    }
  },
  "enabledPlugins": {
    "superpowers@superpowers-marketplace": true
  }
}
```

The setup workflow also continues to manage supported repository MCP and hook files through their
own literal templates. It does not write repository keys that Copilot documents as user-only, such
as subagent concurrency settings.

### Cursor

Cursor templates manage only officially documented project-scoped surfaces: `.cursor/cli.json`
permissions, `.cursor/mcp.json`, project rules, agents, skills, and hooks. Project-level model,
reasoning-effort, and Max Mode defaults are not written because Cursor does not publish a stable
repository configuration contract for them. Model and spend enforcement for Cursor remains an
organization-admin concern rather than an undocumented repository-file convention.

This is a capability mapping, not a promise that every platform accepts identical keys. Each
template expresses the strongest equivalent team baseline the platform officially supports.

## Recommended-Tool Policy Templates

Tool policies live under `assets/templates/recommended-tools/`, with one readable policy per
platform. A policy declares each tool's:

- stable identifier and display name;
- applicability to the platform;
- detection method and bounded command arguments or manifest paths;
- version extraction expression and version scheme;
- strict comparison operator `>`;
- concrete target version;
- installation and upgrade guidance.

The initial policies cover the invoking platform CLI, Superpowers, and CodeGraph when CodeGraph has
a supported integration for that platform. Initial exclusive thresholds are:

| Tool | Target version | Installed versions that pass |
| --- | --- | --- |
| Codex CLI | `0.144.0` | `> 0.144.0` |
| Cursor Agent CLI | `2026.01.27` | `> 2026.01.27` |
| GitHub Copilot CLI | `1.0.58` | `> 1.0.58` |
| Superpowers | `6.0.0` | `> 6.0.0` |
| CodeGraph | `1.4.0` | `> 1.4.0` |

These values are data, not Python constants. Updating a target requires only a policy-template
change. The detector supports semantic numeric versions and Cursor's calendar-prefixed version; it
ignores build metadata when ordering. Missing, unparseable, equal, and lower versions produce
distinct actionable warnings. An equal version fails because the required comparison is strictly
greater than the target.

Superpowers detection first uses the platform's plugin inventory when it exposes version data, then
falls back to the installed platform plugin manifest. CodeGraph detection checks both the executable
version and the relevant platform integration. A tool that is not applicable to a platform is not
reported as missing.

## Cross-Project Daily Hook

Codex, Cursor, and Copilot startup events invoke the same shared checker through native hook
adapters. The checker never checks project configuration or user configuration. It only evaluates
the recommended-tool policy for the invoking platform.

The full check runs once per local calendar day for each user and platform across all repositories.
The state key therefore contains the platform, local date, and policy/checker fingerprint, but no
project path. A Codex run does not suppress Cursor or Copilot, while two Codex sessions in different
repositories share the same daily result.

State is stored under the platform-appropriate user cache directory. An atomic state file and
stale-safe exclusive lock prevent simultaneous session starts from duplicating the check. A changed
checker or policy fingerprint forces a new check on the same day. Manual `check` always runs, and
`hook --force` bypasses the daily result.

Warnings never expose complete configuration or secrets. Ordinary findings count as a completed
daily check. Internal failures do not record success, allowing a later session to retry. Cache,
lock, detection, parsing, and command failures always degrade to a warning or a skipped cache and
the native hook always exits successfully.

## Platform Hook Delivery

- Codex uses a project `SessionStart` hook.
- Cursor uses a project `sessionStart` hook.
- GitHub Copilot uses a repository `sessionStart` hook with Bash and PowerShell commands where the
  native schema supports both.

Hook definitions are themselves literal templates. Reconciliation updates only the setup-owned
hook entry or dedicated hook file and preserves unrelated hooks. A malformed shared hook file is
reported and left byte-identical rather than replaced.

## Validation and Acceptance

- Reading the templates reveals every managed configuration value and tool threshold.
- Searching the Python sync/checker code finds no platform configuration value or recommended-tool
  version constant.
- Setup creates missing project configs and deep-overwrites only template-declared fields.
- Setup preserves every template-external project field and is idempotent.
- `--check` reports the same drift without writing.
- No workflow reads or changes user configuration.
- Hooks inspect tools only, always continue, and perform one full daily check per platform across
  projects.
- Tool versions must be strictly greater than their policy target.
- Codex, Cursor, Copilot, POSIX shell, and PowerShell behaviors have isolated and end-to-end tests.
- English public Markdown changes have matching Simplified-Chinese mirrors.

## Official Capability References

- [Codex configuration reference](https://developers.openai.com/codex/config-reference)
- [GitHub Copilot CLI configuration directory](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference)
- [Cursor project permissions](https://docs.cursor.com/cli/reference/permissions)
- [Cursor models and pricing](https://docs.cursor.com/account/pricing)
