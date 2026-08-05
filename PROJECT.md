# PROJECT

## 报告的目的

给 6 名同行者一份可直接照做的 EBC 徒步行前决策文档：每项决策（怎么进山、办哪些证、请不请向导、买哪个保险、带什么装备、花多少钱）给出结论、金额和出处，另附代理报价的逐项比价，让「自己组」和「找代理」这个选择有数字支撑。产物是单文件 HTML，浏览器打开阅读，打印成 PDF 分享。

## 行程硬约束

- 2026-09-25 上午 11:00 落地加德满都特里布万国际机场（TIA），当天不进山，市内休整一晚。
- 2026-09-26 早班机飞 Lukla，当天徒步进山至 Phakding。
- 2026-10-06 晚上必须回到加德满都，10-07 早上国际段飞回上海。
- 山上共 12 天：9.25 加都休整 1 天 + 9.26–10.5 共 10 个徒步/适应日（只在 Dingboche 安排一个适应日）+ 10.6 转场日 1 天。
- 徒步方式：轻装 + 背夫背驼包 + 沿途茶屋食宿 + 自带睡袋。
- 进出山往返都坐直升机，不走陆路：9.26 早班加都→Lukla，10.6 早班 Lukla→加都。直升机始终从加德满都国内机场直飞，旺季固定翼改飞 Ramechhap 的临时分流影响不到它（sources/03、17）。
- 直升机费用按拼机 USD 404/人/程（USD 400 实报加 NPR 500 机场税）作单点估算，2026 年挂牌 USD 650–700/程是上行风险；一架最多坐 4–5 人，6 人两程共 12 人次座位、拆两架、订座报体重。
- 10-06 返程没有缓冲日，订最早班；拼机订不到座时升级包机，差额预备金每人两程约 USD 342 提前留出。

## 报告结构：四层

信息按「读者要拿它做什么」排序：先给要拍板的两个决定，再给行程强度，支持信息压在后面，出处全部收到最末。

- **摘要**（`sections/summary.html`）：六行结论，每行链到对应节。
- **核心**（`sections/core-*.html`）：§1–§4，同行者最需要读完的四节。
- **支持信息**（`sections/sup-*.html`）：§5–§8，结论与关键数字都在，篇幅压到能查阅的密度。
- **References**（`sections/references.html`）：`{{REFERENCES}}` 由 `scripts/reportgen/citations.py` 渲染成编号条目，给标题、来源方、抓取日期、按域名去重的链接，带「引用于 §N」回链与折叠的要点摘录；没被正文引用过的出处归到第二组「数据与方法来源」。

每节是一个 `<section class="sec" id="s<N>-<slug>">` 块，标题带跳回摘要的回链，事实处用 `[[NN]]` 角标（契约见 PATTERNS.md）。

## 报告章节清单

`report/shell.html` 的 include 顺序即章节顺序，也是节号顺序。

| 章节文件 | 讲什么 | 事实源 |
|---|---|---|
| `sections/header.html` | 大标题、行程窗口、行程硬约束与计价口径导语 | 行程硬约束；`{{BUILD_DATE}}` |
| `sections/summary.html` | 摘要：六行结论（套餐、行前准备、保险、行程强度、总价、返程风险） | 各节结论；`{{TOTAL_USD}}` |
| `sections/core-intro.html` | 核心层标题与一句阅读指引 | — |
| `sections/core-deal.html` | §1 Majestic Trails 12 天套餐值不值：直升机版 USD 1,400 与自组的两档口径差价、拼机实报下沿与 2026 挂牌两种敏感度、两张比价表、四件书面确认 | `data/quote-comparison.csv`、`data/cost-breakdown.csv`、`sources/02`、`03`、`04`、`05`、`07`、`14`、`16` |
| `sections/core-prep.html` | §2 行前准备：按时间倒排的行动清单 + 装备决策表 + 全量装备清单 | `data/packing-list.csv`、`sources/01`、`04`、`05`、`07`、`09`、`14` |
| `sections/core-insurance.html` | §3 保险：九行方案表（主选、叠买、升级、国内外备选、三类排除）、推荐组合与人均金额、安盛援助 5,500m 服务免责这个未决项、下单前五件书面口径、平安 B 款与 C 款的区别 | `sources/08`、`14`、`18`、`19` |
| `sections/core-route.html` | §4 12 天行程与强度：开篇直给强度结论、一张合并的逐日表（距离、总爬升/总下降、终点海拔、当天剖面小图，Day 1 与 Day 12 三列写 `—`）、徒步详图与全程剖面 | `data/itinerary.csv`、`data/day-track-stats.csv`、`sources/06`、`13`、`15`；`assets/route-map-trek.png`、`elevation-profile.png`、`day-profile-02.png`…`day-profile-11.png` |
| `sections/sup-intro.html` | 支持层标题与一句阅读指引 | — |
| `sections/sup-cost.html` | §5 花多少钱：必要开销明细表与参考表、分摊与取值口径 | `data/cost-breakdown.csv` |
| `sections/sup-transport.html` | §6 进出山交通与返程风险：往返直升机的价格口径与班次窗口、6 人拆两架与订座报体重、10.6 无缓冲日的包机差额预备金与残余天气风险；全局路线图 | `sources/02`、`03`、`14`、`17`；`assets/route-map-overview.png` |
| `sections/sup-crew.html` | §7 高反与向导背夫：一个适应日的代价、Diamox、血氧仪、下撤原则、请向导的三条理由与配置价格 | `sources/05`、`06`、`07`、`08`、`09`、`14`、`16` |
| `sections/sup-onsite.html` | §8 签证、许可证、现金与通讯：落地签流程、两个证在哪办、现金额度、Ncell 与 Everest Link、市内安全与天气窗口 | `sources/01`、`04`、`07`、`10`、`12`、`14` |
| `sections/references.html` | References 层标题与 `{{REFERENCES}}` | `sources/*.md` |

