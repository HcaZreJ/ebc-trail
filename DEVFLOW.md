# DEVFLOW

## 命令速查

从仓库根目录跑，路径原样照抄。

| 做什么 | 命令 | 输出 |
|---|---|---|
| 补测两份实测轨迹都没走的 4 段 | `uv run scripts/gap_legs.py [--refresh]` | `data/gap-legs.json`；文件已含 4 段时不发网络请求，加 `--refresh` 强制重抓 |
| 装配 10 天逐日轨迹与统计 | `uv run scripts/day_tracks.py` | `data/day-tracks.json`、`data/day-track-stats.csv` |
| 重生成海拔剖面图 | `uv run --with matplotlib scripts/make_profile.py` | `assets/day-profile-02.png`…`11.png`、`assets/elevation-profile.png`、`data/route-track-stats.csv` |
| 重生成两张地图 | `uv run --with pillow scripts/make_map.py` | `assets/route-map-trek.png`、`assets/route-map-overview.png`；打印各图抓了多少瓦片 |
| 构建报告 | `uv run --with markdown scripts/build_report.py` | `report/EBC-report.html`（末行打印 `wrote <路径>  (N MB)`） |
| 跑测试 | `uv run --with pytest --with markdown pytest tests/ -q` | `267 passed` |

前四条命令按依赖顺序跑：`gap_legs.py` → `day_tracks.py` → `make_profile.py` / `make_map.py`（这两条互不依赖，谁先谁后都行）→ `build_report.py`。`gap_legs.py` 在 `data/gap-legs.json` 已含全部 4 段时不发网络请求，`make_map.py` 在 `assets/.tile-cache/` 齐备时不发网络请求，因此输入齐备时全程可以离线重跑。

## 换轨迹来源

里程与海拔剖面的事实源是两份实测轨迹加一份补测缓存：`assets/ebc-loop.kml`（KMZ 抽出的大环线，20 条导航线首尾相接，17,377 点）、`assets/Everest_Base_Camp.gpx`（标准直上直下线，3,291 点）、`data/gap-legs.json`（两份实测都没走到的 4 段，OSM 步道几何 + SRTM30m 高程补测）。10 天怎么从这三个来源拼接、切片，写死在 `scripts/day_tracks.py` 的 `assemble()` 函数 docstring 里那张表；这张表与 `DAY_SOURCES` 常量（每天的数据来源说明字符串）是换轨迹时要同步改的核心契约。

换一段轨迹来源（换新的 KMZ/GPX，或某一天改接别的数据源）按顺序走：

1. **替换输入文件。** 新 KMZ 抽出 `doc.kml` 存成 `assets/ebc-loop.kml`：`scripts/kmz_loop.py` 按 KML 命名空间 `http://www.opengis.net/kml/2.2` 与两个 Folder 名「导航线」「标注点」解析，Folder 名或坐标格式变了解析会跟着变。新 GPX 存成 `assets/Everest_Base_Camp.gpx`：GPX 1.1，根节点命名空间 `http://www.topografix.com/GPX/1/1`，每个 `<trkpt>` 带 `lat`/`lon` 属性和 `<ele>` 子元素，轨迹点按 Lukla → EBC 的行进顺序排列。同时更新 `sources/15-kmz-loop-track.md`（KMZ）或 `sources/11-gpx-track.md`（GPX）：来源、抓取/下载日期、轨迹点数、覆盖清单。

2. **同步 `scripts/day_tracks.py` 的拼接表。** 新轨迹的导航线下标、GPX 切片端点、需要靠 `gap-legs.json` 补测的缺口天数如果变了，改 `assemble()` docstring 里的那张表和函数体，以及 `DAY_SOURCES` 里对应天的来源说明字符串。

3. **校正村庄坐标。** 新轨迹的标注点坐标写进 `scripts/route_points.py` 的 `TREK_VILLAGES`（坐标换、海拔仍用文献口径不变）；两个海拔适应点与大环线支线节点在 `ACCLIMATIZE_POINTS` / `LOOP_LANDMARKS` 里同步。`day_tracks.py` 用这份坐标在源轨迹上切片，坐标偏了会让切片端点落错地方。

4. **需要时重新标定爬升/下降参数。** `RESAMPLE_STEP_M`（重采样步长）、`SMOOTH_WINDOW`（滚动中位数窗口）、`HYSTERESIS_M`（滞回阈值）写在 `day_tracks.py` 顶部，控制 GPS 海拔噪声压掉多少；新轨迹的噪声水平变了就按 `sources/15` 里的敏感度实测方法重新标定。

5. **需要时重新补测缺口段。** 4 段缺口的起止坐标（`scripts/gap_legs.py` 的 `LEGS` 常量）如果因为坐标校正而变了，跑 `uv run scripts/gap_legs.py --refresh` 强制重抓；坐标没变就不用碰这一步。

6. **按依赖顺序重跑四条命令**：`uv run scripts/day_tracks.py` → `uv run --with matplotlib scripts/make_profile.py` 与 `uv run --with pillow scripts/make_map.py` → `uv run --with markdown scripts/build_report.py`。读每一步的终端输出核对轨迹点数、10 天的总里程与每天的 `source` 是否符合预期；`make_map.py` 的 bbox 是写死的常量（见 TECHSTACK.md「外部服务」），新轨迹走到框外时先放宽这两个常量再跑，框变了要抓的瓦片跟着变，把新抓到的 `assets/.tile-cache/*.png` 一起提交。出图后打开两张 PNG 与 10 张剖面小图，看轨迹有没有被边框截断、曲线是否连续。

