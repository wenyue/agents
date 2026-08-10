# SmartKit Unified Ownership Manifest

Status: ready-for-agent

## Problem Statement

SmartKit setup currently needs separate state mechanisms to manage project external Skills and
Project MCP entries. Rules, Skills, Agents, wrappers, and shared host-configuration fields also use
different deletion and ownership rules. As a result, a maintainer cannot inspect one place to learn
which project assets SmartKit currently owns, and the implementation needs resource-specific lock
parsers plus hard-coded lists of retired paths and retired field names.

The project configuration also exposes information that setup can derive safely, including GitHub
URLs, Skill identifiers, MCP transport, default platforms, static readiness checks, and license
metadata. This makes the configuration shallower than the behavior it controls and increases the
number of fields users must keep consistent.

SmartKit needs one current-state ownership contract that can manage Rules, Skills, MCP entries, and
the rest of setup's managed outputs without embedding compatibility history in the plugin. It must
remain safe when managed content is edited by a user and must preserve every project asset that
SmartKit does not own.

## Solution

Replace the project external-Skill lock and Project MCP lock with one project-local SmartKit
Ownership Manifest. The manifest records every asset that the last successful setup run owns,
including complete files, complete directory trees, and individual fields inside shared structured
configuration files. Each managed asset carries a deterministic digest of the content SmartKit last
wrote. External source resolution, detected license data, and resolved commits live in the same
manifest.

Setup computes a new desired ownership set from the current SmartKit catalog, the simplified
project configuration, and the reviewed generated candidates. Reconciliation compares the previous
manifest with that desired set. Assets present only in the previous set are removed, assets present
only in the desired set are created, and assets in both sets are updated. No retired Rule name,
Skill path, MCP key, or other compatibility history is stored in plugin code.

Only assets listed in the previous Ownership Manifest are eligible for automatic update or
deletion. Before mutating an owned asset, setup compares its current digest with the prior digest.
An unexpected user edit causes a conflict and stops the transaction. Unowned project content is
always preserved. A first setup may adopt an existing asset only when its complete semantic content
equals the desired content; a differing existing asset is a conflict.

The project configuration becomes an intent-only interface. External Skills declare a GitHub
source, an optional ref, and included repository paths. Project MCP declarations use either a URL or
a command, with optional arguments and typed host overrides. Setup derives redundant identities,
transport, default host coverage, static readiness checks, source URLs, destination names, and
license metadata.

## User Stories

1. As a project maintainer, I want one ownership manifest, so that I can see all SmartKit-managed
   project assets in one place.
2. As a project maintainer, I want the manifest to cover Rules, Skills, MCP entries, Agents, and
   wrappers, so that ownership does not depend on resource-specific hidden behavior.
3. As a project maintainer, I want project-authored Rules and Skills omitted from managed ownership,
   so that setup never treats my content as plugin-owned.
4. As a project maintainer, I want setup-seeded but project-owned documents distinguished from
   managed assets, so that their origin is visible without granting SmartKit deletion authority.
5. As a project maintainer, I want each managed file or structured field to carry a digest, so that
   setup detects manual edits before overwriting them.
6. As a project maintainer, I want each managed Skill directory to carry a deterministic tree
   digest, so that local additions, removals, and edits are detected as one ownership conflict.
7. As a project maintainer, I want an edited managed asset to stop setup with a precise diagnostic,
   so that my changes are not silently discarded.
8. As a project maintainer, I want unowned sibling fields in host configuration files preserved, so
   that SmartKit can manage one MCP entry without owning the whole file.
9. As a project maintainer, I want removing an MCP declaration to remove only the previously owned
   native entries, so that unrelated MCP servers survive setup.
10. As a project maintainer, I want removing an external Skill declaration to remove only the
    previously owned Skill tree, so that similarly named project Skills remain safe.
11. As a project maintainer, I want renaming a generated Rule to be expressed by the difference
    between previous and desired ownership, so that the plugin does not contain a history of old
    Rule names.
12. As a SmartKit maintainer, I want retired file and field registries removed, so that the current
    catalog describes only the current release.
13. As a SmartKit maintainer, I want one ownership parser and reconciler, so that files, trees, and
    structured fields share the same safety invariants.
14. As a SmartKit maintainer, I want the ownership planner to be independent of Rule, Skill, and MCP
    naming conventions, so that new managed asset roles do not require another lock format.
15. As a SmartKit maintainer, I want complete desired state rendered before mutation begins, so that
    ownership conflicts are discovered before any project file changes.
16. As a SmartKit maintainer, I want ownership and content changes applied transactionally, so that
    the project and manifest cannot describe different successful states.
17. As a SmartKit maintainer, I want the manifest written last within the successful transaction,
    so that it never claims ownership for content that was not installed.
18. As a SmartKit maintainer, I want a failed transaction to restore both content and the previous
    manifest, so that a retry starts from a coherent state.
19. As a project maintainer, I want external Skill configuration to contain only a GitHub source,
    optional ref, and included paths, so that I do not repeat derivable identifiers or URLs.
