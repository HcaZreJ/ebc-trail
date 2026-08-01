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
| `sections/s5-route.html` | 一张合并的 12 天行程表：天、日期、起点、终点、距离、总爬升/总下降、终点海拔、当天海拔剖面小图（Day 12 转场日三列写 `—`）；徒步详图（大环线全部可走支线 + 按天分色的计划路线）与全程海拔剖面图两张图件；适应日与三餐形态的说明 | `data/itinerary.csv`、`data/day-track-stats.csv`、`sources/06`、`sources/07`、`sources/15`；`assets/route-map-trek.png`、`assets/elevation-profile.png`、`assets/day-profile-01.png`…`day-profile-11.png` |
| `sections/s6-packing.html` | 零装备起步的八条决策要点（睡袋、羽绒服、徒步靴、穿衣体系、头灯、净水、药品、重量约束），租与买的取舍 | `data/packing-list.csv`、`sources/05`、`sources/07`、`sources/09` |
| `sections/s7-insurance.html` | 五个保险产品逐条对比与选购三条核对项、一个实际理赔案例；现金、通讯、高反监控、天气窗口、订房五件其它事项；返程无缓冲日的警示 | `sources/02`、`sources/03`、`sources/05`、`sources/06`、`sources/07`、`sources/08`、`sources/10` |
| `sections/s8-costs.html` | 必要开销明细表与参考项表，每人合计与分摊口径 | `data/cost-breakdown.csv` |
| `sections/s9-action-plan.html` | 从现在到 9.24 登机前按时间倒排的行动清单 | `sources/05`；`data/packing-list.csv` |
| `sections/appendix-a-data.html` | 六张 CSV 的全量表，每张附一段取数说明 | `data/` 全部六张 CSV |
| `sections/appendix-b-sources.html` | `sources/*.md` 全文收录（16 份，按文件名排序，每份一个 `<section class="src">`） | `sources/*.md` |

## 出处文件

`sources/` 一个主题一份文件，含来源 URL、抓取日期和提取出的具体数字。真人走完全程的完整攻略（trip report）是最高优先级来源。当前 15 个编号（`14` 号下两份：代理报价单与小红书实地情报）：

`01` 签证（中国公民）· `02` 加德满都↔Lukla 固定翼（旺季改飞 Ramechhap）· `03` 加德满都↔Lukla 直升机 · `04` 两个许可证 · `05` 向导与背夫 · `06` 路线与逐日行程（Earth Trekkers 完整攻略）· `07` 沿途食宿与杂项价格 · `08` 保险（高海拔 + 直升机救援，中国公民视角）· `09` 装备清单与加德满都租赁 · `10` 中文完整攻略 · `11` GPX 轨迹文件 · `12` 加德满都市内 · `13` 带地形静态地图的选型 · `14` 代理报价单 Majestic Trails Nepal + 小红书中文徒步者实地情报 · `15` KMZ 实测大环线轨迹（里程、爬升、海拔剖面、地形图的共同输入，含 OpenTopoData SRTM30m 与 Overpass API 的用法）

`trek-packages.md` 存代理报价单原文，从它提取出的事实写在 `sources/14`。

## data 目录八个文件的职责与相互关系

`data/` 是表格类数据与轨迹几何的事实源。六张 CSV 是报告表格唯一的数字来源，改数字就改 CSV；两个 JSON 是图件脚本之间传递逐日轨迹点的中间产物，不直接进报告。

