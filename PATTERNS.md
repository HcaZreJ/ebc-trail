# PATTERNS

## include 指令契约

`report/shell.html` 用 include 指令声明装载什么、按什么顺序装载。指令有两种等价写法，各自在宿主语言里是合法注释：

```html
<!-- include: sections/ext-costs.html -->
```

```css
/* include: styles/base.css */
```

- **路径相对 `report/` 解析**，写成 `styles/<名>.css` 或 `sections/<名>.html`。
- **正则锚定整行**（`scripts/reportgen/assemble.py` 的 `INCLUDE_RE`）。指令独占一行，行首行尾的空白允许存在；同一行还有别的内容、路径里含空白、写成 `include`（缺冒号）时该行按普通文本处理。
- **整行被目标文件内容替换**，包含该行的缩进。目标文件末尾的一个换行去掉，其余字节逐字进产物。
- **不递归展开**：被 include 的文件内容里出现的 include 指令按普通文本插入。
- **`shell.html` 的 include 顺序是装载顺序的唯一事实源。** `<style>` 块内五条 CSS include 的先后即层叠顺序，后装载的规则覆盖先装载的同优先级规则；`<main>` 内 section include 的先后即报告章节顺序。调整章节顺序或 CSS 优先级就调 `shell.html` 里这些行的位置。
- **`styles/` 与 `sections/` 下的每个文件被恰好装载一次。** 新建文件的同时在 `shell.html` 加一条 include，删文件的同时删掉那条 include。以 `.` 开头的文件（`.DS_Store` 这类系统产物）按非报告内容跳过。
- **章节之间的空行分隔与 `<div class="appendix">` 包裹层留在 `shell.html` 里**，章节文件自身标签平衡、不带外围空行。

## token provider 契约

CSV 表格、图片、合计数字通过 `{{TOKEN}}` 占位进入章节，值由 `scripts/reportgen/` 下的 provider 提供。

- **每个 provider 暴露一个 `tokens()`**，返回 `{裸 token 名: 已渲染的 HTML 或字符串}`。键不带花括号，加花括号与合并由 `assemble.collect_tokens()` 负责。
- **provider 之间零 import 依赖。** 六个 provider `figures.py` / `costs.py` / `quotes.py` / `route.py` / `packing.py` / `sources.py` 各自只从共用基础设施取东西：`config.py`（`ROOT` 与各目录路径、`RATE`、`PAX`）、`csvio.py`（`read_csv` / `blocks` / `esc` / `signed`）、`tables.py`（`table` 渲染器）、`money.py`（`amt` / `y` / `diff`）、`imgio.py`（`img_uri`，从 `assets/*.png` 生成 base64 data URI，`figures.py` 与 `route.py` 共用）。新增 provider 沿用这条边界。
- **`assemble.py` 只认 `tokens()` 这个接口**，在 `collect_tokens()` 里惰性 import 六个 provider，本身只从 `config.py` 取 `REPORT_DIR`，不知道任何领域细节。
- **token 名全局唯一。** 两个 provider 返回同一个键时构建停下。
- **token 供需精确匹配。** 每个 provider 产出的 token 在某个 section 里被引用，每个 section 引用的 token 有 provider 提供。加一个 token 就同时改 provider 与引用它的 section。
- **token 值原样插入，不做二次替换。** 值里出现的 `{{...}}` 字样会被残留检查报出来。
- 当前 token 分工，共 20 个：`figures.py` 三张图的 base64 data URI（3）；`costs.py` 费用明细表与参考表加合计的人民币与美元两个数字（4）；`quotes.py` 报价评估的两张表加七个内联数字（9）；`route.py` 一张合并的 12 天行程表（1）；`packing.py` 装备全量表（1）；`sources.py` 出处层全文含回链（1）；`BUILD_DATE` 由 `assemble.py` 自己给（1）。

## 构建期闸门

`uv run --with markdown scripts/build_report.py` 在下列任一情况下打印一行中文消息并以退出码 1 停下。消息形态照实：

| 情况 | 消息 |
|---|---|
| include 目标文件不存在 | `shell.html 第 28 行的 include 目标不存在：sections/ext-paperwork.html` |
| 同一路径被 include 两次 | `include 指令重复装载同一文件：sections/ext-todo.html` |
| `styles/` 或 `sections/` 下有文件没被任何 include 装载 | `以下文件没有被 shell.html 装载：sections/ext-packing.html` |
| provider 产出的 token 在所有章节里都没被引用 | `以下 token 没有被任何章节引用：TBL_COSTS_REF` |
| 章节引用了没有 provider 提供的 token | `装配后仍有未解析的 token：'NEW_UNDEFINED_TOKEN'` |
| 两个 provider 返回同一个 token 名 | `token 名冲突：TBL_COSTS_MAIN 同时由 reportgen.route 提供` |

构建成功时输出一行 `wrote <路径>  (12.7 MB)`。

## 三层锚点契约

三层互跳全部走文档内锚点，id 与 href 成对出现，规则如下：

