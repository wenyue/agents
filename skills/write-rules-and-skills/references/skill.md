# Skill

A Skill owns one complete triggered job. For an Ordinary Artifact, this reference applies to the
candidate itself. For a Generation Contract, it defines the semantics the guidance must establish
for the future target.

## Establish the job

Resolve the actor, trigger, inputs, preconditions, start, actions, outcome, owner, boundaries,
completion, stop, failure, recovery, validation, resources, and handoff from accepted intent,
active Skill mechanics, and governing evidence. Every applicable field needs one supported value;
omit a field only when evidence proves that it cannot change execution.

For a Generation Contract, require the guidance to identify the evidence that selects every
applicable target field and to stop when the evidence still permits materially different jobs,
owners, resources, commands, or exits. Do not invent target workflow merely to make the contract
appear complete.

## Resolve invocation metadata

Before the first candidate write, treat model invocation as the default and use accepted intent and
evidence to decide whether user-only invocation is warranted. Keep the two Harness representations
aligned:

- For a new Skill, continue with model invocation without surfacing a choice unless evidence shows
  that the Skill should not be discovered or invoked automatically. In that exception, proactively
  recommend user-only invocation, explain the material trade-off, and stop until the user chooses.
- For an existing Skill, preserve its supported invocation choice. Present the recommendation and
  effects, then stop until the user chooses, when evidence warrants changing that choice or the
  current representations conflict. Otherwise continue without surfacing the choice.
- Encode model invocation by omitting `disable-model-invocation`; omission of
  `policy.allow_implicit_invocation` remains its valid default. When autonomous routing or another
  Skill reaching the job is part of its contract, recommend an explicit
  `policy.allow_implicit_invocation: true` and treat omission as a difference. Encode user-only
  invocation with `disable-model-invocation: true` and `policy.allow_implicit_invocation: false`.

Maintain the Skill's `agents/openai.yaml` in the same Candidate Revision. Create it when absent,
preserve supported interface metadata when updating it, and change invocation policy only through
the resolved choice above.

## Write one complete job

- Keep the main path visible. Put each branch beside its trigger and use ordered steps only when
  order changes correctness, safety, or the result.
- Give every path one prioritized completion, stop, or failure exit. State which exit governs when
  conditions coincide; completion cannot bypass required validation, cleanup, preservation, or
  handoff.
- State recovery only for verified failures that authorize it. Preserve useful partial state and
  route missing decisions, authority, or scope to their owner.
- Use an owned script only for work that is repeated, fragile, and deterministic. Define its
  dependencies, inputs, outputs, failures, recovery, and safe representative tests.
- Reference only resources the runtime job needs and state when to read or execute them. Keep
  durable policy in a separately owned Rule.
- Use headings for job phases or real branches, numbered lists for ordered actions, and bullets for
  independent requirements.

## Review and accept Skill semantics

Semantic Review reconstructs the complete job and branch-to-exit mapping from the candidate and
evidence. Fail an implicit field, invented action, command, dependency, owner, recovery, result, or
path with no exit, multiple unprioritized exits, an unreachable exit, or premature completion.

Select only the highest-risk relevant cases:

- normal completion; and
- the non-completion paths affected by the candidate, such as a missing precondition, stop,
  failure, recovery, handoff, or coincident condition.

With `ordinary-artifact.md`, apply the common Acceptance Runner protocol to the triggered job and
task. With `generation-contract.md`, the fresh reviewer statically verifies that the guidance
obtains the required evidence and chooses one action or stop for the same input classes. Do not
start a Runner or create a target for contract Acceptance.
