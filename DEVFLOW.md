# DEVFLOW

## 命令速查

从仓库根目录跑，路径原样照抄。

| 做什么 | 命令 | 输出 |
|---|---|---|
| 构建报告 | `uv run --with markdown scripts/build_report.py` | `report/EBC-report.html`（12 MB，末行打印 `wrote <路径>  (12.0 MB)`） |
| 重生成海拔图与 GPX 统计 | `uv run --with matplotlib scripts/make_profile.py` | `data/route-track-stats.csv`、`assets/elevation-profile.png`、`assets/elevation-profile-daily.png`；先打印逐村的吸附结果 |
| 重生成两张地图 | `uv run --with pillow scripts/make_map.py` | `assets/route-map-trek.png`、`assets/route-map-overview.png`；打印各图抓了多少瓦片 |
| 跑测试 | `uv run --with pytest pytest tests/ -q` | `28 passed` |

四条命令彼此独立，只要输入齐备就能单独跑。`make_map.py` 在 `assets/.tile-cache/` 齐备时不发网络请求。

## 换 GPX 文件

`assets/Everest_Base_Camp.gpx` 是里程、爬升、海拔剖面、两张地图的共同输入。换轨迹按顺序走完五步：

1. **替换文件。** 新轨迹存成 `assets/Everest_Base_Camp.gpx`（脚本按这个固定文件名读）。格式要求：GPX 1.1，根节点命名空间 `http://www.topografix.com/GPX/1/1`；每个 `<trkpt>` 带 `lat`/`lon` 属性和 `<ele>` 子元素（`make_profile.py` 直接取 `ele` 的文本，缺 `<ele>` 的点会让解析停下）；轨迹点按 Lukla → EBC 的行进顺序排列（累计里程按点序累加，`route_points.py` 的村庄靠吸附定位，点序反了会让里程与剖面反向）。同时更新 `sources/11-gpx-track.md`：来源 URL、下载日期、导出工具、轨迹点数、起点坐标与海拔。

2. **重跑 `uv run --with matplotlib scripts/make_profile.py`。** 它重算 `data/route-track-stats.csv`（逐村累计里程与 GPX 海拔、相邻在轨村庄之间的距离与爬升/下降）并重画两张海拔图。读它的终端输出核对三件事：
   - 轨迹点数与单程长度是否合理（当前 3,291 点、58.3 km）。
   - 每个村庄的 `snap_off`（吸附偏差）。**村庄吸附机制**：`scripts/route_points.py` 的 `TREK_VILLAGES` 里每个村庄的公开坐标吸附到最近的轨迹点，偏差写进 `route-track-stats.csv` 的 `snap_offset_m` 列，11 个村庄全部入表。阈值 400m 决定两件事：偏差小于 400m 的村参与相邻段的爬升/下降统计，并在剖面图上按 GPX 海拔画实心 marker；偏差大于 400m 的村按文献海拔画空心 marker、标注「轨迹旁」，退出逐段统计。当前 Dingboche 与 Pheriche 偏差各 521m（村在谷底、轨迹走高线），其余九个村在轨，逐段统计出 8 段。新轨迹换了走线时在轨名单会变，逐段统计的段数随之变。
   - `d_ele`（GPX 海拔减文献海拔）。差值大到十几米以上的村庄，说明轨迹在该点的海拔与文献口径不同，正文引用海拔时以 `route_points.py` 的文献值为准。

3. **重跑 `uv run --with pillow scripts/make_map.py`。** 它按新轨迹重画徒步详图与全局图。两张图的 bbox 是写死的常量：`make_trek_map()` 里 `(86.665, 27.655, 86.895, 28.035)` z13，`make_overview_map()` 里 `(85.15, 27.28, 87.05, 28.12)` z10。新轨迹走到框外时先把这两个常量放宽，再跑脚本；框变了要抓的瓦片跟着变，缓存未命中时会打瓦片服务，把新抓到的 `assets/.tile-cache/*.png` 一起提交。出图后打开两张 PNG 看轨迹有没有被边框截断。

