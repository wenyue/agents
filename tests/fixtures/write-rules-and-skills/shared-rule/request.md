# Request

Create a Shared Rule for attributing verification signals to the current change.

Attribute a signal to the current change only when the same signal is present with the change and
absent from a valid change-absent control. Classify it as baseline when the same signal is present in
both runs. When the control is unavailable, still contains the change, or produces a different
signal, keep attribution unresolved.

The Rule must require reports to identify the exact command, final exit, relevant signal,
classification evidence, and any surface left unverified. It must remain valid across the two
provided contexts without embedding either project's commands or paths.
