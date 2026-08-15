# Request

Create a Shared Skill for verifying a repository change against every check declared as required by
that repository.

The Skill must discover the active verification contract, avoid modifying the repository, run the
declared checks through their real entries, preserve exact commands and final exits, and report
failed and unverified surfaces. It must stop when no authoritative verification contract can be
found. It must not embed either supplied context's paths or commands.
