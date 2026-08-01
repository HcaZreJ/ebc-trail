# Feature: Q2 报价核对 + 报告改用 USD/NPR 基准

## Overview

两件事一起做：

1. **Q2 数字重核。** 把「Majestic Trails 12 天套餐 vs 自己组」的每个数字从原始出处重算，修掉算错的、补上出处缺的、拆开口径不对等的。目标是让用户能对 6 位同行者说清一句话：代理比自己组贵多少，以及这个"多少"在什么前提下成立。
2. **全报告改以 USD 与 NPR 为基准。** 所有资料的原始报价是 USD 或 NPR，报告先折成人民币再展示，折算层既丢信息又在三种货币波动时让读者无法判断真实金额。取消人民币展示层，金额按其原生币种呈现，可加总的每人金额统一 USD。

## Intent Brief

- **Goal**：Q2 给出可对外汇报的差价结论（含成立前提）；报告通篇以 USD/NPR 计价。
- **Motivation**：用户自己粗算的自组成本比报告高、接近代理报价，怀疑报告把自组算低了、代理的溢价被夸大。核对证实了这个怀疑（见下「核对结论」）。人民币展示层则是在 CNY/USD/NPR 三者同时波动时读不出真实金额。
- **Known context**：`data/cost-breakdown.csv`（22 行必要开销与参考项）、`data/quote-comparison.csv`（11 行逐项比价）、`sources/16`（报价单事实）、`sources/02 04 05 07 12 14`（单价出处）、`scripts/reportgen/{money,config,costs,quotes}.py`（折算与表格装配）。
- **Constraints**：单点最佳估算不给区间（AGENTS.md 铁律 5）；每条结论带出处（铁律 1）；表格数字唯一事实源是 `data/*.csv`（铁律 2）；小红书作者以人民币记录的实付价是原始记录，保留原文数字，另行括注 USD/NPR 折算。
- **Non-goals**：不改行程结构；不改 Q1 之外章节的非货币正文；不重新调研新的价格来源。
- **Success criteria**：`build_report.py` 通过；报告与 `sources/` 内不出现人民币计价的结论金额；Q2 的差价按三档前提分别给出，每档在 CSV 里有对应行与出处；本 plan「核对结论」表里每条问题都在 CSV 或 sources 里落地修掉。
- **Assumptions / Unknowns**：见 Assumption Ledger。

## 核对结论（已完成，2026-08-01）

换算口径：1 USD = 6.8 CNY = 129.2 NPR（129.2 由 repo 既有的 6.8 × 19 推出）。

### 算术本身对的部分

报告 Q2 的加减乘除与百分比全部复算一致：他卖的部分 USD 1,425（套餐 1,015 + 全包餐 410）、自己组 USD 909.69、差额 USD 515.31（+56.6%）、仅基础套餐 +35.7%、餐食占总差额 48%、all-in USD 1,680.15 对 Q1 主计划 USD 1,194.56 高出 40.7%。这些数与报告渲染值一致，没有计算错误。

### 问题一：自组成本漏了一项 —— 向导背夫的进山机票

他的 USD 1,015 含向导背夫的工资、食宿、保险，以及把人从加都带到 Lukla。自己组这一列只算了工资。逐项判定：

| 项 | 判定 | 依据 |
|---|---|---|
| 向导食宿保险 | 已含在日薪内，不另加 | repo 取的 USD 32/天 落在 `sources/05` 英文来源「向导 USD 25–35/天，含他们自己的食宿、保险」的区间内 |
| 背夫食宿保险 | 已含在日薪内，不另加 | `sources/14` 来源 15 的总账可反推：2 名背夫 × 15 天 × ¥150/天 = ¥4,500，4 人分摊人均 ¥1,125，与作者实报人均 ¥1,200 吻合；若另付背夫食宿（2×15×¥100 = ¥3,000）人均会是 ¥1,875，与实报不符 |
| 70L 驼包 + 急救包 + 血氧仪 | 按 0 计入合理 | `data/packing-list.csv` 第 21 行：驼包「旅行社通常提供 确认即可」；血氧仪在 packing-list 里属个人装备，按用户口径 `in_total=no` 另算 |
| **1 向导 + 3 背夫的进山机票** | **漏算** | 尼泊尔徒步业惯例是雇主承担被雇者的进出山交通。repo 内三处佐证：`sources/05` 来源 3「在 Lukla 雇可以省掉向导/背夫从加德满都飞进来的机票」；`sources/14` 来源 16「加都请背夫另需负担背夫回程车费约 ¥100」与「向导可按打包价谈，把往返 Lukla 的机票一起打包进去」 |

