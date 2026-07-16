# Project Rules Standardization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Standardize every rule under `.agents/rules/` while preserving its existing strength, technical policies, responsibilities, and overall direction, without modifying any skill.

**Architecture:** Keep the numbered rule files and their four responsibility layers: global behavior (`00–03`), cross-language design (`10`), language/file-type policy (`11–12`), and project-rule generator contracts (`20–22`). Normalize metadata, normative vocabulary, section order, examples, terminology, and ownership boundaries within each layer; use the existing sync-contract test as the regression harness.

**Tech Stack:** Markdown, Git, PowerShell, Python `unittest`

---

## File Map

- `.agents/rules/00-global-rule-config.md`: Strength, precedence, source ownership, wrappers, numbering, MCP, and skill portability.
- `.agents/rules/01-global-personality.md`: Engineering workflow and communication behavior.
- `.agents/rules/02-global-response-format.md`: Language, response tags, formatting, and work reporting.
- `.agents/rules/03-global-skill-config.md`: Delegation, Superpowers, worktrees, Git safety, and prose language.
- `.agents/rules/10-base-code.md`: Cross-language code-design defaults.
- `.agents/rules/11-base-cpp.md`: C++ defaults.
- `.agents/rules/11-base-flutter.md`: Dart and Flutter defaults.
- `.agents/rules/11-base-go.md`: Go defaults.
- `.agents/rules/12-base-arb.md`: ARB defaults.
- `.agents/rules/20-project-tools.md`: Tool-fact generator contract.
- `.agents/rules/21-project-rules.md`: Behavioral-contract generator contract.
- `.agents/rules/22-project-structure.md`: Structure generator contract.
- `docs/superpowers/specs/2026-07-16-project-rules-standardization-design.md`: Approved semantic baseline; read-only during implementation.

No `.agents/skills/`, wrapper, manifest, script, or test file is modified.

### Task 1: Establish the regression baseline

**Files:**
- Read: `.agents/rules/*.md`
- Read: `.agents/skills/setup-project-agents/scripts/test_sync_public_agent_assets.py`

- [ ] **Step 1: Confirm the approved design commit and working tree**

Run:

```powershell
git log -1 --oneline
git status --short
```

Expected: `4e4c5c3 docs(rules): design rule standardization` is in history and the plan commit is the current baseline. Record and preserve unrelated working-tree files.

- [ ] **Step 2: Run the existing contract tests before editing**

Run:

```powershell
python .agents/skills/setup-project-agents/scripts/test_sync_public_agent_assets.py
```

Expected: exit code `0` and a final `OK`; skips are allowed.

- [ ] **Step 3: Protect the tested wording contracts**

The rewrite must retain these phrases where the existing tests require them:

```text
Strength: `
Scope:
## Generation Contract
## Evidence
## Content
## Boundaries
Skills are portable units
Describe project targets semantically
resolve concrete paths at runtime
tool facts, capabilities, and invocation constraints
supported scope selection
mutation behavior
safe-fix capability
relative cost
.agents/skills/change-set-verification/
verification trigger timing
deduplication
risk-based broadening
```

Expected: the phrases remain under their current rule owners after the rewrite.

### Task 2: Standardize global rules

**Files:**
- Modify: `.agents/rules/00-global-rule-config.md`
- Modify: `.agents/rules/01-global-personality.md`
- Modify: `.agents/rules/02-global-response-format.md`
- Modify: `.agents/rules/03-global-skill-config.md`

- [ ] **Step 1: Rewrite `00-global-rule-config.md` in responsibility order**

Use this exact section order:

```markdown
# Rule Configuration
Strength: `Mandatory`
Scope: Rule strength, precedence, source-of-truth ownership, wrapper maintenance, numbering, MCP configuration, and skill portability.

## Strength Levels
## Precedence
## Sources Of Truth
## Wrapper Maintenance
## Numbering
## MCP Configuration
## Skill Portability
```

Preserve all three strength definitions, four precedence levels, the source table, relative-path rule, thin-wrapper bodies, add-rule/add-subagent steps, numbering ranges, MCP table, and every skill-layout policy. Consolidate repeated wrapper/source instructions. Preserve the three portability phrases from Task 1 verbatim.

- [ ] **Step 2: Rewrite `01-global-personality.md` as an engineering workflow**

Use this exact section order:

```markdown
# Engineering Workflow
Strength: `Default`
Scope: Engineering judgment, preparation, editing behavior, verification, and communication defaults.

