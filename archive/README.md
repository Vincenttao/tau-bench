# 原始工程与历史证据归档

所有内容采用普通文件夹保存，未压缩。按用户最新要求，当前工程不再保留旧命令、根目录链接或旧实验名称的兼容入口。

| 目录 | 内容 |
| --- | --- |
| legacy-workspace/ | 整理前的python、java、enterprise-java、replay-java、config、tests、viewer、skills和日志 |
| legacy-workspace/design-snapshot/ | 本轮整理前的四方案设计、共同study和文档快照 |
| legacy-workspace/root-shortcuts/ | 原根目录快捷链接，仅用于识别历史文件归属 |
| deepagent-source/ | 原DeepAgent完整实现、旧中文入口、Skill发布及历史材料引用 |
| native-skill-history/ | NativeSkillAgent历史运行，不是方案1 |
| deepagent-history/ | DeepAgent历次计划、报告与本地轨迹 |
| agent-hub-history/ | 旧Hub设计及实际上未接入Hub的DeepAgent基线 |
| reference-documents/、reference-reports/、reference-evidence/ | 指标卡、执行计划、用例说明、报告和精选证据 |

原始普通文件与冻结记录不改写；归档中的相对快捷链接尽量指向归档实体，但不保证旧绝对路径、旧代码直接运行或暂停进程恢复。需要复现实验时应显式重建环境和配置，不能直接恢复原进程。

当前执行组件从原工程提取至shared；当前四方案入口在experiments。不要从归档运行旧任务后把结果当作新方案成绩。

归档题目目录 `.deps/` 的本地软链接及缓存链接不提交。中文用例册的原始题目链接使用固定上游提交 `fc0055dc4e0a316c3f83133267fbd6faaa770992`，不依赖克隆者机器上的 `.deps`。本地链接保留供历史查阅，但不作为可移植依赖。

原始runs、日志、凭证和构建产物继续排除Git。只拉取Git不能保证完整历史轨迹可见。最新结构和校验见[主目录整理说明](../docs/root-layout.md)及[迁移记录](../docs/root-layout-migration.json)。
