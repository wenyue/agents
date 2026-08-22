# Codex Harness Adaptation

Strength: `Default`

Scope: Codex-specific mechanics for Subagent tools, `functions.exec` orchestration, and bounded
waits with live Agents.

## Authority

- The active Skill or task owns why an Agent is delegated and what result it must produce; this Rule
  does not change user authorization, Rule precedence, or completion criteria.

## Subagent Tool Mapping

- Use `spawn_agent` to start one concrete, independently useful task. Use the returned task name or
  agent identifier with the other Subagent tools.
- Use `send_message` to add context without starting another turn. Use `followup_task` when an idle
  Subagent must perform a new bounded task.
- Use `interrupt_agent` only when its current work should stop. Use `list_agents` for an intentional
  status inspection, not as a polling loop.

## JavaScript Orchestration

- Within `functions.exec`, map independent calls already selected for concurrent execution to
  `Promise.allSettled` when partial results remain useful and to `Promise.all` when every result is
  required. Keep calls sequential when the current tool schema or an applicable Skill prohibits
  parallel execution.

## Waiting on Agents

- Treat `wait_agent` as an event subscription, not a poll. Continue useful parent work while it is
  available; a completed Agent's mailbox update arrives on the parent's next turn.
- When genuinely idle with live Agents, use `wait_agent` in bounded stretches of 300000–600000 ms
  where the active Harness and runtime allow. A long subscription wakes on mailbox activity with
  the same latency as a short one, so shorter polling adds calls without reducing response time.
- A `wait_agent` timeout means only that no mailbox update arrived during that stretch. Do not
  shorten the next stretch merely because the previous one timed out.
