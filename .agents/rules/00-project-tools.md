# Project Tools

Strength: `Mandatory`

Scope: Safe repository command execution, synchronization, authorized mutation, complete-change
verification, and existing Skill handoffs.

Run repository commands from the repository root. Before directly invoking a repository-owned
Python entry point, resolve a Python 3.10+ launcher from the active environment; `<python>` below
denotes that verified launcher. A wrapper that resolves its own launcher owns that prerequisite.

## Source Changes Requiring Synchronization

| Source change | Synchronize | Read-only drift check | Required synchronized state; review every generated diff |
| --- | --- | --- | --- |
| `VERSION` | `<python> scripts/sync_plugin_version.py` | `<python> scripts/sync_plugin_version.py --check` | Every generated version field matches `VERSION`. |
| `mcp/registry.json` | `<python> scripts/sync_mcp_adapters.py` | `<python> scripts/sync_mcp_adapters.py --check` | Every host adapter matches the MCP registry. |
| `agents/registry.json` or `agents/source/` | `<python> scripts/sync_agent_adapters.py` | `<python> scripts/sync_agent_adapters.py --check` | Every host adapter matches the Agent registry and source. |
| `rules/registry.json` | `<python> scripts/sync_cursor_rule_adapters.py --update` | `<python> scripts/sync_cursor_rule_adapters.py --check` | Every Cursor Rule adapter matches the Rule registry. |

Run a mutating synchronizer only when its canonical-source change belongs to the authorized change
set or the user explicitly authorizes reconciling derived outputs to the current canonical source;
otherwise run its read-only drift check and report any difference.

## Maintainer-authorized Mutation

During external-Skill maintenance, run `<python> scripts/update_external_skills.py --check`. Use
`--update`, optionally scoped by `--source owner/repository`, only with explicit user authorization.
Apply `Project Contracts`' external-Skill ownership boundary; require the updater to report
convergence and review every resulting Skill, lock, and license diff.

## Complete-change Verification

Before claiming verification complete, account for the declared comparison point, staged and
unstaged changes, untracked paths, tool-generated effects, and every affected loading, generation,
ownership, delivery, or runtime surface. Name every uncovered path or surface, run every required
non-fixing baseline check and any additional non-fixing check required by an affected owner or live
configuration, and withhold the claim until every affected path and surface is covered and every
required check passes.

Baseline verification includes the `VERSION`, Agent-adapter, and MCP-adapter read-only drift checks
above, plus:

| Purpose | Command |
| --- | --- |
| Repository-wide contract tests | `<python> -m unittest discover -s tests -p 'test_*.py'` |
| Diff whitespace and conflict-marker integrity | `git diff <comparison-point> --check` |

## Existing Skill Handoff

Hand off initialization or reconciliation of a target repository's `.agents` Rules, Skills, Agents,
MCP declarations, and setup-managed host projections to `setup-project-agents`.
