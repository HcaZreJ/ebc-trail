# Feature: 报告拆成原子化模块

## Overview

`report/template.html`（310 行）是全部报告正文的唯一载体：51 行 CSS + 13 个主题章节 + 2 个附录挤在一个文件里。
`scripts/build_report.py`（247 行）把六张 CSV、14 份 sources、4 张图片填进它，产出 12 MB 自包含的
`report/EBC-report.html`，该产物 tracked 进 git。

用户要并发多个 agent 各自拉 worktree 修不同主题（签证、交通、报价、装备……）。当前结构下：

- 两个 agent 改不同章节 → 落在 `template.html` 的相邻行区 → merge conflict
- 任何一个 agent 改任何 CSV / sources / 图片 → 必须重跑构建 → 12 MB 的 `EBC-report.html` 整份重写 → 每次都冲突
- 一个只改「签证」一节的 agent 要把 310 行正文 + 247 行构建脚本全读进上下文

拆分目标：**一个主题一个文件**，agent 只读自己那一块；构建产物不进 git，冲突面归零。

## Intent Brief

- **Goal**：报告正文按章节切成独立文件，构建脚本按领域切成独立模块，装载顺序由单一事实源声明。
- **Motivation**：并发 agent 在单个大文件里工作产生 merge conflict，且上下文臃肿。
- **Known context**：仓库是行前调研报告生成器，非 Web 应用。`data/*.csv` 与 `sources/*.md` 已经是按主题一文件一主题，报告章节与它们一一对应，切分维度天然存在。
- **Constraints**：
  - 产物必须保持自包含单文件（浏览器直接打开、打印成 PDF 分享），图片继续 base64 内嵌。
  - 拆分是纯重构，渲染结果逐字节不变。
  - 构建入口命令不变：`uv run --with markdown scripts/build_report.py`。
  - 报告正文里的每个事实继续追溯到 `sources/`，拆分不动任何数字与文案。
- **Non-goals**：不改报告文案、不改任何 CSV 数字、不动 `make_map.py` / `make_profile.py` 的绘图逻辑、不把硬编码颜色抽成 CSS 变量（会破坏逐字节守恒，另开一次改动）。
- **Success criteria**：拆分后重跑构建，产物与拆分前的基线逐字节一致。
  基线取自拆分前 `HEAD=b70ff53` 的构建产物，raw sha256
  `259ee9d81450a45e3233c6f385426addfe7e4559abeb73177ae137f66d0ae404`，11,963,467 字节，
  与该 commit 里 tracked 的 `report/EBC-report.html` 零差异。同日构建时 `BUILD_DATE` 同值，
  可以直接比 raw sha256；跨日构建时把两侧的日期串归一化后再比。
- **Assumptions / Unknowns**：见下表。

## Alignment Gate

**I will implement**

- `report/template.html` → `report/shell.html`（骨架 + 装载清单）+ `report/styles/*.css`（5 个）+ `report/sections/*.html`（14 个）
- 装载机制：`<!-- include: <path> -->` 指令，`shell.html` 里的出现顺序即 CSS 级联顺序与报告章节顺序
- `scripts/build_report.py` → 薄入口 + `scripts/reportgen/` 包（配置、CSV 读写、表格渲染、四个领域 token provider、装配器）
- 构建期完整性闸门六道：include 目标存在、同一路径不重复装载、`styles/` 与 `sections/` 下每个文件被装载恰好一次、
  token 供需双向匹配、产物无残留 `{{}}`、provider 之间 token 名不冲突
- `report/EBC-report.html` 与 `scripts/__pycache__/` 移出 git 跟踪，写 `.gitignore`
- AGENTS.md 重写为文档地图 + PROJECT / PATTERNS / TECHSTACK / DEVFLOW 四份内容文档

**I will not implement**

- 报告文案、CSV 数字、图件绘制逻辑的任何改动
- 逐段海拔剖面虚线的数据来源改造（见 Open assumptions，单独一次改动）
- CSS 颜色变量化

**Acceptance criteria**

1. `uv run --with markdown scripts/build_report.py` 成功，产物归一化后 sha256 命中基线值
2. `report/sections/` 下 14 个文件、`report/styles/` 下 5 个文件，各自被 `shell.html` 装载恰好一次
3. 故意制造三类错误（漏装载一个 section、include 指向不存在的文件、章节引用未定义 token）时构建各自报错退出

## Assumption Ledger

