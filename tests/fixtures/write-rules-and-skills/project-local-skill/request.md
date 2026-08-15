# Request

Create a Project-local Skill that refreshes the supplied project's generated catalog through its
declared public entry.

The Skill must check prerequisites before mutation, run `check`, treat exit `3` as the only
recoverable stale state, run `build` at most once, retry `check`, and report exact exits. Exit `0`
completes, exit `2` is a failure, and a missing source stops before execution. Preserve unrelated
files and leave cleanup and handoff explicit.
