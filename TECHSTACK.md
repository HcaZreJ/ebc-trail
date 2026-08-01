# TECHSTACK

## 语言与运行方式

Python 3（当前环境 3.12.13），标准库为主。依赖用 `uv` 管理，在每条命令上用 `--with` 声明该脚本需要的那一个包，仓库里没有 `pyproject.toml` 也没有虚拟环境目录，`uv` 每次自建临时环境：

```
uv run                    scripts/gap_legs.py
uv run                    scripts/day_tracks.py
uv run --with matplotlib  scripts/make_profile.py
uv run --with pillow      scripts/make_map.py
uv run --with markdown    scripts/build_report.py
uv run --with pytest      pytest tests/ -q
```

要装包时用 `uv`（`uv add` / `uv pip install`）。

## 依赖

| 包 | 服务哪个脚本 | 用途 |
|---|---|---|
| `markdown` | `scripts/build_report.py` | `scripts/reportgen/appendix.py` 用 `markdown.Markdown(extensions=["tables"])` 把 `sources/*.md` 转成附录 B 的 HTML |
| `matplotlib` | `scripts/make_profile.py` | 画 `assets/elevation-profile.png`（11 天首尾相接的全程剖面）；逐日小图 `assets/day-profile-01.png`…`11.png` 由 `scripts/profile_thumbs.py` 画，后端固定 `Agg` |
| `pillow` | `scripts/make_map.py` | 拼接 OpenTopoMap 瓦片、画轨迹与 marker、写标注，输出两张 PNG |

`scripts/` 下的脚本互相之间用裸模块名 import（例如 `make_map.py` 写 `from tiles import ...`、`day_tracks.py` 写 `import geo`），靠脚本自身所在目录进 `sys.path` 生效，因此从仓库任意位置以 `scripts/<名>.py` 的路径调用都能跑；`gap_legs.py` 与 `day_tracks.py` 是纯标准库脚本，不需要 `--with` 任何第三方包。`scripts/build_report.py` 同理 `from reportgen.assemble import build`。`tests/` 下的测试自己把 `scripts/` 插进 `sys.path`。

中文字体从系统取：matplotlib 依次尝试 PingFang SC、Hiragino Sans GB、Arial Unicode MS、DejaVu Sans；`make_map.py` 直接读 `/System/Library/Fonts/Helvetica.ttc` 与 `/System/Library/Fonts/Hiragino Sans GB.ttc`。

## 目录结构

