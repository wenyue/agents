# Plugin Rule Configuration

Strength: `Mandatory`

Scope: Rule strength, precedence, ownership, activation, semantic conflicts, and project numbering.

## Strength Levels

- `Mandatory`: Follow unless a higher-priority instruction overrides it.
- `Default`: Follow unless a direct higher-priority instruction or a Rule ranked higher by the
  precedence tuple requires a different outcome.
- `Advisory`: Adapt to the task context when useful.

## Precedence

After direct system, developer, and user instructions, resolve Rule conflicts by this tuple:

1. Strength: `Mandatory` > `Default` > `Advisory`.
2. Owner at equal strength: project > plugin.
3. Specificity at equal strength and owner: narrower applicable file scope > broader applicable
   file scope > the global tier. `always` and `harness` Rules share the global tier; a Harness
   selector changes activation, not precedence.
4. Registry order defines deterministic plugin delivery order; project file order defines
   deterministic project delivery order. Neither order resolves a semantic conflict.

Do not let a lower-strength project Rule override a higher-strength plugin Rule.

## Activation

- `always` Rules apply throughout every supported Harness lifecycle.
- `file` Rules activate from matching paths and remain active for the session according to the
  owning delivery adapter.
- `harness` Rules activate only during a matching Harness's session-context lifecycle. Do not
  generate native Rule wrappers for another Harness from them.
- Register a `harness` Rule only when that Harness has a real session-context delivery route;
  native-wrapper generation does not count as that route.

## Semantic Conflicts

- Do not attempt to infer semantic conflicts in configuration code.
- Apply the precedence tuple before declaring a conflict. Requirements are incompatible when no
  single action or outcome can satisfy both under the same supported facts.
- When incompatible requirements remain tied at the same strength, owner, and specificity, perform
  only the read-only investigation needed to establish the conflict, then stop before any side
  effect. Do not use delivery order as an implicit winner.
- Report the conflicting Rule IDs, sources, strengths, scopes, and the incompatible requirements,
  and ask the user to resolve the conflict.

## Rule Ownership

- Keep each plugin Rule's policy in exactly one source registered by `rules/registry.json`.
- Keep each project Rule's policy in exactly one source under `.agents/rules/`.
- Keep Harness-specific rule wrappers thin: they may contain required Harness metadata or runtime
  fields plus one reference to the owning rule; keep all policy in that owning rule.
- Let the owning Harness configuration or catalog define wrapper paths, templates, and generation
  behavior, and leave those runtime facts there.
- A Harness-scoped Rule may map shared actions to one Harness's native tools, capabilities,
  lifecycle semantics, constraints, and missing-capability fallbacks. Keep it plugin-private and
  mechanics-only; it must not redefine shared policy, user authorization, or completion criteria.

## Numbering

| Range | Scope |
| --- | --- |
| `00–09` | Project rules: tooling, conventions, structure, and utilities. |
| `10–19` | Module rules: features, screens, and bounded subsystems. |
| `20–29` | Domain rules: testing and other cross-cutting concerns. |
| `30–39` | Package and project-plugin rules. |

Plugin Rules use descriptive `core-*` and `file-*` IDs instead of numeric names. Project Rules use
the numeric ranges above and follow this plugin-owned precedence contract.