- **`itinerary.csv`**（人工整理，12 行数据，18 列）— 12 天定点安排：日期、`day_type`（徒步/适应日/转场）、`start_point`/`end_point`、`route`、茶屋与海拔、三餐、单日食宿花费、注意事项、出处。距离与爬升/下降查 `day-track-stats.csv`，两张表按 `day` 列对齐拼成 Section 5 的合并表。
- **`day-track-stats.csv`**（脚本产物，`scripts/day_tracks.py` 写出，11 行数据即 Day 1–11，7 列）— 逐日距离、总爬升、总下降、起点/终点海拔、数据来源。`source` 列区分 KMZ 实测 / GPX 实测 / OSM+SRTM30m 及其组合，与 `day_tracks.py` 里 `DAY_SOURCES` 常量一一对应。算法：轨迹按 25 m 重采样、海拔用窗口 5 的滚动中位数平滑压掉 GPS 跳变、再按 8 m 滞回阈值累计爬升/下降，三个参数写在 `day_tracks.py` 顶部，标定依据见 `sources/15`。
- **`day-tracks.json`**（脚本产物，`scripts/day_tracks.py` 写出）— Day 1–11 逐点轨迹坐标（经度、纬度、海拔），是 `day-track-stats.csv`、11 张逐日剖面小图、全程剖面图、徒步详图共同的上游中间产物。
- **`gap-legs.json`**（脚本产物 + 缓存，`scripts/gap_legs.py` 写出）— KMZ 大环线与 GPX 都没走到的 4 段（两个海拔适应点往返、Lobuche–Pheriche、Pheriche–Pangboche）按 OSM 步道几何 + SRTM30m 高程补测出的逐点序列，供 `day_tracks.py` 装配进对应天数。文件已含全部 4 段时构建期不再发网络请求。
- **`cost-breakdown.csv`**（人工整理，21 行数据，10 列）— 必要开销明细与合计。`in_total=yes` 的行进合计，`in_total=no` 的行进参考表（装备按用户口径另算；兜底预备金不动用不花；放弃当天进山的备选方案供对照）。`shared_by_n` 列声明该项由几个人分摊。`pp_usd` 与 `pp_cny` 是每人单点最佳估算，取值规则见该行 `notes`。`category=合计` 那一行存每人合计的美元与人民币两个值，以人民币列为准，美元列由各行分别取整后求和。
- **`packing-list.csv`**（人工整理，34 行数据，8 列）— 零装备起步的最小装备清单：分类、数量、优先级、放驼包还是随身、购买或租赁渠道、备注、出处。
- **`route-track-stats.csv`**（脚本产物，`scripts/make_profile.py` 写出，10 行数据，5 列）— Day 1–8 接成 Lukla→EBC 上山走廊，10 个在这条走廊上的村庄各自吸附到轨迹后的累计里程、轨迹实测海拔、文献海拔、吸附偏差。Pheriche 只在 Day 9–10 下撤时经过，不在这条上山走廊上，退出这张表，它的里程与海拔在 `day-track-stats.csv` 的 Day 9/10 行里。
- **`quote-comparison.csv`**（人工整理，11 行数据，7 列）— 代理报价与自组成本的逐项比对。`block` 列把行分成 `items`（他的套餐内容逐项）与 `totals`（口径合计）。`ours_pp_usd` 列是每人单值，取自 `cost-breakdown.csv`，取值规则写在 `basis` 列。改了 `cost-breakdown.csv` 之后同步复核这张表。

关系链：`scripts/gap_legs.py`（OSM+SRTM30m 补测 4 段）连同 `assets/ebc-loop.kml`（KMZ 大环线）与 `assets/Everest_Base_Camp.gpx`（标准直上直下线）一起喂给 `scripts/day_tracks.py`，装配出 `day-tracks.json` 与 `day-track-stats.csv`；`day-tracks.json` 再喂给 `scripts/make_profile.py`（11 张剖面小图 + 全程剖面图 + `route-track-stats.csv`）与 `scripts/make_map.py`（徒步详图）；`day-track-stats.csv` 与 `itinerary.csv` 按 `day` 对齐拼成 Section 5 的合并表；`cost-breakdown.csv`（明细与合计）→ 供 `quote-comparison.csv` 的 `ours_pp_usd` 取单值。

## 当前状态

报告全部 14 个章节、六张 CSV、14 份出处、四张图件齐备，构建通过。

**待议事项：是否请向导。** 法规上 Khumbu 地区允许不请（两个独立来源确认，其中一个更新于 2026-01-08）；报告按「请 1 名」计入费用，理由是 World Nomads 承保到 6,000m 的前提是随行有合格向导、旺季逐站订房需要人打电话、高反恶化时需要人协调直升机救援与保险对接。出发前一个月再核实一次豁免政策。这个决定同时决定保险选型。