| Assumption | Confidence | Impact if Wrong | Status |
|---|---:|---:|---|
| `report/EBC-report.html` 可以移出 git：用户需要它时跑一条命令重建 | medium | medium | 已实施，交付时请用户确认；恢复只需删 `.gitignore` 一行 |
| `assets/.tile-cache/` 保留跟踪：它稳定不变、不产生冲突，且避免反复抓 OpenTopoMap 社区瓦片服务 | high | low | 已决策 |
| `assets/*.png` 保留跟踪：它们是报告构建的输入，重新生成需要网络 | high | low | 已决策 |
| 章节切分粒度按报告自身的编号章节（0–9 节 + 两个附录 + 报价评估 + 页头）即可，不需要再往下切到小节 | high | low | 已决策；`s5` 路线一节 31 行是最大的一个，仍在单个 agent 的舒适区 |
| 逐段海拔剖面的虚线用户想要真实地形数据而非文献直线示意 | medium | medium | 未澄清，不在本 plan 范围 |

## 当前构成（实测行号，全部 sed 切割的坐标系）

`report/template.html` 共 310 行：

| 段 | 行号 | 行数 |
|---|---|---:|
| head + `<title>` | 1–6 | 6 |
| `<style>` 内的 CSS | 8–58 | 51 |
| `</head><body><main>` | 59–62 | 4 |
| 页头（标题 · meta · 导语） | 64–67 | 4 |
| 代理报价评估 | 69–93 | 25 |
| 0 · 结论速览 | 95–106 | 12 |
| 1 · 签证 | 108–118 | 11 |
| 2 · 进出山交通 | 120–141 | 22 |
| 3 · 许可证 | 143–149 | 7 |
| 4 · 向导与背夫 | 151–173 | 23 |
| 5 · 12 天路线 | 175–205 | 31 |
| 6 · 装备清单 | 207–219 | 13 |
| 7 · 保险与其它事项 | 221–244 | 24 |
| 8 · 预估总价 | 246–250 | 5 |
| 9 · 行动清单 | 252–260 | 9 |
| `<div class="appendix">` | 262 | 1 |
| 附录 A · 数据表全量 | 264–298 | 35 |
| 附录 B · 出处全文 | 300–302 | 3 |
| `</div>` + 页脚 + 收尾 | 304–310 | 7 |

## 目标构成

```
report/
  shell.html                    骨架；include 指令的出现顺序 = CSS 层叠顺序与章节顺序
  styles/base.css               :root · * · body · main · 标题 · 段落 · .meta · .lede
  styles/tables.css             table · th/td · .table-scroll · td.num · tr.total
  styles/components.css         .warn · figure 系 · code · a
  styles/appendix.css           .appendix 下的一切 · .toc
  styles/print.css              @media print
  sections/header.html          标题 · meta · 导语
  sections/quote-review.html    代理报价评估
  sections/s0-summary.html      0 · 结论速览
  sections/s1-visa.html         1 · 签证
  sections/s2-transport.html    2 · 进出山交通
  sections/s3-permits.html      3 · 许可证
  sections/s4-guide-porter.html 4 · 向导与背夫
  sections/s5-route.html        5 · 12 天路线
  sections/s6-packing.html      6 · 装备清单
  sections/s7-insurance.html    7 · 保险与其它事项
  sections/s8-costs.html        8 · 预估总价
  sections/s9-action-plan.html  9 · 行动清单
  sections/appendix-a-data.html 附录 A · 数据表全量
  sections/appendix-b-sources.html 附录 B · 出处全文
scripts/
  build_report.py               薄入口
  reportgen/config.py           ROOT · RATE · PAX · 四个目录路径
  reportgen/csvio.py            read_csv · blocks · esc · signed
  reportgen/tables.py           table 渲染器
  reportgen/money.py            rng · y · diff
  reportgen/figures.py          img_uri + tokens()
  reportgen/costs.py            tokens()
  reportgen/quotes.py           tokens()
  reportgen/route.py            tokens()
  reportgen/appendix.py         tokens()
  reportgen/assemble.py         include 解析 · 五道闸门 · token 合并与替换
tests/test_assemble.py          装配器契约测试
```

## Work-Unit Specs