```
AGENTS.md              文档地图 · 本仓库铁律 · 「要改 X 就动哪个文件」对照表
CLAUDE.md              一行 @AGENTS.md
PROJECT.md             报告目的 · 章节清单 · data 目录八个文件的职责
PATTERNS.md            include 与 token 契约 · 构建期闸门 · 配方 · 粒度上限
TECHSTACK.md           语言 · 依赖 · 目录结构 · 外部服务
DEVFLOW.md             命令速查 · 换轨迹来源流程 · 并发 worktree 约定
trek-packages.md       代理报价单原文（Majestic Trails Nepal）

data/                  表格类数据与轨迹几何的事实源
  itinerary.csv            12 天定点安排（人工整理）
  day-track-stats.csv      Day 1–11 逐日距离/爬升/下降/起止海拔/来源（day_tracks.py 产物）
  day-tracks.json          Day 1–11 逐点轨迹坐标，给图件脚本用（day_tracks.py 产物）
  gap-legs.json            4 段补测轨迹缓存（gap_legs.py 产物，构建期不打网络）
  cost-breakdown.csv       费用明细与合计（人工整理）
  packing-list.csv         34 项装备清单（人工整理）
  route-track-stats.csv    上山走廊逐村累计里程（make_profile.py 产物）
  quote-comparison.csv     代理报价与自组成本比对（人工整理）

sources/               调研出处，一个主题一份，15 个编号、16 份文件
assets/
  ebc-loop.kml                  KMZ 抽出的大环线轨迹事实源，20 条导航线 + 63 个标注点
  Everest_Base_Camp.gpx         标准直上直下线，3,291 个 trkpt
  day-profile-01.png…11.png     表格内嵌的逐日剖面小图（make_profile.py 产物）
  elevation-profile.png         11 天首尾相接的全程海拔剖面（make_profile.py 产物）
  route-map-trek.png            徒步详图（make_map.py 产物）
  route-map-overview.png        全局路线图（make_map.py 产物）
  .tile-cache/                  OpenTopoMap 瓦片缓存，tracked

report/
  shell.html               骨架 + include 装载清单（装载顺序的唯一事实源）
  styles/                  base · tables · components · appendix（出处层） · print 五个 CSS
  sections/                章节文件（速览 faq · 详解 ext-* · 出处 sources 等，清单见 PROJECT.md）
  EBC-report.html          构建产物，自包含单文件，不进版本库

scripts/
  build_report.py          薄入口，调 reportgen.assemble.build()
  reportgen/
    assemble.py                include 解析与展开 · 闸门 · token 替换 · 写产物
    config.py                  ROOT 与各目录路径 · RATE 6.8 · PAX 6
    csvio.py                   read_csv · blocks · esc · signed
    tables.py                  table 渲染器
    money.py                   amt · y（美元转人民币）· diff
    imgio.py                   img_uri，figures.py 与 route.py 共用
    figures.py                 三张图的 base64 data URI token
    costs.py                   费用明细表 · 参考项表 · 三个合计数字 token
    quotes.py                  报价评估两张表与七个内联数字 token
    route.py                   一张合并的 12 天行程表 token
    packing.py                 装备全量表 token
    sources.py                 出处层 sources 全文与「被引用于」回链 token
  geo.py                    轨迹几何共用工具：haversine · 重采样 · 平滑 · 滞回爬升/下降 · 最近点 · 切片
  kmz_loop.py               解析 assets/ebc-loop.kml：20 条导航线 + 命名标注点
  osm_graph.py              从 Overpass way 元素建无向图 · Dijkstra 最短路 · 最近节点
  gap_legs.py               补测 4 段缺口路线（OSM 步道 + SRTM30m）→ data/gap-legs.json
  day_tracks.py             装配 11 天逐日轨迹 → data/day-tracks.json + data/day-track-stats.csv
  day_colors.py             按天色板与 OPTION_GRAY，剖面图与地形图共用
  tiles.py                  瓦片抓取与绘图原语，两张地图共用
  http_fetch.py             curl 子进程封装（get_bytes/post_text），瓦片与 OSM/高程抓取共用
  profile_thumbs.py         表格内嵌用的逐日剖面小图
  route_points.py           全线关键点位坐标与文献海拔，day_tracks/make_profile/make_map 共用
  make_profile.py           读 day-tracks.json → 剖面图 + route-track-stats.csv

tests/
  test_assemble.py         assemble.py 的契约测试，28 个用例
  visible/                 geo/kmz_loop、gap_legs、day_tracks 三个单元的示例用例
  hidden/                  同三个单元的全面用例
.claude/plans/             跨 session 的设计文档，tracked
```

## 外部服务

**OpenTopoMap 瓦片** — `https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png`，`{s}` 在 a / b / c 三个子域间轮转。带等高线与山体阴影，署名 `© OpenStreetMap contributors, SRTM | map style © OpenTopoMap (CC-BY-SA)` 由 `make_map.py` 的 `attribution()` 画进图片右下角。选型依据见 `sources/13-map-apis.md`。

访问约定（`make_map.py` 的 `fetch_tile()`）：

- User-Agent `ebc-trail-report/1.0 (one-off personal trip map; contact aibrary@ouraca.ai)`，社区瓦片服务要求可识别的 UA。
- 抓到的瓦片落 `assets/.tile-cache/{z}_{x}_{y}.png` 并 tracked 进版本库，命中缓存时不发请求。两张图共需 107 张瓦片（详图 z13 83 张、全局图 z10 24 张），缓存齐备时全程离线出图。
- 每张新抓的瓦片之后 `sleep(0.3)`；失败重试 8 次，退避 `2 × (次数)` 秒并换子域，8 次都失败时抛 `RuntimeError`。
- 请求走 `curl -sSL --fail --http1.1 -m 30`（该瓦片源在本环境与 python `urllib` 的 TLS 握手失败，统一封装进 `scripts/http_fetch.py`），只接受首四字节是 PNG magic 的响应，其余删掉重试。

