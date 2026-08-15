# ADR 0004: Model Agent Hosts as Harnesses and Reuse Rule Delivery for Adaptation

Status: Accepted

Date: 2026-08-15

## Context

SmartKit used `platform` for both operating systems and agent host applications. The same overload
appeared in setup configuration, registries, command-line options, models, templates, tests, and
documentation. It obscured whether a selector referred to Windows or Linux, or to Codex, Cursor,
or GitHub Copilot.

Each agent host exposes different tools and wait semantics. Codex `wait_agent` is an event
subscription whose bounded stretch can end without a mailbox update while the Agent remains live.
Short polling adds tool calls without reducing notification latency. Workflow-specific Skills
already own why they delegate and which results they require, so a global Agent-orchestration Rule
would duplicate those Skills. Creating another registry, loader, or Subagent Skill solely for the
Codex mapping would also duplicate the existing session Rule delivery path.

The plugin's internal JSON documents also carried independent integer versions even though they
ship, upgrade, and validate atomically with the plugin and have no independent consumers.

## Decision

`Harness` means an agent host application such as Codex, Cursor, or GitHub Copilot. `Platform`
means an operating-system family such as Windows, Linux, or macOS. Existing host-facing fields,
types, parameters, command-line options, paths, and documentation move directly from
`platform(s)` to `harness(es)` without aliases, migration readers, or compatibility shims.
This hard cut applies to SmartKit-owned surfaces. Immutable external Skill snapshots retain their
upstream wording and are changed only through their owning updater.

`core-skill-config` becomes `core-skill-governance`. It owns Skill authority, precedence, planning
and delivery routing, and the constraints applied to project, plugin, and external Skills. Workspace
selection, local Git state, commit authority, and remote actions move to
`core-workspace-policy`. SmartKit defines no always-loaded Agent-orchestration policy; each Skill
owns its own delegation and completion requirements.

Harness-specific mechanics use a plugin-private Harness-scoped Rule in `rules/registry.json`.
The `harness` trigger activates only for a matching Harness's session lifecycle. The Codex Rule
maps shared policy to `spawn_agent`, `send_message`, `followup_task`, `interrupt_agent`,
`list_agents`, and `wait_agent`. It records that `wait_agent` is an event subscription, uses
300000–600000 ms bounded stretches when the active Harness and runtime allow, and treats a timeout
only as the absence of mailbox activity during that stretch. It is `Default`, mechanics-only, and
cannot redefine Skill policy, user authority, Rule precedence, or completion criteria. Cursor
receives no generated adapter for a Harness-scoped Rule, and Harnesses without adaptation content
receive no empty Rule.

The existing Rule registry, validator, dispatcher, Hook, ordering, and fail-closed integrity
boundary remain the only delivery mechanism. `core-rule-config` stays first, the Codex adaptation
follows it, and the remaining shared Rules follow the adaptation. Codex reinjects the same session
context after startup, resume, clear, and compact. Its Hook context limit must exceed the verified
combined payload rather than spilling a required Rule.

The plugin version advances from `1.1.1` to `1.2.0`. Internally owned JSON registries, catalogs,
project configuration, workflow messages, ownership manifests, external-skill locks, and test case
documents no longer declare independent integer versions. The plugin version is their only release
version. Versions required by a Harness-native manifest or another external protocol remain.

## Consequences

Configuration using `platforms` or `--platform` fails under the new contract and must be edited to
`harnesses` or `--harness`. The hard cut keeps one vocabulary and one parser path but deliberately
does not migrate older project snapshots.

Harness adaptation adds one Rule trigger and source without adding another runtime subsystem. A
malformed Harness-scoped Rule fails closed with the registry, so release validation must cover its
schema, source, routing, non-delivery to other Harnesses, compaction reinjection, and payload size.
Workflow-specific delegation remains with the invoking Skill; exact tool names and event behavior
remain isolated to Codex.

Removing internal JSON versions reduces coordinated upgrade work and rejects stale version fields
as unknown input. It also means those documents cannot evolve independently from the plugin; that
is intentional because they have no independent release or external dependency boundary.
