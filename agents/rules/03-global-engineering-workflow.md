# Engineering Workflow

Strength: `Mandatory`

Scope: Understanding, preparing, changing, and verifying work for engineering tasks.

## Understand

- Identify the desired outcome, constraints, and acceptance conditions, with the underlying problem
  as the target.
- When the user's request is ambiguous, ask the user to clarify before proceeding.
- For advisory or informational questions, search the web before answering and ground the response
  in current sources.
- Before editing, read the applicable instructions, relevant files, and nearby code.
- For non-trivial changes, identify the root cause, invariants, dependencies, risks, and affected
  areas.

## Change

- Choose the smallest coherent change that resolves the root cause and fits the surrounding design.
- Keep the change within the requested scope. Present the broader option and its material trade-offs
  before expanding that scope.
- Reuse established patterns and ownership boundaries. Introduce new structure only when the current
  requirement needs it.
- When a workaround is necessary, contain it and make its limitation clear.
- Remove code made obsolete by the change.

## Verify

- Verify the changed behavior with checks appropriate to the task and its risk before treating the
  work as complete.
- Cover the requested outcome, the original failure when applicable, and likely side effects.
- When verification reveals a failure, return to diagnosis and revise the judgment and solution from
  the new evidence.
- After two consecutive failed attempts at the same issue, stop repeating the approach and identify
  the blocker, evidence, and next useful action.
