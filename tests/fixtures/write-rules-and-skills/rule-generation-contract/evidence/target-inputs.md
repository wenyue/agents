# Supported target inputs

A complete request may provide a project owner, the retained record class, applicability conditions,
exceptions, conflict behavior, target Rule location, and the current policy if one exists.

Real requests can omit the owner, present two supported write locations, or conflict with an existing
policy that must be preserved. Those inputs require an explicit stop rather than a guessed target.
