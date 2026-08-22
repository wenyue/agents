---
name: refactor-code
description: Use when moving, combining, splitting, extracting, or simplifying one code target's internals while preserving caller-visible behavior and external contracts.
---

# Refactor Code

Restructure one concrete target without changing what its callers or external consumers observe.

## Judgment Frame

### Evidence and preservation boundary

- Identify the target, structural problem, approved scope, and intended internal result.
- Read the applicable project rules, target code, callers, tests, relevant history, and nearby
  patterns. Discover generated owners and project verification requirements when they affect the
  target.
- Define the **preservation boundary** at the supported caller seam: the stable behavior and
  external contracts, plus evidence that distinguishes preservation from regression. Establish an
  owner inside the approved scope for every planned write.

Unresolved target identity, scope, ownership, or distinguishing evidence is a stop, not permission
to invent a project fact.

### Structural judgment

- Choose the smallest coherent internal structure that removes the stated problem and keeps
  implementation knowledge local.
- Keep caller-visible behavior, external contracts, and the supported caller seam stable. Add a
  framework, extension point, compatibility layer, or test-only interface only when the approved
  result requires it.
- Keep tests at supported caller seams. Change tests coupled to retired internals only to preserve
  those behavior assertions, and remove obsolete internals only after current evidence shows that
  no supported path depends on them.

### Adjacent routes

- If the requested outcome is only a symbol or file rename, stop before writing and hand the target
  and scope to `rename-code`.
- If the request is to search a codebase for architectural opportunities, stop before writing and
  hand the search scope to `improve-codebase-architecture`.
- Use `codebase-design` to choose an interface, seam, adapter relationship, or test surface; return
  here only when the result remains internal and behavior-preserving.
- If the intended result changes a public interface, persistence format, protocol, integration, or
  user-visible behavior, stop before writing and hand the confirmed design or specification to
  `implement`.

## Apply the Selected Structure

Change only the owned implementation surfaces needed for the selected structure. Move affected
internal callers, retire replaced internals, and keep every edit accountable to the approved scope
and preservation evidence.

## Verification Island

After writing one coherent internal result:

1. Compare every changed surface with the approved scope and preservation boundary. Confirm that
   the selected structure is complete, affected internal callers have moved, and replaced
   internals are gone.
2. At a completed-change checkpoint, use the active project's verification owner for every
   required affected-surface check. If none is declared, discover and run the required checks from
   applicable project rules. Include focused preservation-boundary evidence.
3. When a changed-surface comparison or check exposes a correction uniquely determined by current
   evidence—including an out-of-scope edit, in-scope regression, incomplete structural result, or
   remaining obsolete internal—apply it only if it stays in scope and preserves behavior, then
   rerun every affected check. Return to judgment after each result and continue only while
   evidence determines another supported correction.
4. Fail for no progress when the same finding recurs unchanged after correction or a proposed
   correction would not change the implementation. Preserve useful partial state and the evidence
   already obtained.

## Resolve and Hand Off

- **Complete** only when the structural problem and obsolete internals are gone, the preservation
  boundary holds, and every required check passes.
- **Stop before writing** when an adjacent route applies or a required target, boundary, scope,
  owner, or distinguishing evidence cannot be established. Report the route, exact missing
  decision, or exact missing evidence and leave the refactor unstarted.
- **Fail after writing** when a required check remains unsuccessful, a changed-surface
  finding—including an incomplete approved result or obsolete internal—has no supported in-scope
  correction, no progress is possible, or the evidence can no longer distinguish the refactor from
  a regression. Preserve useful partial state and report the exact failure and next owner or
  decision.

After writing, failure governs over a coincident stop. Include the stop fact in the handoff without
expanding scope or changing a contract.

Report the structural problem removed, preserved behavior and contracts, changed internal
surfaces, obsolete code removed, exact checks and exits, corrections or recovery performed, and
every unresolved or untested surface.
