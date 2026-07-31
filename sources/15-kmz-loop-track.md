# KMZ 实测轨迹：EBC 大环线（里程、爬升、海拔剖面、地形图的共同输入）

## 出处

用户自有的两步路（2bulu）轨迹文件 `2024.06陆路EBC大环线for ios.kmz`（34.8 MB），2026-07-31 交付本仓库。KMZ 是 zip 容器，内含 `doc.kml`（664 KB）与 44 张沿途照片 PNG。`doc.kml` 抽出后入库为 `assets/ebc-loop.kml`，作为轨迹事实源；照片不入库、不进报告。

轨迹自带的元数据（KML 的 `ExtendedData` 段）：

| 字段 | 值 |
|---|---|
| TrackId | 56224568 |
| 运动类型 | 徒步（SportTypeId 18） |
| TrackTags | 合并获得, 徒步 |
| 起点名 / 终点名 | Thamdanda / Everest Base Camp |
| 轨迹自报里程 | 186,461 m |
| 轨迹自报累计爬升 / 下降 | 10,530.8 m / 10,546.2 m |
| 首个标注点时间戳 | 1716287996218（2024-05-21） |
| 采集设备 / 应用 | iPhone15,2 / 2bulu V9.1.6 |
| 记录者 | 飘然的自由（CreaterId 57505872） |

轨迹自报的累计爬升 10,530 m 是未做噪声处理的逐点累加值，口径与本仓库不同，见下面的「爬升/下降的计算口径」。

## 爬升/下降的计算口径

手机记录的海拔序列带 ±3–8 m 的逐点跳变，直接累加会把噪声当成爬升。本仓库分三步处理，参数写在 `scripts/day_tracks.py` 顶部：

1. **按 25 m 步长沿轨迹重采样**（`RESAMPLE_STEP_M = 25.0`），把不均匀的原始采样密度拉平，使后面两步的窗口有确定的空间含义。
2. **滚动中位数平滑海拔，窗口 5**（`SMOOTH_WINDOW = 5`）。25 m 步长下窗口 5 跨 100 m，远大于手机 GPS 高程噪声的相关长度（几米到二十米），足以压掉跳变；窗口继续放大到 9（跨 200 m）就开始抹掉真实的折返地形。
3. **按 8 m 滞回阈值累计**（`HYSTERESIS_M = 8.0`）：只有偏离当前极值超过 8 m 的起伏才计入，小于这个幅度的波动丢弃。

窗口取值的敏感度实测（hyst 固定 8 m，单位 m）：

| 窗口 | 跨度 m | Day 1 爬升 | Day 2 爬升 | Day 11 爬升 | 全程累计爬升 |
|---:|---:|---:|---:|---:|---:|
| 1（不平滑） | 0 | 363 | 1,310 | 785 | — |
| 3 | 50 | 246 | 1,169 | 685 | 7,303 |
| **5** | **100** | **206** | **1,109** | **594** | **6,846** |
| 9 | 200 | 171 | 1,045 | 529 | 6,369 |
| 25 | 600 | 81 | 967 | 357 | — |

选 5 的依据：Lukla–Phakding 的徒步文献口径爬升约 200 m、Phakding–Namche 约 1,100 m，窗口 5 算出 206 m 与 1,109 m，两处都最贴；窗口 9 把这两天分别压到 171 m 与 1,045 m，窗口 3 则抬到 246 m 与 1,169 m。

按这个口径算出的全程（11 天，含两个适应日往返与 Kala Patthar 支线）为 117.4 km、累计爬升 6,902 m、累计下降 6,824 m。这个爬升数高于攻略常引的约 6,000 m，因为攻略多按逐日净海拔差相加，不计入同一天内的反复起伏。

## 导航线覆盖清单

`导航线` 文件夹里 20 条 LineString 首尾相接组成完整大环线，共 17,377 个点，每点带海拔。二维平面距离合计 183.6 km（轨迹自报的 186.5 km 是三维斜距口径）。下标按在 KML 里的出现顺序，从 0 起：

