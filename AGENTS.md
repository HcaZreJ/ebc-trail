# EBC Trail 调研 Repo

2026-09-24 → 2026-10-07 尼泊尔 EBC（Everest Base Camp）徒步的行前调研与规划。**6 人同行**。硬约束：9-25 上午 11:00 落地加德满都后当天出发进山，10-6 晚上必须回到加德满都（10-7 早国际段回上海）。徒步方式：轻装 + 背夫背驼包 + 沿途茶屋食宿 + 自带睡袋；进出山走飞机/直升机，不走陆路。待议事项：是否请向导（当前报告按「请 1 名」计入费用）。

## 目录结构

- `sources/` — 调研出处。每个主题一个文件，含 URL、抓取日期、提取的具体数字。**报告里的每个事实都必须能追溯到这里的某个文件**。只放核心来源，垃圾信息不进来。真人完整攻略（走完全程的 trip report）是最高优先级来源。
- `data/` — 表格类数据的 source of truth（CSV）。报告只引用，不另立数字：
  - `itinerary.csv` — 12 天逐日行程（日期、区段、里程、海拔、茶屋、三餐、单日花费）
  - `cost-breakdown.csv` — 必要开销明细与合计（`in_total=no` 的行不计入总价：装备按用户口径另算，兜底预备金不动用不花）
  - `packing-list.csv` — 零装备者的最小装备清单
  - `route-track-stats.csv` — 由 GPX 计算的逐村里程/海拔（脚本产物，不手改；Phakding–Namche 峡谷段爬升列受 GPS 噪声影响，以文献数据为准）
- `assets/` — `Everest_Base_Camp.gpx`（轨迹原始文件，来源见 `sources/11`）、`elevation-profile.png`（海拔剖面）、`route-map-trek.png` 与 `route-map-overview.png`（OpenTopoMap 瓦片合成的地形路线图，选型依据见 `sources/13`）、`.tile-cache/`（瓦片缓存，可删）
- `scripts/route_points.py` — 全线关键点位坐标（村庄、机场、Kala Patthar），两个图件脚本共用
- `scripts/make_profile.py` — 解析 GPX、生成 `route-track-stats.csv` 和海拔图：`uv run --with matplotlib scripts/make_profile.py`
- `scripts/make_map.py` — 抓瓦片合成两张路线地图：`uv run --with pillow scripts/make_map.py`
- `report/template.html` + `scripts/build_report.py` — 报告正文写在 template 里，构建脚本把 CSV 表格、sources 全文、图片（base64 内嵌）填进去，产出自包含的 `report/EBC-report.html`（浏览器打开即可打印成 PDF 分享）：`uv run --with markdown scripts/build_report.py`
- **改了任何 CSV、sources 或图件后，重跑 build_report.py 再交付**；报告正文的文字改动改 template.html

## 工作约定（来自用户）

- 每条结论必须带出处；没有出处的信息不进报告。
- 数据以表格呈现；表格类数据 CSV 是唯一事实源，md/html 只引用，方便后续 agent 更新。
- 报告文风：客观、朴素、不追求排版花哨；遵守 de-ai-writing 原则（无压缩词、主谓宾完整、不用"不是…而是…"句式）。
- 费用口径：总价只含对所有人都必要的开销；国际机票和个人装备不计入（每人始发地与既有装备不同）。
- 人数未定，共享成本（向导/背夫/包机/房间）默认按 2 人分摊计算，报告中另给 4-5 人的分摊数。
- 更新任何 CSV 后同步检查报告中引用的合计数字。
- 货币口径：所有花费换算展示为人民币（¥），换算汇率 1 USD ≈ 6.8 CNY（2026-07 参考价）；尼泊尔卢比（NPR）原价保留，不额外折算。
