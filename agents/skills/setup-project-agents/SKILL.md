---
name: setup-project-agents
description: Use when initializing or updating a repository from the wenyue/agents public catalog.
---

# Setup Project Agents

Let the synchronization script maintain deterministic configuration. Use the LLM to choose
subagent models and generate the five repository-specific assets declared by this workflow.

## Ownership

- The script owns deterministic configuration for every supported platform.
- The LLM owns model selection and repository-specific Rule and Skill generation.

## Managed Assets

Generate these Rules from their public blueprints:

- [`20-project-tools.md`](https://github.com/wenyue/agents/blob/master/agents/blueprints/rules/20-project-tools.md)
- [`21-project-rules.md`](https://github.com/wenyue/agents/blob/master/agents/blueprints/rules/21-project-rules.md)
- [`22-project-structure.md`](https://github.com/wenyue/agents/blob/master/agents/blueprints/rules/22-project-structure.md)

Generate these Skills from their public blueprints:

- [`worktree-environment-setup`](https://github.com/wenyue/agents/blob/master/agents/blueprints/skills/worktree-environment-setup/SKILL.md)
- [`change-set-verification`](https://github.com/wenyue/agents/blob/master/agents/blueprints/skills/change-set-verification/SKILL.md)

## Reconciliation Workflow

1. From the target repository root, resolve one model-config path in the system temporary directory
   and retain it for the complete workflow:

   ```sh
   MODEL_CONFIG="$(python -c 'import os, tempfile; print(os.path.join(tempfile.gettempdir(), "setup-project-agent-models.json"))')"
   python .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py \
     --model-request "$MODEL_CONFIG"
   ```

   The script fetches
   `https://github.com/wenyue/agents/archive/refs/heads/master.zip`, synchronizes every
   catalog-declared platform, and writes the model request.

2. Fill every model field in `$MODEL_CONFIG`. Use each subagent's `required_intelligence` to select
   `model` for Codex, Cursor, and GitHub, plus `model_reasoning_effort` for Codex. Existing wrappers
   are not a value source.

3. Open and execute each public blueprint enumerated under Managed Assets. Generate Rules
   at `.agents/rules/<name>.md` and Skills at `.agents/skills/<name>/`. Use current repository
   evidence; previous content may be used as a reference during generation, but it is not a source
   of truth. Each blueprint owns its generation and validation.

4. Apply the completed model configuration after all generated files exist:

   ```sh
   python .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py \
     --model-config "$MODEL_CONFIG"
   ```

## Review Gate

Accept only generated assets that satisfy their public blueprint and preserve unrelated
target-owned files.

## Acceptance Gate

Every enumerated Rule and Skill must be complete, and every required model field must be resolved.

## Validation

Run the final check with the same temporary model configuration. The script checks that every
enumerated output exists and that deterministic configuration has no drift; each blueprint owns
content validation.

```sh
python .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py \
  --check --model-config "$MODEL_CONFIG"
```

Stop on any script or blueprint failure. Do not invoke a real model for validation.

## Output

Report the changed managed files and any unresolved model or blueprint blocker.
