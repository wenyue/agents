---
name: rename-code
description: Use when renaming a symbol or path, including a public API, and updating every real reference.
---

# Rename Code

Rename one identified symbol or path completely within its approved compatibility boundary. Prove
symbol identity with semantic evidence and path identity with exact repository evidence.

## Establish the Rename

1. Read the target project's naming, API, generated-file, and verification instructions. Record the
   old-to-new mapping, target kind, requested scope, and any compatibility choice already made.
2. Prove a symbol's declaration and scope or a path's exact current and destination locations.
   Separate unrelated same-name identities and confirm that the destination does not collide with
   unrelated content.
3. Select one execution path:
   - **Fast Symbol Path:** use only when the target is private or repository-internal, evidence shows
     no external consumer, a project-aware semantic rename operation supports its language and
     scope, and the name has no dynamic, generated, serialized, persisted, protocol, configuration,
     or cross-language identity.
   - **Full Rename Path:** use for every path and for any symbol that does not meet every Fast Symbol
     condition. This includes public APIs, external contracts, generated names, dynamic string
     lookups, and symbols without supported semantic rename tooling.
4. For the Full Rename Path, complete the target's discovery:
   - **Symbol:** use a project-aware reference tool when available. Otherwise combine whole-word
     search with call-site, type, import, inheritance, dispatch, configuration, reflection, and
     registration evidence.
   - **Path:** inspect the repository tree, version-control index, imports, manifests, build files,
     tests, scripts, documentation links, and case-sensitive references. A content search with no
     matches is not complete path evidence.
5. For the Full Rename Path, classify declarations or paths, references, tests, filenames,
   comments, user-visible text, dynamic string lookups, external contracts, and generated outputs.
   Include a textual match only when identity, type, call-site, configuration, or path evidence
   ties it to the target.
6. Resolve Full Rename compatibility before writing:
   - rename a private or repository-internal identity completely only when evidence shows no
     external consumer;
   - for a public API or external contract, state the impact and obtain the missing compatibility
     decision from its owner;
   - preserve serialization keys, protocol fields, persisted names, database columns, and config
     keys unless the approved scope includes them; and
   - create a deprecated alias only when the approved compatibility choice requires it and the
     project supports that migration path.
7. For every generated surface, identify its canonical source owner and supported regeneration
   command. For a path, establish the repository-supported move mechanism and, for a case-only
   rename, a safe intermediate path.

The Fast Symbol Path reduces discovery and reporting work but still requires rediscovery and every
project-required check. Stop before writing when target identity, scope, or path selection is
unresolved; a public compatibility decision is missing; a destination would collide or cannot be
moved safely; or a required generated source owner or regeneration command cannot be established.
Hand the exact missing decision or evidence to its contract, path, generator, or project owner.

## Apply the Rename

1. For the Fast Symbol Path, use the supported semantic rename operation to update the declaration
   and its references.
2. For the Full Rename Path, apply the approved mapping:
   - **Symbol:** update the declaration and every confirmed semantic reference.
   - **Path:** move the exact source through the supported mechanism and update every confirmed path
     reference. Use the established unique intermediate path for a case-only move and never
     overwrite a destination.
3. Rename tests, filenames, comments, documentation, and mirrored text only where evidence ties
   them to the same target.
4. For the Full Rename Path, change generated names through their canonical source owner, then run
   the established generator.

## Rediscover and Verify

1. Repeat the selected path's semantic discovery for a symbol or exact tree, index, and reference
   discovery for a path.
2. Classify every remaining old-name occurrence as an intentional external contract, an unrelated
   identity, or an in-scope missed rename.
3. Run every project-required check for the affected surfaces, including applicable formatting,
   static analysis, generated-output checks, and affected tests.
4. When rediscovery or verification finds an in-scope miss, correct it only when current evidence
   uniquely ties it to the approved rename, then repeat affected discovery and checks. Fail for no
   progress when the same finding recurs unchanged or the proposed correction would not change the
   candidate. Also fail and hand off when evidence cannot classify a required finding or a
   correction requires broader scope, a different compatibility decision, or another owner's
   action.

## Resolve the Run

- **Complete** only when the target has the approved name, every confirmed reference resolves, all
  old-name remnants are classified, generated outputs are current, and every required check passes.
- **Fail after writing** when required verification remains red, the rename cannot be separated
  from unrelated changes, no-progress is reached, or completion requires unapproved scope or
  contract changes. Preserve useful partial state.
- After writing, failure governs over a coincident pre-write stop condition.

Report the selected path, renamed symbol or path, compatibility outcome, affected surfaces, semantic
tool or generator used, corrections, exact checks and exits, and unresolved or untested surfaces.
Itemize every intentional or unresolved old-name occurrence that still identifies the target with
its exact location and classification. Summarize unrelated same-name identities; a clean Fast
Symbol rediscovery needs only a clean result. Name the next owner for every failed or handed-off
condition.
