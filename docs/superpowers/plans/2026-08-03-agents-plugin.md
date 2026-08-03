# Agents Cross-Platform Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package `wenyue/agents` as a versioned Codex, Cursor, and GitHub Copilot plugin that exposes `setup-project-agents`, keeps project setup explicit, and provides a safe tool-maintenance workflow.

**Architecture:** `agents/` is both the plugin root and the single public runtime source. Three native plugin manifests expose its root-native `skills/` tree, while repository marketplaces point at `./agents`. `setup-project-agents` prefers the installed plugin checkout as its source, writes a catalog version into project configuration, and retains an immutable-release fallback for legacy project-local copies. Project hooks call a dedicated `manage-agent-tools` skill and only diagnose drift.

**Tech Stack:** Python 3.11 standard library, JSON/TOML configuration, POSIX shell, PowerShell, `unittest`, Codex/Cursor/Copilot plugin manifests.

## Global Constraints

- Plugin ID is exactly `agents`; marketplace/source name is exactly `wenyue-agents`; initial version is exactly `0.1.0`.
- `agents/` remains the sole English public source; `.agents/` remains this repository's curated runtime; `agents-zh/` is human-readable Simplified Chinese only.
- Plugin installation must not modify a project or register a global SessionStart hook.
- Every project still requires an explicit `setup-project-agents` invocation.
- SessionStart hooks may detect and report tool drift but must never install, upgrade, or trust tools automatically.
- The installed plugin source takes precedence over network retrieval; legacy network fallback must use `v0.1.0` or a 40-character commit, never `master`.
- Existing uncommitted work is preserved. Stage only the files listed by the current task and inspect `git diff --cached` before every commit.
- Use `/home/jinwenhuang/.local/share/uv/python/cpython-3.11.14-linux-x86_64-gnu/bin/python3.11` in this environment. The repository-wide test baseline currently has 167 passing tests and 9 unrelated `test_report_session_usage.py` errors caused by the stale `/home/jinwenhuang/work/wenyue_agents/agents/skills/report-session-usage/scripts/timing.py` path.
- Every completed change set must run the full repository test command and `git diff --check`.

## File Map

- `agents/.codex-plugin/plugin.json`: Codex plugin metadata and root-native Skill path.
- `.agents/plugins/marketplace.json`: Codex repository marketplace pointing at `./agents`.
- `agents/.cursor-plugin/plugin.json`: Cursor plugin metadata and root-native Skill path.
- `.cursor-plugin/marketplace.json`: Cursor repository marketplace pointing at `./agents`.
- `agents/plugin.json`: Copilot plugin metadata and root-native Skill path.
- `.github/plugin/marketplace.json`: Copilot repository marketplace pointing at `./agents`.
- `agents/skills/manage-agent-tools/`: owns recommended-tool policy, diagnostics, platform wrappers, and the explicit maintenance workflow.
- `agents/skills/setup-project-agents/`: owns deterministic project synchronization and plugin/local/legacy source selection.
- `agents/skills/setup-project-agents/references/public_assets.json`: owns public installation membership plus catalog identity and release revision.
- `agents/skills/setup-project-agents/assets/templates/project-config/agents.config.json`: owns managed project catalog metadata.
- `agents/skills/setup-project-agents/references/project-config.schema.json`: validates catalog metadata in target configuration.
- `tests/test_plugin_manifests.py`: validates all native plugin and marketplace contracts.
- `tests/test_public_agent_assets.py`: validates source resolution, catalog synchronization, tool ownership, and existing public installation behavior.
- `README.md` and `agents-zh/README.md`: document plugin installation, explicit project setup, and concise Hook trust behavior.

---

### Task 1: Add Native Plugin and Marketplace Manifests

**Files:**
- Create: `agents/.codex-plugin/plugin.json`
- Create: `.agents/plugins/marketplace.json`
- Create: `agents/.cursor-plugin/plugin.json`
- Create: `.cursor-plugin/marketplace.json`
- Create: `agents/plugin.json`
- Create: `.github/plugin/marketplace.json`
- Create: `tests/test_plugin_manifests.py`

**Interfaces:**
- Consumes: public Skills at `agents/skills/*/SKILL.md`.
- Produces: six JSON entry points with plugin ID `agents`, version `0.1.0`, root-native Skill path `./skills/`, and marketplace source `./agents`.

- [ ] **Step 1: Write the failing manifest contract tests**

Create `tests/test_plugin_manifests.py`:

```python
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_VERSION = '0.1.0'


def load_json(relative_path: str) -> dict:
    value = json.loads((REPO_ROOT / relative_path).read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise AssertionError(f'{relative_path} must contain an object')
    return value


class PluginManifestTest(unittest.TestCase):
    def test_native_plugin_manifests_share_identity_version_and_skills(self):
        for path in (
            'agents/.codex-plugin/plugin.json',
            'agents/.cursor-plugin/plugin.json',
            'agents/plugin.json',
        ):
            with self.subTest(path=path):
                manifest = load_json(path)
                self.assertEqual(manifest['name'], 'agents')
                self.assertEqual(manifest['version'], PLUGIN_VERSION)
                self.assertEqual(manifest['skills'], './skills/')
                self.assertNotIn('hooks', manifest)
                self.assertTrue((REPO_ROOT / 'agents' / manifest['skills']).is_dir())

    def test_codex_marketplace_points_at_repository_plugin_root(self):
        marketplace = load_json('.agents/plugins/marketplace.json')
        self.assertEqual(marketplace['name'], 'wenyue-agents')
        self.assertEqual(marketplace['interface']['displayName'], 'wenyue/agents')
        self.assertEqual(
            marketplace['plugins'],
            [{
                'name': 'agents',
                'source': {'source': 'local', 'path': './agents'},
                'policy': {
                    'installation': 'AVAILABLE',
                    'authentication': 'ON_INSTALL',
                },
                'category': 'Developer Tools',
            }],
        )

    def test_cursor_and_copilot_marketplaces_point_at_repository_root(self):
        for path in (
            '.cursor-plugin/marketplace.json',
            '.github/plugin/marketplace.json',
        ):
            with self.subTest(path=path):
                marketplace = load_json(path)
                self.assertEqual(marketplace['name'], 'wenyue-agents')
                self.assertEqual(marketplace['plugins'][0]['name'], 'agents')
                self.assertEqual(marketplace['plugins'][0]['source'], './agents')
                self.assertEqual(marketplace['plugins'][0]['version'], PLUGIN_VERSION)


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run the suite and verify the new tests fail because manifests are absent**

Run:

```sh
/home/jinwenhuang/.local/share/uv/python/cpython-3.11.14-linux-x86_64-gnu/bin/python3.11 \
  -m unittest discover -s tests -p 'test_*.py'