## Understand
## Change
## Verify
## Communicate
```

Move root-cause analysis, invariants, ambiguity, local-style reading, and risk disclosure to `Understand`; focused edits, ownership, root-cause fixes, dead-code removal, existing patterns, and scope expansion to `Change`; exact checks, skipped-check reporting, two-failure stopping, and follow-up trade-offs to `Verify`; plain language, uncertainty, rationale, and non-repetition to `Communicate`. Do not weaken any directive.

- [ ] **Step 3: Rewrite `02-global-response-format.md` without duplicate tag definitions**

Use this exact section order:

```markdown
# Response Format
Strength: `Default`
Scope: Response language, tag protocol, formatting, and implementation or review reporting.

## Language
## Response Tags
## Tag Rules
## Formatting
## Work Reports
## Example
```

Keep one table for all five tags. Preserve the English first-line restatement, Simplified Chinese default, terminal `🤖`, mutual exclusion of `✅` and `❌`, three-item warning limit, simple-response exception, Markdown conventions, implementation verification reporting, and findings-first reviews. Replace the five repeated examples with one complete example that adds no policy.

- [ ] **Step 4: Rewrite `03-global-skill-config.md` around workflow ownership**

Use this exact section order:

```markdown
# Workflow Configuration
Strength: `Mandatory`
Scope: Subagent delegation, Superpowers activation, worktree workflow ownership, Git safety, and prose language.

## Delegation
## Superpowers
## Worktree Workflow
## Git Safety
## Prose Language
```

Preserve bounded delegation, disjoint edit ownership, critical-path handling, final reporting, explicit-only brainstorming, worktree creation/setup/integration/finish ownership, review-mode default, explicit commit mode, one business commit, optional infrastructure commit, overlap handling, no silent loss of user changes, no unrequested push/PR, Chinese prose/design documents, and English concrete Superpowers plans.

- [ ] **Step 5: Verify and commit the global rewrite**

Run:

```powershell
git diff --check -- .agents/rules/00-global-rule-config.md .agents/rules/01-global-personality.md .agents/rules/02-global-response-format.md .agents/rules/03-global-skill-config.md
python .agents/skills/setup-project-agents/scripts/test_sync_public_agent_assets.py
git add .agents/rules/00-global-rule-config.md .agents/rules/01-global-personality.md .agents/rules/02-global-response-format.md .agents/rules/03-global-skill-config.md
git commit -m "refactor(rules): standardize global guidance"
```

Expected: no diff-check output, tests end in `OK`, and the commit contains only the four global rules.

### Task 3: Standardize cross-language and C++ rules

**Files:**
- Modify: `.agents/rules/10-base-code.md`
- Modify: `.agents/rules/11-base-cpp.md`

- [ ] **Step 1: Normalize `10-base-code.md` without changing its defaults**

Use this exact section order:

```markdown
# Code Design
Strength: `Default`
Scope: Cross-language production-code ownership, public boundaries, naming, extraction, state, dependencies, control flow, and comments.

## Ownership And Public Boundaries
## Naming
## Extraction
## Data And State
## Dependencies
## Control Flow
## Comments
```

Keep owner-local behavior, free-function exceptions, product-driven APIs, precise domain names, boolean conditions, meaningful extraction, the roughly 80-line guidance, immutable explicit data, one mutable-state owner, async dependency timing, narrow dependency passing, adapter boundaries, early returns, local expected-failure handling, visible side effects, and non-narrative comments.

- [ ] **Step 2: Expand `11-base-cpp.md` into consistent normative bullets**

Use this exact section order:

```markdown
# C++ Guidelines
Strength: `Default`
Scope: C++ language, naming, function shape, data ownership, errors, testing, standard-library use, and concurrency defaults.

