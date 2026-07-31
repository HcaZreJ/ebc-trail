# EBC Trail 调研 Repo

2026-09-24 → 2026-10-07 尼泊尔 EBC（Everest Base Camp）徒步的行前调研与规划。硬约束：9-25 上午 11:00 落地加德满都后当天出发进山，10-6 晚上必须回到加德满都（10-7 早国际段回上海）。徒步方式：轻装 + 背夫背驼包 + 沿途茶屋食宿 + 自带睡袋；进出山走飞机/直升机，不走陆路。

## 目录结构

- `sources/` — 调研出处。每个主题一个文件，含 URL、抓取日期、提取的具体数字。**报告里的每个事实都必须能追溯到这里的某个文件**。只放核心来源，垃圾信息不进来。真人完整攻略（走完全程的 trip report）是最高优先级来源。
- `data/` — 表格类数据的 source of truth（CSV）。报告只引用，不另立数字：
  - `itinerary.csv` — 12 天逐日行程（日期、区段、里程、海拔、茶屋、三餐、单日花费）
  - `cost-breakdown.csv` — 必要开销明细与合计（`in_total=no` 的行不计入总价：装备按用户口径另算，兜底预备金不动用不花）
  - `packing-list.csv` — 零装备者的最小装备清单
  - `route-track-stats.csv` — 由 GPX 计算的逐村里程/海拔（脚本产物，不手改；Phakding–Namche 峡谷段爬升列受 GPS 噪声影响，以文献数据为准）
- `assets/` — `Everest_Base_Camp.gpx`（轨迹原始文件，来源见 `sources/11`）和 `elevation-profile.png`（海拔剖面图）
- `scripts/make_profile.py` — 解析 GPX、生成 `route-track-stats.csv` 和海拔图。改村庄点位或样式后用 `uv run --with matplotlib scripts/make_profile.py` 重新生成
- `report/EBC-report.md` — 面向用户的汇总报告，后续可导出 PDF

## 工作约定（来自用户）

- 每条结论必须带出处；没有出处的信息不进报告。
- 数据以表格呈现；表格类数据 CSV 是唯一事实源，md/html 只引用，方便后续 agent 更新。
- 报告文风：客观、朴素、不追求排版花哨；遵守 de-ai-writing 原则（无压缩词、主谓宾完整、不用"不是…而是…"句式）。
- 费用口径：总价只含对所有人都必要的开销；国际机票和个人装备不计入（每人始发地与既有装备不同）。
- 人数未定，共享成本（向导/背夫/包机/房间）默认按 2 人分摊计算，报告中另给 4-5 人的分摊数。
- 更新任何 CSV 后同步检查报告中引用的合计数字。
