# MOA测试执行计划：现有能力

2026-11-17更新。权威范围为 [测试设计](test-design.md) 与 [细化用例](plans/scenarios.json)。英文22题、seed=300、预算和模型参数以共同study/plan联合校验为准。旧中文config/experiment.json及banking-cohort.json不作为当前入口。

执行顺序：规格/制品冻结 → 真实MOA脚本模型协议 → 官方桥契约 → 失联与原生能力边界 → 真实模型诊断 → 正式22题。只有全部核心阻塞项有真实证据才放行；本地暂停专项仅在配置启用且有本地Skill时适用。

普通INPUT_REQUIRED续接、意图切换和下游自行续接分别记录。未完成远端现场恢复不支持是本轮边界，不要求开发检查点/事务调度模块补齐。测试人员不得通过重发原query伪造恢复成功。

当前可运行的局部检查：

```bash
bash experiments/plan-3-moa-refined-skills/java/check-routing.sh
python experiments/plan-3-moa-refined-skills/python/check_native_flow.py --output experiments/plan-3-moa-refined-skills/runs/new-native-flow
python -m unittest discover -s experiments/plan-3-moa-refined-skills/tests -v
python shared/python/study_contracts.py
```

原生链路夹具使用两个真实Runtime与本机脚本模型，核验确认、领域补参和模型输入采集，不调用外部模型。输出目录必须不存在。它们不覆盖全部核心用例；真实driver未实现的项目保持pending。运行真实模型需要独立新目录和既定前置条件。最新局部证据见[检查修订结果](reports/implementation-check-20261117.md)。

发生进程失联、写入结果未知，保留官方轨迹、源hash与关联标识，停止相关题目并核查；不要求MOA提供未实现的跨重启恢复，也不自动重跑未知效果。评分异常保留null；已评分业务失败保留原reward。

原生快慢路由是上游默认；当前slow-only为已有实验裁剪。若改为默认快慢配置，须另冻结新的运行身份，不将两种模式的历史成绩混合比较。
