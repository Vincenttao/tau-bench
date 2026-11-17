# 本地轨迹工作台

从仓库根目录运行：

```bash
python shared/python/trace_viewer.py --port 8877
```

浏览器打开 <http://127.0.0.1:8877>，用 `Ctrl+C` 停止。只依赖 Python 标准库，无需 npm、模型凭据或数据库。服务绑定本机回环地址，不向外发布轨迹；不修改原始测试结果。不要直接双击 `index.html`，页面需要本地 API。

## 查看方式

1. 选择实验批次，按 task ID 或官方评分结果筛选用例。
2. **对话与业务工具**：查看官方轨迹中的用户、Agent、调用参数和工具返回。类别可筛为纯对话。
3. **Agent 内部事件**：按 Skill、Todo、模型、系统事件筛选。`skill_tool` 是文档读取记录；`invoke_skill` 是操作执行记录。展开可查看 Skill 文档内容和原始参数。
4. **MCP 调用**：查看初始化、发现和工具调用；有匹配请求 ID 时附上 `skill.jsonl` 的业务参数及官方调用 ID。
5. 每条记录可展开完整 JSON、复制并定位源文件和行号。用例链接保留批次及用例，便于分享本地定位。

搜索范围为标题、前 650 字内容摘要、源路径和调用 ID；不是全文检索。列表每页 40 条。点击“刷新数据”重新读取磁盘，暂不自动轮询。错误筛选依据结构化 `success=false`、`isError=true` 或非空 `error`，不保证识别自然语言中的全部错误。

## 来源与边界

自动发现 `experiments/*/runs/*/manifest.json`、`archive/*/runs/*/manifest.json` 及归档的嵌套批次，相同真实路径去重。优先读取 `official-trajectory.jsonl`；没有日志时回退到 `result.json` 的第一条 simulation，或 `trajectory-unscored.json` 的 messages。暂不解析 Markdown 轨迹附录；克隆后若没有本地运行原件，需要先恢复归档。

内部事件读取 `deepagent/*/deepagent-events.jsonl`；MCP 读取 `deepagent/*/mcp/mcp.jsonl`，仅按显式 `mcp_request_id` 关联 `skill.jsonl`。未记录的工具、Skill 或 MCP 不补造。

各来源按自身文件顺序展示；多个内部会话按路径分组排列，不推断跨来源全局顺序。官方无时区时间戳保持原文，内部 `time_ms` 显示 Unix 毫秒，MCP 秒时间戳转换为服务所在机器时区。嵌套事件数量不是独立业务调用次数，不能相加为调用量。

页面展示 benchmark 模拟数据；未评分保持未评分。缺失、空或未写完的 JSONL 会给出提示，并保留已解析记录。模型请求上下文可能很大，仅在展开详情时传输。此页面检查不等同于模型调用、真实银行验证或重新评分。

## 验证

```bash
python -m unittest discover -s tests -p 'test_trace*.py' -v
node --check viewer/app.js
```

回归覆盖未评分与损坏尾行、MCP 请求 ID 关联、结果回退、目录越界和空轨迹。浏览器验收另检查来源切换、筛选、完整 JSON、未评分用例、移动端布局和 JavaScript 错误。

## 本轮能力与判定

用例上方新增三个面板：

- **成功 / 失败判定**：显示本轮计划分母、通过/失败/未评分/待核查数量，以及本题 `reward_basis`、实际得分和参与计分的分项。可展开官方检查结果、预期动作、参数与用户模拟器剧本。参考动作和剧本明确标为裁判/模拟器侧信息。
- **Skill 说明**：读取当前用例会话下部署的 `skills/*/SKILL.md`，展示描述、全文、来源和 SHA-256；另列实际 `skill_tool` 请求。部署文档或发起读取请求不等于读取成功。
- **MCP 与可调用工具**：分别展示 `model_request.tools` 中的原生工具定义和部署 `operations.json` 的业务操作，包含描述、参数 Schema、来源及已观测事件数。搜索覆盖本面板的名称、描述和参数。部署目录不冒充 MCP 完整发现结果。

单题成功要求 `status=scored` 且有效数字 reward 为 1；已评分且 `0≤reward<1` 判为失败。缺评分保持未评分；状态/分数无效或 `status.json` 与 `result.json` 分数冲突时待核查。未参与 `reward_basis` 的诊断项失败不单独推翻官方成绩。

本轮全部计划用例通过才显示“本轮全部通过”；存在已评分失败显示“本轮存在失败”，并保留未评分数；其他情况显示待完成/待核查。已评分通过率的分母仅为有效通过数与失败数之和。该汇总规则为查看器规则，不改写 benchmark 评分。

优先从本题 `result.json` 读取标准。如果结果不存在，仅当本地官方题目文件的 SHA-256 与本轮 manifest 匹配时读取题目标准；不匹配或文件缺失则保留未知。展示标准不代表补评分。

新会话的 Skill 说明同时展示部署于 `guides/*.md` 的业务指南全文与哈希；实际读取请求单列。历史批次若只存在合并文档，则按历史原件展示。

版本化会话在 Skill 页展示 assembly 记录中的版本与发布清单哈希，嵌套业务指南保留领域路径。历史记录没有显式版本时照实提示，不自动给旧记录补版本。

## 跨设备同步与轨迹可见性

Git 克隆包含工作台源码、版本化 Skill、正式报告和精选 Markdown 轨迹附录。Git 忽略 `runs/`、原始日志和构建产物，因此仅 `git pull` 不会带来完整的页面数据；`evidence/archive-index.json` 是索引，不包含原件。

另一台设备可直接阅读 `experiments/deepagent-todo-skill-mcp/reports/round-01-20261115-a00/evidence/` 下的精选轨迹。工作台尚不解析这些 Markdown 附录。

要在页面查看完整一轮，通过可信文件同步渠道把该轮目录复制到相同的仓库相对路径，例如：

```text
experiments/deepagent-todo-skill-mcp/runs/round-01-20261115-a00/
  manifest.json
  episodes/
    <episode-key>/
      status.json
      result.json                    # 如原本存在；不要为未评分用例补造
      official-trajectory.jsonl
      trajectory-unscored.json       # 如原本存在
      deepagent/<session-id>/
        deepagent-events.jsonl
        skills/                      # 该会话的部署文档与操作目录
        mcp/mcp.jsonl
        mcp/skill.jsonl
```

最简单的方法是复制该轮的 `manifest.json` 和整个 `episodes/` 目录；无需复制 `.venv`、Java构建目录、完整恢复归档或模型密钥。其余文件可以保留，但复制前应核查数据访问权限。对话、模型上下文和工具结果可能含敏感信息，不应自动作为公开源码上传。

复制完成后用标准 Python 启动：

```bash
python shared/python/trace_viewer.py --port 8877
```

浏览器打开 <http://127.0.0.1:8877>。只查看轨迹不需要 Maven、JDK、模型密钥或调用模型。工作台从所选manifest所在目录定位episodes，不依赖manifest内旧机器的output绝对路径。

若原始result缺失，页面可能需要本地`.deps/tau2-bench`中与历史manifest哈希一致的题目文件才能显示评分标准；缺少时保持未知，不影响现有对话日志的查看。若只复制官方轨迹而未复制DeepAgent/MCP记录，对应内部事件面板会为空。
