# Plugin Rule Configuration

Strength: `Mandatory`

Scope: Rule strength, precedence, ownership, activation, semantic conflicts, and project numbering.

## Strength Levels

- `Mandatory`: Follow unless a higher-priority instruction overrides it.
- `Default`: Follow unless the task or a more specific rule gives good reason to differ.
- `Advisory`: Adapt to the task context when useful.

## Precedence

After direct system, developer, and user instructions, resolve Rule conflicts by this tuple:

1. Strength: `Mandatory` > `Default` > `Advisory`.
2. Owner at equal strength: project > plugin.
3. Specificity at equal strength and owner: narrower file scope > broader file scope > always.
4. Registry order defines deterministic plugin delivery order; project file order defines
   deterministic project delivery order. Neither order resolves a semantic conflict.

Do not let a lower-strength project Rule override a higher-strength plugin Rule.

## Semantic Conflicts

- Do not attempt to infer semantic conflicts in configuration code.
- When applicable Rules require incompatible behavior, perform only the read-only investigation
  needed to establish the conflict, then stop before any side effect.
- Treat incompatible Rules at the same strength, owner, and specificity as a conflict; do not use
  delivery order as an implicit winner.
- Report the conflicting Rule IDs, sources, strengths, scopes, and the incompatible requirements,
  and ask the user to resolve the conflict.

## Rule Ownership

- Keep each plugin Rule's policy in exactly one source registered by `rules/registry.json`.
- Keep each project Rule's policy in exactly one source under `.agents/rules/`.
- Keep platform-specific rule wrappers thin: they may contain required platform metadata or runtime
  fields plus one reference to the owning rule; keep all policy in that owning rule.
- Let the owning platform configuration or catalog define wrapper paths, templates, and generation
  behavior, and leave those runtime facts there.

## Numbering

| Range | Scope |
| --- | --- |
| `00–09` | Project rules: tooling, conventions, structure, and utilities. |
| `10–19` | Module rules: features, screens, and bounded subsystems. |
| `20–29` | Domain rules: testing and other cross-cutting concerns. |
| `30–39` | Package and project-plugin rules. |

Plugin Rules use descriptive `core-*` and `file-*` IDs instead of numeric names. Project Rules use
the numeric ranges above and follow this plugin-owned precedence contract.
