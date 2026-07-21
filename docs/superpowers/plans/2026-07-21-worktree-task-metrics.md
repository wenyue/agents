# Worktree Task Metrics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace manually maintained worktree phase timing with a minimal task receipt and post-hoc log/Tokscale metrics report.

**Architecture:** Keep one schema-versioned receipt with exact task boundaries and registered agent sessions. At report or finish time, subtract Tokscale session/model baselines from current aggregates and classify completed Codex tool-call intervals without retaining transcript content. Preserve read/report/finish compatibility for schema-1 ledgers active during the upgrade.

**Tech Stack:** Python 3.11 standard library, Tokscale JSON CLI, POSIX shell and PowerShell entry points, `unittest`.

## Global Constraints

- `agents/` remains the English public source of truth; update `agents-zh/` and `.agents/` in the same coherent change.
- Tokscale is an optional enrichment: timing must complete when the binary or supported session metadata is unavailable.
- Cost is labelled as Tokscale's estimated API-equivalent cost, never actual billing.
- Do not retain or render prompt, response, command, or tool-output content.
- Wall-clock remains elapsed task time; parallel agent/model/tool durations are summed activity and may exceed wall-clock.

---

### Task 1: Define the receipt and post-hoc analysis contract with failing tests

**Files:**
- Modify: `tests/test_public_agent_assets.py`

**Interfaces:**
- Consumes: existing `load_track_worktree_time_module()` dynamic module loader.
- Produces: tests for `start_task`, `attach_session`, `session_usage_rows`, `usage_delta`, `analyze_codex_tool_activity`, `finish_task`, and `render_markdown`.

- [x] **Step 1: Replace manual-phase happy-path tests with receipt and metric tests**

```python
def test_task_receipt_uses_session_baseline_without_phase_transitions(self):
    state = self.timing.start_task(
        task='measured change', repository='/repo', worktree='/repo/.worktrees/task',
        client='codex', session_id='session-main',
        baseline_rows=[self.usage_row(input_tokens=10, cost=0.1)],
        state_dir=self.state_dir, now=self.at(0),
    )
    self.assertEqual(state['schema_version'], 2)
    self.assertNotIn('active_phase', state)
    self.assertEqual(state['sessions'][0]['baseline']['status'], 'available')

def test_usage_delta_matches_tokscale_rollout_suffix_and_new_models(self):
    baseline = [self.usage_row(session_id='rollout-prefix-session-main', input_tokens=10)]
    final = [
        self.usage_row(session_id='rollout-prefix-session-main', input_tokens=25),
        self.usage_row(session_id='rollout-prefix-session-main', model='new-model', output=7),
    ]
    result = self.timing.usage_delta('codex', 'session-main', baseline, final)
    self.assertEqual(result['totals']['input'], 15)
    self.assertEqual(result['totals']['output'], 7)
```

- [x] **Step 2: Add synthetic JSONL activity classification and unavailable-Tokscale tests**

```python
def test_codex_log_analysis_classifies_completed_tool_intervals(self):
    self.write_codex_log('session-main', call('patch', 1, 'exec', 'tools.apply_patch({})'),
                         output('patch', 4), call('tests', 5, 'exec', 'python -m unittest'),
                         output('tests', 12))
    result = self.timing.analyze_codex_tool_activity(
        ['session-main'], self.at(0), self.at(20), self.codex_home
    )
    self.assertEqual(result['durations_microseconds']['code-generation'], 3_000_000)
    self.assertEqual(result['durations_microseconds']['testing'], 7_000_000)

def test_finish_succeeds_when_tokscale_is_unavailable(self):
    completed = self.timing.finish_task(
        self.task_id, self.state_dir, now=self.at(30),
        snapshot_error='tokscale executable was not found',
    )
    report = self.timing.build_report(completed)
    self.assertEqual(report['usage']['status'], 'unavailable')
    self.assertEqual(report['wall_clock_microseconds'], 30_000_000)
```

- [x] **Step 3: Run the repository suite and verify RED**

Run: `/home/jinwenhuang/.local/share/uv/python/cpython-3.11.14-linux-x86_64-gnu/bin/python3.11 -m unittest discover -s tests -p 'test_*.py'`

Expected: FAIL because the schema-2 receipt and post-hoc analysis interfaces do not exist.

---

### Task 2: Implement deterministic receipt, Tokscale delta, and Codex log analysis

**Files:**
- Modify: `agents/skills/track-worktree-time/scripts/timing.py`
- Create: `agents/skills/track-worktree-time/scripts/task-metrics.sh`
- Create: `agents/skills/track-worktree-time/scripts/task-metrics.ps1`
- Mirror runtime files under: `.agents/skills/track-worktree-time/scripts/`

**Interfaces:**
- Consumes: `CODEX_THREAD_ID`, optional `CODEX_HOME`, Tokscale's `client,session,model` JSON rows.
- Produces: `start`, `attach`, `report`, and `finish` commands; schema-2 JSON receipts; legacy schema-1 report/finish compatibility.

- [x] **Step 1: Add pure usage parsing and delta functions**

```python
def session_id_matches(candidate: str, requested: str) -> bool:
    return candidate == requested or candidate.endswith(f'-{requested}')

def session_usage_rows(payload: dict[str, Any], client: str, session_id: str) -> list[dict[str, Any]]:
    return [normalize_usage_row(row) for row in payload.get('entries', [])
            if row.get('client') == client
            and session_id_matches(str(row.get('sessionId', '')), session_id)]

def usage_delta(
    client: str,
    session_id: str,
    baseline_rows: list[dict[str, Any]],
    final_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return per-provider/model deltas plus aggregate token, cost, and activity totals."""
```