```yaml
- id: T1
  title: CSS 按主题切成 5 个文件
  file_path: report/styles/{base,tables,components,appendix,print}.css
  dependencies: []
  behavioral_contract: |
    template.html 第 8–58 行的 51 行 CSS 按连续行区切出，只切不重排版：
      base.css        8–22   :root · * · body · main · h1/h2/h3 · p/ul/ol · li · .meta · .lede
      tables.css      23–29  table · th/td · .table-scroll · th 背景 · td.num · tr.total
      components.css  30–37  .warn · figure 系 · code · a
      appendix.css    38–46  .appendix 下的一切 · .toc
      print.css       47–58  @media print
    五个文件按此顺序拼接后与原 <style> 内容逐字节一致，层叠优先级不变。
  acceptance: |
    cat 五个文件 | diff - <(sed -n '8,58p' 原 template.html) 零差异

- id: T2
  title: 正文按章节切成 14 个文件
  file_path: report/sections/*.html
  dependencies: []
  behavioral_contract: |
    template.html 的正文按 h2 边界切段，文件名用章节自身的锚点 id，与报告编号对齐：
      header.html              64–67   标题 · meta · 导语
      quote-review.html        69–93   代理报价评估（id=quote）
      s0-summary.html          95–106  0 · 结论速览
      s1-visa.html             108–118 1 · 签证
      s2-transport.html        120–141 2 · 进出山交通
      s3-permits.html          143–149 3 · 许可证
      s4-guide-porter.html     151–173 4 · 向导与背夫
      s5-route.html            175–205 5 · 12 天路线
      s6-packing.html          207–219 6 · 装备清单
      s7-insurance.html        221–244 7 · 保险与其它事项
      s8-costs.html            246–250 8 · 预估总价
      s9-action-plan.html      252–260 9 · 建议的行动清单
      appendix-a-data.html     264–298 附录 A · 数据表全量
      appendix-b-sources.html  300–302 附录 B · 调研出处全文
    章节之间的空行分隔留在 shell.html 里，不进章节文件。
    `<div class="appendix">` 包裹层留在 shell.html 里，两个附录文件各自标签平衡。
  acceptance: |
    按 shell.html 的 include 顺序拼接后与原 template.html 正文段逐字节一致

- id: T3
  title: 构建脚本切成 reportgen 包，装配器实现 include 指令与完整性闸门
  file_path: scripts/build_report.py + scripts/reportgen/*.py
  dependencies: [T1, T2]
  functions:
    - name: reportgen.assemble.build
      behavioral_contract: |
        读 report/shell.html，把每条 `<!-- include: <path> -->` 整行替换为该文件内容
        （path 相对 report/ 解析，去掉文件末尾换行），再用全部 provider 的 token 做替换，
        写出 report/EBC-report.html。
      error_cases:
        - { condition: "include 目标文件不存在", behavior: "SystemExit，报出 shell.html 里的行号与路径" }
        - { condition: "styles/ 或 sections/ 下有文件未被任何 include 装载", behavior: "SystemExit，列出孤儿文件名" }
        - { condition: "同一文件被 include 两次", behavior: "SystemExit，报出重复路径" }
        - { condition: "装配后仍有 {{TOKEN}} 残留", behavior: "SystemExit，报出第一个未解析 token 名" }
        - { condition: "provider 产出的 token 在任何 section 里都没被引用", behavior: "SystemExit，列出未被消费的 token 名" }
    - name: reportgen.<domain>.tokens
      behavioral_contract: |
        四个领域 provider 各自返回 {裸 token 名: 已渲染 HTML 或字符串}，不带花括号。
        assemble 负责加花括号并合并；provider 之间零 import 依赖。
          figures.py   IMG_OVERVIEW_MAP · IMG_TREK_MAP · IMG_ELEV_PROFILE · IMG_ELEV_PROFILE_DAILY
          costs.py     TBL_COSTS_MAIN · TBL_COSTS_REF · TOTAL_CNY_RANGE · TOTAL_USD_RANGE · TOTAL_CNY_MID
          quotes.py    TBL_QUOTE_ITEMS · TBL_QUOTE_TOTALS · QUOTE_* 共 9 个
          route.py     TBL_ROUTE_SEGMENTS · TBL_ITINERARY_DATES
          appendix.py  TBL_*_FULL 共 6 个 · APPENDIX_SOURCES
        共用基础设施：config.py（ROOT · RATE · PAX · 路径）、csvio.py（read_csv · blocks · esc · signed）、
        tables.py（table 渲染器）、money.py（美元转人民币与区间格式化）
  acceptance: |
    产物归一化 BUILD_DATE 后 sha256 == 2a92610e4474d55e0215d862b00c15ab23649441af7fe1ced6b55cbfd7f9ddb2

- id: T4
  title: 构建产物与 pycache 移出 git 跟踪
  file_path: .gitignore
  dependencies: []
  behavioral_contract: |
    .gitignore 收录 report/EBC-report.html · __pycache__/ · *.pyc；
    两者 git rm --cached。assets/*.png 与 assets/.tile-cache/ 保持跟踪。
  acceptance: |
    git status 在跑完构建后是干净的

- id: T5
  title: 文档拆成 AGENTS.md 地图 + 四份内容文档
  file_path: AGENTS.md · PROJECT.md · PATTERNS.md · TECHSTACK.md · DEVFLOW.md
  dependencies: [T3, T4]
  behavioral_contract: |
    AGENTS.md 收敛为文档地图 + 本仓库铁律 + 「要改 X 就动哪个文件」对照表。
    PROJECT.md  报告目的 · 章节清单与各自的事实源 · 数据模型（六张 CSV 的职责）
    PATTERNS.md 模块边界规则 · include 指令契约 · token provider 契约 · 新增一节/一个 token/一张表的配方
    TECHSTACK.md Python + uv · 依赖（markdown/matplotlib/pillow）· 目录结构 · 外部服务（OpenTopoMap）
    DEVFLOW.md  构建命令 · 换 GPX 的完整流程 · 图件重生成 · 并发 worktree 约定 · 交付前检查
    只写当前事实，不写拆分前后的对照叙事。
  acceptance: |
    照 DEVFLOW.md 的命令能从零重建全部产物
```