- **速览行**：`sections/faq.html` 里每个问题一行 `<tr id="faq-q-<slug>">`，问题单元格是指向 `#q-<slug>` 的链接，回答控制在一句话、结论性数字直接给出（可用 token）。
- **详解块**：`<section class="ext" id="q-<slug>">`，首行 `<h3>QN · 问题<a class="back" href="#faq-q-<slug>">↑ 速览</a></h3>`。一个 ext 文件可容纳多个相邻的问题块。
- **引用**：详解正文句末括注 `（<a href="#<出处文件 stem>">sources/NN</a>）`，stem 即 `sources/NN-<主题>.md` 去掉扩展名；表格单元格里的出处保持纯文本（表格渲染器转义 HTML）。
- **出处块**：`scripts/reportgen/sources.py` 渲染每份出处为 `<section class="src" id="<stem>">`，并扫描全部章节文件的 ext 块，把命中 `href="#\d{2}-…"` 的引用汇成「被引用于」回链行，按问题编号排序。回链自动生成，手工只管在正文里放引用链接。

## 配方

### 新增一个问题（速览行 + 详解块）

1. 在 `sections/faq.html` 加一行：`<tr id="faq-q-<slug>">`，问题单元格链接 `#q-<slug>`，回答一句话。
2. 在主题相邻的 `sections/ext-*.html` 里加一个 `<section class="ext" id="q-<slug>">` 块（或新建 ext 文件并在 `shell.html` 目标位置补一条 include），首行 h3 带回链，正文事实括注并链接出处。
3. 这一块需要的出处写进 `sources/NN-<主题>.md`，需要的表格数字写进 `data/<名>.csv`。
4. 跑 `uv run --with markdown scripts/build_report.py`。

### 新增一个 token

1. 在对应领域的 `scripts/reportgen/<领域>.py` 的 `tokens()` 返回字典里加一个键值对；渲染表格用 `tables.table()`，读 CSV 用 `csvio.read_csv()`，美元转人民币用 `money.y()`，千分位格式化用 `money.amt()`。领域不在现有五个里时新建一个模块，只 import `config` / `csvio` / `tables` / `money`，并在 `assemble.collect_tokens()` 的 provider 元组里加上它。
2. 在引用它的 `report/sections/*.html` 里写 `{{该键}}`。
3. 跑构建。两步只做一步时闸门会报出未被引用或未解析。

### 新增一张 CSV 表

1. 新建 `data/<名>.csv`，第一行是列名，取数规则与出处写进独立的列（`note` / `basis` / `source`）。
2. 出处文件 `sources/NN-<主题>.md` 记 URL、抓取日期、提取出的数字。
3. 在领域 provider 里加一个渲染成报告用表的 token（走上面「新增一个 token」的配方），在需要它的 section 里引用。
4. 在 PROJECT.md 的「六张 CSV 的职责与相互关系」补一条，写清它的职责、与其它 CSV 的取数关系、是人工整理还是脚本产物。
5. 跑构建。

## 文件粒度上限

- **单个 section 文件 ≤ 60 行**（当前最大 `ext-transport.html` 约 20 行，其次 `ext-quote.html`/`ext-route.html` 约 18 行）。
- **单个 Python 模块 ≤ 200 行**（当前最大 `make_map.py` 198 行，其次 `day_tracks.py` 197 行 —— 这份文件里有一段 20 行的 docstring 写着 10 天的轨迹拼接表，那张表是 `assemble()` 的核心契约，不是可精简的注释）。
- **单个 CSS 文件 ≤ 40 行**（当前最大 `base.css` 15 行）。

上限的判据是「一个 sub-agent 用一个 context window 能把这个文件读懂并改对」。写到上限时按主题切成两个文件，section 在 `shell.html` 补一条 include，Python 模块按领域拆成新 provider。

## 数据引用规则

- **报告只引用 CSV，不另立数字。** 表格与合计走 `{{TOKEN}}` 从 `data/*.csv` 取，改 CSV 之后报告跟着变。会随 CSV 变动的关键数字尽量走 token（`TOTAL_CNY`、`TOTAL_USD`、`QUOTE_*` 这批已经是这样）。
- **正文里复述的单项金额与 CSV 保持一致。** 速览回答与详解散文、手写表里出现的金额是 `cost-breakdown.csv` 或 `sources/` 对应行的复述。`cost-breakdown.csv` 的每行是单点估算，正文里仍以区间出现的 11 处金额（`¥6,800–9,520` 的独立徒步公开区间、`¥34–54` 的低海拔单餐这类）直接复述 `sources/` 的原始区间，与费用表的单点值各有出处。改了金额之后 `grep` 该数字，把正文里复述它的地方一起改。
- **手写表放在 section 文件里的场合**：内容是分类结论、条款对比、行动清单这类不参与算术的定性信息（保险产品表、装备决策表、行动清单表都是这类），出处在表外的引言句括注或单独一列写 `sources/NN`。参与算术、需要跟合计对齐、或者要出全量的数据进 CSV。
- **脚本产物不手改。** `data/route-track-stats.csv` 与 `assets/*.png` 由 `scripts/make_profile.py` 和 `scripts/make_map.py` 重写，改它们改脚本或改输入。
- **口径写在数据旁边。** 取数规则、估算算法、噪声警示写进 CSV 自己的 `note` / `basis` / `source` 列，引用该表的详解块用一句引言复述这个口径，读报告的人不必回来读 CSV。