| 线 | 点数 | 距离 km | 海拔区间 m | 经过 |
|---|---:|---:|---|---|
| L0 | 391 | 4.2 | 2,748–2,887 | Thamdanda → Paiya |
| L1 | 192 | 2.1 | 2,731–2,800 | Paiya 一带 |
| L2 | 223 | 2.3 | 2,478–2,770 | 下切河谷 |
| L3 | 99 | 1.0 | 2,271–2,478 | → Surke |
| L4 | 330 | 3.4 | 2,290–2,864 | Surke → Lukla |
| L5 | 770 | 8.3 | 2,535–2,877 | Lukla → Phakding |
| L6 | 1,109 | 11.9 | 2,619–3,546 | Phakding → Manjo → Namche |
| L7 | 1,264 | 13.4 | 3,302–3,920 | Namche → Tengboche → Deboche → Pangboche |
| L8 | 1,084 | 11.4 | 3,909–4,757 | Pangboche → Shomare → Dingboche → Chukhung |
| L9 | 552 | 5.7 | 4,744–5,563 | Chukhung 往返 Chukhung Ri |
| L10 | 994 | 10.4 | 4,741–5,535 | Chukhung → Kongma La → Lobuche |
| L11 | 298 | 3.1 | 4,914–5,154 | Lobuche 向 Gorak Shep 方向（未走到） |
| L12 | 741 | 7.8 | 5,138–5,268 | Gorak Shep → EBC → 返 Gorak Shep |
| L13 | 807 | 8.5 | 4,914–5,643 | Gorak Shep → Kala Patthar → 返 Gorak Shep → Lobuche |
| L14 | 611 | 6.4 | 4,742–4,926 | Lobuche → Zonglha |
| L15 | 1,233 | 12.9 | 4,681–5,370 | Zonglha → Cho La → Gokyo |
| L16 | 823 | 8.7 | 4,753–4,937 | Gokyo 往返（Gokyo Ri 方向） |
| L17 | 2,802 | 29.7 | 3,421–5,409 | Gokyo → Renjo La → Thame → Namche |
| L18 | 2,409 | 25.5 | 2,271–3,437 | Namche → Manjo → Phakding → Lukla → Surke |
| L19 | 645 | 6.8 | 2,723–2,893 | Paiya → Thamdanda |

记录者走的是 Three Passes 大环线：上山经 Chukhung 翻 Kongma La 进 Khumbu 谷，下山经 Cho La 到 Gokyo、翻 Renjo La 走 Thame 谷回 Namche。因此这条轨迹**不覆盖** Dingboche → Dughla → Lobuche 与 Lobuche/Pheriche 一带的标准直上直下走线，这两处由 `assets/Everest_Base_Camp.gpx`（sources/11）与本文下半的补测数据填上。

## 标注点坐标

`标注点` 文件夹 63 个点，其中报告用到的：

| 标注点名称 | 纬度 | 经度 | 轨迹海拔 m |
|---|---|---|---:|
| Lukla airport | 27.6882 | 86.7315 | 2,853 |
| Phakding | 27.7392 | 86.7122 | 2,633 |
| Manjo | 27.7701 | 86.7238 | 2,822 |
| Namche | 27.8054 | 86.7124 | 3,495 |
| Deboche | 27.8394 | 86.7705 | 3,723 |
| Pangboche | 27.8547 | 86.7908 | 3,917 |
| Shomare | 27.8674 | 86.8045 | 4,052 |
| Dingboche | 27.8895 | 86.8273 | 4,298 |
| Chukhung | 27.9040 | 86.8702 | 4,729 |
| Chukhung Ri | 27.9254 | 86.8792 | 5,563 |
| Kongma La Pass | 27.9298 | 86.8362 | 5,534 |
| Lobuche | 27.9478 | 86.8104 | 4,932 |
| Gorakshep | 27.9794 | 86.8283 | 5,181 |
| Everest Base Camp | 27.9986 | 86.8489 | 5,253 |
| Kala Patthar | 27.9950 | 86.8287 | 5,601 |
| Zonglha（Dzongla） | 27.9386 | 86.7737 | 4,836 |
| Cho La Pass | 27.9617 | 86.7517 | 5,364 |
| Gokyo | 27.9533 | 86.6946 | 4,767 |
| Gokyo Lake | 27.9513 | 86.6953 | 4,811 |
| Renjo Pass | 27.9474 | 86.6585 | 5,411 |
| Thame | 27.8336 | 86.6515 | 3,859 |

`scripts/route_points.py` 的村庄坐标取自这张表。名称在 KMZ 里与报告用名不一致的三处：`Lukla airport` 对应 Lukla、`Manjo` 对应 Monjo、`Gorakshep` 对应 Gorak Shep。KMZ 没有 Tengboche 与 Pheriche 的标注点：Tengboche 用 27.8361 / 86.7645（该点距 L7 轨迹 40 m），Pheriche 用 27.8941 / 86.8198（取自 OSM，见下）。

