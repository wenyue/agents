# SmartKit MCP Support

Status: ready-for-agent

## Problem Statement

SmartKit can distribute Skills, Rules, Hooks, and project-agent setup assets, but it does not yet
model MCP as a first-class capability. Plugin MCP configuration must currently be handwritten per
host, Project MCP configuration is duplicated across native host files, and the recommended-tool
Hook cannot report whether an MCP has the static prerequisites needed to start. This creates drift
between Codex, Cursor, and Copilot, obscures ownership when a project removes an MCP, and makes
OtakuRoom's Sentry, Flutter Inspector, and application MCP configuration difficult to maintain as a
single project contract.

Third-party Skills and MCP also need an explicit distribution boundary. Plugin hosts load Skills
from plugin-local paths but start or connect to MCP servers from configuration. Treating both as the
same kind of installable artifact would either remove reproducibility from Skills or introduce an
unnecessary MCP vendoring and update system.

The current daily recommended-tool throttle also does not reliably identify the active project,
allows Cursor to evaluate through two scopes, and can rerun on the same day when its policy changes.
Adding MCP checks without correcting that gate would multiply redundant work and prompts.

## Solution

Make MCP a first-class SmartKit configuration contract with separate Plugin MCP and Project MCP
ownership.

Plugin MCP declarations live in one canonical registry and generate explicit host-native MCP
adapters for Codex, Cursor, and Copilot. SmartKit initially declares Playwright as a Configured MCP,
started through the latest npm package in isolated headless mode. The plugin distributes its
configuration rather than copying the Playwright server implementation.

Project MCP declarations live in the repository's canonical project-agent configuration as a
strictly typed array of servers. Setup renders each declaration into the three host-native formats
and records only the Managed MCP Entries in a project ownership lock. Setup adopts an unmanaged
entry only when it is semantically equal to the desired entry, rejects conflicting entries, removes
only entries it previously managed, and preserves unrelated user MCP configuration.

Each Configured MCP may declare an MCP Readiness Profile containing only typed, non-interactive
Static MCP Readiness checks. One shared runner evaluates recommended tools, required values, Plugin
MCP readiness, and Project MCP readiness only after the Daily Project Check Gate permits that
project and host to run. The gate records its start before any detector executes and suppresses all
automatic reruns for the same canonical project root, host, and local calendar day. Runtime
connectivity, OAuth, remote health, and application liveness remain owned by the host or invoking
Skill.

Plugin-level third-party Skills remain Vendored Plugin Skills. Maintainers resolve, license-check,
hash, review, and publish them with SmartKit. Project-level third-party Skills continue to be
resolved and snapshotted by setup. User-session Hooks do not contact Skill upstreams or manage Skill
dependencies.

OtakuRoom adopts three official Flutter Skills and declares Sentry, Flutter Inspector, and its own
application MCP as Project MCP. Its local test and layout routing rules remain authoritative over
the external Skill snapshots.

## User Stories

