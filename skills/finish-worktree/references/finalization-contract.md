# Finalization Contract

Accept exactly one closed contract with `mode` equal to `standalone-task`,
`stage-ticket-into-batch`, or `deliver-ticket-batch`.

Every mode supplies:

- `source` worktree, branch, exact `head` and `tree`, `creation_owner`, and `scope_owner`;
- `target` checkout, branch, `expected_head`, and `target_policy`;
- `evidence` fixed point, acceptance sources, review kind and result, reviewed head and tree,
  verification commands and results, and findings;
- `history_policy` and its complete owned range;
- recovery refs and current and next owners;
- authorized cleanup and retained state; and
- one `authorized_outcome`.

Reject unknown modes, cross-mode fields, missing values, and implicit remote authority.

## Prove Current State

Re-derive every named Git identity, clean owned state, ancestry, range, publication, evidence,
recovery fact, and owner. Snapshot each affected checkout's branch, `HEAD`, index tree, staged,
unstaged, and untracked state. Immediately before every mutation, recheck the facts it depends on.
Stop on stale, ambiguous, published, or unrelated state.

The common contract passes only when one closed mode, exact source and target, current evidence,
authorized recovery and cleanup, and preserved unrelated state are proven. The selected mode
reference then validates its owned history, outcome, and additional fields.
