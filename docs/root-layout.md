# 主目录整理说明

日期：2026-11-16。依据用户最新要求：不再考虑旧入口兼容，四实验独立组织，原始工程直接归档且不压缩。

## 当前布局

```text
README.md                       总入口与能力边界
AGENTS.md                       保留原文件，旧路径已失效
experiments/
  plan-1-deepagent-original-skills/
  plan-2-deepagent-refined-skills/
  plan-3-moa-refined-skills/
  plan-4-agent-hub-refined-skills/
studies/banking-architecture-comparison/
shared/
  python/                       准备、适配、MCP与轨迹读取组件
  java/                         独立DeepAgent桥接构建
  skills/releases/              不可变Skill发布
  config/                       非秘密配置
  tests/                        当前组件回归
  viewer/                       工作台页面
archive/                        完整旧代码与历史资料
docs/                          现行目录说明与校验记录
```

隐藏的Git、基准依赖、虚拟环境和工具目录保留原位，不归档到源码目录。旧根目录python/java/tests等已移走，不留替代软链接。旧实验名称也已移除。

## 独立实验和公共能力的边界

各实验的plan.json固定本方案身份、Skill清单hash和共同study；prepare.py只准备本方案输入，不接受用另一个Skill临时冒充本方案。方案1/2共享执行组件是控制变量需要，不代表两方案共用可变运行状态。

新的准备接口核对22个唯一任务、英文文件hash、共同规格和Skill内容，写preparation.json，明确executable=false。四方案真正执行所需的适配、监督、冻结和评分接线尚未完成。旧完整runner仍存在归档中，但不再作为当前工程入口。

## 归档与证据

[迁移清单](root-layout-migration.json)记录每项旧路径及归档位置。迁移时核验了原目录普通文件的SHA-256；原始Skill、历史manifest和冻结文件没有改写。提取后的当前组件允许修改，原始版本仍能在archive查阅。

工作台从archive及新方案runs发现manifest，保留已有事件读取能力。新MOA/Hub事件解析尚未实现。本次没有启动真实模型或银行业务测试。

AGENTS.md按最初要求不修改，因此该历史指南中的旧命令不再有效。新命令以README.md和shared/README.md为准，这一变化来自用户明确取消兼容要求。

验证结果见[root-layout-validation.json](root-layout-validation.json)。此前兼容迁移的检查结果属于历史阶段，不证明本次新结构；旧文档已归档。