1. As a SmartKit user, I want Playwright MCP to become available when I install the plugin, so that I do not need to hand-configure it in each host.
2. As a Codex user, I want SmartKit's Playwright MCP expressed in Codex's native plugin contract, so that Codex can discover and start it normally.
3. As a Cursor user, I want the same Playwright capability expressed in Cursor's native plugin contract, so that the plugin behaves consistently in Cursor.
4. As a Copilot CLI user, I want the same Playwright capability expressed in Copilot's native plugin contract, so that all supported hosts provide the capability.
5. As a plugin maintainer, I want one Plugin MCP registry, so that host adapters cannot become independent handwritten sources of truth.
6. As a plugin maintainer, I want generated adapter drift detected without mutation, so that CI can reject stale host configuration.
7. As a Playwright user, I want the latest MCP package used in isolated headless mode, so that browser state is not reused across tasks and no browser window is required.
8. As a security-conscious user, I want Playwright tools to retain host approval behavior, so that installing SmartKit does not silently approve browser actions.
9. As a project maintainer, I want Project MCP declared alongside other canonical agent configuration, so that the project owns intent instead of three duplicated native files.
10. As a project maintainer, I want every Project MCP to have a stable identifier, so that setup can update or remove the same logical server across hosts.
11. As a project maintainer, I want HTTP and stdio transports to be strictly typed, so that invalid combinations fail before native configuration is changed.
12. As a project maintainer, I want a server to target all hosts by default or an explicit subset, so that host availability is intentional.
13. As a project maintainer, I want small typed host overrides, so that unavoidable native differences do not fork the entire declaration.
14. As a project maintainer, I want secret-bearing environment variables referenced by name, so that generated repository files contain no secret values.
15. As a project maintainer, I want setup to preserve unrelated MCP entries, so that SmartKit does not take ownership of my complete native configuration files.
16. As a project maintainer, I want an equal existing entry adopted, so that an already-correct project can enter managed state without destructive migration.
17. As a project maintainer, I want a conflicting existing entry rejected with its native location identified, so that setup never silently overwrites user intent.
18. As a project maintainer, I want removal of a Project MCP declaration to remove only its Managed MCP Entries, so that stale generated configuration disappears safely.
19. As a project maintainer, I want the ownership lock to contain no credentials, so that it is safe to commit.
20. As a project maintainer, I want Project MCP rendering and ownership updates applied transactionally, so that failure leaves the previous project state intact.
21. As a SmartKit user, I want one daily project check pipeline, so that adding new checks does not create repeated session prompts.
22. As a SmartKit user, I want daily checks isolated by project, so that opening one repository does not suppress checks for another.
23. As a multi-host user, I want daily checks isolated by host, so that a Codex check does not suppress Cursor- or Copilot-specific requirements.
24. As a user working from a subdirectory, I want the gate to identify the nearest configured project or Git root, so that one project receives one stable daily identity.
25. As a user, I want the gate to record passed, notified, and failed evaluations alike, so that an unhealthy detector does not run repeatedly during the same day.
26. As a maintainer, I want an explicit force option, so that I can intentionally rerun diagnostics without weakening automatic throttling.
27. As a Cursor user, I want readiness evaluated only at session start, so that every submitted prompt does not launch another checker process.
28. As an MCP owner, I want readiness expressed as typed checks beside the MCP declaration, so that checks are removed or renamed with their server.
29. As a security-conscious project user, I want Project MCP declarations unable to inject arbitrary readiness scripts, so that session start does not execute repository-supplied shell code.
30. As a Playwright user, I want SmartKit to check the Node runtime and npx command, so that missing launch prerequisites produce an actionable message.
31. As a Sentry user, I want session start to avoid network and OAuth probes, so that normal offline or unauthenticated sessions are not treated as installation failures.
32. As a Flutter developer, I want SmartKit to detect whether the configured Flutter Inspector executable exists, so that a missing local tool is reported without requiring a running debug application.
33. As an OtakuRoom developer, I want session start to avoid probing the application MCP port, so that the application being stopped remains a normal state.
34. As a user, I want all daily findings aggregated into one consent request, so that I can understand and approve related tool actions together.
35. As a SmartKit maintainer, I want existing recommended-tool and required-value checks preserved within the unified runner, so that MCP support does not remove current environment guarantees.
36. As a SmartKit maintainer, I want internal checker failures to remain non-blocking for the original task, so that diagnostics cannot make the host unusable.
37. As a SmartKit maintainer, I want Matt third-party Skills pinned and vendored before release, so that every host loads identical reviewed Skill content.
38. As a SmartKit user, I want Skill upgrades delivered through a reviewed SmartKit release, so that user Hooks do not contact upstream repositories during sessions.
39. As an OtakuRoom developer, I want the official Flutter integration-test Skill installed as a project external Skill, so that integration testing has a dedicated workflow.
40. As an OtakuRoom developer, I want the official Flutter layout-fix Skill installed, so that runtime diagnostics and screenshots can guide layout repair.
41. As an OtakuRoom developer, I want the official Flutter responsive-layout Skill installed, so that responsive work follows established Flutter guidance.
42. As an OtakuRoom maintainer, I want official Flutter Skills snapshotted without local edits, so that provenance and upgrades remain clear.
43. As an OtakuRoom maintainer, I want local Rules to keep unit and widget testing separate from integration testing, so that overlapping Skills route predictably.
44. As an OtakuRoom maintainer, I want responsive work to preserve RootLayoutWidget ownership and the project's orientation helpers, so that generic external guidance cannot bypass application layout policy.
45. As an OtakuRoom developer, I want Sentry configured as a direct HTTP Project MCP on all hosts, so that native OAuth works without an npm bridge.
46. As an OtakuRoom developer, I want Flutter Inspector configured with host-appropriate executable paths, so that all three hosts reach the same project tool.
47. As an OtakuRoom developer, I want the application MCP configured at its documented default endpoint, so that agents share the same default connection contract.
48. As a release maintainer, I want SmartKit's public version advanced for this feature, so that plugin consumers can identify the new capability set.
49. As an architecture maintainer, I want the Skill snapshot and MCP configuration distribution decision recorded, so that later changes do not accidentally conflate the two lifecycles.
50. As a maintainer, I want the completed SmartKit and OtakuRoom change sets verified through their supported commands, so that generated configuration, ownership, and project behavior are reviewable together.

## Implementation Decisions

