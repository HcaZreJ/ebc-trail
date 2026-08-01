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
| `sections/ext-quote.html` | Q2 Majestic Trails 12 天套餐评估：结论、签约前要改的三处、两张比价表、四件书面确认 | `data/quote-comparison.csv`、`data/cost-breakdown.csv`、`sources/16`、`02`、`03`、`04`、`05`、`06`、`07` |
| `sections/ext-transport.html` | Q3 9.25 当天进山（双直升机包机）+ Q4 10.6 返程与直升机兜底；全局路线图 | `sources/01`、`02`、`03`、`14`；`assets/route-map-overview.png` |
| `sections/ext-route.html` | Q5 12 天行程：一张合并的逐日表（距离、总爬升/总下降、终点海拔、当天海拔剖面小图，Day 12 转场日三列写 `—`）、徒步详图（大环线可走支线 + 按天分色计划路线）与全程剖面两张图件、9.26 备选行程 | `data/itinerary.csv`、`data/day-track-stats.csv`、`sources/06`、`13`、`15`；`assets/route-map-trek.png`、`elevation-profile.png`、`day-profile-01.png`…`day-profile-11.png` |
| `sections/ext-health.html` | Q6 高反：适应日实证、Diamox、血氧监控、下撤原则 | `sources/06`、`09`、`14` |
| `sections/ext-guide.html` | Q7 向导背夫：豁免现状、请向导的三条理由、配置价格、雇佣方式 | `sources/05`、`07`、`08`、`14` |
| `sections/ext-paperwork.html` | Q8 签证 + Q9 许可证 | `sources/01`、`04`、`14` |
| `sections/ext-insurance.html` | Q10 保险：产品核实表、选购三条核对项、买后动作 | `sources/08`、`14` |
| `sections/ext-packing.html` | Q11 装备：决策要点表 + 全量清单 | `data/packing-list.csv`、`sources/07`、`09`、`14` |
| `sections/ext-cash.html` | Q12 现金、通讯、市内安全与天气窗口 | `sources/07`、`10`、`12`、`14` |
| `sections/ext-todo.html` | Q13 从现在到 9.24 登机前按时间倒排的行动清单 | `sources/05`；各详解块 |
| `sections/sources.html` | 出处层：`sources/*.md` 全文（按文件名排序，回链由 `scripts/reportgen/sources.py` 自动生成） | `sources/*.md` |

## 出处文件

`sources/` 一个主题一份文件，含来源 URL、抓取日期和提取出的具体数字。真人走完全程的完整攻略（trip report）是最高优先级来源。当前 16 份：

`01` 签证（中国公民）· `02` 加德满都↔Lukla 固定翼（旺季改飞 Ramechhap）· `03` 加德满都↔Lukla 直升机 · `04` 两个许可证 · `05` 向导与背夫 · `06` 路线与逐日行程（Earth Trekkers 完整攻略）· `07` 沿途食宿与杂项价格 · `08` 保险（高海拔 + 直升机救援，中国公民视角）· `09` 装备清单与加德满都租赁 · `10` 中文完整攻略 · `11` GPX 轨迹文件 · `12` 加德满都市内 · `13` 带地形静态地图的选型 · `14` 小红书中文徒步者实地情报 · `15` KMZ 实测大环线轨迹（里程、爬升、海拔剖面、地形图的共同输入，含 OpenTopoData SRTM30m 与 Overpass API 的用法）· `16` 代理报价单 Majestic Trails Nepal

`trek-packages.md` 存代理报价单原文，从它提取出的事实写在 `sources/16`。

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

报告为三层结构（速览 13 问 + 详解 12 个文件 + 出处 16 份），构建通过，层间锚点成对。逐日里程与海拔剖面来自 KMZ 大环线实测轨迹，缺口 4 段由 OSM 步道 + SRTM30m 补测。push 到 main 后 GitHub Actions 自动重新构建并发布到 `https://hcazrej.github.io/ebc-trail/`（流程见 DEVFLOW.md「发布到 GitHub Pages」）。

**待议事项一：是否请向导。** 法规上 Khumbu 地区允许不请（两个独立来源确认，其中一个更新于 2026-01-08）；报告按「请 1 名」计入费用，理由是 World Nomads 承保到 6,000m 的前提是随行有合格向导、旺季逐站订房需要人打电话、高反恶化时需要人协调直升机救援与保险对接。出发前一个月再核实一次豁免政策。这个决定同时决定保险选型。

**待议事项二：是否走 Majestic Trails 套餐。** 报告结论是价格可接受（跟团区间最低端），但要等他答复两处行程修改（恢复 Namche 适应日、9.25 直升机进山单独报价）与四件书面确认（详见 ext-quote 一节）再定。这个决定与待议事项一联动：走套餐则向导背夫由他配。