4. **人工复核 `data/route-segments.csv`。** 这张表是人工整理的，`make_profile.py` 不写它。逐行对照新的 `route-track-stats.csv`：
   - `note` 列写「GPX 实测」的路段（当前第 1、4、8 段，以及第 5 段的 Tengboche–Pangboche 部分），把 `ascent_m` / `descent_m` / `distance_km` 换成新 GPX 的对应值。
   - `note` 列写「文献口径」「无 GPX 覆盖」「峡谷段 GPS 海拔噪声大」的路段（当前第 2、3、6、7、9、10、11 段）继续用 `sources/06` 的文献口径，GPX 变了不改。
   - 新 GPX 覆盖到了原先没覆盖的路段时，把该行改成 GPX 实测并更新 `note` 说明来源；新 GPX 不再覆盖原先实测的路段时，改回文献口径并在 `note` 写清估算算法。
   - `distance_km` 列的写法是文献值加括注 GPX 值（例如 `7.8（GPX 8.6）`），两个数都要更新。
   - `start_ele_m` / `end_ele_m` / `ele_diff_m` 用 `route_points.py` 的文献海拔，GPX 换了不动。
   - `make_profile.py` 的 `make_daily_profiles()` 按 `route-segments.csv` 的 `order` 列查 `PIECES_BY_ORDER`，路段数量或顺序变了就同步改这个字典与 `SHORT_TITLES`，然后再跑一次 `make_profile.py`。

5. **重跑 `uv run --with markdown scripts/build_report.py`**，把新的 CSV 与图件装进报告。检查 Section 5 正文里复述的里程与爬升说明、图注里的「单程 58.3 km」「往返约 117 km」这类数字，与新 GPX 一致。

## 交付前检查

1. 改了任何 `data/*.csv`、`sources/*.md`、`report/sections/*.html`、`report/styles/*.css`、`report/shell.html` 或 `assets/*.png` 之后跑 `uv run --with markdown scripts/build_report.py`，看到 `wrote ...` 那一行才算通过。
2. 改了 `scripts/reportgen/assemble.py` 之后跑 `uv run --with pytest pytest tests/ -q`。
3. 改了 `data/cost-breakdown.csv` 之后复核 `data/quote-comparison.csv` 的 `ours_pp_usd` 列（它从费用表取单值），并 `grep` 变动的金额，把散文与手写表里复述它的地方一起改。
4. 改了 `scripts/route_points.py` 之后跑 `make_profile.py` 与 `make_map.py`，再跑 `build_report.py`。
5. 新增的事实在 `sources/` 有对应文件，详解正文括注并链接了 `（sources/NN）`。

## 构建产物不进版本库

`report/EBC-report.html` 在 `.gitignore` 里。每个 worktree 自己跑一次构建拿到本地副本，因此并发的多个 worktree 改不同章节时它不产生 merge conflict。要分享报告时先构建，再把 `report/EBC-report.html` 这个文件直接发出去（自包含，图片 base64 内嵌，浏览器打开即可读，`Cmd+P` 打印成 PDF）。`__pycache__/` 与 `*.pyc` 同样在 `.gitignore` 里。

`assets/*.png` 与 `assets/.tile-cache/` 保持 tracked：它们是报告构建的输入，重新生成需要网络。

## 并发 worktree 约定

多个 agent 各自拉一个 worktree 改不同主题时按下面分工，冲突面归零：

- **一个 agent 一个 section 文件 + 它对应的 CSV 与 sources 文件。** 章节文件与事实源的对照表在 PROJECT.md 的章节清单里，认领前先查它，确认自己要动的文件没有被别人认领。
- **`report/shell.html` 只在增删章节时才动。** 改正文、改数字、改样式都不触碰它。要增删章节时在报告里说明这一处改动。
- **`scripts/reportgen/` 的共用基础设施（`config.py` `csvio.py` `tables.py` `money.py` `assemble.py`）由一个 agent 独占改。** 领域 provider（`figures.py` `costs.py` `quotes.py` `route.py` `packing.py` `sources.py`）之间零 import 依赖，可以并行改。
- **`report/styles/` 下五个 CSS 各自独立**，改不同文件可以并行；层叠顺序由 `shell.html` 决定，改顺序算增删章节那一类改动。
- **图件脚本（`make_profile.py` `make_map.py` `route_points.py`）与它们的 PNG 产物由一个 agent 独占改**，因为两个脚本共用 `route_points.py`，PNG 是二进制文件、并发重写无法合并。
- 合并回 main 用 merge。合并后跑一次 `uv run --with markdown scripts/build_report.py`，据输出确认闸门全过。
