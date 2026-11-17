# 持久任务协调器与受控 DeepAgent

`TaskCoordinator` 是方案4独立的 Java 状态模块。它保存单个 episode 的输入、目标、依赖、验收条件、节点、修订、待澄清事项及预算。`TaskHost` 通过私有 JSON-lines 协议连接 Python 控制器；独立的 `HubDeepAgentBridge` 使用原生 DeepAgent、Skill、Todo 和框架 shelve 检查点。实际入口及验收范围见[运行说明](../python/RUNTIME.md)。

从仓库根目录运行离线测试：

```bash
bash experiments/plan-4-agent-hub-refined-skills/java/check-task-coordinator.sh
bash experiments/plan-4-agent-hub-refined-skills/java/build-task-host.sh
bash experiments/plan-4-agent-hub-refined-skills/java/build-runtime.sh
```

测试使用JDK 21编译，目标语言级别为Java 17，无额外依赖；测试数据写入临时目录并删除，编译输出位于忽略的`target/`。

## 当前接口

- `receive`：接收可信适配层提供的episode、消息ID和完整文本；持久保存后阻断新增派发。同ID不同内容拒绝，相同文本不同ID分别处理。
- `apply`：按期待修订提交已经校验的路由，支持新增目标、回应、修改、取消、暂缓、显式恢复和查询；所有动作一次提交。已有目标必须属于当前episode，新目标ID由协调器分配。恢复只从waiting到active；实际派发还须复查节点条件、有效决策与当前权限。
- `clarify`：保存待澄清状态。后续路由必须显式列出全部已解决的澄清消息，才能解除阻断。
- `chargeModelCall`：调用前持久扣减累计次数。失败调用不退款，重开不重置期限和预算。
- `stop`：持久停止，之后拒绝新消息和路由提交。
- `configure_goal / record_condition / accept_goal`：绑定验收条件、保存关联证据、核对全部条件和依赖后关闭目标；工具正常返回和 Todo 完成均不能直接关闭目标。
- `start_node / observe_node`：按固定节点版本与已采纳决策引用保存节点状态，拒绝重复启动及冲突终态。
- `wait_goal`：保存待补充信息。有效回应或修改可恢复任务；累计恢复次数最多 8 次，重启不重置。

`canDispatch(now)`只检查输入/任务层必要条件；返回true仍需要Hub独立校验具体操作、有效判断、权限和参数，不能直接据此执行业务。调用方应提供可信墙钟值，单位与初始化deadline一致。

## 持久化与边界

初期采用有版本的Properties快照及独立锁文件，不引入数据库依赖。先写临时文件并force，再原子替换；文件系统不支持原子移动时拒绝提交。写入失败后实例停止使用。文件锁在整个实例生命周期内持有，锁文件不应手动删除；重启可复用同一路径，进程退出释放锁。

目前是单宿主、进程崩溃范围的基础实现，不承诺断电级持久性或跨主机共享。每个快照最多32个目标为当前保护上限，后续需纳入冻结配置。状态包含用户文本，应写入忽略的运行目录，不提交原始内容。

`InvocationSequence` 为跨执行器重启的 MCP 调用分配不重复序号；`TodoLimit` 将原生 Todo 创建限制为最多 32 项。模型调用前通过控制协议预扣预算，原生执行器只获得本机私有模型代理的临时令牌。

现有实现已连接官方诊断 driver，但节点类型的完整路径覆盖、依赖规划接线及完整隔离重放仍需分别验收。节点注册表中有名字不等于该路径已经实际执行，不能仅凭本模块测试声明完整设计通过。