20. As a project maintainer, I want Skill destination names inferred from selected path basenames,
    so that source identity and destination identity cannot disagree.
21. As a project maintainer, I want setup to resolve a floating branch to an exact commit in the
    manifest, so that the installed snapshot remains auditable.
22. As a project maintainer, I want setup to detect the upstream root license and record its SPDX
    identifier, path, and digest, so that license metadata is verified without appearing in project
    configuration.
23. As a project maintainer, I want external Skill file provenance represented by a deterministic
    tree digest and resolved commit, so that the manifest stays compact while still detecting drift.
24. As a project maintainer, I want an MCP declaration with a URL to imply HTTP transport, so that I
    do not configure the same fact twice.
25. As a project maintainer, I want an MCP declaration with a command to imply stdio transport, so
    that invalid mixed transport fields are impossible.
26. As a project maintainer, I want Project MCP to target all supported hosts by default, so that I
    specify host lists only when behavior genuinely differs.
27. As a project maintainer, I want small typed host overrides, so that unavoidable executable or
    URL differences remain explicit without exposing arbitrary host-native documents.
28. As a project maintainer, I want static MCP readiness inferred from commands, workspace-relative
    executables, and environment-variable references, so that readiness configuration does not
    duplicate the MCP declaration.
29. As a project maintainer, I want HTTP MCP declarations to avoid automatic network and OAuth
    probes, so that setup and daily readiness remain non-interactive.
30. As a project maintainer, I want missing ownership state to make setup conservative, so that it
    adopts only semantically equal desired assets and rejects conflicting existing content.
31. As a project maintainer, I want deleting the manifest to remove SmartKit's deletion authority,
    so that setup cannot infer ownership from filenames alone.
32. As a SmartKit maintainer, I want old project configuration and old lock formats rejected, so that
    the implementation contains no migration, dual-read, or compatibility paths.
33. As an OtakuRoom maintainer, I want its external Flutter and Sentry Skills represented through
    the simplified source declarations, so that the project configuration contains only intent.
34. As an OtakuRoom maintainer, I want Sentry, Flutter Inspector, and OtakuRoom Project MCP managed
    through the same ownership manifest as its generated Rules and external Skills, so that cleanup
    and audit use one mechanism.
35. As an OtakuRoom maintainer, I want its existing Dart MCP and other user configuration omitted
    from SmartKit ownership, so that subsequent setup runs preserve them.
36. As a repository maintainer, I want the ownership manifest committed with generated project
    configuration, so that every clone starts from the same management boundary.
37. As a repository maintainer, I want the manifest to contain no credentials, environment-variable
    values, cookies, or runtime state, so that it is safe to review and commit.

## Implementation Decisions

- Introduce **SmartKit Ownership Manifest** as the canonical term for the single project-local
  record of setup ownership. Introduce **Managed Asset** as a complete file, directory tree, or
  structured field that setup may update or remove because it appears in the previous manifest.
- Treat the Ownership Manifest as current state, not migration history. Plugin catalogs declare
  only current desired assets and contain no retired names, paths, or structured-field keys.
- Replace the external-Skill and Project-MCP project locks with the single Ownership Manifest. The
  former lock documents are not read, migrated, or translated.
- Model ownership through three generic asset shapes: complete files, complete directory trees, and
  fields identified by a structured document plus logical key. A role such as Rule, Skill, MCP,
  Agent, or wrapper is descriptive metadata and does not change reconciliation semantics.
- Record deterministic content digests for every managed asset. File digests cover bytes, tree
  digests cover sorted relative paths and bytes, and structured-field digests cover canonicalized
  semantic values rather than host serialization details.
- Record setup-seeded project-owned outputs separately from managed assets when their origin must
  remain inspectable. Seeded entries grant no update or deletion authority after project ownership
  transfers.
- Build one ownership planning module whose interface accepts previous ownership and complete
  desired assets, and returns a conflict-checked create, update, delete, preserve, and next-manifest
  plan. Resource-specific renderers produce desired assets but do not implement deletion policy.
- Apply the plan transactionally. Validate all paths, field keys, current digests, generated
  content, and the complete next manifest before the first target mutation.
- Delete a previous managed asset only when it is absent from current desired state and its current
  digest still matches the previous manifest. A changed owned asset is a conflict rather than an
  implicit preservation or forced deletion.
- On first adoption, create absent desired assets, adopt semantically equal existing assets, and
  reject differing unowned assets. Do not infer ownership merely because a path resembles a
  SmartKit naming convention.
- Simplify project configuration to current intent. Remove catalog selection fields and the nested
  external-source wrapper. External Skill declarations contain a GitHub `owner/repository`, an
  optional safe ref, and a non-empty list of included repository-relative Skill paths.
- Derive external source URLs from the GitHub identity and derive Skill identifiers and destination
  names from selected path basenames. Preserve the existing path-safety, name, symlink, ref, tag
  movement, license, and snapshot validation behind setup's interface.
- Keep external source resolution data in the Ownership Manifest: requested and resolved refs,
  exact commit, detected root license metadata, and the managed Skill trees associated with that
  source.
