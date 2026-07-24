# Project Tools

Strength: `Mandatory`

Scope: Generation contract for the target repository's executable tooling, runtime services,
verification surfaces, integrations, and tool-to-skill handoffs.

## Generation Contract

Produce a complete target-owned `Project Tools` rule from current repository evidence. Include only
facts and constraints an agent must know before acting because the correct choice is non-obvious,
easy to misuse, expensive to rediscover, or costly to repair. Leave ordinary discoverable detail
with its owning configuration, script, or command help; do not create a tool inventory.

## Evidence

- Inspect package and workspace manifests, lock files, toolchain pins, repository scripts, task
  runners, CI workflows, and tool configuration.
- Confirm consequential commands from their owning script, configuration, or current help output.
  Establish the working directory, prerequisites, supported scope, mutation behavior, outputs, and
  material cost.
- Inspect runtime entry points, service configuration, environment templates, credential
  boundaries, ports, startup dependencies, and health or readiness checks.
- Inspect generator configuration and repository-owned verification or setup selectors without
  copying policy owned by generated files or project skills.
- Inspect project-owned MCP and native agent-platform configuration. Reconcile names and intent
  across supported platforms while preserving each platform's native schema.
- Treat absent, conflicting, or machine-local evidence as unresolved. Do not convert it into a
  repository-wide fact.

## Content

- Record a runtime, package-manager, workspace, toolchain, or working-directory constraint only when
  it materially changes command selection or failure behavior. Point to the owning pin or manifest
  instead of copying a value that agents can safely read there.
- Record a small verified set of canonical commands for repository-owned outcomes that agents must
  invoke directly, such as setup, development, verification, build, packaging, or publication.
  State the required working directory and any non-obvious prerequisites or selectors.
- For other commands, name the owning surface and the decision it owns. Include an exact invocation
  only when its mutations, outputs, or material cost are not safely discoverable there.
- Distinguish non-mutating checks from formatters, fixers, generators, installers, publishers, and
  other state-changing tools when confusing them would create meaningful risk or broad changes.
  Record verified scope selectors and dry-run modes for consequential state-changing tools.
- Describe a runtime service, integration, MCP server, or native agent surface only when an agent
  must connect to, preserve, or validate it and the required behavior is not obvious from live
  configuration.
- Record each consequential generator's owner and either its exact invocation or a reliable
  discovery path, together with its inputs and outputs. Do not let agents improvise generator
  arguments or substitute a broad update workflow for a narrow generation task.
- Make repository-owned setup and verification selectors directly invocable by
  `worktree-environment-setup` or `change-set-verification`. Leave workflow timing, ordering,
  broadening, and result policy to those skills.
- State that a tool or capability is absent only when doing so prevents a consequential invented
  command or workflow.

## Boundaries

- Keep environment-preparation procedure in `worktree-environment-setup` and completed-change
  verification procedure in `change-set-verification`; this rule supplies verified capabilities
  and invocation constraints to both.
- Keep API contracts, domain behavior, generated-file edit policy, and lint interpretation in
  `Project Rules`. Keep module placement and dependency direction in `Project Structure`.
- Leave platform wrapper generation and distribution metadata to their owning configuration or
  synchronization manifest.
- Do not require every recorded command to run for every task, duplicate another owner's policy,
  expose credentials, or infer commands, selectors, costs, services, or integrations that evidence
  does not prove.
