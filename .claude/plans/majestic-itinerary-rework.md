# Feature: 行程改按 Majestic Trails Nepal 结构重排（去 Namche 适应日）

## Overview

现行 `data/itinerary.csv`（"fable 版"）用 9.25 下午直升机硬闯 Lukla + 当天徒步 8km 到 Phakding，换出 Namche、Dingboche 两个适应日都保留。用户认定 9.25 当天硬闯不现实（凌晨机场辗转、上午刚落地就包机+徒步一整天），要求改按 Majestic Trails Nepal 的结构：9.25 纯加都日（不进山），9.26 早班机飞 Lukla 当天徒步到 Phakding，代价是放弃 Namche 适应日、只保留 Dingboche 一天。12 天总天数不变，仍是 9.25→10.6。

这个改动牵出一个原本没点破的连锁点：9.25 当天硬闯之所以要包 2 架直升机（¥5,216/人，全程最大单项开支），唯一原因是"落地当天下午必须飞进山"；一旦改成 9.26 早班机（不再是落地当天），固定翼（10.6 返程已用的同一条路线）就变得可行，预算可大幅下降。但用户直接联系了 Majestic Trails Nepal 的向导 Bibek，得到的信息是：**9.26 早班机从加德满都直飞还是绕道 Ramechhap/Manthali 起降，取决于尼泊尔民航局旺季的实时分流决定，不是固定日历规则，订好之后仍可能临时改变**；Bibek 目前给另一个 9 人团确认的航班是加都直飞（未走 Ramechhap），但明确说这个安排"随时可能变"。这与 `sources/02` 此前呈现的"旺季固定翼全部改飞 Ramechhap"的确定性表述有出入，需要新增一份出处记录这次直接沟通，并在报告里把这个交通方式的不确定性讲清楚，而不是假装已经锁定。

## Intent Brief

- **Goal**：把 12 天行程从"两个适应日 + 9.25 硬闯"改成"一个适应日（Dingboche）+ 9.25 纯加都日 + 9.26 进山"，日期结构与 Majestic 一致；同时把 9.26 进山交通方式（固定翼加都直飞 / 固定翼绕道 Ramechhap / 直升机）标注为待定，给出单点最佳估算但保留应急预备金，并在报告里显式说明这个不确定性。
- **Motivation**：9.25 当天硬闯在体能上不现实（用户原话：半夜睡机场、上午刚过关下午就包机+徒步，"绝对撑不下来"）；Majestic 的结构证明"9.25 纯休整、9.26 进山"是行业验证过的可行走法。
- **Known context**：`sources/16`（Majestic 报价单逐日行程）、`sources/06`（Earth Trekkers 标准 12 天两适应日攻略）、`sources/02`（旺季固定翼改飞 Ramechhap 的既有表述）、用户与 Bibek 的聊天记录（新增为 `sources/17`）。
- **Constraints**：总天数不变（12 天，9.25→10.6）；费用取值仍按 AGENTS.md 铁律 5"单点最佳估算，不给区间"；表格数字唯一事实源仍是 `data/*.csv`；文档只写当前事实，不留历史对照叙事。
- **Non-goals**：不重新核实向导/背夫是否需要请（待议事项一不动）；不修正 `quote-comparison.csv` 与 `cost-breakdown.csv` 之间"向导 11 天 vs 12 天"这类改动前就存在、与本次行程重排无关的口径差异。
- **Success criteria**：`uv run --with markdown scripts/build_report.py` 构建通过；`itinerary.csv` 与 `day-track-stats.csv` 按新 12 行/10 个徒步日对齐；地图与剖面图按新 Day 编号重新生成且无 Namche 适应点残留；Q2/Q3/Q5/Q6/FAQ 与 PROJECT.md 反映新结构；9.26 交通方式不确定性在报告中有明确、不误导的表述。
- **Assumptions**：见下表。
- **Unknowns**：9.26 究竟是加都直飞、绕道 Ramechhap 还是直升机——明确定为"行前需持续跟进、无法现在锁定"的开放事实，不是本轮要消解的假设。

## Alignment Gate

- **I will implement**：itinerary.csv 全量重排；day_tracks.py / day_colors.py / make_map.py / make_profile.py 的 day-key 重新映射与文案更新；重跑三个脚本重新生成 day-tracks.json / day-track-stats.csv / route-track-stats.csv / 图件；cost-breakdown.csv 与其"合计"行的重算；新增 sources/17 记录与 Bibek 的沟通；PROJECT.md 行程硬约束与待议事项二的改写；faq.html、ext-route.html、ext-quote.html、ext-transport.html、ext-health.html、header.html 的对应改写；重跑构建。
- **I will not implement**：不改向导/背夫是否雇佣的结论；不修正 quote-comparison.csv 里与本次无关的既有口径差异；不覆盖用户尚未拍板的 9.26 具体交通方式——报告里如实呈现"待定 + 单点估算 + 应急预备金"。
- **Open assumptions**：见下表，均为 low/medium impact，均可从现有 sources 或既有报告模式（10.6 返程的"主力方案+应急预备金"写法）合理推出，不再追加提问。
- **Acceptance**：构建通过 + 逐文件人工核对 Day 编号、里程、费用合计的算术一致性。

