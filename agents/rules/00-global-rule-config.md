# Rule Configuration

Strength: `Mandatory`

Scope: Rule strength, precedence, source ownership, wrapper boundaries, numbering, and discovery
order.

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

## Rule Ownership

- Keep each project rule's policy in exactly one source under `.agents/rules/`.
- Keep platform-specific rule wrappers thin: they may contain required platform metadata or runtime
  fields plus one reference to the owning rule, but must not duplicate its policy.
- Let the owning platform configuration or catalog define wrapper paths, templates, and generation
  behavior. Do not encode those runtime facts in this rule.

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
