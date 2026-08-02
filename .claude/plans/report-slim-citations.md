# Feature: 报告瘦身与学术式引用改版

## Overview

报告当前 14 问三层结构，正文 37,704 字符，信息全面但人类读不进去。这一版做两件事：把正文按「核心 → 支持 → 引用」重排并削减约 40% 篇幅；把出处层从 18 份 markdown 全文倾泻改成学术论文式 references——正文事实处只留一个上标小角标，点击跳到文末编号条目。

正文聚焦两个核心问题：Majestic Trails Nepal 的套餐值不值、行前要准备什么（装备与保险）。之后跟 12 天行程的强度 breakdown（图件已就绪，用于让 6 名同行者直观看到强度）。其余七个问题降为支持信息，篇幅压缩、内容保留。

## Intent Brief

- **Goal**：一份 6 名同行者愿意读完的报告。核心决策在最前面，支持信息可查但不挡路，每条事实由角标指向文末 references。
- **Motivation**：信息量太大导致无法接收。现有 14 问速览把核心问题与琐碎问题并列，出处层 18 份全文让报告尾部占据篇幅的一半。
- **Known context**：`main` 已含 PR 16（USD/NPR 计价）；PR 15（Q11 两步路保险逐条款核查）在本 worktree 里 merge 进来，冲突按 USD 口径解。图件（徒步详图、全程剖面、10 张逐日剖面小图）已就绪，本次不重做。
- **Constraints**：AGENTS.md 铁律全部适用——每条结论带出处、表格数字唯一事实源是 `data/*.csv`、USD 与 NPR 计价、单点最佳估算、`shared_by_n` 分摊语义、客观朴素文风、交付前重跑构建。图件与 `data/*.csv` 的数字不动。
- **Non-goals**：不重算费用、不重画图、不新增调研、不改 `sources/*.md` 的一手记录内容（仅 merge 冲突已解的那两处除外）。
- **Success criteria**：正文降到 22,000 字符以内；核心四节在报告前 40% 篇幅内讲完；正文零 `（sources/NN）` 括注、全部改为上标角标；references 呈紧凑编号列表，原始记录折叠可展开；构建通过、测试全绿、层间锚点成对。
- **Assumptions**：见下表。
- **Unknowns**：无阻塞项。

## Alignment Gate

**I will implement**

- 章节重排为四层：摘要 → 核心 §1–§4 → 支持 §5–§8 → References。
- 正文篇幅削减约 40%，支持层保留全部事实结论、压缩表述。
- 引用机制换成 `[[NN]]` 标记 + 上标角标 + 文末编号 references，装配后全局展开，CSV 表格的出处列一并变角标。
- 修掉 `ext-todo.html` 里与当前行程冲突的一条（"订 9.25 下午 2 架直升机包机"——行程已改为 9.25 加都休整、9.26 早班机进山，不需要包机）。
- 同步 AGENTS.md / PROJECT.md / PATTERNS.md / DEVFLOW.md 里被这次改动改变的事实。

**I will not implement**

- 不动 `data/*.csv` 的数字、不动 `assets/*.png`、不动轨迹脚本。
- 不把 18 份 sources 拆成 URL 级 reference（正文现有引用只记到文件级，拆到 URL 级需要重做 fact→子来源映射，超出本次范围）。
- 不保留 Q1–Q14 编号体系。

**Open assumptions**：A1、A2、A3（下表）。

**Acceptance criteria**

1. `uv run --with markdown scripts/build_report.py` 打印 `wrote ...`。
2. `uv run --with pytest pytest tests/ -q` 全绿，且新增 citation 引擎的 hidden 测试通过。
3. `report/sections/*.html` 合计 ≤ 22,000 字符。
4. 产物中 `（sources/` 零命中；`[[` 零残留；每个角标的 `href="#ref-NN"` 都有对应的 `id="ref-NN"`。
5. 摘要每一行链接的锚点都存在，每个核心/支持节的回链都指回摘要。

## Assumption Ledger

| Assumption | Confidence | Impact if Wrong | Status |
|---|---:|---:|---|
| A1 · 14 行 FAQ 速览表换成 6 行结论摘要是用户要的「核心信息提炼到最前面」 | high | medium | 按此实现，plan 与汇报中标明 |
| A2 · references 里每条的原始记录用 `<details>` 折叠（默认收起）符合「更极端、更像学术论文」 | medium | medium | 按此实现，信息零丢失，展开即全文 |
| A3 · 废弃 Q1–Q14 编号、改用 §1–§8 分节编号 | high | low | 结构重排的必然结果 |
| A4 · 支持层每节压到原篇幅的 45%–55%，结论与关键数字全留 | high | low | 按此实现 |

