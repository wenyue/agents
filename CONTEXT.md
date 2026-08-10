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

**Managed MCP Entry**:
A host-native MCP server entry owned by setup because it was rendered from a Project MCP declaration
and recorded in the project MCP ownership lock.
_Avoid_: User MCP, entire MCP configuration file

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
A server-owned list of typed, non-interactive static checks interpreted by the shared check runner
after the Daily Project Check Gate allows evaluation.
_Avoid_: MCP-specific Hook, arbitrary check script
