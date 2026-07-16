---
name: rename
description: Use when renaming symbols, files, private or public APIs, fixing naming typos, or enforcing naming consistency across declarations and their real references.
---

# Rename

Rename one identified concept completely within its approved compatibility boundary. Use semantic
reference evidence where possible and preserve external names unless the user approves changing
them.

## Preconditions

1. Identify the target's current name, kind, declaration, scope, and intended new name.
2. Read the target project's naming, generated-file, API, and verification rules.
3. Determine whether the name is private, public, serialized, generated, persisted, reflected, or
   consumed outside the repository.
4. Ask only when symbol identity, intended scope, or a public compatibility decision is ambiguous.

## Find the Rename Surface

Prefer a project-aware symbol or reference tool that understands imports, inheritance, dispatch,
and language semantics. If none is available, combine whole-word repository search with call-site,
type, and configuration inspection.

Classify every match before editing:

- declarations, imports, references, overrides, tests, and filenames that identify the symbol;
- comments and user-visible text that refer to the same concept;
- string-based reflection, registration, routes, or dynamic lookup;
- generated outputs and the sources that own them;
- serialization keys, protocol fields, database columns, config keys, and other external contracts;
- unrelated same-name symbols in different scopes.

Do not treat a textual match as proof that it belongs to the rename.

## Compatibility Boundary

- Rename private and repository-internal symbols completely when evidence shows no external
  consumer.
- For public APIs or external contracts, state the impact and obtain the compatibility decision
  before editing when the request does not already provide one.
- Add a deprecated alias only when compatibility is required and the project supports a migration
  path. Do not create aliases by default.
- Leave serialization, protocol, persistence, and config names unchanged unless they are explicitly
  inside the approved rename scope.
- Edit the source owner of generated files and regenerate; never hand-edit generated output.

## Workflow

1. Record the approved old-to-new mapping and compatibility policy.
2. Update the declaration and every confirmed semantic reference.
3. Rename files, tests, comments, documentation, or mirrored text only when they identify the same
   concept.
4. Regenerate owned outputs when required.
5. Search again for the old name and classify every remaining match as expected or missed.
6. Run the target project's formatter, static checks, and directly affected tests.

## Stop Conditions

- Stop when the same name resolves to multiple plausible symbols and scope cannot be proven.
- Stop before changing an unapproved public or external contract.
- Stop if regeneration is required but its source or command cannot be identified.

## Result

Report the renamed concept, compatibility outcome, affected surfaces, intentional old-name
remnants, regenerated outputs, and verification results.