## Work-Unit Specs

### 契约：citation 标记语法（全部单元共用）

- 正文标记 `[[NN]]`，多源 `[[07,16]]`（两位数字，逗号分隔，逗号后可有空格）。`NN` 对应 `sources/NN-*.md`。
- 标记紧贴被证明的事实文字之后、句末标点之前：`……落在跟团公开区间的低端[[07,16]]。`
- 展开结果 `<sup class="cite"><a id="cite-NN-K" href="#ref-NN">N</a></sup>`，`N` 去前导零，`K` 是该编号在全文里第几次出现。多源共用一个 `<sup>`，内部以 `,` 分隔。
- 展开在装配的最后一步对整份文档做，因此 section 文件、CSV 的出处列、provider 产出的表格里的标记都会被展开。
- 正文不再出现 `（sources/NN）` 括注、不再出现 `<a href="#NN-...">`、不出现 repo 内部路径（`data/*.csv` 这类）。

### 节编号与文件映射（全部单元共用）

| 节 | 标题 | 文件 | section id |
|---|---|---|---|
| — | 摘要 | `sections/summary.html` | `summary` |
| §1 | Majestic Trails 的套餐值不值 | `sections/core-deal.html` | `s1-deal` |
| §2 | 行前准备：时间线与装备 | `sections/core-prep.html` | `s2-prep` |
| §3 | 保险买哪个 | `sections/core-insurance.html` | `s3-insurance` |
| §4 | 12 天行程与强度 | `sections/core-route.html` | `s4-route` |
| §5 | 花多少钱 | `sections/sup-cost.html` | `s5-cost` |
| §6 | 进出山交通与返程风险 | `sections/sup-transport.html` | `s6-transport` |
| §7 | 高反与向导背夫 | `sections/sup-crew.html` | `s7-crew` |
| §8 | 签证、许可证、现金与通讯 | `sections/sup-onsite.html` | `s8-onsite` |
| — | References | `sections/references.html` | `references` |

层标题文件：`sections/core-intro.html`（`<h2 id="core">二 · 核心</h2>`）、`sections/sup-intro.html`（`<h2 id="sup">三 · 支持信息</h2>`）。`summary.html` 自带 `<h2 id="summary">一 · 摘要</h2>`，`references.html` 自带 `<h2 id="references">四 · References</h2>`。

每个节块形如：

```html
<section class="sec" id="s1-deal">
<h3>1 · Majestic Trails 的套餐值不值<a class="back" href="#summary">↑ 摘要</a></h3>
...
</section>
```

### 契约：交叉引用改写（全部单元共用）

正文里的「见 Q5」这类跨节指引按下表换成带链接的节号，写法 `见 <a href="#s4-route">§4</a>`：

| 旧 | 新 | 旧 | 新 |
|---|---|---|---|
| Q1 总价 | §5 `#s5-cost` | Q8 签证 | §8 `#s8-onsite` |
| Q2 套餐 | §1 `#s1-deal` | Q9 许可证 | §8 `#s8-onsite` |
| Q3 进山 | §6 `#s6-transport` | Q10 保险 | §3 `#s3-insurance` |
| Q4 返程 | §6 `#s6-transport` | Q11 两步路保险 | §3 `#s3-insurance` |
| Q5 行程 | §4 `#s4-route` | Q12 装备 | §2 `#s2-prep` |
| Q6 高反 | §7 `#s7-crew` | Q13 现金通讯 | §8 `#s8-onsite` |
| Q7 向导背夫 | §7 `#s7-crew` | Q14 行动清单 | §2 `#s2-prep` |

---

