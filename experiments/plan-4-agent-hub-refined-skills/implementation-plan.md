# 方案4实施细化：Hub最终效果控制

日期：2026-11-17。状态：待实施。本文不改变本方案Skill、题数、重复次数或正式放行要求，不自动授权运行。

## 工作包与交付

| 工作包 | 单一责任角色 | 依赖 | 实施内容 | 验收证据 |
| --- | --- | --- | --- | --- |
| D1 实际Go链 | Hub负责人 | W1和实际Go宿主 | 合法请求从Java经Go到最终Python边界并产生银行效果 | 二进制、decision、payload与receipt可关联 |
| D2 拒绝与变异 | Hub负责人 | D1 | 缺证据、改payload、停Go、固定allow均被检测 | 非法写入未到达银行；合法请求不能全部被拒绝 |
| D3 未知与恢复 | Hub负责人 | D2 | 账本失败、丢回执、重复/迟到、Java/Go重启 | 同意图operation保持，未知结果不盲目重发 |
| D4 禁用与计量 | Hub负责人 | D3 | 证明跨题学习/自发布禁用，计量纠错与控制延迟 | 核心CT及禁用证明均有证据，不回退DeepAgent |

## 公共边界

公共框架负责环境、协议、资源监督和记录；不得替本方案补业务操作、纠正参数或注入其他方案的控制能力。以[公共执行框架](../../studies/banking-architecture-comparison/design/execution-framework.md)和[能力装配矩阵](../../studies/banking-architecture-comparison/design/capability-assembly.md)核查实际接线。

最小链路使用独立合成输入，脚本模型用于协议检查；这不证明真实模型业务效果。最小链路通过后仍须完成全部blocking契约，不能降低正式门禁。真实模型冒烟需另列范围和成本，不自动重复正式22题。

## 失败和停止

发生普通业务错误时按共同规则保留结果；严重错误按episode/arm/study作用范围处理。未知写入先保留和对账，不通过重新开始任务绕过幂等或预算。诊断使用[五段偏差定位](../../studies/banking-architecture-comparison/design/delivery-and-diagnosis.md)，区分直接证据、因果推断与次生错误。

## 放行更新

各工作包完成后，更新[本方案准备报告](readiness-report.md)的专属证据和剩余缺口，记录代码/配置/制品hash及具体执行入口；不要只增加公共测试数量。实际组件描述、声明能力和独立验证结果必须分开保存。责任人和排期由实施前登记，不给未经验证的完成百分比。

本轮已有设计和准备校验，正式run_one/collect及本方案完整接线尚未交付。本文中的工作包不是已完成清单。