7. **检查报告正文。** §4 正文里复述的总里程、总爬升/总下降（当前「10 个徒步日合计 113.2 km，累计爬升 6,502 m、累计下降 6,419 m」）随新一轮 `day-track-stats.csv` 变化，`grep` 这几个数字把复述它们的地方一起改——`sections/core-route.html` 与 `sections/summary.html` 都有。

## 交付前检查

1. 改了任何 `data/*.csv`、`sources/*.md`、`report/sections/*.html`、`report/styles/*.css`、`report/shell.html` 或 `assets/*.png` 之后跑 `uv run --with markdown scripts/build_report.py`，看到 `wrote ...` 那一行才算通过。
2. 改了 `scripts/reportgen/assemble.py`、`scripts/reportgen/citations.py`、`scripts/geo.py`、`scripts/kmz_loop.py`、`scripts/gap_legs.py`、`scripts/osm_graph.py` 或 `scripts/day_tracks.py` 之后跑 `uv run --with pytest --with markdown pytest tests/ -q`，看到 `267 passed` 才算通过。
3. 改了 `data/cost-breakdown.csv` 之后复核 `data/quote-comparison.csv` 的 `ours_pp_usd` 列（它从费用表取单值），并 `grep` 变动的金额，把散文与手写表里复述它的地方一起改。
4. 改了 `scripts/route_points.py` 之后按依赖顺序重跑 `day_tracks.py` → `make_profile.py` 与 `make_map.py` → `build_report.py`。
5. 新增的事实在 `sources/` 有对应文件，正文在该事实处写了 `[[NN]]` 角标；新增一份出处时它的编号进 References 是自动的，但要确认正文真的引用了它，否则它只会出现在末尾的「数据与方法来源」组里。

## 发布到 GitHub Pages

`.github/workflows/deploy-pages.yml` 在 push 到 `main` 且改动落在 `data/`、`sources/`、`report/`、`scripts/`、`assets/` 任一目录时自动触发（也可以在 Actions 页面手动 `workflow_dispatch`）：用 `uv run --with markdown scripts/build_report.py` 重新构建报告，把 `report/EBC-report.html` 复制成 `index.html` 上传成 Pages artifact 并部署，线上地址固定为 `https://hcazrej.github.io/ebc-trail/`。构建产物自包含（图片 base64 内嵌），部署这一步不需要额外静态资源。

## 构建产物不进版本库

`report/EBC-report.html` 在 `.gitignore` 里。每个 worktree 自己跑一次构建拿到本地副本，因此并发的多个 worktree 改不同章节时它不产生 merge conflict。日常分享给同行者直接发 `https://hcazrej.github.io/ebc-trail/` 这个链接；需要离线阅读或打印 PDF 时，本地构建后把 `report/EBC-report.html` 这个文件直接发出去（自包含，图片 base64 内嵌，浏览器打开即可读，`Cmd+P` 打印成 PDF）。`__pycache__/` 与 `*.pyc` 同样在 `.gitignore` 里。

`assets/*.png`、`assets/.tile-cache/`、`data/day-tracks.json`、`data/gap-legs.json`、`data/day-track-stats.csv`、`data/route-track-stats.csv` 保持 tracked：它们是脚本产物，但同时也是报告构建（以及彼此之间）的输入，`gap-legs.json` 与瓦片缓存的重新生成还需要网络。

## 并发 worktree 约定

多个 agent 各自拉一个 worktree 改不同主题时按下面分工，冲突面归零：

- **一个 agent 一个 section 文件 + 它对应的 CSV 与 sources 文件。** 章节文件与事实源的对照表在 PROJECT.md 的章节清单里，认领前先查它，确认自己要动的文件没有被别人认领。
- **`report/shell.html` 只在增删章节时才动。** 改正文、改数字、改样式都不触碰它。要增删章节时在报告里说明这一处改动。
- **`scripts/reportgen/` 的共用基础设施（`config.py` `csvio.py` `tables.py` `money.py` `imgio.py` `assemble.py` `citations.py`）由一个 agent 独占改。** 领域 provider（`figures.py` `costs.py` `quotes.py` `route.py` `packing.py`）之间零 import 依赖，可以并行改。
- **`report/styles/` 下五个 CSS 各自独立**，改不同文件可以并行；层叠顺序由 `shell.html` 决定，改顺序算增删章节那一类改动。
- **轨迹与图件脚本（`geo.py` `kmz_loop.py` `osm_graph.py` `gap_legs.py` `day_tracks.py` `day_colors.py` `tiles.py` `http_fetch.py` `profile_thumbs.py` `route_points.py` `make_profile.py` `make_map.py`）与它们的产物（`data/day-tracks.json` `data/gap-legs.json` `data/day-track-stats.csv` `data/route-track-stats.csv` `assets/*.png`）由一个 agent 独占改**，这条流水线前后相接（`gap_legs.py` → `day_tracks.py` → `make_profile.py`/`make_map.py`），PNG 与部分 JSON/CSV 是脚本产物或二进制文件，并发重写无法合并。
- 合并回 main 用 merge。合并后跑一次 `uv run --with markdown scripts/build_report.py`，据输出确认闸门全过。