- id: T1
  title: citation 引擎
  file_path: scripts/reportgen/citations.py
  functions:
    - name: source_index
      inputs: `sources_dir=None`（缺省时用 `config.SOURCES_DIR`，传入时读该目录下的 `*.md`）
      outputs: `{"07": {"num": 7, "stem": "07-costs-lodging-food", "title": "沿途食宿与杂项价格", "outlets": ["Himalayan Hero《…》", ...], "urls": ["https://…", ...], "date": "2026-07-31", "body_md": "<全文>"}}`
      behavioral_contract: |
        扫 `sources/NN-<主题>.md`，文件名前两位为编号键。
        title 取首行 `# ` 后的文字（去掉首尾空白）。
        outlets 取全部「来源」标题行里冒号后的文字，去掉「来源 N：」前缀；二级 `## 来源…` 与三级 `### 来源…` 都算
        （`sources/05` 与 `sources/14` 用三级，它们把 `##` 留给主题分节，一手来源写在 `###` 下），
        文件里没有这类标题时 outlets 为空列表。
        urls 按出现顺序收集正文里全部 `http` 开头的裸链接，去重保序。
        date 取首个匹配 `(抓取|记录|收到|下载)日期[:：]\s*(\d{4}-\d{2}-\d{2})` 的日期，没有则为空字符串。
        body_md 是文件全文原样。
        编号键按数字升序返回（dict 保序）。
      error_cases:
        - { condition: "sources 目录下有文件名不以两位数字加短横线开头", behavior: "跳过该文件，不进索引" }
    - name: expand
      inputs: `text`（完整文档 HTML）, `index=None`（缺省时自己调 `source_index()`；用于校验编号存在）
      outputs: 展开后的 HTML 字符串
      behavioral_contract: |
        把每处 `[[NN]]` / `[[NN,MM]]` / `[[NN, MM]]` 替换成
        `<sup class="cite"><a id="cite-NN-K" href="#ref-NN">N</a></sup>`。
        N 去前导零（`07` → `7`）。K 从 1 起，按该编号在全文中出现的先后独立计数。
        多个编号共用一个 `<sup>`，内部条目以 `,` 连接，每个条目各自是一个 `<a>`。
        同一个 `[[..]]` 里重复的编号只渲染一次（保序去重）。
      error_cases:
        - { condition: "标记里的编号在 source_index 里不存在", behavior: "SystemExit，消息形如 `正文引用了不存在的出处：sources/99`" }
        - { condition: "展开后文本里仍有 `[[` 残留（语法写错，例如 `[[7]]`、`[[abc]]`）", behavior: "SystemExit，消息形如 `citation 标记语法不合法：[[7]]`" }
    - name: cite_sites
      inputs: `text`（完整文档 HTML，标记未展开）
      outputs: `{"07": [("s1-deal", "1 · Majestic Trails 的套餐值不值"), ...]}`
      behavioral_contract: |
        按 `<section class="sec" id="...">` 切块，块内 `<h3>` 去掉标签与回链后的文字为节标题。
        块内出现的每个编号记一条 (section id, 标题)，同一节内重复引用只记一次，按节在文档中出现的顺序排列。
        落在任何 sec 块之外的标记不记入。
      error_cases:
        - { condition: "文档里没有任何 sec 块", behavior: "返回空 dict" }
    - name: references_layer
      inputs: `text`（完整文档 HTML，标记未展开）, `sources_dir=None`（缺省时用 `config.SOURCES_DIR`）
      outputs: references 层的 HTML 字符串
      behavioral_contract: |
        输出两组 `<ol class="refs">`：第一组是被正文引用过的编号（按编号升序），
        第二组标题为「数据与方法来源」，装被正文引用过零次的编号（按编号升序）；任一组为空时不输出该组的标题与列表。
        每条形如：
        `<li id="ref-07"><span class="refnum">[7]</span> <b>标题</b> · outlets 以 ` · ` 连接 · 抓取日期 · urls 渲染成 <a> 链接`
        （outlets 之间、urls 之间、以及标题/outlets/日期/urls 这几段之间，一律用 ` · ` 连接；
        outlets 为空、date 为空、urls 为空时该段连同它前面的 ` · ` 一起不输出）
        条目要短到像学术 references，所以呈现层对这两段做压缩（`source_index()` 仍返回全量，不截断）：
        · **outlets 最多列 3 个**，总数超过 3 时第 3 个后面接 ` · 等 N 个来源`（N 是总数）。
        · **urls 按域名去重后最多列 4 个**，每个渲染成 `<a href="该域名首次出现的完整 URL">域名</a>`
          （域名即 URL 去掉协议头后到第一个 `/` 之前的部分），去重后超过 4 个时接 ` · 等 N 个站点`（N 是去重后总数）。
          `sources/14` 的 19 条链接同属一个站点，去重后只剩一条，这是这条规则的主要收益。
        后跟 `<p class="citedby">引用于 <a href="#s1-deal">§1</a>…</p>`（该编号被引用过时才输出，§ 号取 section id 里的数字），
        再跟 `<details><summary>原始记录</summary>…markdown 转 HTML…</details>`，最后 `</li>`。
        markdown 转换用 `markdown.Markdown(extensions=["tables"])`，每份转换前 `reset()`。
      error_cases:
        - { condition: "sources 目录为空", behavior: "返回空字符串" }
  dependencies: []
  reuse_candidates: |
    `scripts/reportgen/sources.py` 现有 `cite_map()` / `sources_layer()` 做的是同一类事（扫 ext 块、收 `href="#NN-"`、渲染全文），
    但它按 `href` 锚点收引用、按 `Q\d+` 排序、输出 `<section class="src">` 全文流，与新的角标机制不兼容。
    本单元取代它：`sources.py` 删除，`SOURCES_LINKED` token 消失。markdown 渲染与 reset() 的用法从它继承。
  acceptance: |
    hidden 测试全绿；四个函数的 error_case 都有测试覆盖。

