# Feature: 报告三层结构重构（速览 FAQ · 详解 · 出处）

## Overview

报告信息密度过高，读者没有阅读入口。重构为三层：① 速览——13 个问题各配一句话回答；② 详解——每个问题一块，讲清答案的依据、关键数字与必要表格；③ 出处——sources/*.md 全文收录。三层之间用锚点超链接互跳：速览行 ↔ 详解块，详解句末括注 ↔ 出处原文（出处开头自动列出「被引用于」回链）。删掉附录 A（六张 CSV 全量表）这类查证型内容——要查证的读者直接进出处层。

## Intent Brief

- **Goal**：同一份自包含 HTML 报告，读者先读一屏速览即得全部结论，按需下钻详解与出处。
- **Motivation**：现版 14 章平铺，信息多到没有阅读欲望。
- **Known context**：14 章、6 CSV、15 份出处、4 图件、include/token 构建闸门齐备；测试只覆盖 assemble.py 纯函数（自建 tmp 目录，不读真实 report/）。
- **Constraints**：AGENTS.md 八条铁律（出处、CSV 唯一事实源、单点估算、文风、重跑构建）；PATTERNS.md 的 include/token 契约与文件粒度上限。
- **Non-goals**：不改任何数字口径、不改图件脚本、不改 CSV 数据（除 quote-comparison.csv 的出处编号列）。
- **Success criteria**：构建闸门全过、pytest 28 全绿、三层互跳锚点在产物里成对存在、正文体量明显小于现版。
- **Assumptions**：用户在任务描述里给定三层结构，视为已批准的设计；作为后台任务直接执行，产出 draft PR 供最终 review。

## Alignment Gate

- Will：重构 report/sections、shell.html、reportgen provider（appendix→sources + 新 packing）、components.css；出处 14/15 撞号纠正；同步 PROJECT/AGENTS/PATTERNS/DEVFLOW。
- Won't：改费用/路线数据本身；改 make_map/make_profile；push main。
- Open assumptions：FAQ 的 13 个问题划分由本次设计给出，用户未逐条确认——draft PR 里请用户复核问题清单。
- Acceptance：`uv run --with markdown scripts/build_report.py` 输出 wrote 行；`uv run --with pytest pytest tests/ -q` 全绿；产物中每个 `href="#…"` 有对应 id。

## Assumption Ledger

| Assumption | Confidence | Impact if Wrong | Status |
|---|---:|---:|---|
| 13 个 FAQ 问题的划分符合用户预期 | medium | low（增删问题是局部改动） | draft PR 中请用户复核 |
| 附录 A 全量表可删（查证走出处层 + repo CSV） | medium | low（恢复即加回 include 与 token） | 用户明示「查证自己去读 sources」，据此删 |
| 代理报价单出处编号 14→15（与小红书实地情报撞号） | high | low | 直接执行 |

## Work-Unit Specs

内容重写与小规模 provider 改动强耦合（token 供需闸门双向校验），由本 session 单线程完成，构建闸门 + 既有 pytest 作验收；测试先行的函数级 harness 不适用于散文/HTML 重排。

- T1 出处撞号：`git mv sources/14-agency-quote…md → 15-agency-quote…md`；quote-comparison.csv 出处列同步。
- T2 章节层：删 14 个旧 section 文件，新建 header（微调）、faq、ext-intro、ext-costs、ext-quote、ext-transport、ext-route、ext-health、ext-guide、ext-paperwork、ext-insurance、ext-packing、ext-logistics、ext-todo、sources 共 15 个文件；shell.html include 清单同步。
- T3 provider：appendix.py → sources.py（SOURCES_LINKED，渲染 sources 全文并扫描 ext 块自动生成「被引用于」回链）；新建 packing.py（TBL_PACKING）；assemble.collect_tokens 的 provider 元组同步。删除的 token：TBL_ITINERARY_FULL、TBL_COSTS_FULL、TBL_PACKING_FULL、TBL_TRACKSTATS_FULL、TBL_ROUTE_SEGMENTS_FULL、TBL_QUOTE_CMP_FULL、APPENDIX_SOURCES。
- T4 样式：components.css 加回链与 FAQ 链接样式；appendix.css 继续服务出处层（.appendix 包裹层保留在 shell）。
- T5 文档：PROJECT.md（章节清单、出处清单 15 份、当前状态）、AGENTS.md（结构描述、铁律 1 措辞、改 X 对照表）、PATTERNS.md（锚点契约、token 分工 22 个、配方、粒度现值）、DEVFLOW.md（交付前检查第 5 条措辞）。
- T6 验收：build + pytest + 产物锚点成对性抽查 + de-ai-writing 残渣检测跑新文案。

## 锚点契约（实现依据）

- 速览行：`<tr id="faq-q-<slug>">`，问题单元格是指向 `#q-<slug>` 的链接。
- 详解块：`<section class="ext" id="q-<slug>">`，`<h3>QN · 标题<a class="back" href="#faq-q-<slug>">↑ 速览</a></h3>`。
- 引用：正文句末 `（<a href="#<source 文件 stem>">sources/NN</a>）`；表格单元格里的出处保持纯文本（渲染器转义 HTML）。
- 出处块：`<section class="src" id="<stem>">`（既有），sources.py 扫描各 section 文件的 ext 块，按 `href="#\d{2}-[\w-]+"` 汇成「被引用于」回链行，按 QN 排序。

## FAQ 问题清单（速览顺序 = 详解顺序）

Q1 总价 · Q2 Majestic 套餐 · Q3 9.25 进山 · Q4 10.6 返程兜底 · Q5 12 天行程 · Q6 高反 · Q7 向导背夫 · Q8 签证 · Q9 许可证 · Q10 保险 · Q11 装备 · Q12 现金通讯 · Q13 行动清单

## Status

Completed
