---
name: refactor-code
description: Use when refactoring, restructuring, cleaning up, simplifying, or rewriting existing code, including readability improvements, internal logic replacement, legacy removal, and deliberate public-interface simplification.
---

# Refactor Code

Choose the smallest refactor mode that can achieve the requested outcome. Preserve project rules
and observable contracts unless the selected mode and the user explicitly allow changing them.

## Select the Mode

| Mode | Use when | Contract changes |
| --- | --- | --- |
| Format | Improving names, readability, local structure, duplication, or control flow | None |
| Logic | Replacing internal logic or state flow while preserving the external contract | Private implementation only |
| Deep | Simplifying public interfaces, persistence, protocols, or user-visible behavior | Allowed only after explicit confirmation |

Infer the mode when the request uniquely identifies it. Ask only when two modes would produce
materially different scope or behavior.

## Shared Workflow

1. Read the applicable repository rules, target code, nearby patterns, and affected callers.
2. State the selected mode, behavior boundary, and concrete design problem.
3. Identify existing tests or observable examples that protect the preserved contract.
4. Make the smallest coherent refactor within the selected mode.
5. Remove code made obsolete by the new structure when it is inside the approved scope and no
   supported path depends on it.
6. Run the minimum relevant formatter, static checks, and tests before reporting completion.

Do not introduce frameworks, configuration layers, test-only APIs, or extension points for
hypothetical future needs.

## Format Refactor

- Preserve logic, public interfaces, persistence formats, state semantics, and user-visible
  behavior.
- Improve names, ordering, branching, duplication, and helper boundaries only where they address
  the stated readability problem.
- Do not expand a local cleanup into caller or module restructuring without a concrete need.
- Do not extract tiny helpers merely to reduce line count.

## Logic Refactor

- Preserve public interfaces, external contracts, persistence formats, and observable behavior.
- Define the target responsibilities, data flow, state ownership, error handling, and caller
  interaction before replacing internals.
- Protect complex or risky boundary behavior with tests before the rewrite.
- Replace obsolete internal branches and adapters instead of wrapping the old implementation in a
  second architecture.
- Update tests that depended on retired internals so they assert the preserved external behavior.

## Deep Refactor

Before editing an external surface:

1. List the public APIs, cross-module contracts, persistence shapes, protocols, integrations, or
   user-visible behavior that would change.
2. Explain the benefit, impact, compatibility cost, migration options, and narrower alternatives.
3. Obtain explicit confirmation for the breaking scope and compatibility policy.

After confirmation, update callers, tests, migrations, and documented contracts together. Remove
the old surface and compatibility paths the user agreed to retire; do not keep dormant legacy
entry points.

## Stop Conditions

- Stop when the requested result requires a deeper mode than the one approved.
- Stop before an unapproved public, persistence, protocol, or user-visible change.
- Treat an unclear compatibility requirement as a decision point, not permission to preserve or
  break everything by default.

## Result

Report the selected mode, the problem removed, any deliberate contract change, files affected, and
the exact verification performed.