覆盖范围是写死的常量：`make_trek_map()` 里 `bbox = (86.630, 27.615, 86.900, 28.020)` 配 z13（向西扩到 86.63 以覆盖 Gokyo 与 Thame），`make_overview_map()` 里 `bbox = (85.15, 27.28, 87.05, 28.12)` 配 z10。放宽 bbox 或提高 zoom 时把一次抓取的量控制在几十张，抓完把新瓦片一起提交，后续构建就不再打这个服务。

**Overpass API** — `https://overpass-api.de/api/interpreter`，`scripts/gap_legs.py` 用它取 bbox 内 `highway ~ path|footway|track|steps` 的 way 几何（`[out:json]`，`out body geom`），交给 `scripts/osm_graph.py` 建无向图后跑 Dijkstra，连出 KMZ 与 GPX 都没走过的 4 段缺口路线。抓取走 `http_fetch.post_text`。用法细节与抓取日期见 `sources/15-kmz-loop-track.md`。

**OpenTopoData SRTM30m** — `https://api.opentopodata.org/v1/srtm30m`，`scripts/gap_legs.py` 的 `fetch_elevations` 给 4 段缺口路线的每个点采 SRTM 30m DEM 高程：每请求 ≤100 个 `locations`，请求间隔 ≥1.1 秒，走 `http_fetch.get_bytes`。SRTM30m 与 KMZ 实测 GPS 海拔的偏差实测 8–13 m，见 `sources/15`。

结果缓存进 `data/gap-legs.json`：文件已含 4 段时构建期不再对这两个服务发请求，加 `--refresh` 参数强制重抓。

## 轨迹数据来源

`assets/ebc-loop.kml`：用户自有的两步路（2bulu）轨迹 `2024.06陆路EBC大环线for ios.kmz`（TrackId 56224568）抽出的 `doc.kml`，664 KB。`导航线` 文件夹 20 条 LineString 首尾相接组成完整大环线（17,377 点，每点带海拔，二维距离合计 183.6 km），`标注点` 文件夹 63 个命名点。`scripts/kmz_loop.py` 用 `xml.etree` 按 KML 命名空间 `http://www.opengis.net/kml/2.2` 解析。完整的覆盖清单、标注点坐标、爬升/下降计算口径见 `sources/15-kmz-loop-track.md`。

`assets/Everest_Base_Camp.gpx`：Real World Adventures 免费轨迹库（页面 `https://realworldadventures.com/ebc-maps-facts/`，直链 `https://realworldadventures.com/wp-content/uploads/2023/03/EBC.gpx_.zip`，下载 2026-07-31）。GPX 1.1，Locus Map 于 2023-02-17 导出，轨迹原始出处 outdooractive `https://www.outdooractive.com/r/240405054`。3,291 个 `<trkpt>` 全部带 `<ele>`，无独立 waypoint，起点 Lukla（27.687, 86.732, 2,855m），单程长度 58.3 km。走的是 KMZ 大环线没有覆盖的标准直上直下线（Dingboche→Lobuche、Lobuche→Gorak Shep 一段、Pheriche→Namche 一段）。完整记录见 `sources/11-gpx-track.md`。

`scripts/day_tracks.py` 把 KMZ 导航线、GPX 与 `data/gap-legs.json` 的补测段装配成 11 天逐日轨迹，拼接表见 DEVFLOW.md。

## 没有的东西

数据库、环境变量、端口、后端服务、构建工具链、CI 配置。仓库是一组读文件写文件的本地脚本，全部输入在 `data/` `sources/` `assets/` `report/` 四个目录里，全部输出落 `report/EBC-report.html`、`data/day-track-stats.csv`、`data/route-track-stats.csv`、`assets/*.png`。
