# 持久任务协调器：J0基础实现

`TaskCoordinator`是方案4独立的Java状态模块。它保存单个episode的输入、目标、修订、待澄清事项及预算。`TaskHost`已通过私有JSON-lines协议连接Python/Jev与Go组件诊断，尚未装配到DeepAgent正式driver。见[阶段验收](../reports/controlled-chain-acceptance-20261117.md)。

从仓库根目录运行离线测试：

```bash
bash experiments/plan-4-agent-hub-refined-skills/java/check-task-coordinator.sh
bash experiments/plan-4-agent-hub-refined-skills/java/build-task-host.sh
```

测试使用JDK 21编译，目标语言级别为Java 17，无额外依赖；测试数据写入临时目录并删除，编译输出位于忽略的`target/`。

## 当前接口

- `receive`：接收可信适配层提供的episode、消息ID和完整文本；持久保存后阻断新增派发。同ID不同内容拒绝，相同文本不同ID分别处理。
- `apply`：按期待修订提交已经校验的路由，支持新增目标、回应、修改、取消、暂缓、显式恢复和查询；所有动作一次提交。已有目标必须属于当前episode，新目标ID由协调器分配。恢复只从waiting到active；实际派发还须复查节点条件、有效决策与当前权限。
- `clarify`：保存待澄清状态。后续路由必须显式列出全部已解决的澄清消息，才能解除阻断。
- `chargeModelCall`：调用前持久扣减累计次数。失败调用不退款，重开不重置期限和预算。
- `stop`：持久停止，之后拒绝新消息和路由提交。

`canDispatch(now)`只检查输入/任务层必要条件；返回true仍需要Hub独立校验具体操作、有效判断、权限和参数，不能直接据此执行业务。调用方应提供可信墙钟值，单位与初始化deadline一致。

## 持久化与边界

初期采用有版本的Properties快照及独立锁文件，不引入数据库依赖。先写临时文件并force，再原子替换；文件系统不支持原子移动时拒绝提交。写入失败后实例停止使用。文件锁在整个实例生命周期内持有，锁文件不应手动删除；重启可复用同一路径，进程退出释放锁。

目前是单宿主、进程崩溃范围的基础实现，不承诺断电级持久性或跨主机共享。每个快照最多32个目标为当前保护上限，后续需纳入冻结配置。状态包含用户文本，应写入忽略的运行目录，不提交原始内容。

下一步需要：输入及目标契约的完整schema、Jev路由适配、证据与确认失效处理、节点/WaitRecord、业务操作与回执投影、正式driver和效果边界接线。当前没有业务成功动作，Todo不能通过此接口声明业务完成。
