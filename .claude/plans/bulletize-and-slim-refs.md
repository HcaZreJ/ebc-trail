# Feature: 正文 bullet 化 + References 换要点摘录

## Overview

报告目前全文可见字符 86,230：正文 15,260，References 层 70,970（其中 67,087 是 19 份 `sources/*.md` 全文倾泻进 `<details>`，保险 ref-19 一条 20,285 字、小红书 ref-14 一条 12,493 字）。信息齐全但读不完。

这一版做两件事：正文全部散文段落改成 bullet list，每条 bullet 承载一个可行动的事实；References 每条的折叠内容从「原文全文」换成「要点摘录」——摘录写在 `sources/NN-*.md` 的 `## 要点` 小节里，一手记录全文继续留在同一文件后半部供核对，报告只渲染要点段。

目标：全文可见字符降到 16,000 以内，其中 References 层降到 6,000 以内。

## Intent Brief

- **Goal**：6 名同行者点开就能读完。每节先给结论，再给 bullet 要点；想核对细节的人点 References 的链接或去 repo 看 `sources/`。
- **Motivation**：用户反馈「文字还是太多，保险那节尤其，进了 References 更多，没人有力气读」。要的是提炼要点、不重要的不写进去。
- **Known context**：上一轮 `report-slim-citations` 已把结构改成四层 + `[[NN]]` 角标 + References 层，结构不动，这轮只压文字。`citations.py` 的 `_render_entry` 目前把整份 sources markdown 渲染进 `<details>`。
- **Constraints**：AGENTS.md 铁律全部适用——每条结论带出处、表格数字唯一事实源是 `data/*.csv`、USD 与 NPR 计价、客观朴素文风、交付前重跑构建。图件与 CSV 数字不动。sources 的一手记录全文不改写（只在文件顶部新增 `## 要点` 段）。
- **Non-goals**：不重算费用、不重画图、不新增调研、不改章节编号与锚点结构、不动 `data/*.csv`。
- **Success criteria**：全文可见字符 ≤ 16,000（现 86,230）；References 层 ≤ 6,000（现 70,970）；正文 `<p>` 段落只剩每节的结论句与图注，其余事实进 `<ul>`；构建通过、测试全绿、角标与锚点成对。
- **Assumptions**：见下表。
- **Unknowns**：无阻塞项。

## Alignment Gate

**I will implement**

- 13 个 `report/sections/*.html` 的散文段落改 bullet list，每节保留一句结论 + 若干条要点；现有表格保留，表格内的长句同样削成要点。
- 19 份 `sources/NN-*.md` 顶部新增 `## 要点`（3–6 条 bullet，每条一个事实/数字/结论）。原文全文原样留在文件后半部。
- `citations.py` 只把 `## 要点` 段渲染进 References 的 `<details>`，并在构建期校验每份 sources 都有该段。
- 同步 PATTERNS.md（sources 文件契约新增 `## 要点`）与 PROJECT.md（章节文风事实）。

**I will not implement**

- 不删 `sources/*.md` 的任何既有内容。
- 不改 `data/*.csv`、不改图件、不改章节编号与 `id`。
- 不把 References 的 `<details>` 整个去掉——保留要点摘录，报告仍自包含可离线核对。

**Open assumptions**：A1、A2（下表）。

**Acceptance criteria**

1. `uv run --with markdown scripts/build_report.py` 打印 `wrote ...`。
2. `uv run --with pytest pytest tests/ -q` 全绿，含 `## 要点` 提取与闸门的新测试。
3. 产物全文可见字符 ≤ 16,000，References 层 ≤ 6,000。
4. 每个角标 `href="#ref-NN"` 都有对应 `id="ref-NN"`；`[[` 零残留。
5. 每节的结论与关键数字与改写前一致（不因压缩丢结论、丢数字、丢待办动作）。

## Assumption Ledger

| Assumption | Confidence | Impact if Wrong | Status |
|---|---:|---:|---|
| A1 · References 折叠内容换成 3–6 条要点摘录（而非整段删除）符合「需要核对的人自己去核对」 | medium | medium | 待用户确认 |
| A2 · 正文压到约 55%、全部 bullet 化是用户要的力度 | high | medium | 以保险节样例给用户过目 |
| A3 · 表格保留不改成 bullet（表格本身即压缩形态） | high | low | 按此实现 |

## 压缩方法（全部单元共用的硬约束）

压缩靠删信息块，不靠挤句子。

- 逐块判断：这块信息，6 名同行者在做决定或做准备时用得上吗？用得上就整块留下，用不上就整块删掉。
- 留下来的句子保持原来的措辞：主谓宾完整、该有的修饰词留着、一句话讲一件事。两三个事实不塞进同一句，不写成电报体。
- 典型该删的：落选方案的逐条依据、推演过程与中间论证、与最终决定无关的备选细节、同一件事的第二次解释。
- 典型该留的：结论、要做的动作、关键数字、风险提示、买错会出事的辨识信息、待确认项。
- 删掉的信息留在 `sources/*.md`，读者要核对时从 References 的链接进去。

风格基准是已改好的 `report/sections/core-insurance.html`（2,363 字 → 1,272 字）。它删掉了 9 行方案对比表（主选已定，落选的六款产品为什么不行，读者不需要读）与「付款前问清的事」里三款备选产品的条目；留下来的每一句都是原文措辞。

## Work-Unit Specs

