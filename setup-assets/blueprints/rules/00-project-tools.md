# Project Tools

Strength: `Mandatory`

Scope: Generation contract for the target repository's safe command execution, synchronization,
mutation, complete-change verification, and existing Skill handoffs.

## Generation Frame

Produce one target-owned `.agents/rules/00-project-tools.md` as a project-local Ordinary Mandatory
Rule. Its persistent policy answers only how an agent executes repository tooling safely, which
observed source changes require synchronization, what authority permits mutation, how a complete
change set is verified, and when an existing Skill owns the job.

Derive the Rule's applicability, predicate-to-outcome mappings, exceptions, precedence, and
ownership boundaries from current target evidence. Preserve supported existing semantics and write
only the target Rule unless the accepted request explicitly authorizes another target change. Stop
before writing when mutation authority, the comparison point, preserved behavior, or absent,
conflicting, or machine-local evidence still permits materially different repository-wide outcomes.

## Evidence-to-Policy Mappings

- Inspect repository entry guidance, workspace and package manifests, runtime and toolchain pins,
  repository scripts, task-runner configuration, CI workflows, and command help. State a required
  working directory or runtime prerequisite only when that evidence shows it changes whether a
  supported invocation succeeds, and point to its live owner instead of caching a discoverable
  value or inventory.
- Trace every consequential generated or synchronized surface from its canonical source through
  the repository-owned synchronizer to its outputs and read-only drift check. For each confirmed
  source-change predicate, state the required synchronization outcome, its check-only alternative
  when one exists, and the generated diffs that must be reviewed. Reference the owning command
  surface; include an exact invocation only when agents cannot reliably derive it there.
- Inspect scripts and current help to distinguish read-only from mutating behavior and establish
  selectors, safer modes, affected paths, and failures.
  Co-locate each consequential mutation with the explicit project or user authority that permits
  it, the read-only, scoped, or dry-run outcome required without that authority, and the resulting
  changes to inspect. Tool presence, write access, or a broad task description does not grant
  authority.
- Establish the actual change set from its declared comparison point together with version-control
  status and diff, untracked paths, generated effects, and implicated loading, generation,
  ownership, delivery, or runtime surfaces. Map every path and affected surface to applicable
  non-fixing checks from project guidance, verification selectors, CI, test and build configuration,
  and synchronizer checks. Name every uncovered path or surface and withhold a complete-verification
  claim while one remains uncovered or a required check has not passed.
- Inspect discoverable project Skills and their invocation pointers. Name an existing Skill and its
  observable trigger only when its accepted trigger and bounded outcome own the job. Keep persistent
  invocation constraints and the handoff condition in the Rule; leave procedure, ordering,
  recovery, and result handling in the Skill.

Choose the target Rule's organization from its supported predicates and outcomes rather than from
this contract's headings. Omit tool inventories, environment snapshots, command catalogs,
step-by-step procedures, and behavior already owned by live configuration, command help, scripts,
or Skills.

## Ownership Boundaries

- Keep hard API, generated-source, capability ownership, delivery, installation, dependency, and
  contract-evolution policy in `Project Contracts`. Reference that owner when it determines which
  execution or synchronization outcome applies.
- Keep advisory directory placement, responsibility maps, and architectural seam judgment in
  `Project Structure`; this Rule may name their enforcement command without restating their policy.
- Keep deterministic mechanics in their repository-owned scripts.

## Validation and Handoff

Validate every included mapping and exact command against authoritative target evidence, then hand
the generated Rule to the current Ordinary Artifact route. Hand off its evidence and unresolved
omissions; an uncovered path or surface prevents a complete-verification claim.
