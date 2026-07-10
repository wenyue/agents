# Worktree Integration Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split worktree creation, project environment setup, and completed-change integration into distinct skills, with review-first integration and direct replacement of the legacy project workflow.

**Architecture:** Keep `.agents/rules/03-global-skill-config.md` as a thin router. Continue delegating worktree selection and creation to `superpowers:using-git-worktrees`, generate a target-owned `worktree-environment-setup` from repository evidence, and publish a reusable `worktree-integrate` skill for review or explicit commit integration. Extend the public manifest with project-skill generator metadata so synchronization deletes the legacy target skill without copying the generator contract.

**Tech Stack:** Markdown skill/rule contracts, JSON manifest, Python 3 standard library, `unittest`, Git.

## Global Constraints

- Modify only `/home/jinwenhuang/work/agents`; do not modify any target project.
- Do not create a worktree unless explicitly requested; execute this plan in the clean current checkout.
- `review` is the default integration mode and must preserve current-branch HEAD and index.
- `commit` requires explicit user intent and merges exactly one business commit with `--ff-only`.
- Delete `project-development-workflow` directly; regenerate `worktree-environment-setup` only from current target-repository evidence.
- Run a real worktree acceptance test only when `worktree-environment-setup` is created or materially changed, not on ordinary use.
- Preserve user changes; do not automatically stash, reset, clean, push, or create a PR.
- Use whole-section rewrites for changed contracts instead of accumulating exception clauses.

---

### Task 1: Lock the environment-generator contract with failing tests

**Files:**
- Modify: `.agents/skills/setup-project-agents/scripts/test_sync_public_agent_assets.py`
- Modify: `docs/superpowers/plans/2026-07-10-worktree-integration-skills.md`

**Interfaces:**
- Consumes: current `sync_public_assets()` and public repository files.
- Produces: failing tests that define generator deletion and the environment-only contract.

- [ ] **Step 1: Add a failing generator-deletion test**

Add a test that declares project-skill generator metadata and verifies direct deletion without scaffold creation:

```python
def test_sync_deletes_legacy_project_skill_without_copying_generator_contract(self):
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        source = root / 'agents'
        target = root / 'target'
        skill_root = target / '.agents' / 'skills' / 'setup-project-agents'
        source_skill = source / '.agents' / 'skills' / 'worktree-environment-setup'
        legacy_skill = target / '.agents' / 'skills' / 'project-development-workflow'
        source_skill.mkdir(parents=True)
        legacy_skill.mkdir(parents=True)
        skill_root.mkdir(parents=True)
        (source_skill / 'SKILL.md').write_text(
            '---\nname: worktree-environment-setup\ndescription: Generator contract\n---\n',
            encoding='utf-8',
        )
        (legacy_skill / 'SKILL.md').write_text(
            '---\nname: project-development-workflow\ndescription: Legacy\n---\n',
            encoding='utf-8',
        )
        public_config = {
            'mirror_delete': True,
            'rules': [],
            'skills': [],
            'project_skill_generators': [
                {
                    'name': 'worktree-environment-setup',
                    'legacy_names': ['project-development-workflow'],
                }
            ],
            'agent_prompts': [],
        }
        context = sync.SyncContext(target, source, skill_root, False, [])

        changes = sync.sync_public_assets(
            context,
            public_config,
            {'rules': [], 'agent_prompts': []},
        )

        self.assertFalse(legacy_skill.exists())
        self.assertFalse(
            (target / '.agents' / 'skills' / 'worktree-environment-setup').exists()
        )
        self.assertIn(
            sync.Change('deleted', '.agents/skills/project-development-workflow'),
            changes,
        )
```

- [ ] **Step 2: Replace legacy environment-contract tests**

Assert that:

```python
environment_skill = REPO_ROOT / '.agents' / 'skills' / 'worktree-environment-setup' / 'SKILL.md'

self.assertTrue(environment_skill.is_file())
self.assertIn('## Generation Contract', environment_skill.read_text(encoding='utf-8'))
self.assertFalse(
    (REPO_ROOT / '.agents' / 'skills' / 'project-development-workflow').exists()
)
```

