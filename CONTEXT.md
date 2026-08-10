# SmartKit

SmartKit distributes reusable agent capabilities while preserving each target repository's
ownership of its project-specific agent configuration.

## Language

**Plugin MCP**:
An MCP server distributed with the SmartKit plugin and made available through each supported
host's plugin integration.
_Avoid_: Global MCP, shared project MCP

**Project MCP**:
An MCP server declared by a target repository as canonical project configuration and rendered by
setup into the native configuration of each enabled host.
_Avoid_: Plugin MCP, hard-coded project template

**MCP Adapter**:
A host-native MCP configuration generated from a canonical Plugin MCP or Project MCP declaration.
_Avoid_: MCP source, handwritten platform copy

**Managed Asset**:
A project file, directory tree, or structured field that setup may update or delete because its
identity and current digest are recorded in the SmartKit Ownership Manifest.
_Avoid_: User-owned asset, inferred-by-name asset

**SmartKit Ownership Manifest**:
The target repository's `.agents/smartkit.lock.json`, which records resolved external sources,
digest-bearing managed assets, and non-owned seeded documents. It is the only project setup
ownership authority.
_Avoid_: External Skill lock, Project MCP lock, migration ledger

**Configured MCP**:
An MCP capability delivered as host configuration while its server remains owned by an external
package, remote service, or project runtime; SmartKit does not copy the server implementation merely
to distribute the configuration.
_Avoid_: Vendored MCP, installed MCP

**Vendored Plugin Skill**:
A third-party Skill reviewed, licensed, locked, and copied into SmartKit before release because the
supported plugin hosts load Skills from plugin-local paths and do not share a remote Skill dependency
contract.
_Avoid_: Referenced Skill, runtime-fetched Skill

**Static MCP Readiness**:
The configuration and local prerequisites that can be checked without starting an MCP server,
probing a remote endpoint, triggering authentication, or requiring an application runtime to be live.
_Avoid_: MCP health, live MCP availability

**Daily Project Check Gate**:
The first step of the automatic check pipeline, allowing at most one evaluation per canonical project
root, host platform, and local calendar day regardless of the number or outcome of downstream checks.
_Avoid_: Global daily check, per-check throttle, session throttle

**MCP Readiness Profile**:
A typed, non-interactive static check set interpreted after the Daily Project Check Gate. Plugin MCP
declares it explicitly; Project MCP derives it from command paths and environment-variable names.
_Avoid_: MCP-specific Hook, arbitrary check script