- id: T2
  title: assemble 接线两阶段替换
  file_path: scripts/reportgen/assemble.py
  functions:
    - name: substitute
      inputs: `text`, `tokens`, `strict=True`
      outputs: 替换后的字符串
      behavioral_contract: |
        行为与当前一致，新增 `strict` 参数：`strict=True`（默认）时替换后仍有 `{{...}}` 残留就 SystemExit；
        `strict=False` 时残留原样留在结果里、不报错。现有全部测试在默认参数下行为不变。
      error_cases:
        - { condition: "strict=True 且有未解析 token", behavior: "SystemExit，消息含第一个未解析的 token 名（与当前一致）" }
    - name: build
      inputs: 无
      outputs: OUT 路径
      behavioral_contract: |
        流程改为：
        resolve_includes → check_orphans → collect_tokens（六个 provider 去掉 sources、加上 packing 等既有项，不含 REFERENCES）
        → check_token_usage(text, {**tokens, "REFERENCES": ""})
        → substitute(text, tokens, strict=False)（此时只剩 {{REFERENCES}}）
        → citations.references_layer(body) 建引用图并渲染
        → substitute(body, {"REFERENCES": refs})（strict 默认，残留检查在这里生效）
        → citations.expand(...) 展开全部角标
        → 写 OUT。
      error_cases:
        - { condition: "任一闸门触发", behavior: "沿用现有消息，逐字不变" }
  dependencies: [T1]
  reuse_candidates: |
    `collect_tokens()` 的 provider 元组里去掉 `sources`，其余五个（figures / costs / quotes / route / packing）不动。
  acceptance: |
    `uv run --with pytest pytest tests/ -q` 里 test_assemble.py 全部既有用例保持通过；新增 strict 参数与 build 流程的测试通过。

- id: T3
  title: 角标与 references 样式
  file_path: report/styles/components.css + report/styles/appendix.css + report/styles/print.css
  functions:
    - name: cite-superscript-styles
      behavioral_contract: |
        `sup.cite` 小号、不换行、链接无下划线、颜色比正文浅一档，与前面文字之间零间距。
        `ol.refs` 去掉默认序号（编号由 `.refnum` 自己写），条目之间有间距，`.refnum` 等宽、右对齐观感。
        `.citedby` 小号灰字。`details > summary` 可点、小号、不显示默认三角以外的装饰。
        打印时 `details` 内容不展开（references 保持紧凑），角标仍可见。
        每个 CSS 文件仍 ≤ 40 行。
  dependencies: []
  reuse_candidates: |
    `appendix.css` 现有 `.src` 系列规则服务旧出处层，随 `sources.py` 一起删除。
  acceptance: |
    构建产物在浏览器里角标为小号上标、references 为紧凑编号列表、原始记录默认收起。