Also assert that `public_assets.json` contains a `worktree-environment-setup` entry under `project_skill_generators` with `project-development-workflow` as its legacy name.

- [ ] **Step 3: Add setup-workflow contract assertions**

Assert that `setup-project-agents/SKILL.md` instructs direct deletion, evidence-only regeneration, real-worktree acceptance after material change, and no ordinary-use revalidation.

- [ ] **Step 4: Run the focused tests and verify RED**

Run:

```bash
python3 .agents/skills/setup-project-agents/scripts/test_sync_public_agent_assets.py \
  SyncPublicAgentAssetsTest.test_sync_deletes_legacy_project_skill_without_copying_generator_contract \
  SyncPublicAgentAssetsTest.test_worktree_environment_setup_is_generator_contract \
  SyncPublicAgentAssetsTest.test_setup_project_agents_regenerates_environment_skill
```

Expected: FAIL because the new manifest key, directories, and sync deletion behavior do not exist.

- [ ] **Step 5: Keep the RED tests uncommitted**

Do not commit failing tests. Continue directly to Task 2 and commit the tests together with the passing environment implementation.

### Task 2: Replace the legacy generator with environment setup

**Files:**
- Delete: `.agents/skills/project-development-workflow/SKILL.md`
- Create: `.agents/skills/worktree-environment-setup/SKILL.md`
- Modify: `.agents/skills/setup-project-agents/SKILL.md`
- Modify: `.agents/rules/20-project-tools.md`
- Modify: `.agents/rules/21-project-rules.md`
- Modify: `.agents/rules/22-project-structure.md`
- Modify: `.agents/skills/setup-project-agents/references/public_assets.json`
- Modify: `.agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: target-repository evidence recorded in `.agents/rules/20-project-tools.md`.
- Produces: a generator contract for a target-owned environment-only skill and a setup workflow that deletes the legacy skill before regeneration.

- [ ] **Step 1: Run an environment-contract baseline pressure scenario**

Dispatch a fresh subagent without the new contract:

```text
Using only the current project-development-workflow contract, draft the target skill for a Python repository that uses Poetry, Ruff, mypy, pytest, and generated protobuf modules. The target repository already has a linked worktree. Return only the proposed SKILL.md.
```

Expected RED evidence: the proposed skill owns worktree selection/creation, review, merge-back, or cleanup instead of limiting itself to environment preparation.

- [ ] **Step 2: Initialize and write the new generator contract**

Run the skill initializer for `worktree-environment-setup`, then retain only files required by this repository's generator-contract pattern. Write a concise `SKILL.md` with:

```yaml
---
name: worktree-environment-setup
description: Use when defining, generating, or validating a target repository's environment setup skill for an already-created Git worktree.
---
```

The body must require target evidence, dependency/tool/proto/service setup, command exit checking, and generation-time real-worktree acceptance. It must forbid worktree creation, business edits, baseline tests, Git integration, and ordinary-use self-validation.

- [ ] **Step 3: Rewrite setup-project-agents around delete-and-regenerate**

Change its workflow to:

```text
public sync
→ delete project-development-workflow
→ generate worktree-environment-setup from current evidence
→ review candidate
→ if created/materially changed, test the exact candidate in a real temporary worktree
→ sync wrappers and validate
```

Require the acceptance worktree to receive byte-identical candidate skill and relevant tooling-rule content when those files are not yet committed. Do not restore or consult the legacy skill on failure.

- [ ] **Step 4: Implement generator-driven legacy deletion**

Add `project_skill_generators` to `public_assets.json`:

```json
"project_skill_generators": [
  {
    "name": "worktree-environment-setup",
    "legacy_names": ["project-development-workflow"]
  }
]
```

Add this sync helper and call it from `sync_public_assets()` without mirroring the generator directory:

```python
def _delete_legacy_project_skill_dirs(
    context: SyncContext,
    generators: list[dict[str, Any]],
    mirror_delete: bool,
) -> None:
    if not mirror_delete:
        return
    for generator in generators:
        for legacy_name in _list_value(generator.get('legacy_names')):
            legacy_dir = context.target_root / '.agents' / 'skills' / legacy_name
            skill_file = legacy_dir / 'SKILL.md'
            if _read_frontmatter_value(skill_file, 'name') == legacy_name:
                _delete_path(context, legacy_dir)
