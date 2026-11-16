# 本地轨迹工作台

从仓库根目录运行：

```bash
python python/trace_viewer.py --port 8877
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

自动发现 `experiments/*/runs/*/manifest.json`、`runs/*/manifest.json` 和 `runs/manifest.json`，相同真实路径去重。优先读取 `official-trajectory.jsonl`；没有日志时回退到 `result.json` 的第一条 simulation，或 `trajectory-unscored.json` 的 messages。暂不解析 Markdown 轨迹附录；克隆后若没有本地运行原件，需要先恢复归档。

内部事件读取 `deepagent/*/deepagent-events.jsonl`；MCP 读取 `deepagent/*/mcp/mcp.jsonl`，仅按显式 `mcp_request_id` 关联 `skill.jsonl`。未记录的工具、Skill 或 MCP 不补造。

各来源按自身文件顺序展示；多个内部会话按路径分组排列，不推断跨来源全局顺序。官方无时区时间戳保持原文，内部 `time_ms` 显示 Unix 毫秒，MCP 秒时间戳转换为服务所在机器时区。嵌套事件数量不是独立业务调用次数，不能相加为调用量。

页面展示 benchmark 模拟数据；未评分保持未评分。缺失、空或未写完的 JSONL 会给出提示，并保留已解析记录。模型请求上下文可能很大，仅在展开详情时传输。此页面检查不等同于模型调用、真实银行验证或重新评分。

## 验证

```bash
python -m unittest discover -s tests -p 'test_trace_viewer.py' -v
node --check viewer/app.js
```

回归覆盖未评分与损坏尾行、MCP 请求 ID 关联、结果回退、目录越界和空轨迹。浏览器验收另检查来源切换、筛选、完整 JSON、未评分用例、移动端布局和 JavaScript 错误。
