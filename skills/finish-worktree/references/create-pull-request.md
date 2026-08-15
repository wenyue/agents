# Create a Pull Request

Publish the verified Task Commit without rewriting it, and retain its local worktree for follow-up.

1. Resolve the exact remote, base branch, head branch, pull-request title, body, and draft state.
   Ask for any value that repository evidence and the accepted request do not determine.
2. Reconfirm the Task Worktree is clean, the Task Commit's sole parent is the resolved pull-request
   base commit, and review and verification remain current. A moved base returns to finalization.
3. Push the exact task branch without force, then create the pull request through the available
   host-native or repository-authorized interface.
4. Verify the remote branch commit, pull-request base and head, draft state, and returned URL.
5. Keep the local task branch and worktree for review updates. Preserve later published review-fix
   commits as review history; leave final squash behavior to the repository's pull-request policy.
   Remove local state only after a later, separately authorized completion outcome.

The user's selection of this outcome authorizes the resolved branch push and pull-request creation.
It does not authorize unrelated pushes, remote-branch deletion, merging the pull request, or local
cleanup.