## Language And Documentation
## Naming
## Functions
## Data And Classes
## Resource Safety
## Errors
## Testing
## Standard Library And Concurrency
```

Preserve English code/docs, explicit types, Doxygen, ODR, every naming form, no magic numbers, verb functions, predicate booleans, roughly 20-line functions, early returns, structured parameter objects, `const`, `constexpr`, `std::optional`, SOLID, composition, roughly 200-line classes, Rule of Five/Zero, smart pointers, RAII, exception/result split, Arrange-Act-Assert, one unit test per public function, integration tests per module boundary, all listed STL types, `std::vector` over C arrays, the three concurrency primitives, and atomic guidance.

Keep one `BAD`/`GOOD` example immediately after the function-shape rules. It must still contrast deep nesting and flag parameters with early returns and `ProcessOpts`.

- [ ] **Step 3: Verify and commit the base/C++ rewrite**

Run:

```powershell
git diff --check -- .agents/rules/10-base-code.md .agents/rules/11-base-cpp.md
git diff -- .agents/rules/10-base-code.md .agents/rules/11-base-cpp.md
git add .agents/rules/10-base-code.md .agents/rules/11-base-cpp.md
git commit -m "refactor(rules): standardize code and C++ guidance"
```

Expected: no whitespace errors; every policy listed in Steps 1–2 remains visible; the commit contains only the two rules.

### Task 4: Standardize Dart, Flutter, Go, and ARB rules

**Files:**
- Modify: `.agents/rules/11-base-flutter.md`
- Modify: `.agents/rules/11-base-go.md`
- Modify: `.agents/rules/12-base-arb.md`

- [ ] **Step 1: Reorganize `11-base-flutter.md` without making its stack conditional**

Use this exact section order:

```markdown
# Dart And Flutter Guidelines
Strength: `Default`
Scope: Dart language shape and Flutter application architecture, state, lifecycle, UI, routing, models, imports, and analysis defaults.

## Applicability
## Public Surface And Ownership
## Data Shape
## Naming
## Declaration Order
## Section Comments
## Documentation And Comments
## State Management
## Provider Lifecycle
## Async Boundaries
## Widgets
## Routing
## Data Models
## Imports
## Analysis
```

`Applicability` preserves the project-neutral boundary and routes app names, project modules, custom lints, generated paths, and project-only APIs to project rules. Keep Riverpod, generated providers, provider naming, `watch/read/listen/select`, `keepAlive`, lifecycle disposal, mounted checks, widget choices, `go_router`, typed routes, Navigator overlays, `json_serializable`, Freezed, persistence/domain separation, import ordering, quote/comma/brace/logging/deprecation/time-source rules as established choices, not optional stack suggestions.

Merge the duplicate record guidance into `Data Shape`. Retain examples for owner-local helpers, record inference, declaration order, section comments, provider selection, provider disposal, async mounted checks, and control-flow braces next to their owning rules.

- [ ] **Step 2: Normalize `11-base-go.md` while retaining formatter and lint policy**

Use this exact section order:

```markdown
# Go Guidelines
Strength: `Default`
Scope: Go formatting, code shape, naming, errors, comments, concurrency, collections, and logging defaults.

## Code Shape
## Formatting And Limits
## Naming
## Errors
## Comments
## Context And Concurrency
## Data And Collections
## Logging
```

Retain `golangci-lint-v2 fmt`, formatter ownership, 100 columns, import groups, `funlen`, `cyclop`, `gocyclo`, `nestif`, helper rules, no `init`, API visibility, acronym forms, sentinel/error names, short-name allow list, error checks/wrapping/assertions, top-level-only fatal exits, comment and `nolint` requirements, context placement/cancellation, synchronized state, constants, preallocation, deduplication, tags, package logging, and diagnostic log contents.

- [ ] **Step 3: Normalize `12-base-arb.md` around its grammar**

Use this exact section order:

```markdown
# ARB Guidelines
Strength: `Mandatory`
Scope: ARB source ownership, localization key grammar, metadata, ordering, and generation rules.

