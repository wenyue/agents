---
name: update-project-rules
description: >-
  Update repository agent rule sources and their platform wrappers. Use when Codex must sync
  shared/base rules with a reference project, refresh project-owned rules from current repository
  facts, update AGENTS.md, align Cursor/Claude/GitHub/Codex rule or agent wrappers, or reconcile
  MCP/runtime config that follows the shared agent configuration structure.
---

# Update Project Rules

Update rule sources first. Then align every entry file, wrapper, and runtime config that follows
from those sources.

## Core Rules

- Public assets listed in `public_assets.json` are mirrored directly from `wenyue/agents`;
  do not locally adapt them.
- Run `scripts/sync_public_agent_assets.py` before manually editing project-owned rules.
- Change public rules or public skills in `wenyue/agents` first, then sync target repositories.
- Treat `.agents/rules/<nn>-<name>.md` as the source of truth for project rules.
- Keep wrappers thin: platform metadata plus one `Apply @...` reference.

## Rule Ranges

- `00-*` through `09-*`: shared/global rules. When a reference project is supplied, copy or sync
  these from the reference unless the user explicitly says the current project is the source.
- `10-*` through `19-*`: shared/base rules, usually language-level defaults. Use a reference
  project heavily for structure and wording, but still verify the final content against the
  current repository's actual language, tooling, lint, build, and generated-file setup.
- `20-*` through `59-*`: project-owned rules. Update these from the current repository's actual
  tools, languages, modules, domains, packages, and verification workflows. Use a reference project
  only for structure or wording patterns.
- Other numbered ranges: follow the repository's own numbering policy. If none exists, treat them
  as project-owned.

## Workflow

1. Read `AGENTS.md`, then all applicable `00-*` through `09-*` rules.
2. Run the public sync script:
   `python3 .agents/skills/update-project-rules/scripts/sync_public_agent_assets.py`.
   Use `--source <path>` when `../agents` is not the correct source.
3. Review the script report for created, updated, deleted, unchanged, and skipped files.
4. Only after public sync, update project-owned rules from current repository evidence.

## Evidence Sources

Use current repository evidence for every project-owned rule and for any base rule that mentions
language tools or generated files. Prefer concrete files over assumptions, such as package
manifests, build and lint config, test directories, CI or script commands, MCP config, generated
file config, existing wrapper metadata, and the repository directory structure.

## Wrapper Maps

- Rule source `.agents/rules/<name>.md` maps to:
  - `.cursor/rules/<name>.mdc`
  - `.claude/rules/<name>.md`
  - `.github/instructions/<name>.instructions.md`
- Agent source `.agents/agents/<name>.md` maps to:
  - `.cursor/agents/<name>.md`
  - `.claude/agents/<name>.md`
  - `.codex/agents/<name>.toml`
  - `.github/agents/<name>.agent.md`
- MCP/runtime config uses the repository's shared platform files. Preserve platform schema
  differences and keep server intent aligned across platforms.
- Preserve required wrapper metadata or schema fields. Thin wrappers may keep platform metadata,
  but their reusable instruction body should be only the `Apply @...` reference.

## Validation

Run fresh checks before reporting completion:

```bash
python3 .agents/skills/update-project-rules/scripts/sync_public_agent_assets.py --check
python3 .agents/skills/update-project-rules/scripts/test_sync_public_agent_assets.py
```

## Output

- List changed files, or state that no edits were required.
- Summarize the public-sync result and any project-owned rule work done afterward.
- Report validation commands and whether language build/test commands were skipped.