- id: T4
  title: 摘要 + 层标题 + header
  file_path: report/sections/summary.html + core-intro.html + sup-intro.html + header.html
  behavioral_contract: |
    header.html 压到 600 字符内：大标题、行程窗口 meta 行、一段导语（行程硬约束 + 计价口径两句）。
    summary.html ≤ 1,400 字符：`<h2 id="summary">一 · 摘要</h2>` + 一句 meta（说明角标点开是 references）+ 6 行摘要表，
    每行一句结论、链到对应节锚点，覆盖：套餐值不值（§1）、行前准备时间线（§2）、保险（§3）、行程强度（§4）、总价（§5，用 {{TOTAL_USD}}）、返程无缓冲是最大风险（§6）。
    core-intro.html / sup-intro.html 各 ≤ 250 字符，一个 h2 加一句 meta。
  dependencies: []
  acceptance: 四个文件合计 ≤ 2,500 字符；摘要每行的锚点在 T5–T8 产出的 section id 里存在。

- id: T5
  title: §1 套餐值不值
  file_path: report/sections/core-deal.html
  behavioral_contract: |
    原 `ext-quote.html`（5,216 字符）压到 ≤ 2,700 字符。保留：结论句、两档口径差价（Lukla 会合 / 加都同机）、
    餐食是溢价主要来源这一条、按 6 人档重报 USD 1,015 这个动作、两张 token 表（{{TBL_QUOTE_ITEMS}}、{{TBL_QUOTE_TOTALS}}）、
    五件书面确认（压成一个紧凑列表，每条一句）、值得认可的部分（压成一句）。
    全部 16 个 QUOTE_* 内联 token 保持被引用（闸门要求 token 供需精确匹配，一个都不能丢）。
    删：与 Q1 口径差异的那段元说明、repo 内部路径、重复解释同一件事的句子。
    引用改角标。
  dependencies: []
  acceptance: ≤ 2,700 字符；16 个 QUOTE_* token 与两张表 token 全部出现。

- id: T6
  title: §2 行前准备 + §3 保险
  file_path: report/sections/core-prep.html + report/sections/core-insurance.html
  behavioral_contract: |
    core-prep.html ≤ 2,300 字符：合并原 `ext-todo.html` 的时间倒排清单与 `ext-packing.html` 的装备决策。
    结构是「时间线表（现在→8 月中 / 8 月 / 9 月上旬 / 出发前 1 周 / 9.24 登机前）」+「装备决策表（压到 6 行）」+ {{TBL_PACKING}}。
    时间线里那条「订 9.25 下午 2 架直升机包机」按当前行程改掉：9.25 是加都休整日，要订的是 9.26 早班进山机票（起降机场待定，见 §6）。
    core-insurance.html ≤ 2,700 字符：原 `ext-insurance.html`（8,974 字符）压到三成。保留：
    必买且多数国内产品不合格这个结论、直升机救援实际费用量级与那笔实赔案例、已核实产品表（压到 5 行）、
    选购三条核对项、两步路平台核查的结论（华泰与安盛把尼泊尔整体除外、京东安联那款是唯一可用但尼泊尔直升机封顶约 USD 1,176 且详情页查不到这条）、
    下单前四问（压成一个紧凑列表）。删：条款项号的逐条推演、客服电话之外的流程细节、重复陈述。
  dependencies: []
  acceptance: 两文件合计 ≤ 5,000 字符；{{TBL_PACKING}} 被引用；保险的四条待确认口径与那条封顶发现都在。

- id: T7
  title: §4 12 天行程与强度
  file_path: report/sections/core-route.html
  behavioral_contract: |
    原 `ext-route.html`（2,847 字符）保持在 ≤ 2,400 字符——这一节是给同行者看强度的，图件与逐日表是重点，压缩只针对口径解释的冗长处。
    保留：{{TBL_ITINERARY}}、徒步详图 {{IMG_TREK_MAP}}、全程剖面 {{IMG_ELEV_PROFILE}} 与它们的 figcaption、
    合计 113.2 km / 爬升 6,502 m / 下降 6,419 m、10 张小图共用比例尺可直接比强度这一条、只保留一个适应日导致爬升更密集这一条。
    压缩：重采样与滞回阈值的算法细节压成一句、去掉 repo 内部路径。
    开头补一句直说强度的结论（这是本节对同行者的用处）。
  dependencies: []
  acceptance: ≤ 2,400 字符；三个图件/表格 token 都在。

