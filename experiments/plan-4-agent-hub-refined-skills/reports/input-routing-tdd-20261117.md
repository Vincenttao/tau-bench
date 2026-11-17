# J1首轮输入路由TDD记录

日期：2026-11-17。对应新版设计的逐轮输入判断、H28/H29/H31/H32部分基础要求。**路由提案模块完成离线验证，运行接线及真实模型观察待完成。**

## 红灯到绿灯

1. 先写10项路由测试，因`input_router`模块不存在失败；实现原子问题生成、快照校验、模型绑定和提案组合后通过。
2. 新增暂缓测试，因没有该观察/动作失败；新增独立pause观察，并在Java协调器中保存waiting状态。Java先复现Unsupported action，再实现通过。
3. 新增非法答案类型测试，先复现AttributeError；补齐类型检查后统一抛出JevError，不将异常伪装成判断结果。
4. 补测提供方失败无回退、阈值边界保留未决，并运行相关回归。

## 本次结果

```bash
.venv312/bin/python -m unittest discover -s experiments/plan-4-agent-hub-refined-skills/tests -v
bash experiments/plan-4-agent-hub-refined-skills/java/check-task-coordinator.sh
```

- Python：22项通过，其中14项新增路由测试、8项既有组件测试。
- Java：43条断言通过，比上一轮增加暂缓保留目标及阻断派发检查。
- 真实模型调用：0。官方业务episode：0。

脚本观察只验证控制分支。不能从这些结果推导Jev能正确理解全部22题；真实探针、正式阈值冻结和完整端到端测试仍需后续证据。

## 待推进事项

下一步连接Java任务快照与Python路由请求：持久接收输入→扣减预算→调用Jev→保存判断→按期待修订提交。还需实现新目标候选生成及核验、社交/查询回复与恢复许可边界、目标约束和确认失效，以及Go最终效果边界。

现在的路由器没有从正式driver自动调用，任务协调器也尚未强制控制pilot派发。原先39项契约仍保持待验收；历史审查报告不覆盖本轮新增代码，后续应重新审查接线。

实现和契约说明见[输入路由模块](../python/INPUT_ROUTING.md)、[Java协调器](../java/README.md)。
