---
name: refactor-code
description: Use when restructuring internal code while preserving observable behavior and external contracts.
---

# Refactor Code

Restructure internal code without changing observable behavior or external contracts.

## Preconditions

- Identify the concrete target and structural problem.
- Read the applicable repository rules, target code, nearby patterns, and affected callers.
- Establish tests or observable examples that protect the behavior being preserved.

## Workflow

1. Define the observable behavior and external contracts that must remain unchanged.
2. Identify the smallest coherent internal structure that removes the stated problem.
3. Update the implementation and any tests coupled to retired internals.
4. Remove obsolete internal branches, adapters, and helpers inside the approved scope.
5. Run the relevant formatter, static checks, and tests supported by the project.
6. Confirm the preserved behavior still passes through the same external interface.

Introduce a framework, extension point, compatibility layer, or test-only interface only when the
approved behavior-preserving outcome requires it.

## Architecture Boundary

- When the user requests a codebase-wide search for architectural opportunities, stop and tell them
  to invoke `improve-codebase-architecture`.
- When the change requires choosing an interface, seam, adapter relationship, or test surface, apply
  `codebase-design` before implementation.
- When the selected design changes a public interface, persistence format, protocol, integration, or
  user-visible behavior, stop and tell the user to invoke `implement` with the confirmed design or
  its specification.

## Stop Conditions

- Stop when the concrete target or preserved behavior cannot be established.
- Stop when the requested result requires an external contract or observable behavior change.
- Stop when available verification cannot distinguish the refactor from a behavior regression.

## Result

Report the structural problem removed, preserved behavior and contracts, changed internal surfaces,
obsolete code removed, and exact verification performed.
