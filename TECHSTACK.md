# TECHSTACK

## 语言与运行方式

Python 3（当前环境 3.12.13），标准库为主。依赖用 `uv` 管理，在每条命令上用 `--with` 声明该脚本需要的那一个包，仓库里没有 `pyproject.toml` 也没有虚拟环境目录，`uv` 每次自建临时环境：

```
uv run --with markdown    scripts/build_report.py
uv run --with matplotlib  scripts/make_profile.py
uv run --with pillow      scripts/make_map.py
uv run --with pytest      pytest tests/ -q
```

要装包时用 `uv`（`uv add` / `uv pip install`）。

## 依赖

| 包 | 服务哪个脚本 | 用途 |
|---|---|---|
| `markdown` | `scripts/build_report.py` | `scripts/reportgen/appendix.py` 用 `markdown.Markdown(extensions=["tables"])` 把 `sources/*.md` 转成附录 B 的 HTML |
| `matplotlib` | `scripts/make_profile.py` | 画 `assets/elevation-profile.png`（全程剖面）与 `assets/elevation-profile-daily.png`（4×3 网格的逐段小图），后端固定 `Agg` |
| `pillow` | `scripts/make_map.py` | 拼接 OpenTopoMap 瓦片、画轨迹与 marker、写标注，输出两张 PNG |

`scripts/make_profile.py` 与 `scripts/make_map.py` 各自 `from route_points import ...`，靠脚本自身所在目录进 `sys.path` 生效，因此从仓库任意位置以 `scripts/<名>.py` 的路径调用都能跑。`scripts/build_report.py` 同理 `from reportgen.assemble import build`。`tests/test_assemble.py` 自己把 `scripts/` 插进 `sys.path`。

中文字体从系统取：matplotlib 依次尝试 PingFang SC、Hiragino Sans GB、Arial Unicode MS、DejaVu Sans；`make_map.py` 直接读 `/System/Library/Fonts/Helvetica.ttc` 与 `/System/Library/Fonts/Hiragino Sans GB.ttc`。

## 目录结构

```
AGENTS.md              文档地图 · 本仓库铁律 · 「要改 X 就动哪个文件」对照表
CLAUDE.md              一行 @AGENTS.md
PROJECT.md             报告目的 · 章节清单 · 六张 CSV 的职责
PATTERNS.md            include 与 token 契约 · 构建期闸门 · 配方 · 粒度上限
TECHSTACK.md           语言 · 依赖 · 目录结构 · 外部服务
DEVFLOW.md             命令速查 · 换 GPX 流程 · 并发 worktree 约定
trek-packages.md       代理报价单原文（Majestic Trails Nepal）

data/                  表格类数据的唯一事实源
  itinerary.csv            12 天定点安排
  route-segments.csv       11 段路段库（人工整理）
  cost-breakdown.csv       费用明细与合计
  packing-list.csv         33 项装备清单
  route-track-stats.csv    GPX 逐村里程与逐段爬升（make_profile.py 产物）
  quote-comparison.csv     代理报价与自组成本比对

sources/               调研出处，一个主题一份，14 份，01–14 编号
assets/
  Everest_Base_Camp.gpx        轨迹原始文件，3,291 个 trkpt
  elevation-profile.png        全程海拔剖面（make_profile.py 产物）
  elevation-profile-daily.png  逐段海拔小图（make_profile.py 产物）
  route-map-trek.png           徒步详图（make_map.py 产物）
  route-map-overview.png       全局路线图（make_map.py 产物）
  .tile-cache/                 OpenTopoMap 瓦片缓存，90 张，tracked

report/
  shell.html               骨架 + include 装载清单（装载顺序的唯一事实源）
  styles/                  base · tables · components · appendix · print 五个 CSS
  sections/                14 个章节文件
  EBC-report.html          构建产物，12 MB 自包含单文件，不进版本库

scripts/
  build_report.py          薄入口，调 reportgen.assemble.build()
  reportgen/
    assemble.py                include 解析与展开 · 闸门 · token 替换 · 写产物
    config.py                  ROOT 与各目录路径 · RATE 6.8 · PAX 6
    csvio.py                   read_csv · blocks · esc · signed
    tables.py                  table 渲染器
    money.py                   rng · y（美元转人民币）· diff
    figures.py                 四张图的 base64 data URI token
    costs.py                   费用明细表 · 参考项表 · 三个合计数字 token
    quotes.py                  报价评估两张表与七个内联数字 token
    route.py                   路段库表与日期安排表 token
    appendix.py                附录 A 六张全量表与附录 B sources 全文 token
  route_points.py          全线关键点位坐标与文献海拔，两个图件脚本共用
  make_profile.py          解析 GPX → route-track-stats.csv + 两张海拔图
  make_map.py              抓瓦片 → 两张路线地图

tests/test_assemble.py     assemble.py 的契约测试，28 个用例
.claude/plans/             跨 session 的设计文档，tracked
```

## 外部服务

**OpenTopoMap 瓦片** — `https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png`，`{s}` 在 a / b / c 三个子域间轮转。带等高线与山体阴影，署名 `© OpenStreetMap contributors, SRTM | map style © OpenTopoMap (CC-BY-SA)` 由 `make_map.py` 的 `attribution()` 画进图片右下角。选型依据见 `sources/13-map-apis.md`。

访问约定（`make_map.py` 的 `fetch_tile()`）：

- User-Agent `ebc-trail-report/1.0 (one-off personal trip map; contact aibrary@ouraca.ai)`，社区瓦片服务要求可识别的 UA。
- 抓到的瓦片落 `assets/.tile-cache/{z}_{x}_{y}.png` 并 tracked 进版本库，命中缓存时不发请求。两张图共需 90 张瓦片（详图 z13 66 张、全局图 z10 24 张），缓存齐备时全程离线出图。
- 每张新抓的瓦片之后 `sleep(0.3)`；失败重试 8 次，退避 `2 × (次数)` 秒并换子域，8 次都失败时抛 `RuntimeError`。
- 请求走 `curl -sSL --fail --http1.1 -m 30`（该瓦片源在本环境与 python `urllib` 的 TLS 握手失败），只接受首四字节是 PNG magic 的响应，其余删掉重试。

覆盖范围是写死的常量：`make_trek_map()` 里 `bbox = (86.665, 27.655, 86.895, 28.035)` 配 z13，`make_overview_map()` 里 `bbox = (85.15, 27.28, 87.05, 28.12)` 配 z10。放宽 bbox 或提高 zoom 时把一次抓取的量控制在几十张，抓完把新瓦片一起提交，后续构建就不再打这个服务。

## GPX 数据来源

`assets/Everest_Base_Camp.gpx`：Real World Adventures 免费轨迹库（页面 `https://realworldadventures.com/ebc-maps-facts/`，直链 `https://realworldadventures.com/wp-content/uploads/2023/03/EBC.gpx_.zip`，下载 2026-07-31）。GPX 1.1，Locus Map 于 2023-02-17 导出，轨迹原始出处 outdooractive `https://www.outdooractive.com/r/240405054`。3,291 个 `<trkpt>` 全部带 `<ele>`，无独立 waypoint，起点 Lukla（27.687, 86.732, 2,855m），单程长度 58.3 km。完整记录见 `sources/11-gpx-track.md`。

## 没有的东西

数据库、环境变量、端口、后端服务、构建工具链、CI 配置。仓库是一组读文件写文件的本地脚本，全部输入在 `data/` `sources/` `assets/` `report/` 四个目录里，全部输出落 `report/EBC-report.html`、`data/route-track-stats.csv`、`assets/*.png`。