## 出处文件

`sources/` 一个主题一份文件，含来源 URL、抓取日期和提取出的具体数字。真人走完全程的完整攻略（trip report）是最高优先级来源。文件名前两位是编号，它同时是正文角标显示的数字与 References 条目的 `#ref-NN` 锚点，所以编号一经使用就不重排。当前 18 份：

`01` 签证（中国公民）· `02` 加德满都↔Lukla 固定翼（旺季改飞 Ramechhap）· `03` 加德满都↔Lukla 直升机 · `04` 两个许可证 · `05` 向导与背夫 · `06` 路线与逐日行程（Earth Trekkers 完整攻略）· `07` 沿途食宿与杂项价格 · `08` 保险（高海拔 + 直升机救援，中国公民视角）· `09` 装备清单与加德满都租赁 · `10` 中文完整攻略 · `11` GPX 轨迹文件 · `12` 加德满都市内 · `13` 带地形静态地图的选型 · `14` 小红书中文徒步者实地情报 · `15` KMZ 实测大环线轨迹（里程、爬升、海拔剖面、地形图的共同输入，含 OpenTopoData SRTM30m 与 Overpass API 的用法）· `16` 代理报价单 Majestic Trails Nepal · `17` 与 Majestic Trails Nepal 向导 Bibek 的直接沟通（加都↔Lukla 旺季起降机场的不确定性）· `18` 两步路（携保）平台 208 个在售计划的逐条款核查，含承保国家名单原文、京东安联那款的 ¥8,000 尼泊尔直升机子限额与费率表，以及平台外三条替代路径的对照 · `19` 中国大陆居民可投保方案的逐条款核查（World Nomads 拒中国居民的实测、保游尊享/平安臻享的保单样本与十八份条款、华泰畅意玩 2 号与大地畅行全球两个国内备选、SafetyWing 等国际产品的居住国限制、Global Rescue 与 ÖAV/DAV/AAC 等会籍型救援方案、6 人同时撤离的赔付口径）

`trek-packages.md` 存代理报价单原文，从它提取出的事实写在 `sources/16`。

## data 目录八个文件的职责与相互关系

`data/` 是表格类数据与轨迹几何的事实源。六张 CSV 是报告表格唯一的数字来源，改数字就改 CSV；两个 JSON 是图件脚本之间传递逐日轨迹点的中间产物，不直接进报告。

