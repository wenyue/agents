# Compiler context

Repository Alpha runs a compiler after modifying source files. A valid control is a clean worktree at
the same dependency revision with the candidate source changes absent. Compiler diagnostics have
stable identifiers such as `E17`.

The current run can fail for diagnostics that already exist on the clean worktree. The repository
needs attribution to distinguish candidate regressions from baseline failures without treating a
different diagnostic as proof about `E17`.