## Dependency Graph

```
T1 ─┐
T2 ─┼─> T3 ─┐
T4 ─┘       ├─> T5
            │
```

## Execution Waves

- **Wave 1**（并行，各自只新建文件）：T1 · T2 · T4
- **Wave 2**：T3（依赖 T1/T2 已落地的文件）
- **Wave 3**：守恒校验 —— 归一化 sha256 对比基线
- **Wave 4**：T5

## 迁移正确性策略

**按行号切割，不手抄。** 每个搬迁单元用 `sed -n '<start>,<end>p'` 从原文件取段，切完立即校验。

**四种判据，按被搬的东西选：**

① **CSS —— 拼回逐字节一致。** 五个文件按 `shell.html` 里的 include 顺序 `cat` 起来，与原 `template.html`
第 8–58 行 `diff`，要求零输出：

```
cat report/styles/base.css report/styles/tables.css report/styles/components.css \
    report/styles/appendix.css report/styles/print.css \
  | diff - <(sed -n '8,58p' <原 template.html>)
```

② **正文分节 —— 装配回原文。** 判据合并进 ④，因为 section 文件是构建的输入，拼装结果直接体现在产物里。

③ **Python 逐函数比对。** 领域模块的每个函数体与原 `build_report.py` 对应段落比对，除 import 行、
一级缩进（内嵌函数抽成模块级）、路径常量换名之外应为空。

④ **产物逐字节守恒（总闸门）。** 上面三条都是过程判据，最终判据只有一条：重建产物与基线
逐字节一致。基线是拆分前 `HEAD=b70ff53` 的构建产物，与该 commit 里 tracked 的
`report/EBC-report.html` 零差异。

```
uv run --with markdown scripts/build_report.py
shasum -a 256 report/EBC-report.html
# 期望 259ee9d81450a45e3233c6f385426addfe7e4559abeb73177ae137f66d0ae404
```

**新行为单独走 test-first。** 装配器的五道闸门是本 plan 唯一的新行为，先由 `@test-author` 仅凭契约
写 `tests/test_assemble.py`，架构师审过覆盖度与断言精确度、确认 27 个用例全部因
`NotImplementedError` 失败之后，才交给实现。

**闸门要亲自故障注入验一遍。** 测试用 `tmp_path` 造的小样本证明逻辑，故障注入用仓库真实内容证明
它在真场景下报得准。五种错误各注入一次，确认报出的是具体文件名 / 行号 / token 名。

## Status

Completed。

