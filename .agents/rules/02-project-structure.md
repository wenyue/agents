# Project Structure

Strength: `Advisory`

Scope: Evidence-based placement ranking for repository changes and architectural seams.

`Project Contracts` determines whether a placement is valid. Among valid placements, the narrowest
established owner that can carry a decision through its implementation and observing tests ranks
highest. These recommendations grant no ownership, installation, delivery, exposure, or dependency
authority.

## Evidence Weight

- Direct calls and imports, registry or schema relationships, generator flows, runtime entry
  points, and behavioral tests outweigh directory names, co-location, naming, and plugin packaging.
- One consumer with one behavioral test seam favors local placement. Multiple independent
  consumers of the same stable decision, or repeated local code that knows another owner's
  internals, points toward an existing shared seam.
- A new common seam ranks higher only when the shared decision is evidenced now. Similar-looking
  host or target branches favor remaining separate when their selecting predicates or behavior
  differ.

## Repository Seams

- When Rule registry parsing or validation is shared by Hook delivery and Cursor adapter
  generation, `runtime/rules/contract.py` ranks above either consumer: both
  `runtime/rules/dispatch.py` and `scripts/sync_cursor_rule_adapters.py` import it. Event selection
  and context delivery favor `dispatch.py`; Cursor frontmatter projection favors the synchronizer.
- Direct evidence that a target or harness predicate selects a projection of canonical intent
  favors that branch in its synchronizer or renderer when moving the decision upstream would
  discard context needed to choose the behavior. Per-harness Agent and MCP syntax and field
  projections are current examples. A change to cross-target intent points back to the applicable
  contract owner; similar local branches and generated adapters are representation evidence, not
  shared upstream policy seams.
- Within project setup, catalog and project-configuration shape or selection behavior favors
  `agents_setup/catalog.py`, with `setup-assets/catalog/project-config.schema.json` as
  corroboration. Target-state projection favors `agents_setup/renderer.py`;
  current-versus-desired comparison favors `agents_setup/planner.py`; filesystem commit and
  rollback behavior favors `agents_setup/transaction.py`. The `setup_project_agents.py` entry point
  ranks higher only for behavior that coordinates those stages rather than belonging wholly to one
  of them.
- Within the recommended-tool runtime, live detection and readiness evaluation favor
  `check_recommended_tools.py`, while execution and verification of an approved maintenance action
  favor `maintain_recommended_tools.py`. Hook event-routing or command-representation changes favor
  their manifests because the manifest commands enter those runtime paths directly.
- Behavioral coverage favors the existing test module that directly imports or executes the
  changed seam. A broader contract test ranks higher when the behavior is observable only across a
  registry-to-generator, entrypoint-to-runtime, or render-to-transaction path.

Command execution, synchronization procedure, authoring workflow, and machine-validation
requirements remain with their active owners. Where repository evidence does not distinguish two
valid placements, this Rule makes no recommendation.