机票金额取决于两件事，其中票价口径在 repo 内缺出处：

| 情形 | 每人 USD | 出处状态 |
|---|---:|---|
| 向导背夫在 Lukla 会合（本地雇，或代理合同里指定会合地为 Lukla） | 0 | `sources/05` 结论段推荐的做法 |
| 从加都同机进山，按**外国人**票价（4 人 × 往返 USD 210 × 2 ÷ 6） | 280.00 | 票价有出处，但把国民按外国人价算是高估上限 |
| 从加都同机进山，按**尼泊尔国民**票价 | ~66.67 | 估算值，repo 内无国民票价出处，需补 |

结论对比（他卖的部分固定 USD 1,425）：

| 做法 | 自己组 每人 USD | 他贵出 | 6 人共 |
|---|---:|---:|---:|
| 自己组 · 向导背夫 Lukla 会合（当前报告口径） | 909.70 | +515 (+57%) | +3,092 |
| 自己组 · 加都同机，国民票价估算 | 976.36 | +449 (+46%) | +2,692 |
| 自己组 · 加都同机，外国人票价（上限） | 1,189.70 | +235 (+20%) | +1,412 |

**只比基础套餐（不买他的全包餐）时结论翻转**：他 USD 1,015 对自己组 Lukla 会合的 USD 747.93 是 +36%；对自己组加都同机按外国人票价的 USD 1,027.93，他反而便宜 USD 13。他的溢价 48% 集中在全包餐一项（USD 410 对自付 USD 161.76）。

用户粗算得出的「和代理差不多」对应「加都同机 + 买全包餐」这条组合。报告只呈现 Lukla 会合口径，且未把这个前提写进正文。

### 问题二：`sources/02` 的往返机票成本自相矛盾，并传导出一个错结论

`sources/02` 第 25 行：单程综合成本 ¥1,394–1,496，同一行写「往返约 ¥3,482」。¥3,482 ÷ 2 = ¥1,741，超出它自己的单程区间上沿；按区间算往返应为 ¥2,788–2,992（USD 410–440）。

`sources/16` 第 74 行据 ¥3,482（USD 512）与报价单标注的 USD 520 对比，得出「几乎一致，说明地面段很可能已含在价内」。按正确值 USD 410–440，他的 USD 520 高出 USD 80–110，这个推断失去依据，地面段是否含在内只能向他核实。

### 问题三：单价的出处标注错了四处

| 位置 | 现状 | 事实 |
|---|---|---|
| `cost-breakdown.csv` 拼车行 notes | 「2024-11 实付 NPR 3000 与英文来源 USD 30 吻合」 | NPR 3,000 = USD 23.2，与 USD 30 差 23%，不吻合；且 `sources/14` 内查不到这条 NPR 3,000 拼车实报，取值实际只有 `sources/02` 的 USD 30 一个来源 |
| `cost-breakdown.csv` 茶屋行 notes、`sources/14` 十一节 | 「2026-02 基础双人间约 ¥26/人/晚（来源 13）」 | ¥26/晚 出自 `sources/14` 来源 11（2024-11，NPR 6,850 全程人均，折每晚约 ¥24）；来源 13（2026-02）没有这个数。日期标错动摇「取日期最接近 2026-09-24 的值」这条取值规则 |
| `cost-breakdown.csv` 9.26 进山行 | notes 写「加都直飞票价 USD 208（sources/02）」，source 列只列 `sources/02` `sources/17` | USD 208 = (官网 225 + Thamel 190) ÷ 2，出自 `sources/14` 来源 5；`sources/02` 给的加都直飞是 ¥1,462–1,632（USD 215–240）且注明仅淡季有 |
| `quote-comparison.csv` 驼包行 | source 列写 `—` | 无出处的项按 0 计入合计，直接压低自组成本 |

### 问题四：两处换算取整与一处口径混用

- 许可证 NPR 6,000 记为 USD 46（精确值 46.44）；机场接送记 USD 2.06（精确值 2.01）。改 USD 基准后按 NPR 原价重算。
- `quote-comparison.csv` 往返机票用 USD 420（Ramechhap 往返），`cost-breakdown.csv` 主计划用 USD 418（进山直飞 208 + 返程 210），两处口径不同。
- `ext-quote.html` 同一段里出现两个「自己组」：表格 all-in 行是 USD 1,164.84（11 天、2 趟接送口径），正文却拿 Q1 的 USD 1,194.56（12 天、4 趟接送口径）与他比。差异来自天数与接送趟数，报告没说明。

### 问题五：`sources/16` 残留与当前行程矛盾的两条

