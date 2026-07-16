---
name: debug-mode
description: Use only when the user explicitly asks to enter debug mode or an ordinary diagnosis has stalled on a hard-to-reproduce bug; never auto-activate it for routine debugging.
---

# Debug Mode

Use testable hypotheses, targeted file-based instrumentation, and human reproduction to diagnose a
bug before fixing it. Follow the phases in order and stop at each reproduction gate.

## Preconditions

- Confirm that the user explicitly requested Debug Mode. Otherwise only mention that the workflow
  is available.
- Read the target repository's rules and the relevant source, call chain, and data flow.
- Collect expected and actual behavior, reproduction steps, errors, and any existing traces or
  failing tests. Use conclusive existing evidence; instrument only what remains unresolved.

## Instrumentation Contract

- Write debug output to a file, never to `print`, `debugPrint`, `console.log`, stdout, or stderr.
- Prefer `{project_root}/.agents/debug.log`. Before clearing or deleting it, confirm that this debug
  session owns the file; otherwise choose a task-specific file under `.agents/` and report its path.
- Resolve the absolute log path once before instrumentation. Do not derive it at runtime from the
  process working directory.
- For browser code, use an existing local debug endpoint when available. If a temporary endpoint is
  necessary, keep it local-only and remove it during cleanup; do not expose debug logging in a
  production build.
- Prefix each entry with its hypothesis number, such as `[DEBUG H2]`, and log only the state,
  timing, branch, or lifecycle event needed to evaluate that hypothesis.
- Wrap every temporary change in a language-appropriate region:

```text
// #region DEBUG       Dart, JavaScript, TypeScript, Java, C#, Go, Rust, C, C++
# #region DEBUG        Python, Ruby, Shell, YAML
<!-- #region DEBUG --> HTML, Vue, Svelte
-- #region DEBUG       Lua, SQL
```

Use the matching `#endregion DEBUG` form for the language.

## Phase 1: Define the Problem

State the expected behavior, actual behavior, shortest known reproduction, and relevant execution
path. Ask only for missing information that prevents a testable hypothesis.

## Phase 2: Form Hypotheses

List a small numbered set of plausible, distinguishable hypotheses. Include non-obvious timing,
state, ownership, initialization, and lifecycle causes when the evidence supports them. For each
hypothesis, state what observation would confirm or rule it out.

## Phase 3: Instrument and Wait

1. Confirm ownership of the log file and clear it before reproduction.
2. Add the minimum region-wrapped instrumentation needed for the active hypotheses.
3. Tell the user exactly how to reproduce and which log file will be populated.
4. Stop and wait for the user to reproduce the bug.

## Phase 4: Diagnose

1. Inspect log size before reading content. Use platform-native filtering to extract hypothesis
   entries when the file is large.
2. Mark each hypothesis `confirmed`, `ruled out`, or `unresolved`, citing log evidence.
3. State the root cause only when evidence distinguishes it from the alternatives.
4. If unresolved, revise the hypotheses, clear the owned log, adjust instrumentation, and return to
   the reproduction gate.

## Phase 5: Fix and Wait

Implement the narrow root-cause fix while keeping instrumentation in place. Clear the owned log,
ask the user to verify the original reproduction, then stop and wait.

## Phase 6: Clean Up

After the user confirms the fix:

1. Remove every `DEBUG` region and any temporary endpoint.
2. Delete only the log file owned by this debug session.
3. Run the relevant project checks and summarize the root cause, evidence, fix, and verification.

If the fix fails, keep the instrumentation and recovery evidence, read the new log, and return to
Phase 2.

## Stop Conditions

- Do not patch a suspected cause before the evidence distinguishes it.
- Do not continue past either reproduction request without the user's result.
- Do not clear or delete a pre-existing file that this session does not own.
- Do not remove instrumentation before the user verifies the fix.