```

- [ ] **Step 5: Remove stale responsibilities from project rule contracts and README**

Make `20-project-tools.md` own stable setup/verification facts and hand environment preparation to `worktree-environment-setup`. Remove worktree/merge-back routing from `21-project-rules.md` and `22-project-structure.md`. Keep README concise while naming the generated environment skill and the public integration skill.

- [ ] **Step 6: Run focused tests and quick validation**

Run:

```bash
python3 .agents/skills/setup-project-agents/scripts/test_sync_public_agent_assets.py
python3 /home/jinwenhuang/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  .agents/skills/worktree-environment-setup
```

Expected: all currently defined tests pass.

- [ ] **Step 7: Forward-test the environment contract**

Dispatch a fresh subagent with the new contract and the same Python tooling evidence. Expected GREEN behavior: it returns environment-only setup, includes functional linter/checker/formatter checks for generation-time acceptance, and excludes creation, business implementation, merge-back, and cleanup.

- [ ] **Step 8: Commit the environment contract**

```bash
git add README.md .agents/rules/20-project-tools.md .agents/rules/21-project-rules.md \
  .agents/rules/22-project-structure.md .agents/skills/setup-project-agents/SKILL.md \
  .agents/skills/worktree-environment-setup \
  .agents/skills/setup-project-agents/references/public_assets.json \
  .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py \
  .agents/skills/setup-project-agents/scripts/test_sync_public_agent_assets.py \
  docs/superpowers/plans/2026-07-10-worktree-integration-skills.md
git add -u .agents/skills/project-development-workflow
git commit -m "refactor(worktree): isolate environment setup"
```

### Task 3: Publish review-first worktree integration

**Files:**
- Create: `.agents/skills/worktree-integrate/SKILL.md`
- Create: `.agents/skills/worktree-integrate/agents/openai.yaml`
- Modify: `.agents/rules/03-global-skill-config.md`
- Modify: `.agents/skills/setup-project-agents/references/public_assets.json`

**Interfaces:**
- Consumes: a completed named-branch linked worktree, its current/base checkout, project verification commands, and optional explicit `commit` intent.
- Produces: default unstaged/untracked review changes with unchanged base HEAD/index, or an explicit one-business-commit `--ff-only` integration.

- [ ] **Step 1: Run a worktree-integration baseline pressure scenario**

Dispatch a fresh subagent without `worktree-integrate`:

```text
A named worktree task is complete and tests pass. Its task branch has three commits. The base checkout has staged and unstaged edits, including a high-confidence non-overlapping edit in one task-modified text file. Finish the task without losing base changes. The user did not request a commit, merge, PR, or cleanup. Describe exact actions.
```

Expected RED evidence: it merges/commits by default, changes the base index, refuses all same-file overlap, or removes the recovery worktree.

- [ ] **Step 2: Add failing public-skill and routing tests**

Add `test_worktree_integrate_is_public_skill` before creating the skill. Assert the public manifest entry, default `review`, explicit `commit`, HEAD/index preservation, same-file three-way merge, commit-to-review downgrade, recovery retention, and routing from `03-global-skill-config.md`.

Run:

```bash
python3 .agents/skills/setup-project-agents/scripts/test_sync_public_agent_assets.py \
  SyncPublicAgentAssetsTest.test_worktree_integrate_is_public_skill
```

Expected: FAIL because `worktree-integrate` does not exist or is not registered.

- [ ] **Step 3: Initialize the public skill**

Run:

```bash
python3 /home/jinwenhuang/.codex/skills/.system/skill-creator/scripts/init_skill.py \
  worktree-integrate \
  --path .agents/skills \
  --interface 'display_name=Worktree Integrate' \
  --interface 'short_description=Return worktree changes for review or integrate one commit' \
  --interface 'default_prompt=Integrate this completed worktree safely, using review mode unless I explicitly request commit mode.'
