---
name: write-agent-skill
description: Use when authoring a shared Skill or Skill-generation contract, adding a Skill-owned scripted workflow, or changing Skill discovery or distribution surfaces.
---

# Write Agent Skill

Apply `writing-for-agents` first. It owns general Agent-document writing, context pointers,
information hierarchy, pruning, and Skill invocation mechanics. This Skill adds the SmartKit
contract for ownership, distribution, scripts, and generation gates.

## Classify

Choose one class from distribution, ownership, and the requested output.

| Condition | Class |
| --- | --- |
| One repository owns and executes the complete job | Project-local Skill |
| A distributed Skill executes the same stable workflow across repositories | Shared Skill |
| A distributed artifact authors a complete target-owned Skill | Shared Skill-generation contract |

Removing local details does not make a Skill shared. Use the shared class only when its workflow is
stable across repositories and target-specific facts can be discovered at runtime.

A project-local or shared Skill may be operational, diagnostic, or an orchestrator. Record that
distinction only when it changes ownership, execution, gates, or completion.

## Owned Surfaces

Inspect the surfaces controlled by the selected class:

- the Skill directory, owned resources, scripts, mirrors, and tests;
- callers, wrappers, indexes, manifests, and other discovery or distribution entries;
- for a project-local Skill, the repository facts and commands needed to execute it;
- for a shared Skill, representative repositories and platforms plus every target fact that must be
  discovered at runtime; and
- for a Skill-generation contract, a representative target plus the authoring, review, acceptance,
  and handoff surfaces.

Modify only the Skill and the owned resources, wrappers, indexes, manifests, mirrors, and contract
tests required to execute or distribute it. When another owner must change, report the dependency
and obtain approval before expanding the scope.

Tracked Skills use repository-relative, Skill-root-relative, or stable protocol-owned paths. Derive
runtime absolute paths from a discovered root or task input.

## Authoring Contract

1. Select the class and define its owner, supported outcome, boundaries, and completion result.
2. Apply the matching class contract below to the Skill and every owned surface.
3. When the Skill creates or updates a durable Rule, apply `write-agent-rule` to that separate
   artifact and complete its standalone review before handoff.
4. For a Skill-generation contract, preserve separate authoring, Review Gate, Acceptance Gate, and
   handoff evidence through completion.

## Class Contracts

### Project-local Skill

- Encode verified repository facts and finish at the repository's requested outcome.
- Use the project's established runtime for Skill-owned scripts when one exists.
- Keep reusable procedure in the Skill and policy in project Rules.

### Shared Skill

- Replace project-specific assumptions with runtime discovery, Skill-owned resources, stable
  protocol paths, and explicit stop conditions.
- Preserve one supported outcome across target contexts; do not silently degrade it on an
  unsupported platform.
- Provide paired `.sh` and `.ps1` entry points for every Skill-owned scripted workflow. Both entry
  points must target the same outcome while allowing verified platform differences.

### Shared Skill-generation Contract

- Separate the authoring workflow from the generated Skill's runtime procedure.
- Define the target evidence and required generated outcome without inventing target facts.
- Require a Review Gate for the complete candidate and an Acceptance Gate that exercises the
  candidate in a representative target context.
- Hand off only after both gates pass. Include the candidate, supporting evidence, both decisions,
  and unresolved or untested surfaces.

## Owned Resources

A Skill may reference owned resources only one level deep, and each reference must state when the
resource is required. Skill-owned scripts require explicit dependencies, failure recovery, and safe
representative tests. Add assets only when the Skill consumes them in an output.

Do not add a README, changelog, installation guide, or quick reference unless an external packaging
contract requires it. Keep wrappers limited to platform metadata and one source reference.

## Validate

### Ownership and Distribution

- Verify the selected class, owner, owned resources, scripts, discovery entries, distribution
  surfaces, mirrors, and required gates.
- Confirm every repository or platform claim and command from current evidence.
- Confirm the change is limited to the Skill's owned surfaces and approved dependencies.
- Compare language mirrors structurally and preserve paths, commands, identifiers, code blocks,
  classification, and behavior.

### Execution and Gates

- Validate a project-local script with the project's runtime. For paired shared entry points, run the
  current platform's entry point and report the other as not run.
- Exercise shared Skills in materially different target contexts when broad portability is claimed.
- For a generation contract, review the complete generated candidate first, then exercise its real
  workflow in a representative target and preserve separate review and acceptance evidence.

Run the current validators, contract tests, and diff-integrity checks for every changed discovery or
distribution surface. Do not report success while an owned surface or required gate remains
unverified.

## Result

Report the Skill class and owner, owned resources and distribution surfaces, scripts and gates,
approved dependency changes, and exact validation outcomes.
