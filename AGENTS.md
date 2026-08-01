# EBC Trail 调研 Repo

2026-09-25 → 2026-10-06 尼泊尔 EBC（Everest Base Camp）徒步的行前调研与规划，6 人同行。仓库把三类素材装配成一份自包含的 HTML 报告：正文按章节存成 `report/sections/*.html`，表格数字存在 `data/*.csv`，出处存在 `sources/*.md`；`scripts/build_report.py` 产出 `report/EBC-report.html`，浏览器打开即可阅读或打印成 PDF 分享。报告分三层，层间以锚点互跳：速览（13 个问题各一句话回答）→ 详解（每个问题一个块）→ 出处（sources 全文，含自动生成的「被引用于」回链）。

## 文档地图

| 文档 | 内容 |
|---|---|
| [PROJECT.md](PROJECT.md) | 报告目的与行程硬约束 · 三层结构与各章节讲什么、事实源 · data 目录八个文件的职责与相互关系 · 当前状态与待议事项 |
| [PATTERNS.md](PATTERNS.md) | include 指令契约 · token provider 契约 · 三层锚点契约 · 构建期闸门 · 新增一个问题/一个 token/一张 CSV 表的配方 · 文件粒度上限 · 数据引用规则 |
| [TECHSTACK.md](TECHSTACK.md) | Python 与 uv 用法 · 三个依赖各自服务哪个脚本 · 目录结构 · OpenTopoMap 瓦片、Overpass、OpenTopoData 等外部服务 · GPX/KMZ 数据来源 |
| [DEVFLOW.md](DEVFLOW.md) | 构建与图件重生成命令 · 测试 · 换轨迹来源的完整流程 · 交付前检查 · 并发 worktree 约定 |

## 本仓库铁律

1. **每条结论带出处。** 写进报告的事实在 `sources/` 里有对应文件，详解正文在句末括注 `（sources/NN）` 并超链接到出处层对应原文（锚点契约见 PATTERNS.md），表格用单独一列写 `sources/NN`（纯文本）。速览行不带括注，出处由它链接到的详解块承载。
2. **表格数字的唯一事实源是 `data/*.csv`。** 章节引用 CSV，改数字就改 CSV，改完重跑构建，报告里的合计随之更新。
3. **货币口径。** 花费展示为人民币（¥），换算汇率 1 USD ≈ 6.8 CNY、1 CNY ≈ 19 NPR（2026-07 参考价）。USD 汇率写在 `scripts/reportgen/config.py` 的 `RATE`。NPR 报价在表里保留原价，同时按 19 折出人民币；19 取自 2025–2026 年多位徒步者的实付折算（NPR 399 折 ¥22、NPR 21,000 折 ¥1,100、NPR 500 折 ¥25），见 `sources/14-xiaohongshu-field-intel.md`。运营商的美元原始报价保留在表格的「原报价」列。
4. **费用口径。** 总价只含对所有人都必要的开销。国际机票与个人装备在 `cost-breakdown.csv` 里记 `in_total=no`，列进参考表供对照，合计不收它们。
5. **费用取值给单点最佳估算，不给区间。** `cost-breakdown.csv` 每行取一个数：有标注日期的数据时取日期最接近 2026-09-24 的那个（同季同年的实付价优先于攻略站挂牌价）；可用数据的时间点都不接近时取各来源平均。取值理由写在该行 `notes` 列。正文复述 `sources/` 原始区间的地方保留区间，并指明出处。
6. **人数分摊。** 共享成本按 `cost-breakdown.csv` 的 `shared_by_n` 列分摊：直升机包机、向导、向导背夫小费 ÷6；背夫、Thamel 双人间 ÷2；机场市区交通 ÷3；其余 14 行按每人计。同行人数 6 写在 `config.py` 的 `PAX`。
7. **报告文风。** 客观朴素，主谓宾完整，不追求排版花哨。
8. **交付前重跑构建。** 改了任何 CSV、`sources/`、章节文件、样式或图件之后跑 `uv run --with markdown scripts/build_report.py`，据它的输出确认构建通过。

## 要改 X 就动哪个文件

| 要做的改动 | 动这些文件 | 之后跑 |
|---|---|---|
| 改某一节的正文文字 | `report/sections/<该节>.html`（对照表见 PROJECT.md 章节清单） | `build_report.py` |
| 改某个数字 | 该数字所属的 `data/*.csv`，同时更新它引用的 `sources/NN-*.md` | `build_report.py` |
| 给某节加一张手写小表 | 该节的 `report/sections/*.html`，直接写 `<table>`（样式由 `styles/tables.css` 统一提供） | `build_report.py` |
| 加一张 CSV 驱动的表 | 新建 `data/<名>.csv` + `scripts/reportgen/<领域>.py` 的 `tokens()` + 引用它的详解块（配方见 PATTERNS.md） | `build_report.py` |
| 加一个 token | `scripts/reportgen/<领域>.py` 的 `tokens()` 返回值加一个键，并在某个 section 里写 `{{该键}}`（供需必须同时改，闸门双向校验） | `build_report.py` |
| 改样式 | `report/styles/` 下对应那一个：`base.css` 版式与字号、`tables.css` 表格、`components.css` 警示块与图片与代码与链接与回链、`appendix.css` 出处层、`print.css` 打印 | `build_report.py` |
| 改地图配色 | `scripts/day_colors.py` 顶部的按天色板 `DAY_COLORS` 与可走线路的 `OPTION_GRAY`，海拔剖面图与地形图共用；只调单张图改 `scripts/make_map.py` 的 per-figure 参数 | `make_map.py` 再 `build_report.py` |
| 改海拔剖面 | `scripts/make_profile.py`：全程图在 `full_profile()`；表格内嵌的逐日小图在 `scripts/profile_thumbs.py` 的 `day_thumbnail()` | `make_profile.py` 再 `build_report.py` |
| 换轨迹来源 | `assets/ebc-loop.kml`（KMZ 大环线）或 `assets/Everest_Base_Camp.gpx`，按 DEVFLOW.md 的换轨迹来源流程逐步走 | 见 DEVFLOW.md |
| 改村庄坐标或文献海拔 | `scripts/route_points.py`（`day_tracks.py`、`make_profile.py`、`make_map.py` 共用） | `day_tracks.py` → `make_profile.py` + `make_map.py` 再 `build_report.py` |
| 加一份出处 | 新建 `sources/NN-<主题>.md`（出处层按文件名排序自动全文收录，回链自动生成），在引用它的详解块里括注 `（sources/NN）` 并链接 `#NN-<主题>` | `build_report.py` |
| 增删一个 FAQ 问题 | `sections/faq.html` 加/删一行（`tr id="faq-q-<slug>"`）+ 对应 `sections/ext-*.html` 的详解块（`section id="q-<slug>"`，两边锚点成对）；新开文件时同步 `shell.html`（配方见 PATTERNS.md） | `build_report.py` |
| 增删一个章节 | `report/sections/` 增删文件 + `report/shell.html` 的 include 清单同步（闸门要求两边恰好一一对应） | `build_report.py` |
| 改报告标题或页头页脚 | `report/shell.html`（`<title>`、`<main>` 骨架、页脚 meta 行）或 `report/sections/header.html`（大标题、行程窗口、导语） | `build_report.py` |
