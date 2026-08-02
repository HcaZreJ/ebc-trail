# EBC Trail 调研 Repo

2026-09-25 → 2026-10-06 尼泊尔 EBC（Everest Base Camp）徒步的行前调研与规划，6 人同行。仓库把三类素材装配成一份自包含的 HTML 报告：正文按章节存成 `report/sections/*.html`，表格数字存在 `data/*.csv`，出处存在 `sources/*.md`；`scripts/build_report.py` 产出 `report/EBC-report.html`，浏览器打开即可阅读或打印成 PDF 分享。报告分四层，层间以锚点互跳：摘要（六行结论）→ 核心（§1 代理套餐值不值 · §2 行前准备 · §3 保险 · §4 12 天行程与强度）→ 支持信息（§5 费用 · §6 进出山交通 · §7 高反与向导背夫 · §8 签证许可证现金通讯）→ References（编号条目，给来源方、链接、抓取日期与折叠的原始记录全文，带跳回正文的「引用于 §N」）。正文的事实处写 `[[NN]]` 标记，构建时展开成上标角标，点一下跳到 References 对应条目。

## 文档地图

| 文档 | 内容 |
|---|---|
| [PROJECT.md](PROJECT.md) | 报告目的与行程硬约束 · 三层结构与各章节讲什么、事实源 · data 目录八个文件的职责与相互关系 · 当前状态与待议事项 |
| [PATTERNS.md](PATTERNS.md) | include 指令契约 · token provider 契约 · 三层锚点契约 · 构建期闸门 · 新增一个问题/一个 token/一张 CSV 表的配方 · 文件粒度上限 · 数据引用规则 |
| [TECHSTACK.md](TECHSTACK.md) | Python 与 uv 用法 · 三个依赖各自服务哪个脚本 · 目录结构 · OpenTopoMap 瓦片、Overpass、OpenTopoData 等外部服务 · GPX/KMZ 数据来源 |
| [DEVFLOW.md](DEVFLOW.md) | 构建与图件重生成命令 · 测试 · 换轨迹来源的完整流程 · 交付前检查 · 并发 worktree 约定 |

## 本仓库铁律

1. **每条结论带出处。** 写进报告的事实在 `sources/` 里有对应文件，正文在事实处写 `[[NN]]`（多源 `[[07,16]]`），紧贴事实文字、句末标点之前；构建时展开成上标角标，跳到 References 的 `#ref-NN`（citation 契约见 PATTERNS.md）。表格用单独一列写出处，CSV 的出处列由 `csvio.cite()` 转成同样的标记，与散文在同一步展开。
2. **表格数字的唯一事实源是 `data/*.csv`。** 章节引用 CSV，改数字就改 CSV，改完重跑构建，报告里的合计随之更新。
3. **货币口径。** 花费以美元（USD）与尼泊尔卢比（NPR）计价，换算 1 USD ≈ 129.2 NPR（2026-07 参考价），写在 `scripts/reportgen/config.py` 的 `NPR_PER_USD`。单价写进表格的「原报价」列，用该项报出时的货币（许可证 NPR 3000、向导 USD 32/天）；由中国徒步者以人民币记录的实付价按 19 NPR/CNY 折成卢比后填这一列。可加总的每人金额列与合计统一用美元。129.2 由 1 USD ≈ 6.8 CNY 与 1 CNY ≈ 19 NPR 推出，19 取自 2025–2026 年多位徒步者的实付折算（NPR 399 折 ¥22、NPR 21,000 折 ¥1,100、NPR 500 折 ¥25），见 `sources/14-xiaohongshu-field-intel.md`。人民币原值连同它的美元折算留在 `sources/` 里，一手记录不改写。
4. **费用口径。** 总价只含对所有人都必要的开销。国际机票与个人装备在 `cost-breakdown.csv` 里记 `in_total=no`，列进参考表供对照，合计不收它们。
5. **费用取值给单点最佳估算，不给区间。** `cost-breakdown.csv` 每行取一个数：有标注日期的数据时取日期最接近 2026-09-24 的那个（同季同年的实付价优先于攻略站挂牌价）；可用数据的时间点都不接近时取各来源平均。取值理由写在该行 `notes` 列。正文复述 `sources/` 原始区间的地方保留区间，并指明出处。
6. **人数分摊。** 共享成本按 `cost-breakdown.csv` 的 `shared_by_n` 列分摊：向导、向导背夫小费 ÷6；背夫、茶屋双人间、Thamel 双人间 ÷2；机场市区交通 ÷3；其余 15 行按每人计。分摊语义只写在 `shared_by_n` 列里——`pp_usd` 恒等于「原报价 × `qty` ÷ `shared_by_n`」，双人间报每间价就把 ÷2 交给 `shared_by_n`，这条恒等式由 `tests/hidden/money_test.py` 逐行校验。同行人数 6 写在 `config.py` 的 `PAX`。
7. **报告文风。** 客观朴素，主谓宾完整，不追求排版花哨。
8. **交付前重跑构建。** 改了任何 CSV、`sources/`、章节文件、样式或图件之后跑 `uv run --with markdown scripts/build_report.py`，据它的输出确认构建通过。

