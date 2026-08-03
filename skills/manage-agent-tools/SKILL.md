---
name: manage-agent-tools
description: Use when checking, diagnosing, installing, or upgrading the supported agent platform, Superpowers, CodeGraph, or Tokscale.
---

# Manage Agent Tools

Diagnose the current platform's declared tool policy and apply user-approved fixes through the tool's original plugin manager or package manager. Complete when a fresh uncached check has no findings, or report every unresolved finding and why it remains.

## Ownership

- This Skill owns interactive diagnosis and user-approved tool maintenance.
- `references/recommended-tools/<platform>.json` owns target versions, detectors, and install or upgrade guidance.
- Project SessionStart Hooks may call the checker in `hook` mode; they report findings but never mutate tools.
- `setup-project-agents` owns project configuration and Hook installation, not third-party tool mutation.

## Workflow

1. Determine the active platform as `codex`, `cursor`, or `copilot` from the current runtime. If the runtime cannot be identified, ask the user for the platform and stop this turn.
2. Resolve the directory containing this active `SKILL.md` as `MANAGE_AGENT_TOOLS_ROOT`; do not assume a repository-local `.agents/` path.
3. Run `sh "$MANAGE_AGENT_TOOLS_ROOT/scripts/check_recommended_tools.sh" check --platform PLATFORM` on POSIX, or `& "$MANAGE_AGENT_TOOLS_ROOT/scripts/check_recommended_tools.ps1" check --platform PLATFORM` on Windows.
4. If the command exits `0`, report that the declared policy is satisfied and stop.
5. If the command exits `2`, report that diagnosis failed, include stderr, and do not attempt installation or upgrade.
6. If the command exits `1`, classify each finding as a missing tool, unreadable version, outdated version, required-value mismatch, or detector failure.
7. For each missing or outdated tool, inspect how it is installed. Use the active platform's plugin manager for Superpowers. Use the executable location and available package-manager metadata for CodeGraph and Tokscale.
8. Present the exact commands and affected tools before mutation. Ask the user to approve those commands and stop this turn.
9. After approval, execute only the approved commands. Do not replace one package manager with another when the original installation source is known.
10. Run the uncached check again. Report the satisfied tools, unresolved findings, commands executed, and any command that failed.

## Stop Conditions

- Stop before mutation when user approval is absent.
- Stop without mutation when installation provenance is ambiguous; report the candidate sources and request direction.
- Stop after an upgrade command fails twice for the same tool; report both failures and the next safe manual action.
- Do not edit platform trust stores. Hook trust remains an explicit platform action.

## Validation

- Confirm the final checker exit status.
- Confirm every executed command was included in the user's approval.
- Confirm SessionStart Hook mode performed no installation or upgrade command.

## Result

Report the platform, policy path, before and after findings, approved commands, command results, and unresolved work.
