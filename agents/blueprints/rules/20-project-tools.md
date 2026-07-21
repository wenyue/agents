# Project Tools

Strength: `Mandatory`

Scope: Generation contract for the target repository's executable tooling, runtime services,
verification surfaces, integrations, and tool-to-skill handoffs.

## Generation Contract

Produce a complete target-owned `Project Tools` rule from current repository evidence. State only
facts and constraints an agent needs to select, invoke, or preserve the repository's real tooling;
do not turn the target rule into an inventory of everything installed on one machine.

## Evidence

- Inspect package and workspace manifests, lock files, toolchain pins, repository scripts, task
  runners, CI workflows, and tool configuration.
- Confirm commands from their owning script, configuration, or current help output. Establish the
  required working directory, prerequisites, supported scope, mutation behavior, outputs, and cost.
- Inspect runtime entry points, service configuration, environment templates, credential boundaries,
  ports, data locations, startup dependencies, and health or readiness checks.
- Inspect generator configuration and repository-owned verification or setup selectors without
  copying the policy owned by generated files or project skills.
- Inspect project-owned MCP and native agent-platform configuration. Reconcile names and intent
  across supported platforms while preserving each platform's native schema.
- Treat absent, conflicting, or machine-local evidence as unresolved. Do not convert it into a
  repository-wide fact.

## Content

- State the supported runtimes, package managers, workspace topology, toolchain pins, and working
  directories that materially affect command execution.
- Organize commands by outcome, such as setup, development, generation, formatting, repair,
  analysis, lint, test, build, packaging, and publication. For every recorded command, make its
  prerequisites, scope, mutation behavior, outputs, and material cost or side effects clear.
- Distinguish non-mutating checks from formatters, fixers, generators, installers, publishers, and
  other state-changing tools. Record safe scope selectors and dry-run modes only when verified.
- Describe required runtime services and integrations with their purpose, owning configuration,
  startup dependencies, ports or endpoints, environment and credential needs, and readiness check.
- Describe project-owned MCP servers and native agent integrations only when they are part of the
  repository's supported tool surface.
- Record generator entry points, their source inputs, and their outputs. Leave semantic ownership
  and hand-edit restrictions to `Project Rules`.
- Record repository-owned setup and verification selectors that `worktree-environment-setup` or
  `change-set-verification` can invoke. Leave workflow timing, ordering, broadening, and result
  policy to those skills.
- When the repository does not declare a tool or capability, say so only when that absence prevents
  agents from inventing a consequential command or workflow.

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