## Assumption Ledger

| Assumption | Confidence | Impact if Wrong | Status |
|---|---:|---:|---|
| 9.26 进山交通费按"固定翼加都直飞 USD 208/人"作单点估算，绕道 Ramechhap 与直升机作为应急预备金列参考表 | medium | medium | 用户已明确交通方式待定，本假设只影响主表单点值，不影响行程结构；已在报告中显式标注不确定性 |
| Day1（9.25）不产生额外向导/背夫/三餐外的新增费用，仅新增一晚加都酒店 + 相应机场市区交通趟数 | medium | low | 参照 Majestic 报价单"加都酒店 2 晚"的既有口径，风险低 |
| day-track-stats.csv 与 route-track-stats.csv 由脚本重新生成而非手工改数，以保持"脚本产物"契约 | high | high（手工改会与脚本定义漂移） | 已按此执行 |
| 向导/背夫按 12 天计价的既有口径不因本次重排而变（即使 Day1 他们可能并不实际随行） | medium | low | 沿用报告原有计价惯例，不在本轮扩大范围去动它 |

## Work-Unit Specs

- **T1 新增 sources/17**：记录与 Majestic Trails Nepal 向导 Bibek 的聊天（航线不确定性）。file: `sources/17-majestic-flight-routing-uncertainty.md`。deps: —
- **T2 route_points.py**：`ACCLIMATIZE_POINTS` 去掉 Hotel Everest View，只留 Nangkartshang。deps: —
- **T3 day_tracks.py**：`raw{}`/`DAY_SOURCES` 重新映射（去掉 Namche 适应日、1→2、2→3、4-11 不变），docstring 更新。deps: T2（route_points 里的村庄坐标不变，但 assemble() 引用需确认无残留）
- **T4 day_colors.py**：`DAY_COLORS`/`ASCENT_DAYS`/`ACCLIMATIZE_DAYS` 重新映射，docstring 数字更新。deps: —
- **T5 make_map.py**：循环区间 `range(2,12)`、`ACCLI_DAY`/`ACCLI_LABEL` 去掉 Hotel Everest View、`BADGE_DX` 去掉 `3:45`、图例文案（Day 2–8 / Day 6）。deps: T2, T4
- **T6 make_profile.py**：docstring/标题/坐标轴/print 文案（10 天、Day 2–11）、`landmarks` 只留 1 个适应点、`_write_route_track_stats` 区间改 `range(2,9)`。deps: T2, T4
- **T7 重跑脚本**：依次 `day_tracks.py` → `make_profile.py` → `make_map.py`，验证产物。deps: T3, T4, T5, T6
- **T8 itinerary.csv 全量重排**：12 行，Day1 加都、Day2-11 徒步/适应日、Day12 转场。deps: T1（Day2 行要引用 sources/17）
- **T9 cost-breakdown.csv 重算**：交通行、茶屋房费（11→10 晚）、加都酒店（1→2 晚）、机场市区交通（2→4 趟）、合计行手工重算。deps: T1
- **T10 PROJECT.md**：行程硬约束、待议事项二改写。deps: T8, T9
- **T11 报告 section 改写**：`header.html`、`faq.html`、`ext-route.html`、`ext-quote.html`、`ext-transport.html`、`ext-health.html`。deps: T7, T8, T9, T10
- **T12 构建 + 核验**：`uv run --with markdown scripts/build_report.py`，核对锚点/token 闸门与合计算术。deps: T11

## Dependency Graph

```
T1 ─┬─> T8 ─┐
    └─> T9 ─┼─> T10 ─> T11 ─> T12
T2 ─┬─> T3 ─┤
    ├─> T5 ─┤
    └─> T6 ─┤
T4 ─┬─> T5 ─┤
    └─> T6 ─┤
T3,T4,T5,T6 ─> T7 ──────────┘
```

## Execution Waves

- Wave 1（无依赖，可并行）：T1, T2, T4
- Wave 2（deps 已完成）：T3, T5, T6, T9（T9 只依赖 T1）
- Wave 3：T7（重跑脚本）、T8（itinerary 重排，只依赖 T1）
- Wave 4：T10
- Wave 5：T11
- Wave 6：T12

本任务是内容/数据/脚本重排，不涉及新的可测函数契约，架构师直接执行（不派 test-author/function-implementer；正确性由仓库既有 pytest 套件 + 构建期锚点/token 闸门 + 人工算术核对保证）。用户在交互中已明确指示"把后面这些全部重新捋一遍"，本轮跳过 BACKLOG 审批环节直接执行。

## Status

Completed
