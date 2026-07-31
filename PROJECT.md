# PROJECT

## 报告的目的

给 6 名同行者一份可直接照做的 EBC 徒步行前决策文档：每项决策（怎么进山、办哪些证、请不请向导、买哪个保险、带什么装备、花多少钱）给出结论、金额区间和出处，另附代理报价的逐项比价，让「自己组」和「找代理」这个选择有数字支撑。产物是单文件 HTML，浏览器打开阅读，打印成 PDF 分享。

## 行程硬约束

- 2026-09-25 上午 11:00 落地加德满都特里布万国际机场（TIA），当天出发进山。
- 2026-10-06 晚上必须回到加德满都，10-07 早上国际段飞回上海。
- 山上共 12 天，其中两个适应日（Namche、Dingboche）与一个转场日。
- 徒步方式：轻装 + 背夫背驼包 + 沿途茶屋食宿 + 自带睡袋。
- 进出山走飞机与直升机，不走陆路。
- 9-25 当天进山只有一个可行方案：提前包 2 架直升机下午从加德满都直飞 Lukla（旺季固定翼全部改从 Ramechhap 的 Manthali 机场起降，且只飞上午）。
- 10-06 返程没有缓冲日，固定翼因天气取消时当场改乘直升机，这笔额度（每人 ¥3,400–4,760）提前留出。

## 报告章节清单

`report/shell.html` 的 include 顺序即章节顺序。每个文件一节，锚点 id 写在该文件的 `<h2>` 上。

| 章节文件 | 讲什么 | 事实源 |
|---|---|---|
| `sections/header.html` | 大标题、行程窗口、6 人、汇率口径与徒步方式的总述导语 | 行程硬约束；`{{BUILD_DATE}}` |
| `sections/quote-review.html` | 代理 Majestic Trails Nepal 12 天套餐评估：按同一行程形态、同一覆盖范围逐项比价，三条要点（人数档位、砍掉 Namche 适应日、9.25 当天进山未解决），以及要向他书面确认的四件事 | `data/quote-comparison.csv`、`data/cost-breakdown.csv`、`sources/14`、`sources/02`、`sources/03`、`sources/06`、`sources/07` |
| `sections/s0-summary.html` | 七条结论速览（签证、9.25 进山、许可证、向导、背夫、保险、必要开销总价）加一条最大风险 | `sources/01`–`sources/05`、`sources/08`；`data/cost-breakdown.csv` |
| `sections/s1-visa.html` | 落地签类型与办理地点、中国边检出境所需材料、费用、机上到柜台的流程 | `sources/01` |
| `sections/s2-transport.html` | 旺季固定翼改从 Ramechhap 起降的 CAAN 规定、直升机拼机与包机价格；9.25 包机进山、10.6 固定翼出山、天气取消时的直升机兜底；全局路线图 | `sources/02`、`sources/03`；`assets/route-map-overview.png` |
| `sections/s3-permits.html` | 两个许可证（Khumbu 市政证、Sagarmatha 国家公园门票）各自的价格、办理地点、所需材料，以及本行程在哪天顺路办 | `sources/04` |
| `sections/s4-guide-porter.html` | Khumbu 地区向导豁免的现状与核实建议；请一名向导的三条理由（保险条款、旺季订房、突发处置）；1 向导 + 3 背夫的配置、价格与雇佣方式 | `sources/05`、`sources/07`、`sources/08` |
| `sections/s5-route.html` | 路段库表（11 段固定点对点路线）与 12 天定点安排表；逐段海拔小图、全程海拔剖面、徒步详图三张图件；适应日与三餐形态的说明 | `data/route-segments.csv`、`data/itinerary.csv`、`sources/06`、`sources/07`；`assets/elevation-profile-daily.png`、`assets/elevation-profile.png`、`assets/route-map-trek.png` |
| `sections/s6-packing.html` | 零装备起步的八条决策要点（睡袋、羽绒服、徒步靴、穿衣体系、头灯、净水、药品、重量约束），租与买的取舍 | `data/packing-list.csv`、`sources/05`、`sources/07`、`sources/09` |
| `sections/s7-insurance.html` | 五个保险产品逐条对比与选购三条核对项、一个实际理赔案例；现金、通讯、高反监控、天气窗口、订房五件其它事项；返程无缓冲日的警示 | `sources/02`、`sources/03`、`sources/05`、`sources/06`、`sources/07`、`sources/08`、`sources/10` |
| `sections/s8-costs.html` | 必要开销明细表与参考项表，每人合计与分摊口径 | `data/cost-breakdown.csv` |
| `sections/s9-action-plan.html` | 从现在到 9.24 登机前按时间倒排的行动清单 | `sources/05`；`data/packing-list.csv` |
| `sections/appendix-a-data.html` | 六张 CSV 的全量表，每张附一段取数说明 | `data/` 全部六张 CSV |
| `sections/appendix-b-sources.html` | `sources/*.md` 全文收录（14 份，按文件名排序，每份一个 `<section class="src">`） | `sources/*.md` |

