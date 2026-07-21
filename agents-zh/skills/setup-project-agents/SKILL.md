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
- LLM 负责模型选择，以及仓库特有 Rule 和 Skill 的生成。
- 每个启动 Hook 仅检查触发该 Hook 的平台所需的推荐工具，不检查项目配置或用户配置，也绝不阻断平台继续运行。

## 托管资产

根据以下公共蓝图生成 Rule：

- [`20-project-tools.md`](https://github.com/wenyue/agents/blob/master/agents/blueprints/rules/20-project-tools.md)
- [`21-project-rules.md`](https://github.com/wenyue/agents/blob/master/agents/blueprints/rules/21-project-rules.md)
- [`22-project-structure.md`](https://github.com/wenyue/agents/blob/master/agents/blueprints/rules/22-project-structure.md)

根据以下公共蓝图生成 Skill：

- [`worktree-environment-setup`](https://github.com/wenyue/agents/blob/master/agents/blueprints/skills/worktree-environment-setup/SKILL.md)
- [`change-set-verification`](https://github.com/wenyue/agents/blob/master/agents/blueprints/skills/change-set-verification/SKILL.md)

## 协调流程

1. 在目标仓库根目录解析系统临时目录中的模型配置路径，并在整个流程中保留该路径：

   ```sh
   MODEL_CONFIG="$(python -c 'import os, tempfile; print(os.path.join(tempfile.gettempdir(), "setup-project-agent-models.json"))')"
   python .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py \
     --model-request "$MODEL_CONFIG"
   ```

   脚本会获取 `https://github.com/wenyue/agents/archive/refs/heads/master.zip`，同步公共目录声明的
   所有平台，并写出模型请求。

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

   将 `PLATFORM` 替换为 `codex`、`cursor` 或 `copilot`。平台原生启动 Hook 会自动执行同一项提示性检查。

## 审查关卡

只验收满足自身公共蓝图的生成资产，并保留无关的目标仓库自有文件。

## 验收关卡

所有枚举的 Rule 和 Skill 均应完整，所有必填模型字段均应得到解决，模板托管的项目配置也必须完成
协调。工具检查发现只产生警告，不构成阻塞。

## 验证

使用同一份临时模型配置执行最终检查。脚本检查所有枚举的输出是否存在，以及确定性配置、模板和
原生 Hook 注册是否存在偏差；内容验证由各蓝图负责。`--check` 只报告偏差而不写入文件。

```sh
python .agents/skills/setup-project-agents/scripts/sync_public_agent_assets.py \
  --check --model-config "$MODEL_CONFIG"
```

同步脚本或蓝图失败时停止；推荐工具 `check` 的状态和发现仍然只作提示。不得调用真实模型进行验证。

## 输出

报告发生变化的托管文件，以及尚未解决的模型或蓝图阻塞项。
