# PROJECT

## 报告的目的

给 6 名同行者一份可直接照做的 EBC 徒步行前决策文档：每项决策（怎么进山、办哪些证、请不请向导、买哪个保险、带什么装备、花多少钱）给出结论、金额和出处，另附代理报价的逐项比价，让「自己组」和「找代理」这个选择有数字支撑。产物是单文件 HTML，浏览器打开阅读，打印成 PDF 分享。

## 行程硬约束

- 2026-09-25 上午 11:00 落地加德满都特里布万国际机场（TIA），当天出发进山。
- 2026-10-06 晚上必须回到加德满都，10-07 早上国际段飞回上海。
- 山上共 12 天，其中两个适应日（Namche、Dingboche）与一个转场日。
- 徒步方式：轻装 + 背夫背驼包 + 沿途茶屋食宿 + 自带睡袋。
- 进出山走飞机与直升机，不走陆路。
- 9-25 当天进山只有一个可行方案：提前包 2 架直升机下午从加德满都直飞 Lukla（旺季固定翼全部改从 Ramechhap 的 Manthali 机场起降，且只飞上午）。
- 10-06 返程没有缓冲日，固定翼因天气取消时当场改乘直升机，这笔额度（每人 ¥3,400–4,760）提前留出。

## 报告结构：三层

- **速览**（`sections/faq.html`）：13 个问题各配一句话回答，问题链接到对应详解块。
- **详解**（`sections/ext-*.html`）：每个问题一个 `<section class="ext">` 块，讲答案的依据、关键数字与必要表格，标题带跳回速览的回链，句末括注链接到出处层。
- **出处**（`sections/sources.html`）：`sources/*.md` 全文收录，每份开头由构建脚本自动列出「被引用于」的问题回链。

## 报告章节清单

`report/shell.html` 的 include 顺序即章节顺序。速览行、详解块与问题的对应关系如下（锚点契约见 PATTERNS.md）。

| 章节文件 | 讲什么 | 事实源 |
|---|---|---|
| `sections/header.html` | 大标题、行程窗口、汇率与取值口径导语 | 行程硬约束；`{{BUILD_DATE}}` |
| `sections/faq.html` | 速览：13 个问题（Q1–Q13）各一句话回答 | 各详解块的结论 |
| `sections/ext-intro.html` | 详解层的标题与阅读指引 | — |
| `sections/ext-costs.html` | Q1 总价：必要开销明细表与参考表、分摊与取值口径 | `data/cost-breakdown.csv` |
| `sections/ext-quote.html` | Q2 Majestic Trails 12 天套餐评估：结论、签约前要改的三处、两张比价表、四件书面确认 | `data/quote-comparison.csv`、`data/cost-breakdown.csv`、`sources/15`、`02`、`03`、`04`、`05`、`06`、`07` |
| `sections/ext-transport.html` | Q3 9.25 当天进山（双直升机包机）+ Q4 10.6 返程与直升机兜底；全局路线图 | `sources/01`、`02`、`03`、`14`；`assets/route-map-overview.png` |
| `sections/ext-route.html` | Q5 12 天行程：日期安排表、路段库表、三张图件、9.26 备选行程 | `data/itinerary.csv`、`data/route-segments.csv`、`sources/06`、`11`；`assets/` 三张图 |
| `sections/ext-health.html` | Q6 高反：适应日实证、Diamox、血氧监控、下撤原则 | `sources/06`、`09`、`14` |
| `sections/ext-guide.html` | Q7 向导背夫：豁免现状、请向导的三条理由、配置价格、雇佣方式 | `sources/05`、`07`、`08`、`14` |
| `sections/ext-paperwork.html` | Q8 签证 + Q9 许可证 | `sources/01`、`04`、`14` |
| `sections/ext-insurance.html` | Q10 保险：产品核实表、选购三条核对项、买后动作 | `sources/08`、`14` |
| `sections/ext-packing.html` | Q11 装备：决策要点表 + 33 项全量清单 | `data/packing-list.csv`、`sources/07`、`09`、`14` |
| `sections/ext-cash.html` | Q12 现金、通讯、市内安全与天气窗口 | `sources/07`、`10`、`12`、`14` |
| `sections/ext-todo.html` | Q13 从现在到 9.24 登机前按时间倒排的行动清单 | `sources/05`；各详解块 |
| `sections/sources.html` | 出处层：`sources/*.md` 全文（按文件名排序，回链由 `scripts/reportgen/sources.py` 自动生成） | `sources/*.md` |

## 出处文件

`sources/` 一个主题一份文件，含来源 URL、抓取日期和提取出的具体数字。真人走完全程的完整攻略（trip report）是最高优先级来源。当前 15 份：