- SmartKit advances to version 1.1.0 because MCP introduces new public plugin and project configuration capabilities.
- Plugin MCP and Project MCP are distinct ownership concepts and share terminology without sharing storage or lifecycle.
- Plugin MCP uses a canonical registry plus generated host adapters. Every host manifest explicitly references its adapter when the host contract permits it.
- Playwright is a Configured MCP launched through the latest npm package with isolated headless flags. SmartKit does not copy or pin the Playwright package.
- Codex, Cursor, and Copilot retain their native MCP schemas. The canonical registry carries common intent; adapters carry host representation.
- Project MCP is an optional additive field in the sole version 1 project configuration contract. No alternate schema version or compatibility parser is introduced.
- Project MCP servers form an array with stable identifiers. The common contract includes transport, URL or command arguments, working directory, environment-variable names, enabled platforms, typed host overrides, and an MCP Readiness Profile.
- Platform remains a host capability enum containing Codex, Cursor, and Copilot. Copilot project MCP renders to the native VS Code MCP configuration without adding a duplicate VS Code platform identity.
- Project MCP ownership is entry-level. The ownership lock records the native path and logical key for every Managed MCP Entry and records no secret or server artifact provenance.
- Initial adoption succeeds only when an unmanaged same-name native entry is semantically equal to the desired adapter. A differing entry is a conflict.
- A setup run removes all entries recorded by the previous ownership lock before applying current declarations, allowing managed updates and exact stale-entry deletion while preserving unrecorded siblings.
- Readiness checks are declarative and interpreted by one shared runner. The supported set is intentionally narrow and contains command availability, allowlisted runtime minimums, workspace-relative file availability, and environment-variable presence.
- Runtime-version checks select an allowlisted runtime profile rather than executing project-supplied arbitrary commands.
- Static MCP Readiness excludes remote connectivity, authentication, tool-list negotiation, application ports, and live debug sessions.
- The Daily Project Check Gate is the first automatic check step. Its identity is the canonical project root, active host, and local date. Policy changes do not invalidate the same-day gate.
- Canonical project-root discovery prefers the nearest project-agent configuration, then the nearest Git marker, then the normalized current working directory.
- The gate records a started outcome before detectors execute. Passed, notified, and error outcomes all suppress further automatic evaluation until the next local day. Manual force remains available.
- Cursor retains only the session-start readiness Hook. Rule delivery remains native and is not subject to the daily gate.
- Rule delivery Hooks in other hosts remain event-driven. They are not environment checks and must not be throttled daily.
- Plugin-level third-party Skills remain reviewed, licensed, locked snapshots distributed inside SmartKit. Project-level external Skills remain setup-managed snapshots in the target repository.
- OtakuRoom consumes the three official Flutter Skills from their upstream repository and locks the resolved commit without modifying the snapshots.
- OtakuRoom keeps a static default application MCP endpoint. Runtime port discovery remains outside SmartKit setup.
- Sentry uses direct Streamable HTTP on all three hosts.
- A short architecture decision record documents canonical MCP declarations, host adapters, entry ownership, and the different Skill/MCP distribution models.
- The implementation follows the current contract only. Removed throttle scopes, bridge configuration, and other superseded shapes receive no aliases, migrations, or dual-read behavior.

## Testing Decisions

- Tests assert observable registry, setup, Hook, and target-repository behavior rather than private helper call order.
- Plugin MCP is tested at the adapter-sync seam: one canonical registry produces valid native adapters, the three manifests reference existing outputs, and a read-only check detects drift.
- The Codex plugin validator is exercised against the completed plugin because it is the highest available local ingestion contract.
- Project MCP is tested through the public setup workflow on representative target repositories, with unit coverage beneath it for strict parsing, native representation, semantic adoption, user conflict, stale-entry deletion, preservation, and rollback.
- Existing structured-config tests provide the prior art for preserving unknown JSON, JSONC, and TOML fields while changing owned leaves.
- Daily readiness is tested through the host Hook command seam with isolated temporary project roots and cache directories. Tests cover project/host/date identity, start-before-detector state, concurrency, errors, force, and next-day execution.
- MCP readiness tests exercise every typed check and verify that invalid or arbitrary check declarations do not execute.
- Cursor manifest tests prove that only one readiness Hook remains and that its cross-platform dispatcher is usable.
- OtakuRoom acceptance parses all three native configurations, validates the external Skill lock and setup ownership lock, and requires the public setup workflow to report a clean finish.
- OtakuRoom focused verification covers command MCP exposure and any project Rule or Skill owner changed by the routing update.
- Live Sentry authentication, Flutter VM attachment, Playwright browser interaction, and OtakuRoom application liveness are manual integration checks and are not prerequisites for the deterministic suite.
- The complete SmartKit unit suite and diff-integrity check must pass. OtakuRoom uses its pinned Flutter/Dart environment and change-set verification commands for the final project change set.

## Out of Scope

- Bundling or vendoring the Playwright MCP server implementation.
- A generic MCP artifact downloader, binary installer, package lock, or background updater.
- Automatic installation or mutation from SessionStart Hooks.
- Remote HTTP health probes, OAuth automation, credential validation, or secret storage.
- Automatic discovery of OtakuRoom's configured runtime port.
- Replacing host-native MCP approval or organization allowlist behavior.
- Remote Skill dependency resolution by plugin hosts or user-session upstream version checks.
- Editing official Flutter Skill snapshots to encode OtakuRoom policy.
- Supporting a fourth logical VS Code platform distinct from Copilot.
- Compatibility handling for superseded project MCP, Hook throttle, or Sentry bridge configuration.

## Further Notes

- The repository contained partial uncommitted implementation work when this specification was
  published. Ticket acceptance criteria remain authoritative; implementers must review, complete,
  or replace that work rather than assuming it is correct.
- The supported host schemas are intentionally adapted rather than normalized away. A host-specific
  field belongs in a typed override only when the common contract cannot express the same intent.
- Plugin installation registers MCP configuration. A package-backed server may download when the
  host first starts it, which is distinct from plugin installation time.
