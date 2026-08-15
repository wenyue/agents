---
name: refactor-code
description: Use when moving, combining, splitting, extracting, or simplifying one code target's internals while preserving caller-visible behavior and external contracts.
---

# Refactor Code

Restructure one concrete target without changing what its callers or external consumers observe.

## Establish the refactor

1. Identify the target, structural problem, approved scope, and intended internal result.
2. Read the applicable project rules, target code, callers, tests, and nearby patterns.
3. Define the **preservation boundary**: behavior and external contracts that must remain stable at
   the existing caller seam, plus evidence that distinguishes preservation from regression.
4. Confirm that the chosen structure is implementation detail and every planned write has an owner
   inside the approved scope.

## Route adjacent work

- For a pure symbol or file rename, stop this run before writing and hand off to `rename-code`.
- For a codebase-wide search for architectural opportunities, stop this run before writing and hand
  off to `improve-codebase-architecture`.
- When the refactor requires choosing an interface, seam, adapter relationship, or test surface,
  apply `codebase-design` first. Continue here only for an internal, behavior-preserving result.
- When the result changes a public interface, persistence format, protocol, integration, or
  user-visible behavior, stop and hand the confirmed design or specification to `implement`.

## Restructure the internals

1. Choose the smallest coherent structure that removes the problem. Add a framework, extension
   point, compatibility layer, or test-only interface only when the approved result requires it.
2. Update the implementation inside scope. Adjust tests coupled to retired internals only to keep
   behavior assertions at a supported caller seam.
3. Remove obsolete internals after their callers have moved to the new structure.
4. Run every required project check for the affected surfaces, including focused evidence for the
   preservation boundary.
5. Compare the changed surfaces with the approved scope and boundary. If this refactor caused an
   in-scope regression or is incomplete, make one correction pass and rerun every affected check.

## Resolve the run

- **Complete** only when the problem and obsolete internals are gone, the preservation boundary
  holds at the supported caller seam, and every required check passes.
- **Stop before writing** when an adjacent-work route applies; the target, boundary, scope, owner,
  or distinguishing evidence cannot be established; or the requested result requires an
  external-contract change. Report the route, missing decision, or evidence and leave the refactor
  unstarted.
- **Fail after writing** when a check still fails after the correction pass, no in-scope correction
  exists, or the evidence can no longer distinguish the refactor from a regression. Preserve useful
  partial state and report the exact failure and required owner or decision.

After writing, failure governs over a coincident stop condition. Include the stop fact in the
handoff instead of expanding scope, changing a contract, or inventing a project fact.

## Handoff

Report the structural problem removed, preserved behavior and contracts, changed internal surfaces,
obsolete code removed, exact checks and exits, recovery performed, and every unresolved or untested
surface.