第 72 行「两个适应日必须都保留」、第 73 行「9.25 当天进山要包直升机」，与当前行程（只在 Dingboche 安排一个适应日、9.26 早班机进山）矛盾。

## Alignment Gate

**I will implement**
- 修问题二至五的每一处，落在对应 CSV / sources / section。
- `quote-comparison.csv` 增加口径不对等三项，Q2 按乐观/中性/保守三档给差价，主结论用中性档。
- 取消人民币展示层：`money.py` 与 `config.py` 改为 USD 基准 + NPR 折算；`cost-breakdown.csv` 的 `pp_cny` 列去掉，`pp_usd` 成为唯一每人金额列，单价列写原生币种。
- `sources/*.md` 内 repo 自己折出的人民币价格还原为原始 USD/NPR；小红书作者原文以人民币记的实付保留原数字并补 USD/NPR 折算。
- 同步 `AGENTS.md` 货币口径铁律、`PROJECT.md`、`PATTERNS.md`、`header.html` 导语、`faq.html` 各行金额。

**I will not implement**
- 不重新调研价格来源，不引入新的 sources 文件。
- 不改行程结构、路线、图件。
- 不替换 6.8 与 19 这两个折算常数背后的取值依据。

**Open assumptions**：见 Ledger 第 1、2 条，需用户确认。

**Acceptance**：`uv run --with markdown scripts/build_report.py` 通过；`grep -c '¥' report/EBC-report.html` 只在小红书原文引述处命中；Q2 三档差价在 `quote-comparison.csv` 里各有一行；本 plan 核对结论表内每条问题在 diff 里可追到修改点。

## Assumption Ledger

| Assumption | Confidence | Impact if Wrong | Status |
|---|---:|---:|---|
| 1 · Q2 主结论用「向导背夫 Lukla 会合」口径（他贵 USD 517 / +57%），加都同机口径按外国人票价作为上界并列 | medium | high | 已按此实现；`sources/05` 结论段推荐 Lukla 会合，与「要持证向导」的顾虑可通过代理合同指定会合地兼顾。若最终确认向导背夫要从加都同机进山，改 `quote-comparison.csv` 加购行即可切换主口径 |
| 2 · 每人金额列统一 USD，单价列保留原生币种（NPR 项写 NPR，USD 项写 USD） | high | medium | 用户已确认 |
| 3 · 1 USD = 129.2 NPR，沿用 repo 既有的 6.8 × 19 推出值 | medium | low | 采用；与市场 132–136 的偏差对每人合计影响小于 USD 2 |
| 4 · 小红书作者以人民币记的实付价保留原文数字并补折算，不改写成 USD | high | medium | 采用；抹掉原文数字等于篡改一手记录 |
| 5 · 向导背夫日薪含其食宿与保险 | high | medium | 已由 `sources/05` 明文与 `sources/14` 来源 15 总账反推双向证实 |
| 6 · 尼泊尔国民的 Lukla 机票价 | low | medium | repo 内无出处，缺一份来源；Q2 按「Lukla 会合 = 0」与「外国人票价 = 上限」两端呈现，国民价档待补出处后再进表 |

## Work-Unit Specs