## 要改 X 就动哪个文件

| 要做的改动 | 动这些文件 | 之后跑 |
|---|---|---|
| 改某一节的正文文字 | `report/sections/<该节>.html`（对照表见 PROJECT.md 章节清单） | `build_report.py` |
| 改某个数字 | 该数字所属的 `data/*.csv`，同时更新它引用的 `sources/NN-*.md` | `build_report.py` |
| 给某节加一张手写小表 | 该节的 `report/sections/*.html`，直接写 `<table>`（样式由 `styles/tables.css` 统一提供） | `build_report.py` |
| 加一张 CSV 驱动的表 | 新建 `data/<名>.csv` + `scripts/reportgen/<领域>.py` 的 `tokens()` + 引用它的那一节（配方见 PATTERNS.md） | `build_report.py` |
| 加一个 token | `scripts/reportgen/<领域>.py` 的 `tokens()` 返回值加一个键，并在某个 section 里写 `{{该键}}`（供需必须同时改，闸门双向校验） | `build_report.py` |
| 改样式 | `report/styles/` 下对应那一个：`base.css` 版式与字号、`tables.css` 表格、`components.css` 警示块与图片与代码与链接与回链与角标、`appendix.css` References 列表、`print.css` 打印 | `build_report.py` |
| 改地图配色 | `scripts/day_colors.py` 顶部的按天色板 `DAY_COLORS` 与可走线路的 `OPTION_LINE`，海拔剖面图与地形图共用；只调单张图改 `scripts/make_map.py` 的 per-figure 参数 | `make_map.py` 再 `build_report.py` |
| 改海拔剖面 | `scripts/make_profile.py`：全程图在 `full_profile()`；表格内嵌的逐日小图在 `scripts/profile_thumbs.py` 的 `day_thumbnail()` | `make_profile.py` 再 `build_report.py` |
| 换轨迹来源 | `assets/ebc-loop.kml`（KMZ 大环线）或 `assets/Everest_Base_Camp.gpx`，按 DEVFLOW.md 的换轨迹来源流程逐步走 | 见 DEVFLOW.md |
| 改村庄坐标或文献海拔 | `scripts/route_points.py`（`day_tracks.py`、`make_profile.py`、`make_map.py` 共用） | `day_tracks.py` → `make_profile.py` + `make_map.py` 再 `build_report.py` |
| 加一份出处 | 新建 `sources/NN-<主题>.md`（References 按编号自动收录，回链与折叠原文自动生成），在引用它的正文处写 `[[NN]]` | `build_report.py` |
| 增删一节 | `report/sections/` 增删 `core-*.html` 或 `sup-*.html` + `report/shell.html` 的 include 清单同步（闸门要求两边恰好一一对应）+ `sections/summary.html` 的摘要行同步；节号插在中间时后面各节的编号、`id` 与跨节引用一起改（配方见 PATTERNS.md） | `build_report.py` |
| 改摘要里的某条结论 | `report/sections/summary.html`（六行，每行链到对应节；结论性数字用 token 不写死） | `build_report.py` |
| 改报告标题或页头页脚 | `report/shell.html`（`<title>`、`<main>` 骨架、页脚 meta 行）或 `report/sections/header.html`（大标题、行程窗口、导语） | `build_report.py` |