- id: T8
  title: §5–§8 支持层四节
  file_path: report/sections/sup-cost.html + sup-transport.html + sup-crew.html + sup-onsite.html
  behavioral_contract: |
    sup-cost.html ≤ 700 字符：原 `ext-costs.html`，保留 {{TOTAL_USD}}、{{TBL_COSTS_MAIN}}、{{TBL_COSTS_REF}}，
    口径压成两句（分摊规则 + 单点估算规则）。
    sup-transport.html ≤ 1,700 字符：原 `ext-transport.html`（3,394）合并 Q3 与 Q4，保留 {{IMG_OVERVIEW_MAP}}、
    三个进山选项及其价格、起降机场待定这个事实、返程无缓冲与直升机兜底额度。
    sup-crew.html ≤ 1,900 字符：合并原 `ext-health.html`（2,163）与 `ext-guide.html`（2,189），
    保留高反三条（一个适应日的代价、Diamox、血氧仪与手表偏差）、下撤原则、法规允许不请但建议请 1 名的三条理由、
    配置价格（每人约 USD 215）、Lukla 会合省机票、订房委托向导。
    sup-onsite.html ≤ 1,700 字符：合并原 `ext-paperwork.html`（1,605）与 `ext-cash.html`（2,012），
    保留签证（免费、30 天档、行前 2–3 天电子签）、两个许可证（各 NPR 3,000、在哪办）、现金额度、Ncell 与 Everest Link、
    市内安全三条压成一句、雨季尾巴与人流这一条。
    四节都改角标引用，都不出现 repo 内部路径。
  dependencies: []
  acceptance: 四文件合计 ≤ 6,000 字符；全部既有 token 保持被引用。

- id: T9
  title: shell 重排 + references 章节 + 文档同步
  file_path: report/shell.html + report/sections/references.html + AGENTS.md + PROJECT.md + PATTERNS.md + DEVFLOW.md
  behavioral_contract: |
    shell.html 的 include 清单按新顺序重排，与 sections/ 下的文件一一对应（闸门双向校验）。
    references.html ≤ 400 字符：`<h2 id="references">四 · References</h2>` + 一句 meta（编号对应正文角标，展开看原始记录）+ {{REFERENCES}}。
    文档同步：AGENTS.md 的三层结构描述与「要改 X 就动哪个文件」表、PROJECT.md 的章节清单与结构段与当前状态、
    PATTERNS.md 的锚点契约（换成 citation 标记契约与节锚点契约）与 token 分工数、DEVFLOW.md 的交付前检查第 5 条。
    文档只写当前事实。
  dependencies: [T1, T2, T4, T5, T6, T7, T8]
  acceptance: 构建通过；测试全绿；四份文档里对旧 Q 编号与旧出处层的描述已换成当前事实。

## Dependency Graph

```
T1 (citation 引擎) ──> T2 (assemble 接线) ──┐
T3 (样式)  ────────────────────────────────┤
T4 (摘要/层标题/header) ───────────────────┤
T5 (§1 套餐) ─────────────────────────────┼──> T9 (shell 重排 + 文档同步)
T6 (§2/§3 准备与保险) ─────────────────────┤
T7 (§4 行程) ─────────────────────────────┤
T8 (§5–§8 支持层) ────────────────────────┘
```

无环。T3 与 T4–T8 只依赖上面写死的语法契约与节编号表，不依赖 T1 的实现，因此与 T1/T2 同波并行。

## Execution Waves

- **Wave 1（并行）**：T1（test-first：test-author → 架构师审测试 → implementer）、T3、T4、T5、T6、T7、T8。各单元目标文件互不重叠。
- **Wave 2**：T2（依赖 T1 的模块接口）。
- **Wave 3**：T9（依赖全部上游），随后跑构建 + 全量测试 + 只读终审。

## Status

Completed。正文 37,704 → 18,540 字符（−51%）；References 条目头合计 9,521 → 3,973 字符（−58%），最长一条 1,269 → 395；正文角标 197 个，18 条 references 锚点全部成对、无悬空。构建通过，`267 passed`。

两处收尾时发现并修掉、原 spec 未点名的问题：费用表原本没有出处列（违反「每条结论带出处」），补上后表内 16 行各带角标；`sources/05` 与 `sources/14` 用三级 `### 来源` 标题，原 `source_index()` 只收二级，导致这两份出处的来源方一个都没显示，放宽后 `sources/14` 的 22 条一手笔记以「等 22 个来源」呈现。

终审由架构师亲自完成（派出的两个只读审计员都因 session limit 中断）：核对了 spec 保留清单逐项在位、`data/*.csv` 数字零改动（符合 Non-goals）、`sources.py` 删除后无遗留引用、产物无未转义标签、文件粒度上限守住。