`01` 签证（中国公民）· `02` 加德满都↔Lukla 固定翼（旺季改飞 Ramechhap）· `03` 加德满都↔Lukla 直升机 · `04` 两个许可证 · `05` 向导与背夫 · `06` 路线与逐日行程（Earth Trekkers 完整攻略）· `07` 沿途食宿与杂项价格 · `08` 保险（高海拔 + 直升机救援，中国公民视角）· `09` 装备清单与加德满都租赁 · `10` 中文完整攻略 · `11` GPX 轨迹文件 · `12` 加德满都市内 · `13` 带地形静态地图的选型 · `14` 小红书实地情报汇总 · `15` 代理报价单 Majestic Trails Nepal

`trek-packages.md` 存代理报价单原文，从它提取出的事实写在 `sources/15`。

## 六张 CSV 的职责与相互关系

`data/` 是表格类数据的唯一事实源，报告只引用，不另立数字。

- **`itinerary.csv`**（12 行数据，20 列）— 12 天定点安排：日期、`day_type`（徒步/适应日/转场）、`start_point`/`end_point`、`route`、茶屋与海拔、三餐、单日食宿花费、注意事项、出处。里程与爬升强度查 `route-segments.csv`，`route` 列负责把日期接到路段上。
- **`route-segments.csv`**（11 行数据，10 列）— 路段库，与日期解耦：EBC 徒步涉及的 11 段固定点对点路线（含 2 段适应日往返），每段的距离、起止海拔、海拔差、总爬升、总下降。人工整理：GPX 覆盖且无噪声标记的路段直接取 `route-track-stats.csv` 的爬升/下降（`note` 列写「GPX 实测」）；无 GPX 覆盖的路段按 `sources/06` 的文献净海拔差估算（单调假设，即中途不折返），算法与出处写在 `note` 列。哪天走哪段由 `itinerary.csv` 的 `route` 列对应。
- **`cost-breakdown.csv`**（21 行数据，10 列）— 必要开销明细与合计。`in_total=yes` 的行进合计，`in_total=no` 的行进参考表（装备按用户口径另算；兜底预备金不动用不花；放弃当天进山的备选方案供对照）。`shared_by_n` 列声明该项由几个人分摊。`pp_usd` 与 `pp_cny` 是每人单点最佳估算，取值规则见该行 `notes`。`category=合计` 那一行存每人合计的美元与人民币两个值，以人民币列为准，美元列由各行分别取整后求和。
- **`packing-list.csv`**（33 行数据，8 列）— 零装备起步的最小装备清单：分类、数量、优先级、放驼包还是随身、购买或租赁渠道、备注、出处。
- **`route-track-stats.csv`**（脚本产物，两个表块）— 由 `scripts/make_profile.py` 从 GPX 计算：第一块是 11 个村庄的累计里程、GPX 海拔、文献海拔、吸附偏差；第二块是相邻在轨村庄之间的 8 段距离与爬升/下降。峡谷段（Phakding–Monjo、Monjo–Namche）的爬升列受 GPS 噪声影响偏大，`note` 列标注，正文与 `route-segments.csv` 以文献数据为准。这张表由脚本重写，手工改动会在下次重跑时被覆盖。
- **`quote-comparison.csv`**（11 行数据，7 列）— 代理报价与自组成本的逐项比对。`block` 列把行分成 `items`（他的套餐内容逐项）与 `totals`（口径合计）。`ours_pp_usd` 列是每人单值，取自 `cost-breakdown.csv`，取值规则写在 `basis` 列。改了 `cost-breakdown.csv` 之后同步复核这张表。

关系链：`route-track-stats.csv`（GPX 实测）→ 供 `route-segments.csv` 取爬升/下降 → 经 `itinerary.csv` 的 `route` 列接到日期；`cost-breakdown.csv`（明细与合计）→ 供 `quote-comparison.csv` 的 `ours_pp_usd` 取单值。

## 当前状态

报告为三层结构（速览 13 问 + 详解 12 个文件 + 出处 15 份），六张 CSV、四张图件齐备，构建通过，层间锚点成对。

**待议事项一：是否请向导。** 法规上 Khumbu 地区允许不请（两个独立来源确认，其中一个更新于 2026-01-08）；报告按「请 1 名」计入费用，理由是 World Nomads 承保到 6,000m 的前提是随行有合格向导、旺季逐站订房需要人打电话、高反恶化时需要人协调直升机救援与保险对接。出发前一个月再核实一次豁免政策。这个决定同时决定保险选型。

**待议事项二：是否走 Majestic Trails 套餐。** 报告结论是价格可接受（跟团区间最低端），但要等他答复两处行程修改（恢复 Namche 适应日、9.25 直升机进山单独报价）与四件书面确认（详见 ext-quote 一节）再定。这个决定与待议事项一联动：走套餐则向导背夫由他配。