The implementation groups rows by provider/model, subtracts every numeric token, cost, and activity
field, rejects negative counters, and returns both non-zero rows and their aggregate totals.

- [x] **Step 2: Add receipt lifecycle and optional Tokscale snapshots**

```python
def start_task(task, repository, worktree, client=None, session_id=None,
               baseline_rows=None, baseline_error=None, state_dir=None, now=None) -> dict[str, Any]
def attach_session(task_id, client, session_id, entire_session=False,
                   baseline_rows=None, baseline_error=None, state_dir=None, now=None) -> dict[str, Any]
def capture_tokscale_snapshot(clients, started_at, ended_at,
                              runner=subprocess.run) -> dict[str, list[dict[str, Any]]]
def finish_task(task_id, state_dir=None, now=None, final_rows_by_client=None,
                snapshot_error=None, codex_home=None) -> dict[str, Any]
```

- [x] **Step 3: Add content-free Codex tool interval classification**

```python
def analyze_codex_tool_activity(
    session_ids: list[str],
    started_at: datetime,
    ended_at: datetime,
    codex_home: Path | None = None,
) -> dict[str, Any]
```

The implementation discovers matching JSONL files, pairs `custom_tool_call` and
`custom_tool_call_output` by `call_id`, classifies transient tool names and inputs, retains only
category durations/counts, and reports missing or incomplete intervals as warnings.

- [x] **Step 4: Add portable entry points**

```sh
#!/usr/bin/env sh
set -eu
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
for python_command in python3.13 python3.12 python3.11 python3 python; do
  if command -v "$python_command" >/dev/null 2>&1 &&
     "$python_command" -c 'import sys; raise SystemExit(sys.version_info < (3, 11))'; then
    exec "$python_command" "$script_dir/timing.py" "$@"
  fi
done
if command -v uv >/dev/null 2>&1; then
  python_command=$(uv python find '>=3.11')
  exec "$python_command" "$script_dir/timing.py" "$@"
fi
echo 'ERROR: Python 3.11 or newer is required.' >&2
exit 2
```

```powershell
$script = Join-Path $PSScriptRoot 'timing.py'
if (Get-Command py -ErrorAction SilentlyContinue) { & py -3.11 $script @args; exit $LASTEXITCODE }
if (Get-Command python3 -ErrorAction SilentlyContinue) { & python3 $script @args; exit $LASTEXITCODE }
& python $script @args
exit $LASTEXITCODE
```

- [x] **Step 5: Run the repository suite and verify GREEN**

Run: `/home/jinwenhuang/.local/share/uv/python/cpython-3.11.14-linux-x86_64-gnu/bin/python3.11 -m unittest discover -s tests -p 'test_*.py'`

Expected: all tests pass.

---

### Task 3: Rewrite the skill and global worktree contract

**Files:**
- Modify: `agents/skills/track-worktree-time/SKILL.md`
- Modify: `agents-zh/skills/track-worktree-time/SKILL.md`
- Modify: `.agents/skills/track-worktree-time/SKILL.md`
- Modify: `agents/rules/04-global-skill-config.md`
- Modify: `agents-zh/rules/04-global-skill-config.md`
- Modify: `.agents/rules/04-global-skill-config.md`
- Modify: `tests/test_public_agent_assets.py`

**Interfaces:**
- Consumes: Task 2's `start`, `attach`, `report`, and `finish` entry points.
- Produces: one shared operational skill contract and aligned English/Chinese/runtime discovery surfaces.

- [x] **Step 1: Replace phase-transition instructions with receipt workflow**

```markdown
1. Run `scripts/task-metrics.sh start --task "<summary>" --repository "<repository>" --worktree "<worktree>"` before worktree preparation.
2. Attach each additional agent session once; use `--entire-session` for a session created for the task.
3. Record participants without stable session IDs with `gap`; never guess by workspace or date.
4. Do not maintain manual phase transitions; after integration, run `finish`.
```

- [x] **Step 2: Define metric meaning and privacy/failure boundaries**

```markdown
- Wall-clock is the receipt's start-to-finish elapsed time.
- Tokscale token, cost, and model activity are baseline deltas for registered sessions.
- Tool activity is post-hoc classification, summed across agents and not a wall-clock partition.
- Cost is estimated API-equivalent cost, not an invoice or subscription charge.
- Never invoke a summarizer or `tokscale submit`; never persist transcript content.
- Missing Tokscale or session attribution does not block timing completion; render affected metrics unavailable.
```

- [x] **Step 3: Update global rule and contract assertions**

```markdown
Use `track-worktree-time` for worktree code tasks, create one task receipt before preparation,
attach participating sessions, and include the reconciled post-hoc metrics report after integration.
```

- [x] **Step 4: Run the POSIX entry point and full verification**

Run: `sh agents/skills/track-worktree-time/scripts/task-metrics.sh --help`

Expected: exit 0 and list `start`, `attach`, `gap`, `report`, `finish`.

Run: `/home/jinwenhuang/.local/share/uv/python/cpython-3.11.14-linux-x86_64-gnu/bin/python3.11 -m unittest discover -s tests -p 'test_*.py'`

Expected: all tests pass.

Run: `git diff --check`

Expected: exit 0 with no output.