| 单元 | 状态 | 实测结果 |
|---|---|---|
| T1 CSS 切 5 个文件 | 完成 | 拼回与原第 8–58 行 `diff` 零输出。base 15 · tables 7 · components 8 · appendix 9 · print 12 = 51 行 |
| T2 正文切 14 个文件 | 完成 | 共 224 行，最大 `appendix-a-data.html` 35 行，最小 `appendix-b-sources.html` 3 行 |
| T3 reportgen 包 + 装配器 | 完成 | 11 个模块 395 行，最大 `assemble.py` 125 行；`build_report.py` 247 → 15 行。契约测试 28/28 全绿 |
| T4 产物移出 git | 完成 | `report/EBC-report.html`、`scripts/__pycache__/*.pyc` 取消跟踪并进 `.gitignore`；`.claude/worktrees/` 与 `.DS_Store` 一并收录 |
| T5 文档 | 完成 | AGENTS.md 40 行收敛为地图，新增 PROJECT 63 · PATTERNS 88 · TECHSTACK 102 · DEVFLOW 62 行，CLAUDE.md 一行 `@AGENTS.md` |

**总闸门**：重建产物 raw sha256 `259ee9d81450a45e3233c6f385426addfe7e4559abeb73177ae137f66d0ae404`、
11,963,467 字节，与基线**位级相同**（不只是归一化后相同 —— 同日构建，`BUILD_DATE` 同值）。

**六道闸门故障注入实测输出**（`collect_tokens()` 里的 token 名冲突是第六道）：

```
missing      SystemExit → shell.html 第 28 行的 include 目标不存在：sections/nope.html
dupe         SystemExit → include 指令重复装载同一文件：sections/s1-visa.html
orphan       SystemExit → 以下文件没有被 shell.html 装载：sections/s3-permits.html
unresolved   SystemExit → 装配后仍有未解析的 token：'NO_SUCH_TOKEN'
unconsumed   SystemExit → 以下 token 没有被任何章节引用：GHOST
collision    SystemExit → token 名冲突：TBL_COSTS_MAIN 同时由 reportgen.route 提供
```

`check_orphans` 跳过以 `.` 开头的文件：macOS 的 `.DS_Store` 落进 `report/sections/` 时构建照常通过，
同时留一个真孤儿 `sections/zz-stale.html` 时闸门只报真孤儿。

**结构边界校验**：14 个 section 文件各自标签平衡（div · table · ul · ol · figure · section · p · h2 · h3 · li · tr
开闭计数相等），5 个 CSS 文件各自花括号平衡 —— 切分落在规则与元素边界上，改一个章节不会破坏
另一个章节的文档结构。

**provider 隔离实测**：五个 provider 只 import `config` / `csvio` / `tables` / `money`，互相之间零 import。
token 供需精确匹配 28 = 28。

### 过程中清算的两处漂移

- `QUOTE_BASE_OURS` 与 `QUOTE_OURS_ALLIN` 两个 token 被计算出来却没有任何章节引用，随本次拆分删除。
  产出它们的中间变量 `base_ours` / `ours_all` 仍服务于表格里的小计行与差额计算，保留。
  这类死 token 今后由 `check_token_usage` 闸门当场拦住。
- `substitute` 改为单趟 `re.sub`。原实现是按字典顺序逐个 `str.replace`，token 值里若出现另一个
  token 的占位符会被二次展开。当前六张 CSV 与 14 份 sources 里 `{{` 零命中，两种实现输出相同，
  单趟替换把这条隐患一并关掉。

### 计划外查明的一件事（不在本 plan 范围）

逐段海拔剖面里 6 张小图画的是虚线直线。原因不是 GPX 缺数据：`assets/Everest_Base_Camp.gpx` 在
Dingboche/Pheriche 走廊（沿轨迹 km 37–43）有 **215 个连续轨迹点**，海拔从 4,123 m 实测爬到 4,519 m。
`make_profile.py` 用 400 m 作为村庄吸附阈值（`on_track = [s for s in snapped if s[5] < 400]`），
而 Dingboche 与 Pheriche 的最近轨迹点偏移都是 **521 m**（轨迹从两村之间的谷地上行，不进村），
于是所有触及这两个村的路段退化成按文献海拔点连的直线。

真正不在 GPX 上的只有三条支线：Everest View Hotel、Nangkartshang、Kala Patthar。

处置分两层，另开 plan：把锚点规则从「超过 400 m 就弃用 GPX」改为「锚到最近轨迹点并披露偏移」，
可以让第 5 · 7 · 10 段与第 9 段的 Gorak Shep→Pheriche 一段变成实测地形曲线；三条支线需要补数据源。