```yaml
- id: T1
  title: 货币层改造（USD 基准 + NPR 折算）
  file_path: scripts/reportgen/config.py, scripts/reportgen/money.py
  functions:
    - name: money.usd / money.npr / money.diff / money.amt
      behavioral_contract: |
        usd(v) 输出 "USD 1,015" 形式；npr(v) 输出 "NPR 3,000" 形式；
        diff(his, ours) 输出 "+USD 394（+38%）"；amt 保留纯数字格式化。
        config 定义 NPR_PER_USD = 129.2 与 PAX = 6，去掉 RATE。
      error_cases:
        - { condition: "ours 为 0", behavior: "百分比位写 —，不抛除零" }
  dependencies: []
  reuse_candidates: |
    money.py 现有 y()/diff()/amt() 三个函数即改造对象，无其它折算实现。
  acceptance: 构建通过且报告内金额全为 USD/NPR 形式。

- id: T2
  title: cost-breakdown.csv 去 CNY 列 + 修四处出处 + 单价改原生币种
  file_path: data/cost-breakdown.csv
  dependencies: [T1]
  acceptance: |
    22 行数据的 pp_usd 由原生币种精确折出（许可证 46.44、接送 4.02 等）；
    合计行只留 USD；拼车、茶屋、9.26 进山三行的 notes 与 source 列与本 plan
    问题三一致。

- id: T3
  title: quote-comparison.csv 增向导背夫机票行 + 两档合计
  file_path: data/quote-comparison.csv
  dependencies: [T2]
  acceptance: |
    items 块新增「1 向导 + 3 背夫进山机票」行，Lukla 会合口径记 0 并在 basis
    列写明这个前提与 sources/05 依据；驼包行的 basis 改引 packing-list 的
    「旅行社通常提供」，不再写「实际值几十美元」；
    totals 块给两行合计：Lukla 会合口径与加都同机（外国人票价上限）口径，
    ours 列取值与本 plan 结论对比表一致。

- id: T4
  title: quotes.py 装配两档 + 新 token
  file_path: scripts/reportgen/quotes.py
  dependencies: [T3]
  acceptance: |
    两档差价与百分比由 CSV 算出；另供一个「仅基础套餐」对比的 token
    （他 USD 1,015 对自己组两档），section 引用的 token 全部有供给。

- id: T5
  title: costs.py 表头与合计改 USD
  file_path: scripts/reportgen/costs.py
  dependencies: [T1, T2]
  acceptance: 两张表的「每人 ¥」列头改 USD，TOTAL_CNY token 退出。

- id: T6
  title: ext-quote.html 重写差价叙述 + 修口径混用 + 加第五件确认项
  file_path: report/sections/ext-quote.html
  dependencies: [T4]
  acceptance: |
    结论段给 Lukla 会合口径的差价并写明这个前提，加都同机口径作为上界并列；
    写出「只比基础套餐时他反而便宜 USD 13」与「溢价 48% 集中在全包餐」两条；
    all-in 段两边同口径比较，不再混用 Q1 的 12 天口径；
    机票 USD 520 的核实理由改为「比自己订往返高 USD 80–110」；
    书面确认清单增第五件：向导背夫的进山机票由谁承担、能否指定 Lukla 会合。

- id: T7
  title: 其余 section 与 faq 的金额改 USD
  file_path: report/sections/{faq,header,ext-costs,ext-transport,ext-guide,ext-insurance,ext-packing,ext-cash,ext-paperwork}.html
  dependencies: [T1, T5]
  acceptance: 无人民币计价的结论金额；header 导语改口径说明。

- id: T8
  title: sources/*.md 价格还原原始币种
  file_path: sources/{02,03,04,05,07,08,09,10,12,14,16}.md
  dependencies: []
  acceptance: |
    英文来源价格写回 USD/NPR；sources/02 第 25 行往返值改为 USD 410–440；
    sources/16 第 74 行结论按新值改写、第 72–73 行与当前行程对齐；
    sources/14 十一节的取值表改原生币种并修正来源编号。

- id: T9
  title: 权威文档同步
  file_path: AGENTS.md, PROJECT.md, PATTERNS.md
  dependencies: [T1, T2, T3]
  acceptance: 货币口径铁律改为 USD/NPR 基准；data 目录职责段与 CSV 实际列一致。
```

## Dependency Graph

```
T1 ─┬─> T2 ─> T3 ─> T4 ─> T6
    │         │
    │         └─────────────> T9
    ├─> T5 ─> T7
    └─> T7
T8 (独立)
```

## Execution Waves

- Wave 1：T1、T8（无依赖，不同文件）
- Wave 2：T2
- Wave 3：T3、T5
- Wave 4：T4、T7
- Wave 5：T6、T9
- Wave 6：全量构建 + 终审

## 交付结果

九个单元全部完成。全量测试 231 passed（改造前基线 143，本次新增 88 个货币层与 CSV 不变量用例），`build_report.py` 构建通过。

Q2 的最终数字（每人，6 人组）：

| 口径 | 他 | 自己组 | 他高出 |
|---|---:|---:|---:|
| 套餐 + 全包餐 · 向导背夫在 Lukla 会合 | USD 1,425 | USD 908 | +USD 517（+57%），6 人共 USD 3,104 |
| 套餐 + 全包餐 · 向导背夫从加都同机进山 | USD 1,425 | USD 1,186 | +USD 239（+20%），6 人共 USD 1,432 |
| 只比基础套餐 · Lukla 会合 | USD 1,015 | USD 746 | +USD 269（+36%） |
| 只比基础套餐 · 加都同机 | USD 1,015 | USD 1,025 | 他便宜 USD 10 |

溢价的 48% 落在全包餐一项（他 USD 410 对自付 USD 162）。Q1 主计划每人合计 USD 1,195。

改造范围超出原 spec 的两处：`data/itinerary.csv`（`food_lodging_cny_pp` 列改名 `food_lodging_usd_pp` 并换算，`lodge_options` 与 `notes` 里的人民币改原生币种）与 `data/packing-list.csv`（五处租赁与消耗品价格），原 spec 只点了两张费用 CSV。`packing-list.csv` 的价格进报告表格，属必改。

## Status

Completed
