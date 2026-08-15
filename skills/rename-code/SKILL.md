---
name: rename-code
description: Use when renaming symbols, files, private or public APIs, fixing naming typos, or enforcing naming consistency across declarations and their real references.
---

# Rename Code

Rename one identified symbol or path completely within its approved compatibility boundary. Use
semantic reference evidence for symbols and exact path evidence for files or directories. Preserve
external names unless the user approves changing them.

## Establish the Rename

1. Identify the target as either one symbol identity or one exact repository path, then record its
   current name, intended new name, kind, and approved scope.
2. Read the target project's naming, generated-file, API, and verification rules.
3. For a symbol, establish its declaration and determine whether it is private, public, serialized,
   generated, persisted, reflected, or consumed outside the repository. For a path, establish its
   exact current path, destination, filesystem case behavior, and every path-based reference.
4. Before writing, identify every generated surface and prove its source owner and regeneration
   command. Confirm that the destination does not already identify unrelated content and that a
   case-only path rename has a supported move strategy.
5. Ask only when target identity, intended scope, destination ownership, or a public compatibility
   decision remains ambiguous.

## Find the Rename Surface

Prefer a project-aware symbol or reference tool that understands imports, inheritance, dispatch,
and language semantics. If none is available, combine whole-word repository search with call-site,
type, and configuration inspection.

For a symbol, classify every match before editing:

- declarations, imports, references, overrides, tests, and filenames that identify the symbol;
- comments and user-visible text that refer to the same concept;
- string-based reflection, registration, routes, or dynamic lookup;
- generated outputs and the sources that own them;
- serialization keys, protocol fields, database columns, config keys, and other external contracts;
- unrelated same-name symbols in different scopes.

Require declaration, type, call-site, configuration, or other semantic evidence before treating a
textual match as part of the rename.

For a path, inspect the repository tree, version-control index, imports, manifests, build files,
tests, scripts, documentation links, and case-sensitive references. Treat a content search with no
matches as insufficient proof that the path rename is complete.

## Compatibility Boundary

- Rename private and repository-internal symbols completely when evidence shows no external
  consumer.
- For public APIs or external contracts, state the impact and obtain the compatibility decision
  before editing when the request does not already provide one.
- Add a deprecated alias only when compatibility is required and the project supports a migration
  path.
- Leave serialization, protocol, persistence, and config names unchanged unless they are explicitly
  inside the approved rename scope.
- Change generated names through their source owner and regenerate the output.

## Workflow

1. Record the approved old-to-new mapping and compatibility policy.
2. For a symbol, update its declaration and every confirmed semantic reference. For a path, move
   the exact source to the approved destination through the repository's supported mechanism and
   update every confirmed path reference. Use a unique intermediate path when a direct case-only
   move is not supported; never overwrite the destination.
3. Rename tests, comments, documentation, or mirrored text only when they identify the same target.
4. Regenerate each owned output from its established source.
5. Re-run semantic reference discovery for a symbol or exact path discovery for a path. Classify
   every remaining old-name occurrence as an intentional external contract, an unrelated identity,
   or a missed rename.
6. Run every verification check required by the target repository for the affected surfaces,
   including applicable formatting, static analysis, generated-output checks, and affected tests.
7. If rediscovery or verification exposes an in-scope missed rename, make one correction pass,
   then rerun the affected discovery and every affected check.

## Resolve the Run

- **Complete** only when the target has the approved name, every confirmed reference resolves, all
  old-name remnants are classified, generated outputs are current, and every required check passes.
- **Stop before writing** when identity or scope cannot be proven; a destination collision or
  case-only move has no safe strategy; an unapproved public or external contract would change; or a
  required generated source or command cannot be established.
- **Fail after writing** when a required check still fails after the correction pass, recovery
  would expand scope or change a contract, or the rename can no longer be distinguished from an
  unrelated change. Preserve useful partial state and report the exact failed check and next owner.

After writing, failure governs over a coincident stop condition. Report the stop fact without
inventing a contract, command, or broader rename scope.

## Result

Report the renamed symbol or path, compatibility outcome, affected surfaces, intentional old-name
remnants, generated outputs, correction performed, exact checks and exits, and every unresolved or
untested surface.
