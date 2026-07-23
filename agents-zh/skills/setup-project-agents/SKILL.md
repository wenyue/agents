---
name: setup-project-agents
description: 从 wenyue/agents 公共目录初始化或更新仓库时使用。
---

# 设置项目 Agent

同步确定性的 Agent 配置，选择 Subagent 模型，并生成本流程声明的五个仓库特有资产。

模板托管的项目配置为所有开发者提供一致的仓库默认值。脚本执行部分深度合并：模板字段覆盖偏差，
模板未声明的字段保持不变，常规同步会自动修复缺失或过期的托管值。流程绝不读取或修改用户配置。

## 所有权

- 脚本负责所有受支持平台的确定性配置。
- 字面量模板负责项目配置值及平台原生启动 Hook；Python 只包含通用的协调逻辑。
- 目标仓库在 `.agents/config.json` 中负责声明第三方 Skill；脚本负责获取并协调每个已声明的
  Skill。
- LLM 负责模型选择，以及仓库特有 Rule 和 Skill 的生成。
- 每个启动 Hook 每天只检查一次当前平台的推荐工具，不读取项目配置或用户配置。发现问题时，Agent
  先停止当前任务并询问是否安装；用户回复后即可继续。

## 托管资产

根据以下公共蓝图生成 Rule：

- [`20-project-tools.md`](https://github.com/wenyue/agents/blob/master/agents/blueprints/rules/20-project-tools.md)
- [`21-project-rules.md`](https://github.com/wenyue/agents/blob/master/agents/blueprints/rules/21-project-rules.md)
- [`22-project-structure.md`](https://github.com/wenyue/agents/blob/master/agents/blueprints/rules/22-project-structure.md)

根据以下公共蓝图生成 Skill：

- [`worktree-environment-setup`](https://github.com/wenyue/agents/blob/master/agents/blueprints/skills/worktree-environment-setup/SKILL.md)
- [`change-set-verification`](https://github.com/wenyue/agents/blob/master/agents/blueprints/skills/change-set-verification/SKILL.md)

## 项目第三方 Skill

仓库可以在 `.agents/config.json` 中声明第三方 Skill：

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

每项声明负责完整的 `.agents/skills/<name>/` 目录。同步时，脚本会从指定的 GitHub 仓库、
ref 和路径整体替换该目录，包括覆盖本地修改、删除上游已经移除的文件。删除声明不会删除已经
安装的目录。

写入任何公共资产或第三方 Skill 前，脚本会先下载并验证所有声明的来源。如果某个来源失败，且
目标仓库没有可用的旧版本，同步会在应用任何变更前终止。如果已安装可用的旧版本，脚本会保留
旧版本、继续同步其余内容并报告 warning；`--check` 会报告同一 warning，并以状态码 1 退出。

## 协调流程

1. 在目标仓库根目录解析系统临时目录中的模型配置路径，并在整个流程中保留该路径：

   ```sh
   MODEL_CONFIG="$(python -c 'import os, tempfile; print(os.path.join(tempfile.gettempdir(), "setup-project-agent-models.json"))')"
   python .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py \
     --model-request "$MODEL_CONFIG"
   ```

   脚本会获取 `https://github.com/wenyue/agents/archive/refs/heads/master.zip`，同步公共目录声明的
   所有平台，预检项目第三方 Skill，并写出模型请求。

2. 填写 `$MODEL_CONFIG` 中的全部模型字段。根据每个 Subagent 的 `required_intelligence`，为
   Codex、Cursor 和 GitHub 选择 `model`，并为 Codex 选择 `model_reasoning_effort`。现有
   Wrapper 不是取值来源。

3. 依次打开并执行“托管资产”中枚举的公共蓝图。Rule 输出到 `.agents/rules/<name>.md`，Skill
   输出到 `.agents/skills/<name>/`。生成内容以目标仓库的当前证据为准；
   旧内容可在生成过程中作为参考，但不是事实源。生成和验证方式由各蓝图定义。

4. 所有生成文件存在后，应用填写完成的模型配置：

   ```sh
   python .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py \
     --model-config "$MODEL_CONFIG"
   ```

   同一次同步会从可读模板创建或更新 Codex、Cursor 和 Copilot 的项目原生配置及 Hook 文件。
   不要另外修改用户级配置，也不要移除模板未声明的项目字段。

5. 需要立即获得设置反馈时，仅针对当前执行平台运行不使用缓存的推荐工具检查：

   ```sh
   python .agents/skills/setup-project-agents/scripts/check_recommended_tools.py check --platform PLATFORM
   ```

   将 `PLATFORM` 替换为 `codex`、`cursor` 或 `copilot`。平台原生启动 Hook 会自动检查。发现问题时，
   先询问用户是否安装并等待回复；用户选择安装时，完成后运行
   `check_recommended_tools.py hook --platform PLATFORM --force`。其他回复不影响继续当前任务。

## 审查关卡

只验收满足自身公共蓝图的生成资产，并保留无关的目标仓库自有文件。

## 验收关卡

所有枚举的 Rule 和 Skill 均应完整，所有必填模型字段均应得到解决，模板托管的项目配置也必须完成协调。

## 验证

使用同一份临时模型配置执行最终检查。脚本检查所有枚举的输出是否存在，以及确定性配置、模板和
原生 Hook 注册是否存在偏差；内容验证由各蓝图负责。`--check` 只报告偏差而不写入文件。

```sh
python .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py \
  --check --model-config "$MODEL_CONFIG"
```

同步脚本或蓝图失败时停止；推荐工具检查及其内部故障不阻断验证。不得调用真实模型进行验证。

## 输出

报告发生变化的托管文件，以及尚未解决的模型或蓝图阻塞项。