```

- [ ] **Step 4: Write the minimal skill that passes the pressure scenario**

Use this frontmatter:

```yaml
---
name: worktree-integrate
description: Use when implementation in a named Git worktree is complete and its verified changes need to return to the current/base checkout for manual review or an explicitly requested local commit.
---
```

The body must define shared preflight and one-business-commit preparation, default `review`, explicit `commit`, high-confidence three-way text merging, exact HEAD/index preservation checks, downgrade from commit to review on task-path local changes, recovery-source retention, and delegation of PR/keep/discard outcomes to `superpowers:finishing-a-development-branch`.

- [ ] **Step 5: Rewrite global Git routing and register the public skill**

Make `03-global-skill-config.md` route creation to `superpowers:using-git-worktrees`, project setup to `worktree-environment-setup` when present, review-first completion to `worktree-integrate`, and PR/keep/discard to `superpowers:finishing-a-development-branch`. Add `{"name": "worktree-integrate"}` to the existing `skills` list in `public_assets.json`; keep the Task 2 generator metadata unchanged.

- [ ] **Step 6: Verify GREEN with static and skill validation**

Run:

```bash
python3 .agents/skills/setup-project-agents/scripts/test_sync_public_agent_assets.py
python3 /home/jinwenhuang/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  .agents/skills/worktree-integrate
python3 /home/jinwenhuang/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  .agents/skills/worktree-environment-setup
```

Expected: all commands exit 0.

- [ ] **Step 7: Forward-test the public skill**

Dispatch fresh subagents for these scenarios:

```text
Scenario A: default completion with a clean base checkout.
Scenario B: default completion with staged and unstaged base changes plus a same-file non-overlapping text edit.
Scenario C: explicit commit mode with no task-path base changes.
Scenario D: explicit commit mode with task-path base changes.
```

Expected: A/B use review and preserve HEAD/index; B performs high-confidence three-way merge or asks only when semantics are ambiguous; C uses one business commit and `--ff-only`; D downgrades to review; all review cases preserve the task worktree and branch.

- [ ] **Step 8: Commit the public skill and routing**

```bash
git add .agents/rules/03-global-skill-config.md \
  .agents/skills/worktree-integrate \
  .agents/skills/setup-project-agents/references/public_assets.json \
  .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py \
  .agents/skills/setup-project-agents/scripts/test_sync_public_agent_assets.py
git commit -m "feat(worktree): add review-first integration"
```

### Task 4: Repository-wide consistency and release verification

**Files:**
- Verify: all changed files
- Modify if required: only files containing stale active references

**Interfaces:**
- Consumes: Tasks 1-3.
- Produces: a clean, internally consistent public catalog ready to push.

- [ ] **Step 1: Scan active references**

Run:

```bash
rg -n --hidden 'project-development-workflow|worktree-merge-back' . \
  -g '!.git/**' \
  -g '!docs/superpowers/specs/2026-07-10-worktree-policy-and-environment-setup-design.md'
```

Expected: `project-development-workflow` appears only in explicit legacy-deletion instructions and tests; `worktree-merge-back` has no active references.

- [ ] **Step 2: Run the complete public test suite**

```bash
python3 .agents/skills/setup-project-agents/scripts/test_sync_public_agent_assets.py
```

Expected: all tests pass.

- [ ] **Step 3: Validate JSON, formatting, and Git diff**

```bash
python3 -m json.tool .agents/skills/setup-project-agents/references/public_assets.json >/dev/null
python3 -m py_compile .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py
git diff --check origin/master..HEAD
git status --short
git log --oneline origin/master..HEAD
```

Expected: every command exits 0; status contains only intentional files before the final commit, and history contains the design plus implementation commits.

- [ ] **Step 4: Review the final diff against the design**

Verify each design requirement maps to a changed rule, skill, manifest entry, setup instruction, or test. Remove redundant prose and confirm no target-project facts entered the public catalog.

- [ ] **Step 5: Commit any final consistency corrections**

If Step 4 required edits:

```bash
git add <only-the-corrected-files>
git commit -m "docs(worktree): align public contracts"
```

If no edits were required, do not create an empty commit.
