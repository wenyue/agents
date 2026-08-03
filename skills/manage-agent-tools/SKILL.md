---
name: manage-agent-tools
description: Use when diagnosing or user-approved upgrading of Codex, Cursor, Copilot, Superpowers, CodeGraph, or Tokscale is needed.
---

# Manage Agent Tools

This shared operational Skill diagnoses one active platform's recommended-tool policy and performs only explicitly approved maintenance. It starts with a read-only doctor and finishes after a fresh check reports the remaining findings. Project Hooks may diagnose, but never install or upgrade anything.

## Ownership and Policy

- The plugin owns the authoritative policies in `config/recommended-tools/`.
- A project snapshot owns its copied policies in `references/recommended-tools/`; the checker prefers those files so a Hook evaluates the snapshot that installed it.
- `setup-project-agents` owns project snapshots and explicit Hook enablement. This Skill does not change project configuration, plugin caches, or Hook trust.

## Doctor

1. Identify the active platform as `codex`, `cursor`, or `copilot`. If it cannot be identified, ask the user and stop.
2. Resolve the directory containing this `SKILL.md` as `MANAGE_AGENT_TOOLS_ROOT`.
3. Run `sh "$MANAGE_AGENT_TOOLS_ROOT/scripts/check_recommended_tools.sh" check --platform PLATFORM` on POSIX, or `& "$MANAGE_AGENT_TOOLS_ROOT/scripts/check_recommended_tools.ps1" check --platform PLATFORM` on Windows.
4. Treat this command as read-only. Exit `0` means the policy is satisfied; exit `1` reports findings; exit `2` is a diagnostic failure and stops maintenance.
5. Report the selected policy path and each finding as missing, unreadable, outdated, required-value mismatch, or detector failure.

## Approved Upgrade

1. Determine each affected tool's installation provenance before proposing a command.
2. Present the exact command, affected tool, and expected effect. Ask for approval and stop this turn before executing any command.
3. After approval, execute only the approved command through its native manager:
   - For a Copilot plugin, use `copilot plugin update`.
   - For a Codex plugin, refresh the configured marketplace and use the available native Codex install or update flow; report the exact supported command before executing it.
   - For a Cursor plugin, direct the user to Cursor's official Extensions UI when no stable non-interactive update command is available.
   - For CodeGraph or Tokscale, stop when the package-manager or installation provenance is ambiguous; report the candidate sources and request direction.
4. Do not replace a known original manager with another manager. Do not edit plugin caches, platform trust stores, or editor trust data.
5. Run doctor again and report executed commands, their results, and unresolved findings.

## Hook Boundary

When invoked as a SessionStart Hook, the checker may use its daily cache, lock, timeout, and platform-native output. It must only diagnose and render findings; it must not call an install or upgrade runner, change configuration, or request implicit approval.

## Stop Conditions

- Stop before mutation when approval for the exact command is absent.
- Stop without mutation after a doctor failure or ambiguous CodeGraph or Tokscale provenance.
- Stop after the same approved upgrade command fails twice; report both failures and the next safe manual action.

## Validation and Result

- [ ] Run doctor after every approved change; confirm its exit status and remaining findings.
- [ ] Confirm every executed command exactly matches the approved command.
- [ ] When a Hook ran, confirm it only produced diagnostic output.

Report the platform, policy path, before and after findings, approved commands, command results, and unresolved work.
