# Rule Configuration

Strength: `Mandatory`

Scope: Rule strength, precedence, source-of-truth ownership, wrapper maintenance, numbering, and
MCP configuration.

## Strength Levels

- `Mandatory`: Follow unless a higher-priority instruction overrides it.
- `Default`: Follow unless the task or a more specific rule gives good reason to differ.
- `Advisory`: Adapt to the task context when useful.

## Precedence

Resolve conflicts in this order:

1. Direct system, developer, and user instructions override repository rules.
2. More specific rules, including narrower globs or scopes, override more general rules.
3. Among rules with equal specificity, `Mandatory` overrides `Default`, which overrides `Advisory`.
4. Enforced constraints, such as mandatory project rules or lints, override advisory guidance.

## Sources Of Truth

Keep one source of truth for each asset. Platform-specific files are thin wrappers that reference
the source.

| Asset | Source of truth |
| --- | --- |
| Project rules | `.agents/rules/<nn>-<name>.md` |
| Agent prompts | `.agents/agents/<name>.md` |
| Project skills | `.agents/skills/<skill>/SKILL.md` |
| Third-party skills | `.skillshare/skills/<skill>/SKILL.md` |
| Copilot guidance | `.github/instructions/*.instructions.md` |

- Use repository-root-relative paths in tracked configuration; do not use absolute filesystem paths.
- When content appears in more than one wrapper, move it to the source and reduce the wrappers.
- A thin wrapper contains only platform metadata or runtime fields plus one source reference.

## Wrapper Maintenance

Rule wrappers use these locations:

- Cursor: `.cursor/rules/<same-name>.mdc`
- Copilot: `.github/instructions/<same-name>.instructions.md`

Use this body for both rule wrapper types:

```text
Apply @.agents/rules/<nn>-<name>.md
```

When adding a rule:

1. Author the source in `.agents/rules/<nn>-<name>.md`.
2. Add Cursor and Copilot wrappers for each platform that loads it.
3. Update `AGENTS.md` when the rule changes applicable paths or workflows.

When adding a subagent:

1. Author the shared prompt in `.agents/agents/<name>.md`.
2. Add thin Cursor, Codex, and Copilot wrappers for platforms that expose it.
3. Keep repository-wide Copilot guidance in `.github/instructions/*.instructions.md`; do not
   duplicate it in subagent prompts.

## Numbering

| Range | Scope |
| --- | --- |
| `00–09` | Global rules: strength, personality, response format, and skills. |
| `10–19` | Base rules: languages and shared defaults. |
| `20–29` | Project rules: tooling, conventions, structure, and utilities. |
| `30–39` | Module rules: features, screens, and bounded subsystems. |
| `40–49` | Domain rules: testing and other cross-cutting concerns. |
| `50–59` | Plugin, third-party plugin, and package-specific rules. |

Finish reading all applicable `00–09` global rules before deciding which later rules apply.

## MCP Configuration

Keep server names and intent consistent across platforms. Put project-specific server names, ports,
binaries, and service dependencies in the project tooling rule or the owning configuration. Prefer
relative or command-based configuration over machine-specific paths.

| Platform | File | Notes |
| --- | --- | --- |
| Cursor | `.cursor/mcp.json` | Shared intent. |
| Codex | `.codex/config.toml` | Runtime MCP entries. |
| Copilot CLI | `.vscode/mcp.json` | Top-level key is `servers`. |