- Simplify Project MCP declarations by inferring HTTP from `url` and stdio from `command`. Reject
  declarations containing both. Default host coverage to Codex, Cursor, and Copilot; keep optional
  typed host subsets and typed overrides only for real platform differences.
- Infer Project MCP static readiness from its effective declarations: bare executables require a
  command check, workspace-relative executables require a workspace-file check, and referenced
  environment-variable names require presence checks. HTTP declarations do not gain connectivity
  checks.
- Keep Plugin MCP registry and plugin-level external Skill release provenance outside the project
  Ownership Manifest. They belong to the plugin distribution process, while this specification
  changes project setup ownership.
- Amend the accepted Skill-snapshot/MCP-configuration architecture decision so that both Project
  MCP and project external Skills use the unified Ownership Manifest. Preserve the decision to
  snapshot Skills, configure rather than vendor MCP implementations, and keep secrets outside
  generated state.
- Keep the project configuration at its current schema version because SmartKit supports only the
  current contract. Remove old field handling and reject old inputs instead of adding a version
  migration.
- Update OtakuRoom directly to the new configuration and ownership contract in the same change set.
  Do not ship a general migration utility or compatibility reader.

## Testing Decisions

- Use the public `setup-project-agents` start/finish workflow as the primary feature seam. Tests
  supply project configuration, target state, and previous ownership, then assert the complete
  target result, next Ownership Manifest, finish status, and clean convergence check.
- Prefer external behavior assertions over private helper assertions: ownership is demonstrated by
  which assets are created, updated, removed, preserved, or rejected and by whether a second setup
  run is a no-op.
- Exercise first install with no manifest, adoption of equal existing content, rejection of unequal
  existing content, idempotent repeat setup, current-contract update, rename as delete-plus-create,
  and declaration removal.
- Exercise digest conflicts for a managed Rule file, an external Skill tree, and one host-native MCP
  field. Each case must stop before writes and preserve the old manifest and target content.
- Exercise preservation of unowned Rules, Skills, MCP siblings, host configuration fields, and
  project documents in the same workflow-level fixtures.
- Exercise a source containing several external Skills and confirm one resolved commit and detected
  license feed multiple managed Skill-tree entries without duplicated project configuration.
- Exercise missing, unrecognized, symlinked, and ambiguous source license inputs through setup's
  public failure result.
- Exercise HTTP and stdio MCP inference, all-host defaults, host subsets, typed overrides, inferred
  readiness, invalid mixed declarations, and environment-variable-name handling through project
  configuration parsing and workflow results.
- Exercise removal of previously owned native MCP fields without deleting a shared host
  configuration file that still contains user fields.
- Exercise removal of a previously owned Skill tree without rediscovering it as a project-owned
  Skill during the same run.
- Exercise transaction failure at representative file, tree, field, and manifest application
  points and confirm complete rollback.
- Retain focused pure tests for deterministic canonicalization and digest computation because those
  algorithms have many boundary values, but do not make their internal call structure part of the
  feature contract.
- Remove tests whose only purpose is the old two-lock formats, retired-name catalogs, or
  compatibility behavior. Replace them with assertions against current ownership behavior.
- Run the complete SmartKit test suite, configuration and generated-adapter drift checks, and diff
  integrity checks after the focused workflow tests.
- Perform a real OtakuRoom start/finish acceptance run using the pinned SmartKit source. Acceptance
  requires `phase: finish`, `check: clean`, one unified Ownership Manifest, no former project lock
  files, preserved Dart MCP and user configuration, and a second no-op convergence check.

## Out of Scope

- Migrating, translating, or dual-reading former project configuration or former lock documents.
- Keeping hard-coded histories of renamed or removed Rule, Skill, Agent, wrapper, or MCP identifiers.
- Merging plugin-release provenance for Vendored Plugin Skills into a target project's Ownership
  Manifest.
- Vendoring MCP server implementations or recording MCP package contents in project ownership.
- MCP network health checks, OAuth validation, live application-port discovery, or debug-session
  availability checks.
- Automatically resolving user edits to managed assets. Conflicts require an explicit human choice
  followed by a new setup run.
- Treating every file originally created by setup as permanently managed. Project-owned seeded
  documents remain outside automatic update and deletion authority.
- Background synchronization, per-session upstream checks, or mutation outside the explicit setup
  workflow.
- Storing credentials, environment-variable values, authentication state, caches, or session data
  in project configuration or the Ownership Manifest.

## Further Notes

- The unified manifest is a safety capability, not a runtime dependency. Applications and MCP
  servers do not read it; only setup uses it to reconcile ownership.
- One file may produce more frequent textual merge conflicts than two specialized locks, but setup
  is already a maintainer-run project transaction. A single inspectable ownership boundary and one
  reconciliation model are more valuable than splitting state by resource type.
- The deletion test for the new ownership module is favorable: without it, Rule, Skill, MCP, Agent,
  and wrapper renderers would each need their own adoption, drift, update, and deletion behavior.
- The existing architecture decision currently names separate Project MCP and external Skill locks.
  Implementation must amend that decision rather than leaving contradictory accepted guidance.
