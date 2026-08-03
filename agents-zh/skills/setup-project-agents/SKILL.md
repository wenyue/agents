---
name: setup-project-agents
description: 从 wenyue/agents 公共目录初始化或更新仓库时使用。
---

# 设置项目 Agent

同步确定性的 Agent 配置，选择 Subagent 模型，并生成本流程声明的五个仓库特有资产。

从已安装插件提供的活跃 Skill 开始。如果平台加载的是之前安装在项目内的副本，该副本仍可作为
兼容旧流程的入口。

模板托管的项目配置为所有开发者提供一致的仓库默认值。脚本执行部分深度合并：模板字段覆盖偏差，
模板未声明的字段保持不变，常规同步会自动修复缺失或过期的托管值。用户配置不属于本流程。

## 所有权

- 脚本负责所有受支持平台的确定性配置。
- 字面量模板负责项目配置值及平台原生启动 Hook；Python 只包含通用的协调逻辑。
- 公共清单负责声明公共包必需的第三方 Skill。
- 公共清单负责在 `.agents/config.json` 中记录的目录身份和版本。
- 目标仓库负责在 `.agents/config.json` 中声明可选的第三方 Skill；脚本负责获取并协调所有
  公共及项目声明。
- LLM 负责模型选择，以及仓库特有 Rule 和 Skill 的生成。
- `manage-agent-tools` 负责交互式工具诊断，以及经用户批准的安装或升级；项目启动 Hook 只报告
  漂移，绝不修改工具。
- 每个启动 Hook 按项目、按本地日期检查一次当前平台的推荐工具和策略声明的运行时实际生效值。
  它只分析声明的检测命令输出，不直接解析项目配置或用户配置。发现问题时，Agent 先停止当前任务
  并询问是否使用 `manage-agent-tools`；用户回复后即可继续。

## 托管资产

根据以下公共蓝图生成 Rule：

- [`20-project-tools.md`](https://github.com/wenyue/agents/blob/master/agents/blueprints/rules/20-project-tools.md)
- [`21-project-rules.md`](https://github.com/wenyue/agents/blob/master/agents/blueprints/rules/21-project-rules.md)
- [`22-project-structure.md`](https://github.com/wenyue/agents/blob/master/agents/blueprints/rules/22-project-structure.md)

根据以下公共蓝图生成 Skill：

- [`worktree-environment-setup`](https://github.com/wenyue/agents/blob/master/agents/blueprints/skills/worktree-environment-setup/SKILL.md)
- [`change-set-verification`](https://github.com/wenyue/agents/blob/master/agents/blueprints/skills/change-set-verification/SKILL.md)

## 项目第三方 Skill

公共包第三方 Skill 会自动安装。仓库只在 `.agents/config.json` 中声明项目额外选择的 Skill；
不要重复声明公共包 Skill：

```json
{
  "version": 1,
  "skills": {
    "external": [
      {
        "name": "example-skill",
        "repository": "owner/repository",
        "ref": "main",
        "path": "skills/example-skill"
      }
    ]
  }
}
```

每项公共或项目声明负责完整的 `.agents/skills/<name>/` 目录。同步时，脚本会从指定的
GitHub 仓库、ref 和路径整体替换该目录，包括覆盖本地修改、删除上游已经移除的文件。删除项目
声明不会删除已经安装的目录。

写入任何公共资产或第三方 Skill 前，脚本会先下载并验证所有公共及项目来源。如果某个来源
失败，且目标仓库没有可用的旧版本，同步会在应用任何变更前终止。如果已安装可用的旧版本，
脚本会保留旧版本、继续同步其余内容并报告 warning；`--check` 会报告同一 warning，并以状态码
1 退出。

## 协调流程

1. 在目标仓库根目录，将当前活跃的 `setup-project-agents` `SKILL.md` 所在目录解析为
   `SETUP_PROJECT_AGENTS_ROOT`。该路径必须从平台加载的 Skill 文件推导；不要假设 Skill 位于
   仓库本地的 `.agents/` 路径，也不要持久化特定机器的路径。在 POSIX 上运行其
   `scripts/sync_public_agent_assets.sh` 入口；在 Windows 上运行
   `scripts/sync_public_agent_assets.ps1`。在系统临时目录中解析一个模型配置路径，并为两个阶段保留该路径：

   ```sh
   MODEL_CONFIG="$(python -c 'import os, tempfile; print(os.path.join(tempfile.gettempdir(), "setup-project-agent-models.json"))')"
   sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/sync_public_agent_assets.sh" \
     --model-request "$MODEL_CONFIG"
   ```

   该入口使用包含活跃 Skill 的已安装插件或仓库目录。项目本地旧版副本会获取其固定的目录源。
   它会同步公共目录声明的所有平台，并写出模型请求。

2. 填写 `$MODEL_CONFIG` 中的全部模型字段。根据每个 Subagent 的 `required_intelligence`，为
   Codex、Cursor 和 GitHub 选择 `model`，并为 Codex 选择 `model_reasoning_effort`。现有
   Wrapper 不是取值来源。

3. 依次打开并执行“托管资产”中枚举的公共蓝图。Rule 输出到 `.agents/rules/<name>.md`，Skill
   输出到 `.agents/skills/<name>/`。生成每条 Rule 时使用 `write-rule`，生成每个 Skill 时使用
   `write-skill`。生成内容以目标仓库的当前证据为准；旧内容可在生成过程中作为参考，但不是事实源。
   生成和验证方式由各蓝图定义。

4. 所有生成文件存在后，应用填写完成的模型配置：

   ```sh
   sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/sync_public_agent_assets.sh" \
     --model-config "$MODEL_CONFIG"
   ```

   同一次同步会从可读模板创建或更新 Codex、Cursor 和 Copilot 的项目原生配置及 Hook 文件。
   这些托管字段（包括记录的目录版本）统一由同步流程维护，同时保留用户级配置和模板未声明的项目字段。

## 审查关卡

- [ ] 对照各自的公共蓝图审查每条生成的 Rule 和每个生成的 Skill。
- [ ] 确认无关的目标仓库自有文件保持不变。

## 验收关卡

- [ ] 确认所有枚举的 Rule 和 Skill 都是完整成品。
- [ ] 确认所有必填模型字段都已解决。
- [ ] 确认模板托管的项目配置已经协调完成。
- [ ] 确认 `.agents/config.json` 记录了已安装的目录身份和版本。

## 验证

使用同一份临时模型配置执行最终检查。脚本检查所有枚举的输出是否存在，以及确定性配置、模板和
原生 Hook 注册是否存在偏差；内容验证由各蓝图负责。`--check` 只报告偏差而不写入文件。

```sh
sh "$SETUP_PROJECT_AGENTS_ROOT/scripts/sync_public_agent_assets.sh" \
  --check --model-config "$MODEL_CONFIG"
```

同步脚本或蓝图失败时停止；启动时的项目健康检查及其内部故障不阻断验证。验证过程不调用真实模型。

## 输出

报告发生变化的托管文件，以及尚未解决的模型或蓝图阻塞项。