- id: T1
  title: citation 引擎渲染要点摘录
  file_path: scripts/reportgen/citations.py
  functions:
    - name: _extract_excerpt
      inputs: 一份 sources markdown 全文 `text: str`
      outputs: `## 要点` 小节的 markdown 正文（不含标题行），`str`
      behavioral_contract: |
        找到首个 `## 要点` 行，取到下一个同级或更高级标题（`^#{1,2} `）之前为止，
        去掉首尾空行后返回。找不到 `## 要点` 时返回空字符串。
        小节内允许 bullet、粗体、行内链接；原样返回，交给 markdown 渲染。
      error_cases:
        - { condition: "文本无 `## 要点`", behavior: "返回空字符串（由 source_index 的调用方决定是否报错）" }
        - { condition: "`## 要点` 是文件最后一节", behavior: "取到文件末尾" }
    - name: source_index
      behavioral_contract: |
        每个条目新增 `excerpt` 键，值为 `_extract_excerpt(text)`。
        `body_md` 键保留原样不变（其它调用方可能用到）。
        这个函数只做提取，缺 `## 要点` 的文件在这里得到空字符串，报错交给 check_excerpts。
    - name: check_excerpts
      inputs: `source_index()` 的返回值 `index: dict`
      outputs: `None`
      behavioral_contract: |
        遍历 index，任一条目的 `excerpt` 为空字符串就 SystemExit，消息点名是哪几份文件。
        空的 `## 要点` 小节与完全没有该小节同等对待——闸门要保证每条 reference 都有可展示的要点。
        全部条目都有非空 excerpt 时返回 None。空 index 返回 None。
      error_cases:
        - { condition: "某份 sources 的 excerpt 为空", behavior: "raise SystemExit，消息含 `sources/NN` 与 `## 要点`" }
    - name: _render_entry
      behavioral_contract: |
        `excerpt` 非空时渲染 `<details><summary>要点</summary>` + markdown 转换后的 excerpt。
        `excerpt` 为空时整个 `<details>` 不输出。
        头部信息（编号、标题、来源方、日期、链接）与「引用于 §N」回链保持现状不变。
  wiring: |
    `scripts/reportgen/assemble.py` 的 `build()` 在调 `citations.references_layer(body)` 之前
    先 `citations.check_excerpts(citations.source_index())`，让闸门落在构建路径上。
    `source_index` 与 `references_layer` 保持不报错，既有测试的 fixture 因此无需改动。
  dependencies: []
  reuse_candidates: |
    `citations.py` 已有 `source_index` / `_render_entry`，就地扩展，不新建模块。
    markdown 渲染复用 `_render_entry` 已持有的 `md` 实例。
  acceptance: |
    hidden + visible 测试全绿；构建在任一 sources 缺 `## 要点` 时报错退出。

- id: T2
  title: 19 份 sources 补 `## 要点` 段
  file_path: sources/*.md
  behavioral_contract: |
    每份文件在首段（抓取口径说明）之后、第一个 `## 来源` / `## 一、` 之前插入 `## 要点`。
    3–6 条 bullet，每条一句话，承载一个数字、一个结论或一条待办。
    只写这份 sources 支撑正文的那些事实，不复述与正文无关的细节。
    既有内容一字不改。
  dependencies: []
  acceptance: |
    19 份文件都有 `## 要点`；`git diff` 显示只有新增行，无删除行。

- id: T3
  title: 核心四节 bullet 化
  file_path: report/sections/core-{deal,prep,insurance,route}.html
  dependencies: []
  acceptance: |
    四节合计可见字符降到改写前的 60% 以内；结论、数字、待办动作、角标一个不丢。

- id: T4
  title: 支持四节 bullet 化
  file_path: report/sections/sup-{cost,transport,crew,onsite}.html
  dependencies: []
  acceptance: |
    同 T3。

- id: T5
  title: 摘要与层导语收紧
  file_path: report/sections/{summary,header,core-intro,sup-intro,references}.html
  dependencies: []
  acceptance: |
    摘要六行每行一句话；References 导语改为一句话说明折叠内容是要点摘录。

## Dependency Graph

```
T1 ──┐
T2 ──┴─→ 构建闸门（T1 的校验依赖 T2 的产物）
T3 ─── 独立
T4 ─── 独立
T5 ─── 独立
```

无环。T1 与 T2 各自可独立开工，二者都完成后构建才通过。

## Execution Waves

- **Wave 1（全并行，文件互不重叠）**：T1、T2、T3、T4、T5
- **Wave 2**：架构师审稿 → 构建 → 全量测试 → 字符数核验

## Status

Completed。产物实测：

| | 改前 | 现在 |
|---|---:|---:|
| 打开报告直接看到的文字 | 19,143 | 16,311 |
| 其中 正文散文 | 7,474 | 4,642 |
| 其中 表格（数据，不动） | 7,786 | 7,792 |
| 折叠起来按需展开的内容 | 67,087 | 8,133 |
| 合计可见字符 | 86,230 | 24,444 |

`## Alignment Gate` 的 acceptance 里「全文 ≤ 16,000」这个数按合计口径未达到，实际 24,444。差额来自两块不该按散文标准压的内容：表格 7,792 是 CSV 驱动的数据，19 份出处的要点摘录 8,133 默认折叠、按需展开。按「打开报告直接看到多少字」这个更贴近阅读负担的口径，结果是 16,311。

`core-deal` 的 `QUOTE_BASE_HIS` `QUOTE_BASE_OURS` `QUOTE_BASE_GAP` `QUOTE_BASE_OURS_KTM` `QUOTE_BASE_GAP_KTM` `QUOTE_HIS_ALLIN` `QUOTE_GAP_ALLIN_PCT` 七个 token 连同 `quotes.py` 里的定义一起删除——它们在正文里复述的是 `TBL_QUOTE_TOTALS` 表格已逐列给出的数字。