标注点的海拔是 GPS 记录值，与报告展示的文献海拔口径不同（例如 Namche 记录 3,495 m、文献 3,440 m，差异来自村内不同建筑的高差）。报告表格与图注的「终点海拔」一律用 `scripts/route_points.py` 里的文献海拔。

另有 30 个标注点是记录者写的路况提示（`危险有落石`、`冰川路段注意旗子方向`、`千万不要听尼泊尔人的走新路 最终要直上爬山`、`走河谷最佳不要走高处` 等），不进报告表格。

## 补测数据：OSM 步道几何 + SRTM30m 高程

KMZ 与 GPX 都没走过的 4 段，用两个公开 API 补成逐点海拔序列，结果缓存进 `data/gap-legs.json`：

| API | 用途 | 参数 | 抓取日期 |
|---|---|---|---|
| Overpass API `https://overpass-api.de/api/interpreter` | 取 bbox 内 `highway ~ path\|footway\|track\|steps` 的 way 几何，建图跑 Dijkstra 连出走线 | `[out:json]`，`out body geom` | 2026-07-31 |
| OpenTopoData `https://api.opentopodata.org/v1/srtm30m` | 逐点采 SRTM 30 m DEM 高程 | 每请求 ≤100 个 locations，间隔 ≥1.1 s | 2026-07-31 |

四段与端点坐标：

| leg_id | 起点 | 终点 | 形态 | 实测点数 | 距离 km | 爬升/下降 m | 海拔区间 m |
|---|---|---|---|---:|---:|---|---|
| namche-everest-view | Namche 27.8054 / 86.7124 | Hotel Everest View 27.8167 / 86.7235 | 往返 | 465 | 4.2 | 400 / 405 | 3,487–3,893 |
| dingboche-nangkartshang | Dingboche 27.8895 / 86.8273 | Nangkartshang 峰 27.9055 / 86.8355 | 往返 | 219 | 4.3 | 739 / 739 | 4,297–5,039 |
| lobuche-pheriche | Lobuche 27.9478 / 86.8104 | Pheriche 27.8941 / 86.8198 | 单程 | 193 | 6.9 | 23 / 684 | 4,259–4,920 |
| pheriche-pangboche | Pheriche 27.8941 / 86.8198 | Pangboche 27.8547 / 86.7908 | 单程 | 313 | 6.1 | 224 / 561 | 3,922–4,288 |

四段全部在 OSM 步道图里连通，没有一段走直线回退分支。

端点坐标取自 OSM 命名要素（2026-07-31 查得）：`Hotel Everest View` guest_house 27.8167 / 86.7235 标注 ele=3880、`Nangkartshang` peak 27.9055 / 86.8355 标注 ele=5073、`Pheriche Snooker House` 27.8941 / 86.8198、`Thukla Bakery Cafe` 27.9239 / 86.8054。`Hotel Everest View` 自带的 ele 标注与徒步文献常用的 3,880 m 一致，报告的适应点海拔取这个值。

两个适应日支线与文献口径对照：Nangkartshang 文献 4–6 km、爬升约 670 m、山脊约 5,080 m，实测 4.3 km、739 m、最高 5,039 m；Hotel Everest View 往返文献 3–5 km、约 3,880 m，实测 4.2 km、最高 3,893 m。

SRTM30m 与 KMZ 实测 GPS 海拔的实测偏差，用于判断补测精度是否可接受：

| 位置 | KMZ 实测 m | SRTM30m m | 差 m |
|---|---:|---:|---:|
| Lobuche | 4,932 | 4,924 | 8 |
| Pheriche | — | 4,260 | — |
| Kala Patthar | 5,601 | 5,588 | 13 |

两处可比对的点差 8 m 与 13 m，小于同一村庄内不同建筑的高差，补测段与实测段放在同一张剖面图上不产生可见的接缝。

Overpass 的步道图在某段上不连通时，回退为端点间大圆折线按 100 m 间隔取点采 SRTM，`data/gap-legs.json` 的 `source` 字段写明这种情况；此时海拔仍是 DEM 实采值，水平距离偏短。

## 数据授权

- 轨迹：用户自有文件，仅用于本次行程规划。
- OSM 步道几何：© OpenStreetMap contributors，ODbL。
- 高程：SRTM（NASA/USGS），由 OpenTopoData 提供查询服务。