## 出处文件

`sources/` 一个主题一份文件，含来源 URL、抓取日期和提取出的具体数字。真人走完全程的完整攻略（trip report）是最高优先级来源。当前 14 份：

`01` 签证（中国公民）· `02` 加德满都↔Lukla 固定翼（旺季改飞 Ramechhap）· `03` 加德满都↔Lukla 直升机 · `04` 两个许可证 · `05` 向导与背夫 · `06` 路线与逐日行程（Earth Trekkers 完整攻略）· `07` 沿途食宿与杂项价格 · `08` 保险（高海拔 + 直升机救援，中国公民视角）· `09` 装备清单与加德满都租赁 · `10` 中文完整攻略 · `11` GPX 轨迹文件 · `12` 加德满都市内 · `13` 带地形静态地图的选型 · `14` 代理报价单 Majestic Trails Nepal

`trek-packages.md` 存代理报价单原文，从它提取出的事实写在 `sources/14`。

## 六张 CSV 的职责与相互关系

`data/` 是表格类数据的唯一事实源，报告只引用，不另立数字。

- **`itinerary.csv`**（12 行数据，20 列）— 12 天定点安排：日期、`day_type`（徒步/适应日/转场）、`start_point`/`end_point`、`route`、茶屋与海拔、三餐、单日食宿花费、注意事项、出处。里程与爬升强度查 `route-segments.csv`，`route` 列负责把日期接到路段上。
- **`route-segments.csv`**（11 行数据，10 列）— 路段库，与日期解耦：EBC 徒步涉及的 11 段固定点对点路线（含 2 段适应日往返），每段的距离、起止海拔、海拔差、总爬升、总下降。人工整理：GPX 覆盖且无噪声标记的路段直接取 `route-track-stats.csv` 的爬升/下降（`note` 列写「GPX 实测」）；无 GPX 覆盖的路段按 `sources/06` 的文献净海拔差估算（单调假设，即中途不折返），算法与出处写在 `note` 列。哪天走哪段由 `itinerary.csv` 的 `route` 列对应。
- **`cost-breakdown.csv`**（20 行数据，12 列）— 必要开销明细与合计。`in_total=yes` 的行进合计，`in_total=no` 的行进参考表（装备按用户口径另算；兜底预备金不动用不花；放弃当天进山的备选方案供对照）。`shared_by_n` 列声明该项由几个人分摊。`category=合计` 那一行存每人区间的美元与人民币四个值。
- **`packing-list.csv`**（33 行数据，8 列）— 零装备起步的最小装备清单：分类、数量、优先级、放驼包还是随身、购买或租赁渠道、备注、出处。
- **`route-track-stats.csv`**（脚本产物，两个表块）— 由 `scripts/make_profile.py` 从 GPX 计算：第一块是 11 个村庄的累计里程、GPX 海拔、文献海拔、吸附偏差；第二块是相邻在轨村庄之间的 8 段距离与爬升/下降。峡谷段（Phakding–Monjo、Monjo–Namche）的爬升列受 GPS 噪声影响偏大，`note` 列标注，正文与 `route-segments.csv` 以文献数据为准。这张表由脚本重写，手工改动会在下次重跑时被覆盖。
- **`quote-comparison.csv`**（11 行数据，7 列）— 代理报价与自组成本的逐项比对。`block` 列把行分成 `items`（他的套餐内容逐项）与 `totals`（口径合计）。`ours_pp_usd` 列是每人单值，取自 `cost-breakdown.csv`：有明确来源值的用来源值，只给区间的取中值，取值规则写在 `basis` 列。改了 `cost-breakdown.csv` 之后同步复核这张表。

关系链：`route-track-stats.csv`（GPX 实测）→ 供 `route-segments.csv` 取爬升/下降 → 经 `itinerary.csv` 的 `route` 列接到日期；`cost-breakdown.csv`（明细与合计）→ 供 `quote-comparison.csv` 的 `ours_pp_usd` 取单值。

## 当前状态

报告全部 14 个章节、六张 CSV、14 份出处、四张图件齐备，构建通过。

**待议事项：是否请向导。** 法规上 Khumbu 地区允许不请（两个独立来源确认，其中一个更新于 2026-01-08）；报告按「请 1 名」计入费用，理由是 World Nomads 承保到 6,000m 的前提是随行有合格向导、旺季逐站订房需要人打电话、高反恶化时需要人协调直升机救援与保险对接。出发前一个月再核实一次豁免政策。这个决定同时决定保险选型。