- **`itinerary.csv`**（人工整理，12 行数据，18 列）— 12 天定点安排：日期、`day_type`（转场/徒步/适应日）、`start_point`/`end_point`、`route`、茶屋与海拔、三餐、单日食宿花费、注意事项、出处。Day 1（加都休整）与 Day 12（转场回加都）没有徒步轨迹；距离与爬升/下降查 `day-track-stats.csv`，两张表按 `day` 列对齐拼成 Section 5 的合并表。
- **`day-track-stats.csv`**（脚本产物，`scripts/day_tracks.py` 写出，10 行数据即 Day 2–11，7 列）— 逐日距离、总爬升、总下降、起点/终点海拔、数据来源。`source` 列区分 KMZ 实测 / GPX 实测 / OSM+SRTM30m 及其组合，与 `day_tracks.py` 里 `DAY_SOURCES` 常量一一对应。算法：轨迹按 25 m 重采样、海拔用窗口 5 的滚动中位数平滑压掉 GPS 跳变、再按 8 m 滞回阈值累计爬升/下降，三个参数写在 `day_tracks.py` 顶部，标定依据见 `sources/15`。
- **`day-tracks.json`**（脚本产物，`scripts/day_tracks.py` 写出）— Day 2–11 逐点轨迹坐标（经度、纬度、海拔），是 `day-track-stats.csv`、10 张逐日剖面小图、全程剖面图、徒步详图共同的上游中间产物。
- **`gap-legs.json`**（脚本产物 + 缓存，`scripts/gap_legs.py` 写出）— KMZ 大环线与 GPX 都没走到的 4 段（Namche 往返 Everest View、Dingboche 往返 Nangkartshang、Lobuche–Pheriche、Pheriche–Pangboche）按 OSM 步道几何 + SRTM30m 高程补测出的逐点序列；`day_tracks.py` 只装配其中 3 段（行程只在 Dingboche 安排适应日，Namche 往返段缓存着但不参与装配）。文件已含全部 4 段时构建期不再发网络请求。
- **`cost-breakdown.csv`**（人工整理，18 行数据，9 列）— 必要开销明细与合计。`in_total=yes` 的行进合计，`in_total=no` 的行进参考表（装备按用户口径另算；拼机订不到座时的包机差额预备金不动用不花）。`shared_by_n` 列声明该项由几个人分摊。`unit_price_quote` 列写该项报出时的原始货币（许可证 NPR 3000、向导 USD 32/天），`pp_usd` 是每人单点最佳估算的美元值，取值规则见该行 `notes`。`category=合计` 那一行存每人合计，由各行精确值求和后取整。
- **`packing-list.csv`**（人工整理，34 行数据，8 列）— 零装备起步的最小装备清单：分类、数量、优先级、放驼包还是随身、购买或租赁渠道、备注、出处。
- **`route-track-stats.csv`**（脚本产物，`scripts/make_profile.py` 写出，10 行数据，5 列）— Day 2–8 接成 Lukla→EBC 上山走廊，10 个在这条走廊上的村庄各自吸附到轨迹后的累计里程、轨迹实测海拔、文献海拔、吸附偏差。Pheriche 只在 Day 9–10 下撤时经过，不在这条上山走廊上，退出这张表，它的里程与海拔在 `day-track-stats.csv` 的 Day 9/10 行里。
- **`quote-comparison.csv`**（人工整理，13 行数据，7 列）— 代理报价与自组成本的逐项比对。`block` 列把行分成 `items`（他的套餐内容逐项，9 行）与 `totals`（口径合计，4 行）。`ours_pp_usd` 列是每人单值，取自 `cost-breakdown.csv`，取值规则写在 `basis` 列。自组成本分两档：向导背夫在 Lukla 会合时不承担他们的进山交通，从加德满都随行（坐固定翼）时要付他们的往返，`totals` 块里的加购行是这笔钱。改了 `cost-breakdown.csv` 之后同步复核这张表。

关系链：`scripts/gap_legs.py`（OSM+SRTM30m 补测 4 段）连同 `assets/ebc-loop.kml`（KMZ 大环线）与 `assets/Everest_Base_Camp.gpx`（标准直上直下线）一起喂给 `scripts/day_tracks.py`，装配出 `day-tracks.json` 与 `day-track-stats.csv`；`day-tracks.json` 再喂给 `scripts/make_profile.py`（11 张剖面小图 + 全程剖面图 + `route-track-stats.csv`）与 `scripts/make_map.py`（徒步详图）；`day-track-stats.csv` 与 `itinerary.csv` 按 `day` 对齐拼成 Section 5 的合并表；`cost-breakdown.csv`（明细与合计）→ 供 `quote-comparison.csv` 的 `ours_pp_usd` 取单值。

## 当前状态

报告为四层结构（摘要 6 行 + 核心 §1–§4 + 支持 §5–§8 + References 19 条），构建通过，层间锚点成对、无悬空角标，全量测试 306 passed。逐日里程与海拔剖面来自 KMZ 大环线实测轨迹，缺口 4 段由 OSM 步道 + SRTM30m 补测。push 到 main 后 GitHub Actions 自动重新构建并发布到 `https://hcazrej.github.io/ebc-trail/`（流程见 DEVFLOW.md「发布到 GitHub Pages」）。

**待议事项一：是否请向导。** 法规上 Khumbu 地区允许不请（两个独立来源确认，其中一个更新于 2026-01-08）；报告按「请 1 名」计入费用，理由是旺季逐站订房需要人打电话、高反恶化时需要人协调直升机救援与保险对接，以及持证向导在保险上有两处用处：华泰畅意玩 2 号要求户外运动「经过专业人士培训和指导」，而多数意外险主险把「探险活动」列为除外高风险运动，随行持证向导的商业徒步团是反驳这条认定的依据。出发前一个月再核实一次豁免政策。

**待议事项二：是否走 Majestic Trails 直升机版套餐（USD 1,400/人，2026-08-05 报价，见 sources/16）。** 本行程与他的日程结构一致（9.25 加都休整、只在 Dingboche 安排一个适应日），报告结论是可以签：直升机升级差价 USD 385 与市场差价约 USD 390 一致；按拼机实报下沿 USD 404/程 算自组便宜每人约 USD 266（套餐本体口径、Lukla 会合档），按 2026 年挂牌 USD 650–700/程 算自组反超、他更便宜，且 12 人次旺季座位的凑座与天气改签由他兜。签约前等四件书面确认（1,400 按 6 人成团、含餐与否、含不含机场税；拼机还是包机、拆架与天气取消的处理；10.6 当天傍晚前回加都；向导背夫日薪口径与其固定翼交通安排）再定。这个决定与待议事项一联动：走套餐则向导背夫由他配。
