# Project Contracts

Strength: `Mandatory`

Scope: Generation contract for the persistent conditions that make a target repository change
valid across capability ownership, installation, documentation, evaluation, contract evolution,
distribution, and hard dependency or exposure boundaries.

## Generation Contract

Produce target-owned `.agents/rules/01-project-contracts.md` titled `Project Contracts` as a
project-local Ordinary Mandatory Rule answering: what persistent conditions must remain true for a
project change to be valid?

Derive the target's scope and applicability, observable predicate-to-outcome mappings, exceptions,
precedence, and ownership boundaries from current repository evidence. Include only supported
policy clusters and choose one activation cohort that covers the included validity conditions.
Organize the target around its own evidence rather than copying this contract's headings or order.

Preserve every supported semantic obligation in an existing target unless accepted intent and
authoritative current evidence select its change or retirement. Stop before target writes when the
activation cohort, applicability, required outcome, exception, precedence, or preservation boundary
still permits materially different policies.

## Conditional Evidence and Selection

Read the existing target Rule, its discovery entry, narrower project Rules, accepted specifications,
and tests that exercise the claimed contract. Treat an existing statement as evidence to preserve
or challenge, not as an outline. For each supported cluster, state the activating facts, observable
outcome, exact exceptions, precedence, and decision owner. Resolve conflicts in favor of the
narrowest authoritative current owner, reference narrower policy when needed, and preserve its
precedence instead of duplicating or silently overriding it. Absent, conflicting, historical, or
machine-local evidence does not establish project policy.

- Trace public APIs, routes, schemas, events, serialization, domain models, persistence and
  migration behavior, state owners, lifecycle transitions, cancellation, concurrency, and cleanup.
  Include a condition only when this evidence shows that a consumer, state, compatibility, or
  cleanup boundary determines whether the change remains valid.
- Trace each capability from its canonical registry or source through synchronizers, renderers,
  adapters, manifests, catalogs, and delivery surfaces. When evidence selects one authoritative
  source and constrains edits or delivery, distinguish source authority from transformation,
  adapter, and transport responsibility in the required outcome.
- Inspect target setup state, ownership manifests, deterministic digests, structured-field
  composition, adoption and conflict handling, and removal planning. When setup claims or mutates
  target content, define its claim, preservation, conflict, replacement, and retirement outcomes
  from that ownership evidence.
- Compare public documentation boundaries, canonical-language sources, translations, runtime
  loading, and delivery configuration. Include policy only when evidence distinguishes public from
  contributor-facing material, canonical from derived languages, or documentation from runtime or
  delivery inputs, and state the required boundary or derivation outcome.
- Inspect evaluators, fixtures, schemas, behavioral tests, accepted Standards, task specifications,
  and verdict invalidation behavior. Include evaluation policy when structure and natural-language
  semantics require different proof or governing evidence determines which prior verdicts remain
  valid; state the proof boundary and invalidation outcome.
- Trace retirement across implementation, documentation, tests, validation, persisted state, and
  callers. Include current-contract policy when removal must remain coherent across those owners,
  and identify any compatibility or recovery behavior that evidence retains as current correctness.
- Inspect imports, call paths, loaders, package and plugin manifests, visibility controls, and
  generated distribution paths. Include one-way distribution and hard dependency or exposure
  policy when violating a verified direction, visibility boundary, or public/private surface makes
  the change invalid, and state the required direction or exposure outcome.

## Boundaries

- Keep command discovery, setup mechanics, synchronization, mutation, testing, and verification
  procedure in their owning tools and Skills. This Rule may constrain their valid outcomes but does
  not prescribe their execution workflow.
- Leave file, directory, command, configuration, schema, registry, and inventory facts with the
  environment when an agent can reliably discover them. Record the persistent relationship or
  decision boundary instead of caching those facts.
- Keep advisory placement, responsibility maps, and architectural heuristics in `Project
  Structure`; put hard dependency, distribution, and exposure conditions in this Rule.

## Validation and Handoff

Validate every included mapping against its authoritative evidence, including the nearest included
and excluded cases, ownership boundaries, Rule conflicts, packaging, discovery, and affected
project-owned machine surfaces. Hand off the target through the current Ordinary Rule route with a
report of preserved obligations, approved changes, evidence-backed omissions, and unresolved
surfaces.
