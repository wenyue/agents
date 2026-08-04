# WenYue SmartKit Rename Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the public plugin identity from `agents@wenyue-agents` to `smartkit@wenyue` while presenting the brand as `WenYue SmartKit`.

**Architecture:** Treat plugin identity, marketplace identity, and display branding as three explicit metadata fields and update every host manifest and installation document consistently. Preserve the repository URL `https://github.com/wenyue/agents` and the root `agents/` runtime-resource directory because neither is part of the approved rename.

**Tech Stack:** JSON plugin manifests, Markdown documentation, Python `unittest` contract tests.

## Global Constraints

- Public display name is exactly `WenYue SmartKit`.
- Plugin manifest name is exactly `smartkit`.
- Marketplace name is exactly `wenyue`.
- Installed plugin ID is exactly `smartkit@wenyue`.
- Preserve `https://github.com/wenyue/agents` until the remote repository is renamed separately.
- Preserve `agents/`, `"agents": "./agents/"`, and agent-asset terminology where they describe runtime resources rather than the former plugin identity.
- Preserve all pre-existing staged and unstaged user changes; do not commit.

---

### Task 1: Encode the new plugin identity in contract tests

**Files:**
- Modify: `tests/test_plugin_manifests.py`
- Modify: `tests/test_setup_source.py`
- Modify: `tests/test_setup_catalog.py`

**Interfaces:**
- Consumes: JSON manifests at `.codex-plugin/plugin.json`, `.cursor-plugin/plugin.json`, `plugin.json`, `.agents/plugins/marketplace.json`, `.cursor-plugin/marketplace.json`, and `.github/plugin/marketplace.json`; canonical source fixtures used by setup validation.
- Produces: Contract assertions and source fixtures for `smartkit`, `wenyue`, and `WenYue SmartKit`.

- [x] **Step 1: Replace the old manifest-name assertion and add marketplace identity assertions**

```python
self.assertEqual(manifest['name'], 'smartkit')

self.assertEqual(codex['name'], 'wenyue')
self.assertEqual(codex['interface']['displayName'], 'WenYue SmartKit')
self.assertEqual(codex['plugins'][0]['name'], 'smartkit')
```

For Cursor and Copilot marketplace manifests, assert top-level `name == 'wenyue'` and the first plugin `name == 'smartkit'`. For host plugin manifests that expose a display name, assert it is exactly `WenYue SmartKit`.

Update canonical source fixtures so native manifest `name` and catalog plugin `id` are `smartkit`. Keep runtime resource fields such as `"agents": "./agents/"` unchanged.

- [x] **Step 2: Run the focused test and verify the old metadata fails**

Run: `/home/jinwenhuang/.local/share/uv/python/cpython-3.11.14-linux-x86_64-gnu/bin/python3.11 -m unittest tests.test_plugin_manifests tests.test_setup_source`

Expected: FAIL because the manifests still contain `agents`, `wenyue-agents`, and `wenyue/agents`.

### Task 2: Rename manifests, marketplace metadata, and installation documentation

**Files:**
- Modify: `.codex-plugin/plugin.json`
- Modify: `.cursor-plugin/plugin.json`
- Modify: `plugin.json`
- Modify: `.agents/plugins/marketplace.json`
- Modify: `.cursor-plugin/marketplace.json`
- Modify: `.github/plugin/marketplace.json`
- Modify: `catalog/project-assets.json`
- Modify: `skills/setup-project-agents/scripts/agents_setup/source.py`
- Modify: `README.md`
- Modify: `docs/zh-CN/README.md`

**Interfaces:**
- Consumes: The identity contract established in Task 1.
- Produces: A cross-host plugin named `smartkit`, distributed through marketplace `wenyue`, displayed as `WenYue SmartKit`, and installed as `smartkit@wenyue`.

- [x] **Step 1: Update plugin manifests**

Set plugin `name` to `smartkit` in all three root manifests. Set `.codex-plugin/plugin.json` and `.cursor-plugin/plugin.json` display names to `WenYue SmartKit`. Preserve versions, source directories, repository URLs, descriptions, and runtime entry points.

- [x] **Step 2: Update marketplace manifests**

Set every marketplace top-level `name` to `wenyue`, every marketplace plugin entry `name` to `smartkit`, and the Codex marketplace `interface.displayName` to `WenYue SmartKit`. Preserve sources, policies, category, version, and descriptions.

- [x] **Step 3: Update English and Chinese installation documentation**

Use `WenYue SmartKit` for user-facing branding, `smartkit` when referring to the plugin identifier, `smartkit@wenyue` in install commands, and `wenyue` in marketplace update commands. Keep `codex plugin marketplace add wenyue/agents` and `copilot plugin marketplace add wenyue/agents` because those commands identify the current GitHub repository.

- [x] **Step 4: Update canonical setup identity validation**

Set `catalog.plugin.id` and both native manifest/catalog identity checks in `skills/setup-project-agents/scripts/agents_setup/source.py` to `smartkit`. Preserve the canonical repository URL and runtime root-field validation.

- [x] **Step 5: Re-run the focused manifest and source tests**

Run: `/home/jinwenhuang/.local/share/uv/python/cpython-3.11.14-linux-x86_64-gnu/bin/python3.11 -m unittest tests.test_plugin_manifests tests.test_setup_source`

Expected: PASS.

- [x] **Step 6: Search for stale public identity references**

Run: `rg -n --hidden --glob '!.git/**' --glob '!docs/superpowers/**' 'wenyue-agents|agents@wenyue-agents|# wenyue/agents' .`

Expected: no output. Current repository URLs such as `https://github.com/wenyue/agents` and marketplace-add source commands remain outside this old-identity pattern.

- [x] **Step 7: Run repository verification**

Run: `/home/jinwenhuang/.local/share/uv/python/cpython-3.11.14-linux-x86_64-gnu/bin/python3.11 -m unittest discover -s tests -p 'test_*.py'`

Expected: PASS.

Run: `git diff --check`

Expected: exit code 0 with no output.

- [x] **Step 8: Leave changes uncommitted for user review**

Do not alter the index or create a commit because the working tree contains pre-existing user changes.