```

Expected: the new `PluginManifestTest` cases fail with `FileNotFoundError`; the existing 9 unrelated session-usage errors remain.

- [ ] **Step 3: Add the minimal Codex plugin and marketplace**

Create `agents/.codex-plugin/plugin.json`:

```json
{
  "name": "agents",
  "version": "0.1.0",
  "description": "Install and maintain shared project-agent workflows across repositories.",
  "author": {
    "name": "wenyue",
    "url": "https://github.com/wenyue"
  },
  "homepage": "https://github.com/wenyue/agents",
  "repository": "https://github.com/wenyue/agents",
  "keywords": ["coding-agents", "project-setup", "skills"],
  "skills": "./skills/",
  "interface": {
    "displayName": "wenyue/agents",
    "shortDescription": "Set up and maintain project agent tooling",
    "longDescription": "Install versioned workflows for project rules, skills, agents, hooks, and recommended-tool diagnostics.",
    "developerName": "wenyue",
    "category": "Developer Tools",
    "capabilities": ["Read", "Write"],
    "websiteURL": "https://github.com/wenyue/agents",
    "defaultPrompt": [
      "Use setup-project-agents to initialize this repository.",
      "Check and update this repository's agent assets."
    ]
  }
}
```

Create `.agents/plugins/marketplace.json`:

```json
{
  "name": "wenyue-agents",
  "interface": {
    "displayName": "wenyue/agents"
  },
  "plugins": [
    {
      "name": "agents",
      "source": {
        "source": "local",
        "path": "./agents"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Developer Tools"
    }
  ]
}
```

- [ ] **Step 4: Add the minimal Cursor plugin and marketplace**

Create `agents/.cursor-plugin/plugin.json`:

```json
{
  "name": "agents",
  "displayName": "wenyue/agents",
  "version": "0.1.0",
  "description": "Install and maintain shared project-agent workflows across repositories.",
  "author": {
    "name": "wenyue"
  },
  "homepage": "https://github.com/wenyue/agents",
  "repository": "https://github.com/wenyue/agents",
  "keywords": ["coding-agents", "project-setup", "skills"],
  "category": "developer-tools",
  "skills": "./skills/"
}
```

Create `.cursor-plugin/marketplace.json`:

```json
{
  "name": "wenyue-agents",
  "owner": {
    "name": "wenyue"
  },
  "metadata": {
    "description": "Cross-platform project agent workflows",
    "version": "0.1.0"
  },
  "plugins": [
    {
      "name": "agents",
      "source": "./agents",
      "version": "0.1.0",
      "description": "Install and maintain shared project-agent workflows across repositories."
    }
  ]
}
```

- [ ] **Step 5: Add the minimal Copilot plugin and marketplace**

Create `agents/plugin.json`:

```json
{
  "name": "agents",
  "version": "0.1.0",
  "description": "Install and maintain shared project-agent workflows across repositories.",
  "author": {
    "name": "wenyue",
    "url": "https://github.com/wenyue"
  },
  "homepage": "https://github.com/wenyue/agents",
  "repository": "https://github.com/wenyue/agents",
  "keywords": ["coding-agents", "project-setup", "skills"],
  "skills": "./skills/"
}
```

Create `.github/plugin/marketplace.json`:

```json
{
  "name": "wenyue-agents",
  "owner": {
    "name": "wenyue"
  },
  "metadata": {
    "description": "Cross-platform project agent workflows",
    "version": "0.1.0"
  },
  "plugins": [
    {
      "name": "agents",
      "source": "./agents",
      "version": "0.1.0",
      "description": "Install and maintain shared project-agent workflows across repositories."
    }
  ]
}
```

- [ ] **Step 6: Validate the Codex package and run the manifest tests**

Run:

```sh
/home/jinwenhuang/.local/share/uv/python/cpython-3.11.14-linux-x86_64-gnu/bin/python3.11 \
  /home/jinwenhuang/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py agents
/home/jinwenhuang/.local/share/uv/python/cpython-3.11.14-linux-x86_64-gnu/bin/python3.11 \
  -m unittest tests.test_plugin_manifests
```

Expected: the official local Codex validator exits `0`, and all `PluginManifestTest` cases pass.
Then run the repository-wide Python 3.11 command from Step 2 and confirm only the same 9 unrelated
session-usage errors remain.

- [ ] **Step 7: Commit only the plugin contract files**

```sh
git add -- agents/.codex-plugin/plugin.json .agents/plugins/marketplace.json \
  agents/.cursor-plugin/plugin.json .cursor-plugin/marketplace.json \
  agents/plugin.json .github/plugin/marketplace.json tests/test_plugin_manifests.py
git diff --cached --check
git commit -m "feat: package agents for three plugin hosts"
```

---

### Task 2: Give Tool Maintenance a Dedicated Shared Skill

**Files:**
- Create: `agents/skills/manage-agent-tools/SKILL.md`
- Create: `agents-zh/skills/manage-agent-tools/SKILL.md`
- Move: `agents/skills/setup-project-agents/scripts/check_recommended_tools.py` to `agents/skills/manage-agent-tools/scripts/check_recommended_tools.py`
- Move: `agents/skills/setup-project-agents/scripts/check_recommended_tools.sh` to `agents/skills/manage-agent-tools/scripts/check_recommended_tools.sh`
- Move: `agents/skills/setup-project-agents/scripts/check_recommended_tools.ps1` to `agents/skills/manage-agent-tools/scripts/check_recommended_tools.ps1`
- Move: `agents/skills/setup-project-agents/assets/templates/recommended-tools/*.json` to `agents/skills/manage-agent-tools/references/recommended-tools/*.json`
- Modify: `agents/skills/setup-project-agents/references/public_assets.json`
- Modify: `agents/skills/setup-project-agents/assets/templates/project-config/codex.hooks.json`
- Modify: `agents/skills/setup-project-agents/assets/templates/project-config/cursor.hooks.json`
- Modify: `agents/skills/setup-project-agents/assets/templates/project-config/copilot.tool-check.hooks.json`
- Modify: `tests/test_public_agent_assets.py`

**Interfaces:**
- Consumes: existing `Finding`, `check_policy`, `run_hook`, `check`, and `hook --force` behavior.
- Produces: shared Skill `manage-agent-tools`; project Hook commands under `.agents/skills/manage-agent-tools/scripts/`; policy lookup at `references/recommended-tools/<platform>.json`.

- [ ] **Step 1: Update tests first to declare the new owner**

Replace the module-level checker constant, add the policy-root constant beside it, and add the
method below inside the existing `SyncPublicAgentAssetsTest` class:

```python
MANAGE_AGENT_TOOLS_ROOT = REPO_ROOT / 'agents' / 'skills' / 'manage-agent-tools'
RECOMMENDED_TOOL_CHECKER = (
    MANAGE_AGENT_TOOLS_ROOT / 'scripts' / 'check_recommended_tools.py'
)
RECOMMENDED_TOOL_POLICIES = (
    MANAGE_AGENT_TOOLS_ROOT / 'references' / 'recommended-tools'
)
```

```python

    def test_manage_agent_tools_owns_checker_policy_and_project_hook_commands(self):
        public_config = sync.load_json(REPO_REFERENCES / 'public_assets.json')
        self.assertIn({'name': 'manage-agent-tools'}, public_config['skills'])
        for platform in ('codex', 'cursor', 'copilot'):
            self.assertTrue(
                (RECOMMENDED_TOOL_POLICIES / f'{platform}.json').is_file()
            )
        hook_templates = (
            REPO_TEMPLATES / 'project-config' / 'codex.hooks.json',
            REPO_TEMPLATES / 'project-config' / 'cursor.hooks.json',
            REPO_TEMPLATES / 'project-config' / 'copilot.tool-check.hooks.json',
        )
        for template in hook_templates:
            self.assertIn(
                '.agents/skills/manage-agent-tools/scripts/',
                template.read_text(encoding='utf-8'),
            )
```

- [ ] **Step 2: Run the suite and verify the ownership test fails**

Run the repository-wide Python 3.11 test command.

Expected: the new test fails because `manage-agent-tools` and its files do not exist; the 9 unrelated baseline errors remain.

- [ ] **Step 3: Move the existing checker, wrappers, and policies without changing behavior**

Use patch-based renames so the current Hook/multi-agent worktree edits move intact. Update `default_policy_path` in the moved Python file to:

```python
def default_policy_path(platform: str) -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / 'references'
        / 'recommended-tools'
        / f'{platform}.json'
    )
```

Update all three project Hook templates so their commands point to the corresponding entry point under:

```text
.agents/skills/manage-agent-tools/scripts/
```

Add `{"name": "manage-agent-tools"}` to `public_assets.json` immediately before `setup-project-agents` so the health-check runtime is installed before Hook templates are reconciled.

Replace every test fixture or assertion that reads
`REPO_TEMPLATES / 'recommended-tools' / <platform>.json` with
`RECOMMENDED_TOOL_POLICIES / <platform>.json`. Do not leave the old template directory as a
compatibility copy; the new Skill is the sole policy owner.

- [ ] **Step 4: Author the shared English Skill with write-skill**

Create `agents/skills/manage-agent-tools/SKILL.md`:

```markdown
---
name: manage-agent-tools
description: Use when checking, diagnosing, installing, or upgrading the supported agent platform, Superpowers, CodeGraph, or Tokscale.
---

# Manage Agent Tools

Diagnose the current platform's declared tool policy and apply user-approved fixes through the tool's original plugin manager or package manager. Complete when a fresh uncached check has no findings, or report every unresolved finding and why it remains.

## Ownership

- This Skill owns interactive diagnosis and user-approved tool maintenance.
- `references/recommended-tools/<platform>.json` owns target versions, detectors, and install or upgrade guidance.
- Project SessionStart Hooks may call the checker in `hook` mode; they report findings but never mutate tools.
- `setup-project-agents` owns project configuration and Hook installation, not third-party tool mutation.

## Workflow

1. Determine the active platform as `codex`, `cursor`, or `copilot` from the current runtime. If the runtime cannot be identified, ask the user for the platform and stop this turn.
2. Resolve the directory containing this active `SKILL.md` as `MANAGE_AGENT_TOOLS_ROOT`; do not assume a repository-local `.agents/` path.
3. Run `sh "$MANAGE_AGENT_TOOLS_ROOT/scripts/check_recommended_tools.sh" check --platform PLATFORM` on POSIX, or `& "$MANAGE_AGENT_TOOLS_ROOT/scripts/check_recommended_tools.ps1" check --platform PLATFORM` on Windows.
4. If the command exits `0`, report that the declared policy is satisfied and stop.
5. If the command exits `2`, report that diagnosis failed, include stderr, and do not attempt installation or upgrade.
6. If the command exits `1`, classify each finding as a missing tool, unreadable version, outdated version, required-value mismatch, or detector failure.
7. For each missing or outdated tool, inspect how it is installed. Use the active platform's plugin manager for Superpowers. Use the executable location and available package-manager metadata for CodeGraph and Tokscale.
8. Present the exact commands and affected tools before mutation. Ask the user to approve those commands and stop this turn.
9. After approval, execute only the approved commands. Do not replace one package manager with another when the original installation source is known.
10. Run the uncached check again. Report the satisfied tools, unresolved findings, commands executed, and any command that failed.

## Stop Conditions

- Stop before mutation when user approval is absent.
- Stop without mutation when installation provenance is ambiguous; report the candidate sources and request direction.
- Stop after an upgrade command fails twice for the same tool; report both failures and the next safe manual action.
- Do not edit platform trust stores. Hook trust remains an explicit platform action.

## Validation

- Confirm the final checker exit status.
- Confirm every executed command was included in the user's approval.
- Confirm SessionStart Hook mode performed no installation or upgrade command.

## Result

Report the platform, policy path, before and after findings, approved commands, command results, and unresolved work.
```

- [ ] **Step 5: Add the Simplified-Chinese mirror**

Create `agents-zh/skills/manage-agent-tools/SKILL.md`:

```markdown
---
name: manage-agent-tools
description: 当需要检查、诊断、安装或升级受支持的智能体平台、Superpowers、CodeGraph 或 Tokscale 时使用。
---

# 管理智能体工具

诊断当前平台声明的工具策略，并通过工具原本的插件管理器或包管理器应用经用户批准的修复。全新无缓存检查不再报告发现项时任务完成；否则报告每个尚未解决的发现项及其原因。

## 归属

- 本 Skill 负责交互式诊断，以及经用户批准的工具维护。
- `references/recommended-tools/<platform>.json` 负责目标版本、检测器以及安装或升级指引。
- 项目 SessionStart Hook 可以用 `hook` 模式调用检查器；它只报告发现项，绝不修改工具。
- `setup-project-agents` 负责项目配置和 Hook 安装，不负责修改第三方工具。

## 工作流

1. 根据当前运行时将活跃平台确定为 `codex`、`cursor` 或 `copilot`。如果无法识别运行时，请用户指定平台，并结束本轮。
2. 将当前活跃 `SKILL.md` 所在目录解析为 `MANAGE_AGENT_TOOLS_ROOT`；不要假设 Skill 位于仓库本地的 `.agents/` 路径。
3. 在 POSIX 上运行 `sh "$MANAGE_AGENT_TOOLS_ROOT/scripts/check_recommended_tools.sh" check --platform PLATFORM`；在 Windows 上运行 `& "$MANAGE_AGENT_TOOLS_ROOT/scripts/check_recommended_tools.ps1" check --platform PLATFORM`。
4. 如果命令以 `0` 退出，报告声明的策略已满足，然后停止。
5. 如果命令以 `2` 退出，报告诊断失败并包含 stderr；不要尝试安装或升级。
6. 如果命令以 `1` 退出，将每个发现项分类为工具缺失、版本不可读、版本过旧、必需值不匹配或检测器失败。
7. 对每个缺失或过旧的工具，检查它的安装来源。Superpowers 使用活跃平台的插件管理器；CodeGraph 和 Tokscale 使用可执行文件位置及可用的包管理器元数据。
8. 修改前展示确切命令和受影响工具。请用户批准这些命令，并结束本轮。
9. 获得批准后，只执行已批准的命令。已知原始安装来源时，不要改用另一种包管理器。
10. 再次执行无缓存检查。报告已满足的工具、尚未解决的发现项、已执行命令，以及任何失败命令。

## 停止条件

- 未获得用户批准时，在修改前停止。
- 安装来源存在歧义时，不进行修改；报告候选来源并请求用户决定。
- 同一工具的升级命令失败两次后停止；报告两次失败和下一项安全的手动操作。
- 不要编辑平台信任存储。Hook 信任仍然必须由用户执行明确的平台操作。

## 验证

- 确认最终检查器退出状态。
- 确认执行的每条命令都包含在用户批准范围内。
- 确认 SessionStart Hook 模式没有执行安装或升级命令。

## 结果

报告平台、策略路径、修改前后的发现项、已批准命令、命令结果，以及尚未完成的工作。
```

- [ ] **Step 6: Run the suite and validate checker CLI behavior**

Run the repository-wide Python 3.11 test command.

Then run:

```sh
sh agents/skills/manage-agent-tools/scripts/check_recommended_tools.sh \
  check --platform codex
```

Expected: ownership and existing checker tests pass. The representative CLI exits `0` or `1` with structured diagnostics, not `2`; it performs no mutation. The 9 unrelated session-usage errors remain in the full suite.

- [ ] **Step 7: Commit the ownership migration**

```sh
git add -- agents/skills/manage-agent-tools agents-zh/skills/manage-agent-tools \
  agents/skills/setup-project-agents/references/public_assets.json \
  agents/skills/setup-project-agents/assets/templates/project-config/codex.hooks.json \
  agents/skills/setup-project-agents/assets/templates/project-config/cursor.hooks.json \
  agents/skills/setup-project-agents/assets/templates/project-config/copilot.tool-check.hooks.json \
  agents/skills/setup-project-agents/scripts/check_recommended_tools.py \
  agents/skills/setup-project-agents/scripts/check_recommended_tools.sh \
  agents/skills/setup-project-agents/scripts/check_recommended_tools.ps1 \
  agents/skills/setup-project-agents/assets/templates/recommended-tools \
  tests/test_public_agent_assets.py
git diff --cached --check
git commit -m "feat: add explicit agent tool maintenance workflow"
```

---

### Task 3: Prefer Installed Plugin Sources and Pin Legacy Fallbacks

**Files:**
- Modify: `agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py`
- Create: `agents/skills/setup-project-agents/scripts/sync_public_agent_assets.sh`
- Create: `agents/skills/setup-project-agents/scripts/sync_public_agent_assets.ps1`
- Modify: `agents/skills/setup-project-agents/references/public_assets.json`
- Modify: `tests/test_public_agent_assets.py`

**Interfaces:**
- Produces: `_public_source_root(path: Path) -> Path`, `validate_source_root(path: Path) -> Path`, `find_plugin_source(installed_skill_root: Path) -> Path | None`, and `resolve_source(public_config, installed_skill_root, explicit_source_root=None) -> Path`.
- CLI produces: `--source-root PATH` override for development and testing.

- [ ] **Step 1: Replace archive-only source tests with precedence and immutability tests**

Add these methods inside the existing `SyncPublicAgentAssetsTest` class and update former
archive-only expectations:

```python
    def test_resolve_source_prefers_explicit_validated_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / 'source'
            skill = source / 'agents' / 'skills' / 'setup-project-agents'
            (skill / 'references').mkdir(parents=True)
            (skill / 'references' / 'public_assets.json').write_text('{}\n')
            result = sync.resolve_source({}, REPO_SKILL_ROOT, source)
        self.assertEqual(result, source.resolve())

    def test_resolve_source_finds_repository_plugin_root_without_fetching(self):
        with mock.patch.object(sync, '_fetch_archive_source') as fetch:
            result = sync.resolve_source(
                sync.load_json(REPO_REFERENCES / 'public_assets.json'),
                REPO_SKILL_ROOT,
            )
        self.assertEqual(result, (REPO_ROOT / 'agents').resolve())
        fetch.assert_not_called()

    def test_resolve_source_finds_installed_plugin_with_arbitrary_cache_name(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin = Path(temp_dir) / 'cache-entry-42'
            skill = plugin / 'skills' / 'setup-project-agents'
            (skill / 'references').mkdir(parents=True)
            (skill / 'references' / 'public_assets.json').write_text('{}\n')
            with mock.patch.object(sync, '_fetch_archive_source') as fetch:
                result = sync.resolve_source({}, skill)
        self.assertEqual(result, plugin.resolve())
        fetch.assert_not_called()

    def test_resolve_source_rejects_invalid_explicit_source_before_fetch(self):
        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.object(
            sync, '_fetch_archive_source'
        ) as fetch:
            with self.assertRaises(sync.SyncError):
                sync.resolve_source({}, REPO_SKILL_ROOT, Path(temp_dir))
        fetch.assert_not_called()

    def test_source_archive_url_requires_release_tag_or_commit(self):
        with self.assertRaises(sync.SyncError):
            sync._source_archive_url({
                'source_repo': 'https://github.com/wenyue/agents',
                'source_ref': 'master',
            })
        self.assertEqual(
            sync._source_archive_url({
                'source_repo': 'https://github.com/wenyue/agents',
                'source_ref': 'v0.1.0',
            }),
            'https://github.com/wenyue/agents/archive/v0.1.0.zip',
        )
```

Replace `test_parser_rejects_local_source_argument` with:

```python
    def test_parser_accepts_source_root_and_rejects_obsolete_source(self):
        parser = sync.build_parser()
        self.assertEqual(
            parser.parse_args(['--source-root', 'local-agents']).source_root,
            Path('local-agents'),
        )
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            parser.parse_args(['--source', 'local-agents'])
```

In each existing archive fallback test, create
`legacy_skill_root = root / 'legacy' / 'setup-project-agents'`, pass it as the second argument to
`resolve_source`, and patch `_source_archive_url` to return `archive.resolve().as_uri()`. For example,
replace `source = sync.resolve_source(public_config)` with:

```python
with mock.patch.object(
    sync,
    '_source_archive_url',
    return_value=archive.resolve().as_uri(),
):
    source = sync.resolve_source(public_config, legacy_skill_root)
```

Apply the same signature update to `first` and `second` in
`test_resolve_source_refetches_archive_every_time`. Use
`{'source_repo': 'https://github.com/wenyue/agents', 'source_ref': 'v0.1.0'}` as the config in all
three archive tests; `source_archive_url` is no longer a supported public escape hatch.

- [ ] **Step 2: Run the suite and verify the new source tests fail**

Run the repository-wide Python 3.11 test command.

Expected: new source-resolution tests fail on missing signatures/options; the 9 unrelated baseline errors remain.

- [ ] **Step 3: Implement validated source discovery and immutable archive URLs**

Add this minimal implementation near the existing source functions:

```python
_RELEASE_REF_PATTERN = re.compile(r'^v[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$')
_COMMIT_REF_PATTERN = re.compile(r'^[0-9a-fA-F]{40}$')


def _public_source_root(path: Path) -> Path:
    root = path.expanduser().resolve()
    for candidate in (root, root / _PUBLIC_SOURCE_DIRECTORY):
        manifest = (
            candidate
            / 'skills'
            / 'setup-project-agents'
            / 'references'
            / 'public_assets.json'
        )
        if manifest.is_file():
            return candidate
    raise SyncError(f'Public source is missing setup-project-agents: {root}')


def validate_source_root(path: Path) -> Path:
    root = path.expanduser().resolve()
    _public_source_root(root)
    return root


def find_plugin_source(installed_skill_root: Path) -> Path | None:
    installed = installed_skill_root.resolve()
    for candidate in installed.parents:
        try:
            public_root = _public_source_root(candidate)
        except SyncError:
            continue
        if (public_root / 'skills' / 'setup-project-agents').resolve() == installed:
            return validate_source_root(candidate)
    return None


def resolve_source(
    public_config: dict[str, Any],
    installed_skill_root: Path,
    explicit_source_root: Path | None = None,
) -> Path:
    if explicit_source_root is not None:
        return validate_source_root(explicit_source_root)
    plugin_source = find_plugin_source(installed_skill_root)
    if plugin_source is not None:
        return plugin_source
    return _fetch_archive_source(public_config)
```

Remove `_DEFAULT_SOURCE_REF` and the `source_archive_url` branch. Replace `_source_archive_url`
with the immutable-ref implementation below:

```python
def _source_archive_url(public_config: dict[str, Any]) -> str:
    repo = public_config.get('source_repo')
    if not isinstance(repo, str) or not repo:
        raise SyncError('public_assets.json requires source_repo')
    ref = public_config.get('source_ref')
    if not isinstance(ref, str) or not (
        _RELEASE_REF_PATTERN.fullmatch(ref) or _COMMIT_REF_PATTERN.fullmatch(ref)
    ):
        raise SyncError('source_ref must be a release tag or 40-character commit')
    encoded_ref = urllib.parse.quote(ref, safe='')
    return f'{repo.rstrip("/")}/archive/{encoded_ref}.zip'
```

Add `--source-root` as `type=Path` to `build_parser`, and call:

```python
source_root = resolve_source(
    installed_config,
    installed_skill_root,
    args.source_root,
)
```

Set `source_ref` in `public_assets.json` to `v0.1.0`.

Replace the five hard-coded `source_root / _PUBLIC_SOURCE_DIRECTORY` lookups in archive validation,
`_public_skill_source`, rule copying, agent-prompt copying, and `main` with
`_public_source_root(source_root)` (or `_public_source_root(context.source_root)`) before appending
`skills`, `rules`, or `agents`. This keeps existing repository/archive fixtures valid while also
supporting an installed plugin whose cache directory is not literally named `agents`.

- [ ] **Step 4: Add paired platform entry points for the shared setup workflow**

Create `sync_public_agent_assets.sh`:

```sh
#!/bin/sh
set -eu
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$script_dir/sync_public_agent_assets.py" "$@"
```

Create `sync_public_agent_assets.ps1`:

```powershell
$ErrorActionPreference = 'Stop'
$scriptPath = Join-Path $PSScriptRoot 'sync_public_agent_assets.py'
python $scriptPath @args
exit $LASTEXITCODE
```

- [ ] **Step 5: Run the suite and exercise the local plugin source path**

Run the repository-wide Python 3.11 test command.

Then run:

```sh
sh agents/skills/setup-project-agents/scripts/sync_public_agent_assets.sh --help
```

Expected: all source-resolution and parser tests pass; help includes `--source-root`; no network is accessed; the 9 unrelated baseline errors remain.

- [ ] **Step 6: Commit only source-selection files**

```sh
git add -- agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py \
  agents/skills/setup-project-agents/scripts/sync_public_agent_assets.sh \
  agents/skills/setup-project-agents/scripts/sync_public_agent_assets.ps1 \
  agents/skills/setup-project-agents/references/public_assets.json \
  tests/test_public_agent_assets.py
git diff --cached --check
git commit -m "feat: sync projects from installed plugin releases"
```

---

### Task 4: Record the Synchronized Catalog Version

**Files:**
- Modify: `agents/skills/setup-project-agents/references/public_assets.json`
- Modify: `agents/skills/setup-project-agents/assets/templates/project-config/agents.config.json`
- Modify: `agents/skills/setup-project-agents/references/project-config.schema.json`
- Modify: `tests/test_public_agent_assets.py`
- Modify: `tests/test_plugin_manifests.py`

**Interfaces:**
- Produces: managed `.agents/config.json.catalog` object `{id, version, revision}`.
- Consumes: plugin version `0.1.0` and release revision `v0.1.0`.

- [ ] **Step 1: Write failing version-alignment and synchronization tests**

Add this method inside `PluginManifestTest` in `tests/test_plugin_manifests.py`:

```python
    def test_public_catalog_matches_native_plugin_version(self):
        public = load_json(
            'agents/skills/setup-project-agents/references/public_assets.json'
        )
        self.assertEqual(
            public['catalog'],
            {'id': 'agents', 'version': PLUGIN_VERSION, 'revision': 'v0.1.0'},
        )
```

Add these methods inside `SyncPublicAgentAssetsTest` in
`tests/test_public_agent_assets.py`:

```python
    def test_agents_config_template_records_managed_catalog_version(self):
        template = json.loads(
            (
                REPO_TEMPLATES
                / 'project-config'
                / 'agents.config.json'
            ).read_text(encoding='utf-8')
        )
        self.assertEqual(
            template['catalog'],
            {'id': 'agents', 'version': '0.1.0', 'revision': 'v0.1.0'},
        )

    def test_agents_config_schema_requires_catalog_identity(self):
        schema = json.loads(
            (REPO_REFERENCES / 'project-config.schema.json').read_text(
                encoding='utf-8'
            )
        )
        catalog = schema['properties']['catalog']
        self.assertEqual(catalog['required'], ['id', 'version', 'revision'])
        self.assertFalse(catalog['additionalProperties'])
```

In `test_agents_project_config_template_preserves_project_owned_fields`, add this stale value to
the JSON object written to the target:

```python
'catalog': {
    'id': 'agents',
    'version': '0.0.1',
    'revision': 'v0.0.1',
},
```

After the existing `project_owned` assertion, add:

```python
self.assertEqual(
    result['catalog'],
    {'id': 'agents', 'version': '0.1.0', 'revision': 'v0.1.0'},
)
```

This reuses the existing reconciliation fixture, which already proves that unknown target-owned
fields and external Skill declarations survive managed template updates.

- [ ] **Step 2: Run the suite and verify catalog tests fail**

Run the repository-wide Python 3.11 test command.

Expected: catalog tests fail because catalog metadata is absent; the 9 unrelated baseline errors remain.

- [ ] **Step 3: Add the catalog identity to public and project manifests**

Add to the top of `public_assets.json` after `source_ref`:

```json
"catalog": {
  "id": "agents",
  "version": "0.1.0",
  "revision": "v0.1.0"
},
```

Change `agents.config.json` to:

```json
{
  "$schema": "skills/setup-project-agents/references/project-config.schema.json",
  "version": 1,
  "catalog": {
    "id": "agents",
    "version": "0.1.0",
    "revision": "v0.1.0"
  }
}
```

Add this schema property:

```json
"catalog": {
  "type": "object",
  "required": ["id", "version", "revision"],
  "properties": {
    "id": {"const": "agents"},
    "version": {"type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"},
    "revision": {"type": "string", "minLength": 1}
  },
  "additionalProperties": false
}
```

- [ ] **Step 4: Run the suite and verify drift behavior**

Run the repository-wide Python 3.11 test command.

Expected: catalog alignment, preservation, and repair tests pass; the same 9 unrelated baseline errors remain.

- [ ] **Step 5: Commit the catalog contract**

```sh
git add -- agents/skills/setup-project-agents/references/public_assets.json \
  agents/skills/setup-project-agents/assets/templates/project-config/agents.config.json \
  agents/skills/setup-project-agents/references/project-config.schema.json \
  tests/test_public_agent_assets.py tests/test_plugin_manifests.py
git diff --cached --check
git commit -m "feat: record synchronized agent catalog versions"
```

---

### Task 5: Update Setup Workflow and Public Documentation

**Files:**
- Modify: `agents/skills/setup-project-agents/SKILL.md`
- Modify: `agents-zh/skills/setup-project-agents/SKILL.md`
- Modify: `README.md`
- Modify: `agents-zh/README.md`

**Interfaces:**
- Consumes: paired sync entry points, plugin marketplaces, `manage-agent-tools`, and catalog metadata.
- Produces: one concise installation and update path for each platform; one explicit per-project setup path.

- [ ] **Step 1: Rewrite setup commands around the active Skill root**

In the English and Chinese setup Skills, replace direct assumptions about `.agents/skills/setup-project-agents` with this executable rule:

```text
Resolve the directory containing the active setup-project-agents SKILL.md. On POSIX run its
scripts/sync_public_agent_assets.sh entry point; on Windows run
scripts/sync_public_agent_assets.ps1. Keep one model-config path for both stages.
```

Use these POSIX examples in the English source and mirror the commands unchanged in Chinese:

```sh
MODEL_CONFIG="$(python -c 'import os, tempfile; print(os.path.join(tempfile.gettempdir(), "setup-project-agent-models.json"))')"
sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/sync_public_agent_assets.sh" \
  --model-request "$MODEL_CONFIG"

sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/sync_public_agent_assets.sh" \
  --model-config "$MODEL_CONFIG"

sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/sync_public_agent_assets.sh" \
  --check --model-config "$MODEL_CONFIG"
```

State that `SETUP_PROJECT_AGENTS_ROOT` is derived from the Skill file the host loaded; never persist a machine-specific path.

- [ ] **Step 2: Replace README onboarding with plugin-first installation**

Replace the current `## New Project Setup` and `## Review Project Hooks` sections in `README.md`
with this exact content:

````markdown
## Install the Plugin

Install `agents` once for the host you use.

Codex:

```sh
codex plugin marketplace add wenyue/agents
codex plugin add agents@wenyue-agents
```

Cursor: add `https://github.com/wenyue/agents` as a plugin source, then install `agents`.

GitHub Copilot CLI:

```sh
copilot plugin marketplace add wenyue/agents
copilot plugin install agents@wenyue-agents
```

Installing the plugin only makes its Skills available; it does not modify repositories. Open each
target repository and ask the installed plugin to use `setup-project-agents`. Run that Skill again
whenever you want to synchronize the repository with the installed catalog version.

## Review Project Hooks

`setup-project-agents` installs a project-health `sessionStart` Hook for each supported host. The
Hook checks recommended tools and effective runtime requirements at most once per project per day;
it reports drift but never installs, upgrades, or trusts tools. Review the command using the host's
normal trust flow before allowing it to run.

| Agent | Project Hook | Required user action |
| --- | --- | --- |
| Codex | `.codex/hooks.json` | Start `codex`, enter `/hooks`, inspect the project Hook, and trust its exact definition. |
| Cursor | `.cursor/hooks.json` | Open the repository as a trusted workspace and inspect the Hook under `Cursor Settings > Hooks`. |
| GitHub Copilot | `.github/hooks/*.json` | Start `copilot` in the repository and accept the prompt to trust the current directory. |

Hook support is enabled explicitly for all three hosts. Multi-agent support is not force-enabled by
project configuration; the health check validates each host's effective default state and reports
when it has been disabled.
````

- [ ] **Step 3: Update the Simplified-Chinese README mirror**

Replace the current `## 审查项目 Hook` section in `agents-zh/README.md`, and insert the installation
section immediately before it, using this exact content:

````markdown
## 安装插件

为你使用的平台安装一次 `agents`。

Codex：

```sh
codex plugin marketplace add wenyue/agents
codex plugin add agents@wenyue-agents
```

Cursor：将 `https://github.com/wenyue/agents` 添加为插件源，然后安装 `agents`。

GitHub Copilot CLI：

```sh
copilot plugin marketplace add wenyue/agents
copilot plugin install agents@wenyue-agents
```

安装插件只会让平台能够使用其中的 Skill，不会修改任何仓库。打开每个目标仓库，并要求已安装
的插件使用 `setup-project-agents`。需要将仓库同步到已安装的目录版本时，再次运行该 Skill。

## 审查项目 Hook

`setup-project-agents` 会为每个受支持的平台安装一个项目健康检查 `sessionStart` Hook。该 Hook
每个项目每天最多检查一次推荐工具和有效运行时要求；它只报告漂移，绝不安装、升级或信任
工具。允许运行前，请通过平台的正常信任流程审查命令。

| 智能体 | 项目 Hook | 用户需要执行的操作 |
| --- | --- | --- |
| Codex | `.codex/hooks.json` | 启动 `codex`，输入 `/hooks`，检查项目 Hook，并信任其当前的精确定义。 |
| Cursor | `.cursor/hooks.json` | 将仓库作为受信任工作区打开，然后在 `Cursor Settings > Hooks` 中检查该 Hook。 |
| GitHub Copilot | `.github/hooks/*.json` | 在仓库中启动 `copilot`，并在提示时确认信任当前目录。 |

三个平台都显式启用 Hook 支持。项目配置不会强制启用多智能体能力；健康检查会验证各平台的
有效默认状态，并在它被禁用时发出报告。
````

- [ ] **Step 4: Review complete Skills and documentation without the diff**

Read both complete Skill pairs and README files. Confirm:

- setup begins from an installed plugin and still supports project-local legacy execution;
- all executable paths are derived, not machine-specific;
- tool mutation belongs only to `manage-agent-tools`;
- plugin installation is not described as project setup;
- English and Chinese commands and behavioral gates match.

- [ ] **Step 5: Run the repository-wide checks**

Run:

```sh
/home/jinwenhuang/.local/share/uv/python/cpython-3.11.14-linux-x86_64-gnu/bin/python3.11 \
  -m unittest discover -s tests -p 'test_*.py'
git diff --check
```

Expected: 167+ public/plugin tests pass; only the 9 pre-existing absolute-path errors in `test_report_session_usage.py` remain; `git diff --check` exits `0`.

- [ ] **Step 6: Commit only documentation and setup workflow files**

```sh
git add -- README.md agents-zh/README.md \
  agents/skills/setup-project-agents/SKILL.md \
  agents-zh/skills/setup-project-agents/SKILL.md
git diff --cached --check
git commit -m "docs: document plugin-first project setup"
```

---

### Task 6: Final Cross-Platform Contract Verification

**Files:**
- No file changes expected. If verification exposes a regression, return to the task that owns the
  failing file and repeat that task's test, implementation, and commit cycle.

**Interfaces:**
- Consumes: all manifests, Skills, source selection, catalog metadata, generated project assets, and docs.
- Produces: one verified change set with no plugin-specific or public-sync regressions.

- [ ] **Step 1: Validate Codex plugin structure with the plugin-creator validator**

Run:

```sh
/home/jinwenhuang/.local/share/uv/python/cpython-3.11.14-linux-x86_64-gnu/bin/python3.11 \
  /home/jinwenhuang/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py agents
```

Expected: exit `0`, with no incomplete manifest values or missing Skill root. On any nonzero exit,
record the validator output and return to Task 1; do not weaken the manifest contract during final
verification.

- [ ] **Step 2: Run all repository verification**

Run:

```sh
/home/jinwenhuang/.local/share/uv/python/cpython-3.11.14-linux-x86_64-gnu/bin/python3.11 \
  -m unittest discover -s tests -p 'test_*.py'
git diff --check
```

Expected: no failures in `test_plugin_manifests.py` or `test_public_agent_assets.py`; only the 9 known unrelated `test_report_session_usage.py` path errors remain; diff integrity passes.

- [ ] **Step 3: Audit mutation boundaries**

Run:

```sh
rg -n "install|upgrade|marketplace add|plugin add|npm install" \
  agents/skills/manage-agent-tools \
  agents/skills/setup-project-agents/assets/templates/project-config
```

Expected: install and upgrade commands appear only in interactive Skill guidance or policy guidance; no SessionStart Hook template directly executes them.

- [ ] **Step 4: Audit the final staged scope before the final commit**

```sh
git status --short
git diff --cached --name-only
git diff --check
```

Expected: no unrelated file is staged, conflict markers are absent, and pre-existing unrelated work remains preserved.

- [ ] **Step 5: Report the release prerequisite**

Report that remote legacy fallback points to `v0.1.0`; it becomes externally usable only after the maintainer creates and publishes that tag. Do not create or push the tag without an explicit user request.