## Source Files
## Key Grammar
## Key Components
## Metadata Contract
## Prohibited Forms
```

Retain `zh.arb` as template/source of truth, `en.arb` fallback, matching metadata, alphabetical order, the exact `${module}_${filename?}_${name}{index?}` grammar, module derivation, filename conversion, purpose/index rules, English metadata, bracketed module, readable location, purpose types, layout-derived bounds, Latin/CJK counting, and all prohibited forms. Keep one valid/invalid key example and one complete metadata example.

- [ ] **Step 4: Verify and commit the language-rule rewrite**

Run:

```powershell
git diff --check -- .agents/rules/11-base-flutter.md .agents/rules/11-base-go.md .agents/rules/12-base-arb.md
git diff -- .agents/rules/11-base-flutter.md .agents/rules/11-base-go.md .agents/rules/12-base-arb.md
git add .agents/rules/11-base-flutter.md .agents/rules/11-base-go.md .agents/rules/12-base-arb.md
git commit -m "refactor(rules): standardize language guidance"
```

Expected: no whitespace errors; all policies listed in Steps 1–3 remain represented; the commit contains only the three rules.

### Task 5: Standardize the project-rule generator contracts

**Files:**
- Modify: `.agents/rules/20-project-tools.md`
- Modify: `.agents/rules/21-project-rules.md`
- Modify: `.agents/rules/22-project-structure.md`

- [ ] **Step 1: Apply the shared contract skeleton**

Each file keeps its existing title, `Strength`, and `Scope`, followed by:

```markdown
## Generation Contract
## Evidence
## Content
## Boundaries
```

Use parallel verbs across the family: `Author` in the generation contract, source nouns in `Evidence`, `Record` in `Content`, and `Keep` / `Exclude` / `Do not` in `Boundaries`.

- [ ] **Step 2: Normalize `20-project-tools.md`**

Retain `Mandatory`, all evidence sources, runtime/package facts, commands plus prerequisites/inputs/outputs/scoping/mutation/safe-fix/cost, runtime services, generation entry points, selectors, and workflow exclusions. Preserve every tested phrase in Task 1 and keep semantic generated-file ownership in `21-project-rules.md`.

- [ ] **Step 3: Normalize `21-project-rules.md`**

Retain `Default`, behavioral evidence, public contract types, framework/lint interpretation, generated-file and external-schema ownership, terminology/copy, persistence/migration/state/lifecycle/cancellation/concurrency, evidence-based base-rule overrides, and the boundaries with `20` and `22`.

- [ ] **Step 4: Normalize `22-project-structure.md`**

Retain `Advisory`, structural evidence, top-level responsibilities, feature/module placement, shared locations, allowed/forbidden dependency directions, cross-area ownership, enforcement-mechanism references, and prohibitions on generic advice, speculative structure, self-explanatory inventories, and duplicate ownership statements.

- [ ] **Step 5: Verify and commit the generator-contract rewrite**

Run:

```powershell
python .agents/skills/setup-project-agents/scripts/test_sync_public_agent_assets.py
git diff --check -- .agents/rules/20-project-tools.md .agents/rules/21-project-rules.md .agents/rules/22-project-structure.md
git add .agents/rules/20-project-tools.md .agents/rules/21-project-rules.md .agents/rules/22-project-structure.md
git commit -m "refactor(rules): standardize project contracts"
```

Expected: tests end in `OK`, no diff-check output, and the commit contains only the three project-rule files.

### Task 6: Verify the complete rule set

**Files:**
- Verify: `.agents/rules/*.md`
- Verify unchanged: `.agents/skills/**`

- [ ] **Step 1: Check required metadata on every rule**

Run:

```powershell
Get-ChildItem '.agents/rules' -File | ForEach-Object {
  $content = Get-Content -Raw $_.FullName
  if ($content -notmatch '(?m)^# ' -or
      $content -notmatch '(?m)^Strength: `(Mandatory|Default|Advisory)`$' -or
      $content -notmatch '(?m)^Scope: ') {
    throw "Invalid rule metadata: $($_.Name)"
  }
}
```

Expected: no output and exit code `0`.

- [ ] **Step 2: Check the implementation scope and skill boundary**

Run:

```powershell
$baseline = git rev-list -n 1 --grep='docs(plan): standardize project rules'
git diff $baseline --name-only -- .agents
git diff --quiet $baseline -- .agents/skills
```

Expected: the first command lists only the twelve `.agents/rules/*.md` files; the second exits with code `0` and prints nothing.

- [ ] **Step 3: Run focused validation**

Run:

```powershell
python .agents/skills/setup-project-agents/scripts/test_sync_public_agent_assets.py
$baseline = git rev-list -n 1 --grep='docs(plan): standardize project rules'
git diff --check $baseline -- .agents/rules
```

Expected: the Python suite ends in `OK`; `git diff --check` prints nothing.

- [ ] **Step 4: Review semantic preservation file by file**

Run:

```powershell
$baseline = git rev-list -n 1 --grep='docs(plan): standardize project rules'
git diff --word-diff=plain $baseline -- .agents/rules
```

Expected: every deletion has a clearer replacement or is a true duplicate; no strength, technical selection, threshold, source-of-truth rule, prohibition, workflow owner, or ownership boundary disappears.

- [ ] **Step 5: Confirm final repository state**

Run:

```powershell
git status --short
git log --oneline -5
```

Expected: no uncommitted rule changes remain. Unrelated pre-existing files remain untouched and uncommitted. History contains the design commit, plan commit, and four scoped implementation commits.
