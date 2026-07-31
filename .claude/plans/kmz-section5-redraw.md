# Feature: 用 KMZ 实测轨迹重绘 Section 5

## Overview

用户提供了自己走完整大环线的两步路 KMZ（`2024.06陆路EBC大环线for ios.kmz`，34 MB，含 44 张照片）。把 Section 5「12 天路线」按这份实测数据重做三件事：

1. 逐日海拔剖面全部改用实测轨迹，消灭虚线。
2. 徒步地形图上画出全部可走线路（大环线各支线），叠加我们选定的直上直下路线，按天分色并标 `Day N`，两个海拔适应点标出名称与海拔。
3. 路段库与日期安排合并成一张表，列只留：天、日期、起点、终点、距离、总爬升/总下降、终点海拔、海拔剖面图。

## Intent Brief

- **Goal** — Section 5 变成一张能直接看懂「哪天走哪段、多远、多累、爬到多高」的表，配一张能看懂「还有哪些线路可走、它们有多远、为什么我们不走」的地形图。
- **Motivation** — 现版本三处让用户读不下去：剖面图一半是虚线（精度可疑）；地图只画了我们这一条线，看不出取舍的尺度；表格把距离写成 `7.8（GPX 8.6）` 这类多来源并列的形态，一格塞多个数字。
- **Known context** — KMZ 解出 `doc.kml` 664 KB：`导航线` 文件夹 20 条 LineString 首尾相接组成完整大环线（17,377 点，每点带海拔），`标注点` 文件夹 63 个命名点（村庄、山口、危险区提示）。现有 `assets/Everest_Base_Camp.gpx` 3,291 点、单程 58.3 km，走的是标准直上直下线。报告已在 origin/main 上拆成 `report/shell.html` + `sections/*.html` + `scripts/reportgen/*`，契约见 PATTERNS.md。
- **Constraints** — 单个 Python 模块 ≤150 行、section 文件 ≤60 行（PATTERNS.md）；provider 之间零 import 依赖；每个 token 供需精确匹配，否则构建期闸门停下；表格数字的唯一事实源是 `data/*.csv`；脚本产物不手改；每条事实带 `sources/NN` 出处。
- **Non-goals** — 不改 12 天行程本身（日期、宿营村、茶屋、费用一个不动）；不动 Section 5 以外的章节；不改全局图 `route-map-overview.png` 的构图（只跟着换轨迹来源）。
- **Success criteria** — ① 11 张逐日剖面图零虚线，每张都由实测或 DEM 采样的逐点序列画出；② 徒步图上同时可见全部环线支线与按天分色的我们的路线，两个适应点带「海拔适应点」字样与海拔；③ Section 5 只有一张行程表，列如上，距离格里只有一个数字；④ `uv run --with markdown scripts/build_report.py` 通过闸门；⑤ `uv run pytest tests/` 全绿。
- **Assumptions** — 见 Assumption Ledger。
- **Unknowns** — Overpass 的步道几何在 4 段缺口上能否连成通路（已验证四片区域都有 path/footway，但未验证连通性）。

## Alignment Gate

**I will implement**

- `assets/ebc-loop.kml`（从 KMZ 抽出的 664 KB KML，入库作为事实源）+ `sources/15-kmz-loop-track.md` 记出处。
- 用 KMZ 标注点坐标校正 `scripts/route_points.py` 的村庄坐标。
- 4 段两份轨迹都没覆盖的路线用 OSM 步道几何 + SRTM30m 高程补成实测序列，缓存进 `data/gap-legs.json`。
- 11 天徒步逐日轨迹装配、里程与爬升/下降计算，落 `data/day-track-stats.csv` 与 `data/day-tracks.json`。
- 逐日剖面小图 11 张（嵌进表格单元）+ 全程剖面图 1 张，全部实线。
- 徒步地形图重绘：环线全支线 + 按天分色的计划路线 + `Day N` 标签 + 两个海拔适应点标注 + 图例。
- Section 5 合并成一张表，删掉 `data/route-segments.csv`。
- 按 Living Documentation 更新 PROJECT / PATTERNS / TECHSTACK / DEVFLOW / AGENTS。

**I will not implement**

- 12 天行程内容的任何改动（含把 Day 9 的宿点 Pheriche 换成在实测轨迹上的 Dingboche —— 这是行程决策，留给用户）。
- Section 5 以外章节的正文。
- 照片：KMZ 里 44 张 PNG 不入库、不进报告。

**Open assumptions** — 见 Ledger 里 status 非 `settled` 的行。

**Acceptance** — Success criteria 五条全部满足，且用户看过渲染出的地图与表格后认可。

## Assumption Ledger

| Assumption | Confidence | Impact if Wrong | Status |
|---|---:|---:|---|
| 表格保留「天」列（用户只列了 7 列，但要求地图标 `Day N`，表与图需要能对上） | high | low | 按保留实现，已在汇报里点明 |
| 「终点海拔」展示文献口径的村庄海拔（Namche 3,440m），不展示 GPS 读数（3,491m） | high | low | 按文献口径实现，口径写进表脚 |
| 4 段缺口用 OSM 步道 + SRTM30m 补测，精度可接受 | high | medium | settled：SRTM30m 与 KMZ 实测在 Lobuche 差 7m、Kala Patthar 差 13m |
| Overpass 步道图在 4 段缺口上连通 | medium | medium | 未验证；不通时回退为端点间大圆折线采样 SRTM，仍是实测高程序列，在 CSV 的 source 列标明 |
| 「可走 options」指 KMZ 大环线记录到的各条支线，不含 Three Passes 以外的线路 | high | low | 按此实现 |

## Work-Unit Specs

```yaml
- id: T1
  title: 几何工具与 KMZ 解析
  file_path: scripts/geo.py, scripts/kmz_loop.py
  functions:
    - name: geo.haversine_m
      inputs: [lat1, lon1, lat2, lon2]
      outputs: 大圆距离（米，float）
      behavioral_contract: |
        标准 haversine，地球半径 6371000 m。同一点返回 0.0。
    - name: geo.cum_km
      inputs: "pts: [(lon, lat, ele), ...]"
      outputs: "[累计公里数], 长度与 pts 相同，首元素 0.0"
      behavioral_contract: |
        逐点累加 haversine。空序列返回 []，单点返回 [0.0]。
    - name: geo.resample
      inputs: "pts, step_m=25.0"
      outputs: 沿轨迹每 step_m 线性插值一个点后的 [(lon, lat, ele)]
      behavioral_contract: |
        首点与末点必定保留且各出现一次（末点不得因为「走完再补一个端点」而重复）。
        相邻点间距大于 step_m 时插入中间点，小于 step_m 时跳过被吞掉的点。
        ele 一起线性插值。两点间距恰好 200 m、step_m=50 时输出 5 个点。
      error_cases:
        - { condition: "step_m <= 0", behavior: "ValueError" }
        - { condition: "pts 少于 2 个点", behavior: "原样返回" }
    - name: geo.smooth_ele
      inputs: "eles, window=9"
      outputs: 等长的滚动中位数序列
      behavioral_contract: |
        窗口在两端收缩（不做 padding），半径一律取 window//2，
        所以 window=4 与 window=5 产生完全相同的输出。window=1 时原样返回。
        取的是真中位数：窗口内元素个数为偶数时取中间两个的平均值
        （[1,2] 的中位数是 1.5，不是 2）。序列两端因窗口收缩常落到偶数个元素，
        这个约定决定了首末几个值。压掉 GPS 单点跳变，这是消除「抖动」的关键一步。
    - name: geo.gain_loss
      inputs: "eles, hyst=8.0"
      outputs: "(总爬升 m, 总下降 m)"
      behavioral_contract: |
        极值追踪型滞回滤波，用来在保留真实起伏的同时压掉 GPS 海拔的单点跳变：

        维护「当前移动的起点值」与「当前移动的极值」。处于上行时追踪极大值，
        一旦当前值从极大值回落超过 hyst，就把这一段上行结算进 up（结算量 = 极大值 − 起点值），
        然后把方向翻成下行、起点值设为该极大值、极值设为当前值。下行对称。
        序列走完时还有一段没结算的移动：它的幅度（|极值 − 起点值|）超过 hyst 才结算，
        否则丢弃（这一条是「全部波动都小于 hyst 时返回 (0,0)」成立的原因）。

        三条必须同时成立的保证：
        - 单调上升序列返回 (末 − 首, 0)，不做任何量化截断
        - 单调下降序列返回 (0, 首 − 末)
        - 全部波动幅度都小于 hyst 时返回 (0, 0)

        朴素写法（维护单个锚点、每步比较、超过 hyst 就把差值计入并移动锚点）不满足第一条：
        它把结果量化成 hyst 的整数倍，单调上升 0→100、hyst=8 时只给出 96。不要用那种写法。
    - name: geo.nearest_index
      inputs: "pts, lat, lon"
      outputs: "(索引, 距离 m)"
      behavioral_contract: 线性扫描取 haversine 最近的点。
    - name: geo.slice_between
      inputs: "pts, a=(lat, lon), b=(lat, lon)"
      outputs: 从最接近 a 的点到最接近 b 的点的子序列
      behavioral_contract: |
        两个端点索引都取 nearest_index。a 的索引大于 b 的索引时结果反向，
        使返回序列总是从 a 走向 b。含首含尾。
      error_cases:
        - { condition: "两端点吸附到同一索引", behavior: "返回该单点组成的长度 1 序列" }
    - name: kmz_loop.load_lines
      inputs: "kml_path=assets/ebc-loop.kml"
      outputs: "[[(lon, lat, ele), ...], ...] —— 导航线文件夹里 LineString 的出现顺序"
      behavioral_contract: |
        用 xml.etree 解析 KML 命名空间 http://www.opengis.net/kml/2.2。
        只取 name 含「导航线」的 Folder 下的 Placemark/LineString/coordinates。
        coordinates 是空白分隔的 lon,lat,ele 三元组。返回 20 条线。
    - name: kmz_loop.load_waypoints
      inputs: "kml_path=assets/ebc-loop.kml"
      outputs: "{名称: (lat, lon, ele)}"
      behavioral_contract: |
        只取 name 含「标注点」的 Folder 下带 Point 的 Placemark。
        名称为空的点跳过。同名重复时保留第一个。CDATA 包裹的名称要脱掉 CDATA。
  dependencies: []
  reuse_candidates: |
    现有 scripts/make_profile.py 里有 haversine_m、rolling_median、gain_loss(hyst=15)
    三个等价实现，逐字搬进 geo.py 后从原处删掉，两个图件脚本改为 import。
    hyst 由 15 降到 8：现在的输入是 resample+smooth 之后的序列，噪声已被压过一轮，
    15 会把 Namche 前后真实的小起伏一起吃掉。
  acceptance: |
    geo 与 kmz_loop 的 hidden 测试全绿；load_lines 返回 20 条、
    总点数 17377；load_waypoints 含 Lukla airport / Namche / Gorakshep / Kala Patthar。

- id: T2
  title: 缺口路段补测（OSM 步道 + SRTM 高程）
  file_path: scripts/gap_legs.py
  functions:
    - name: build_graph
      inputs: "overpass_json"
      outputs: "{node_id: (lat, lon)}, {node_id: [(邻居 id, 边长 m)]}"
      behavioral_contract: |
        从 Overpass `out body geom` 的 way 元素建无向图，相邻 geometry 点连边，
        边权为 haversine 米数。多条 way 共享同一 node id 时自动连通。
    - name: shortest_path
      inputs: "nodes, adj, start_id, goal_id"
      outputs: "[(lat, lon), ...] 或 None"
      behavioral_contract: |
        Dijkstra（heapq）。start 与 goal 相同时返回单点。不连通返回 None。
      error_cases:
        - { condition: "start_id 或 goal_id 不在图里", behavior: "KeyError" }
    - name: fetch_elevations
      inputs: "[(lat, lon), ...]"
      outputs: "[ele_m]，与输入等长"
      behavioral_contract: |
        api.opentopodata.org/v1/srtm30m，每请求 ≤100 个 locations，请求间隔 ≥1.1 s，
        走 curl 子进程（与 make_map.py 抓瓦片同一理由：该环境 urllib 对部分站点 TLS 握手失败）。
        返回 null 的点用相邻有效值线性补。
        分批按顺序切：前 100 个一批、再 100 个一批、余数最后一批，结果按批次顺序拼接。
      error_cases:
        - { condition: "HTTP 失败或 status 非 OK", behavior: "同一批最多尝试 3 次（首次加两次重试），仍失败抛 RuntimeError" }
    - name: build_leg
      inputs: "leg_id, start=(lat, lon), goal=(lat, lon), bbox, out_and_back: bool"
      outputs: "{'id':…, 'points': [[lon, lat, ele], …], 'source': 说明字符串}"
      behavioral_contract: |
        Overpass 取 bbox 内 highway ~ path|footway|track|steps 的 way，建图，
        取距 start / goal 最近的图节点跑 Dijkstra，对路径点采 SRTM 高程。
        out_and_back 为真时把路径反向接在后面，形成往返序列。
        shortest_path 返回 None 时回退：start→goal 的大圆折线按 100 m 间隔取点采 SRTM，
        source 里写明「OSM 步道不连通，按直线采样 SRTM30m」。
    - name: main
      inputs: []
      outputs: 写 data/gap-legs.json
      behavioral_contract: |
        data/gap-legs.json 的结构是以 leg_id 为键的字典，这是 T2 与 T3 之间的契约：
          {"namche-everest-view": {"points": [[lon, lat, ele], ...], "source": "..."}, ...}
        坐标 6 位小数、海拔 1 位小数。

        LEGS 常量声明 4 段：
          namche-everest-view    Namche(27.8054,86.7124) → Everest View 观景台(27.8116,86.7183) 往返
          dingboche-nangkartshang Dingboche(27.8895,86.8273) → Nangkartshang 峰(27.9055,86.8355) 往返
          lobuche-pheriche       Lobuche(27.9478,86.8104) → Pheriche(27.8941,86.8198) 单程
          pheriche-pangboche     Pheriche(27.8941,86.8198) → Pangboche(27.8547,86.7908) 单程
        data/gap-legs.json 已存在且包含全部 4 个 id 时直接退出，不发网络请求
        （构建可离线复现）。加 --refresh 参数强制重抓。
  dependencies: []
  reuse_candidates: |
    scripts/make_map.py 的 fetch_tile 有「urllib 对该源 TLS 失败，改走 curl」的先例与重试写法，
    fetch_elevations 沿用同一形态。OSM 端点坐标已从 Overpass 查得：
    Everest View 观景台 ele=3885、Nangkartshang 峰 ele=5073、Thukla 27.9239/86.8054。
  acceptance: |
    hidden 测试全绿（build_graph / shortest_path / 回退分支用固定 JSON 夹具，不打网络）；
    真跑一次 main 后 data/gap-legs.json 含 4 段，每段点数 ≥20，
    海拔单调性合理（往返段首尾海拔差 <30 m）。

- id: T3
  title: 逐日轨迹装配与统计
  file_path: scripts/day_tracks.py, scripts/route_points.py
  functions:
    - name: route_points 坐标校正
      inputs: []
      outputs: TREK_VILLAGES 用 KMZ 标注点坐标
      behavioral_contract: |
        11 个村庄的 (lat, lon) 换成 kmz_loop.load_waypoints() 里对应标注点的坐标，
        海拔列保持文献口径不变（报告展示的是文献海拔）。
        Dingboche 现值 (27.8925, 86.8312) 距 KMZ 标注点约 510 m，
        正是「Dingboche 不在轨迹上」这个误判的根因，必须换掉。
        另加 ACCLIMATIZE_POINTS（Everest View 观景台 3880m、Nangkartshang 5080m）
        与 LOOP_LANDMARKS（Kongma La 5535、Cho La 5368、Renjo La 5411、Gokyo 4790、
        Chukhung 4740、Chukhung Ri 5546、Dzongla 4830、Thame 3860），供地图标注。
    - name: day_tracks.assemble
      inputs: []
      outputs: "{day: [(lon, lat, ele)]} —— Day 1..11"
      behavioral_contract: |
        每天的轨迹按下表拼接，拼接处用 geo.slice_between 在源轨迹上切，
        再 resample(25 m) + smooth_ele(9)。K=KMZ 导航线（0 基下标），G=现有 GPX，P=gap-legs：
          D1  Lukla→Phakding            K5
          D2  Phakding→Namche           K6
          D3  Namche 往返适应点          P namche-everest-view
          D4  Namche→Tengboche          K7 切 Namche→Tengboche
          D5  Tengboche→Dingboche       K7 切 Tengboche→Pangboche + K8 切 Pangboche→Dingboche
          D6  Dingboche 往返适应点       P dingboche-nangkartshang
          D7  Dingboche→Lobuche         G 切 Dingboche→Lobuche（经 Dughla）
          D8  Lobuche→Gorakshep→EBC 往返 G 切 Lobuche→Gorakshep + K12 整条
          D9  Gorakshep→KP 往返→Pheriche K13 整条 + P lobuche-pheriche
        K12 本身就是 Gorakshep→EBC→返 Gorakshep 的完整往返（7.8 km），K13 本身就是
        Gorakshep→Kala Patthar→返 Gorakshep→Lobuche 的完整序列（8.5 km），两条都直接用，不切。
          D10 Pheriche→Tengboche→Namche P pheriche-pangboche + G 切 Pangboche→Namche 反向
          D11 Namche→Lukla              K18 切 Namche→Lukla
        Day 12 是转场日，没有轨迹，不进这个字典。
    - name: day_tracks.stats
      inputs: "{day: pts}"
      outputs: 每天的 distance_km / ascent_m / descent_m / start_ele_m / end_ele_m / source
      behavioral_contract: |
        输入已经是 assemble 重采样并平滑过的序列，stats 自己不再做任何平滑或重采样，
        直接在收到的点上算。
        distance_km = cum_km 末值，一位小数。ascent/descent 走 gain_loss(hyst=8)，取整。
        start_ele_m / end_ele_m 取序列首末点的海拔，取整。
        返回按 day 升序排列，不受输入字典键序影响。

        source 无法从点序列推出来，取自模块级常量 DAY_SOURCES —— 一张写死的
        {天: 来源字符串} 表，与 assemble 的拼接表一一对应：
          1,2,4,5,11 → "KMZ 实测"
          3,6        → "OSM+SRTM30m"
          7          → "GPX 实测"
          8          → "GPX 实测 + KMZ 实测"
          9          → "KMZ 实测 + OSM+SRTM30m"
          10         → "OSM+SRTM30m + GPX 实测"
        DAY_SOURCES 里没有的天回落成空字符串以外的占位说明，不抛异常。
    - name: day_tracks.main
      inputs: []
      outputs: data/day-tracks.json 与 data/day-track-stats.csv
      behavioral_contract: |
        day-tracks.json：{"1": [[lon, lat, ele], ...], ...}，坐标 6 位小数、海拔 1 位小数。
        day-track-stats.csv 列：day,distance_km,ascent_m,descent_m,start_ele_m,end_ele_m,source。
  dependencies: [T1, T2]
  reuse_candidates: |
    现有 make_profile.py 的村庄吸附逻辑（snap_off < 400 过滤）不再需要：
    坐标校正后所有村庄都吸得上，过滤条件删掉。
  acceptance: |
    hidden 测试全绿；真跑一次后 11 天全部有轨迹，
    每天 distance_km 与文献值（itinerary.csv 原 dist_km_lit）差 <25%，
    D7 与 D9 不再出现「无覆盖」，全部 source 里没有「文献估算」字样。

- id: T4
  title: 海拔剖面渲染
  file_path: scripts/make_profile.py
  functions:
    - name: day_thumbnail
      inputs: "day, pts, x_max, y_range"
      outputs: 写 assets/day-profile-NN.png
      behavioral_contract: |
        表格单元内嵌用的小图：figsize 约 (2.6, 0.95)、dpi 200，实线 + 填充，
        无坐标轴文字无标题（比例尺信息由表脚统一说明），11 张共用同一 x_max 与
        y_range=(2300, 5900)，所以格与格之间的高矮胖瘦可直接比强度。
    - name: full_profile
      inputs: "{day: pts}"
      outputs: 写 assets/elevation-profile.png
      behavioral_contract: |
        11 天首尾相接画成一条连续曲线，每天一个颜色（与地图同一套按天色板），
        天与天的交界画竖向分隔线并标 Day N，村庄标注用文献海拔。
        适应日的往返段就地凸起，不额外拉平。
    - name: main
      inputs: []
      outputs: 11 张小图 + 全程图 + data/route-track-stats.csv
      behavioral_contract: |
        读 data/day-tracks.json，不重新解析 KML/GPX（装配的事实源是 T3 的产物）。
        route-track-stats.csv 重算成逐村累计里程与海拔两段块，口径与现有列名保持一致。
  dependencies: [T3]
  reuse_candidates: |
    现有 make_profile.py 的 matplotlib 中文字体设置、配色 #2a78d6、
    网格与 spine 样式逐字沿用；make_daily_profiles 的 PIECES_BY_ORDER 整块删除
    （它就是虚线的来源）。
  acceptance: |
    11 张小图与全程图都生成，图里不出现任何 linestyle="--"；
    我（架构师）逐张看过，确认曲线连续、无锯齿状跳变。

- id: T5
  title: 地形图渲染（options + 按天分色）
  file_path: scripts/http_fetch.py, scripts/tiles.py, scripts/make_map.py
  functions:
    - name: http_fetch.get_bytes / http_fetch.post_text
      inputs: "url, ua, timeout, retries / url, body, timeout, retries"
      outputs: 响应字节 / 文本
      behavioral_contract: |
        走 subprocess.run(["curl", ...])，模块限定调用。带指数退避重试，
        重试耗尽抛 RuntimeError。这一份实现给瓦片抓取与 OSM/高程抓取共用
        （该环境 urllib 对这些站点 TLS 握手失败，curl 是既有先例）。
    - name: tiles.*
      inputs: []
      outputs: 瓦片抓取与绘图原语
      behavioral_contract: |
        把现有 make_map.py 的 global_px / fetch_tile / build_basemap / mute /
        draw_path / draw_dashed / marker / label / attribution 搬过来，
        瓦片抓取改用 http_fetch.get_bytes，
        使 make_map.py 回到 150 行以内（PATTERNS.md 的模块粒度上限）。
        新增 offset_polyline(px_pts, dx)：沿每段法线平移像素折线，
        用于让上山与下撤两条重合的路线并排可见。
    - name: make_map.make_trek_map
      inputs: []
      outputs: 写 assets/route-map-trek.png
      behavioral_contract: |
        底图 z13、bbox 覆盖整个大环线（含 Gokyo 与 Thame，向西扩到 86.63），
        轻度压色（saturation 0.45、whiten 0.30）让等高线仍可读又腾出色相空间。
        三层叠加，从下到上：
          ① 全部 20 条 KMZ 导航线，中性灰 (150,150,145)、宽 6、无 casing —— 「可走的线路」
          ② 我们的路线 Day 1..11，每天一个颜色、宽 9、白 casing；
             上山日（1,2,4,5,7,8）与下撤日（9,10,11）走同一走廊，
             用 offset_polyline 分别向两侧平移 7 px，两条都看得见
          ③ 村庄 marker + 名称海拔；每天轨迹中点放一个 `Day N` 圆底徽标
        两个适应点画成方形 marker，标 `海拔适应点 3,880m` / `海拔适应点 5,080m`。
        环线支线的关键节点标名称与海拔：Kongma La 5,535m、Cho La 5,368m、
        Renjo La 5,411m、Gokyo 4,790m、Chukhung Ri 5,546m、Thame 3,860m。
        图例说明三层含义。
    - name: make_map.make_overview_map
      inputs: []
      outputs: 写 assets/route-map-overview.png
      behavioral_contract: |
        构图与现状一致，轨迹来源换成 data/day-tracks.json 的 11 天串联，
        图例里「EBC 徒步轨迹（GPX 实测）」改为「EBC 徒步轨迹（KMZ 实测）」。
  dependencies: [T1, T3]
  reuse_candidates: |
    瓦片缓存 assets/.tile-cache/ 已有 z13 与 z10 的瓦片；
    bbox 向西扩后需要补抓 z13 瓦片，缓存机制照用。
  acceptance: |
    两张 PNG 生成；我逐张看过，确认支线与计划路线都能分辨、
    Day N 标签不互相压、两个适应点标注清楚、上山与下撤两条线并排可见。

- id: T6
  title: 报告接线（合并表 + Section 5 正文）
  file_path: scripts/reportgen/route.py, scripts/reportgen/imgio.py, scripts/reportgen/figures.py, scripts/reportgen/appendix.py, report/sections/s5-route.html, report/sections/appendix-a-data.html
  functions:
    - name: imgio.img_uri
      inputs: "name"
      outputs: data URI 字符串
      behavioral_contract: |
        从 figures.py 抽出来的共用基础设施，figures.py 与 route.py 都用它。
        PATTERNS.md 的「provider 之间零 import 依赖」因此多一个共用模块，
        要在 PATTERNS.md 的共用基础设施清单里补上 imgio。
    - name: route.itinerary_table
      inputs: []
      outputs: 一张 HTML 表
      behavioral_contract: |
        join data/itinerary.csv（天、日期、起点、终点、终点海拔的文献口径）
        与 data/day-track-stats.csv（距离、爬升、下降），按 day 对齐。

        同时从 data/itinerary.csv 删掉 dist_km_lit 与 dist_km_gpx 两列：距离的唯一事实源
        改成 day-track-stats.csv 的实测值，留着这两列就有了三个来源。
        其余列（含 start_ele_m / end_ele_m / sleep_ele_m / hours）保留 ——
        end_ele_m 是表格「终点海拔」的取值来源，sleep_ele_m 在 Day 8/9 与它不同
        （Day 8 终点 EBC 5,364m、宿 Gorak Shep 5,164m），两列各有用处。
        列：天 | 日期 | 起点 | 终点 | 距离 | 总爬升/总下降 | 终点海拔 | 海拔剖面。
        「天」列 `D1`…`D12`；「日期」列 `09-25` 形态（月-日，年份在报告页头）；
        「距离」列一个数字加单位 `8.3 km`，没有第二个数字没有括注；
        「总爬升/总下降」列 `+98 / −334 m` 单格；「终点海拔」列 `2,610 m`；
        「海拔剖面」列内嵌 <img class="dayprof" src="data:...">。
        Day 12 是转场日：距离、爬升/下降、剖面三列写 `—`。
        适应日的起点与终点相同（Namche → Namche），行本身即可读出往返。
      error_cases:
        - { condition: "itinerary.csv 的 day 在 day-track-stats.csv 里没有对应行且不是 Day 12", behavior: "SystemExit，消息点名缺哪天" }
    - name: route.tokens
      inputs: []
      outputs: "{'TBL_ITINERARY': …}"
      behavioral_contract: |
        只剩一个 token。TBL_ROUTE_SEGMENTS 与 TBL_ITINERARY_DATES 一并删掉，
        引用它们的 section 同步改，否则构建期闸门会报未被引用。
    - name: sections/s5-route.html
      inputs: []
      outputs: ≤60 行的章节文件
      behavioral_contract: |
        一张 {{TBL_ITINERARY}} 加表脚口径说明（距离与爬升口径、剖面小图共用比例尺、
        终点海拔为文献口径），{{IMG_TREK_MAP}} 与 {{IMG_ELEV_PROFILE}} 两张图各带 figcaption，
        原有的行程结构、茶屋三餐、备选行程三段说明保留。
        删掉 {{IMG_ELEV_PROFILE_DAILY}} 的 figure（4×3 网格图被表内小图取代）。
    - name: appendix-a-data.html 与 appendix.py
      inputs: []
      outputs: 附录 A 换表
      behavioral_contract: |
        A.5 的 route-segments 换成 day-track-stats，`<p class="meta">` 改写口径说明；
        appendix.py 的 tokens() 里 TBL_ROUTE_SEGMENTS_FULL 换成 TBL_DAY_TRACK_STATS_FULL。
  dependencies: [T3, T4, T5]
  reuse_candidates: |
    tables.table() 直接用；内嵌 <img> 需要一条 .dayprof 样式（宽 100%、max-width 180px、
    vertical-align middle），加进 report/styles/components.css。
  acceptance: |
    uv run --with markdown scripts/build_report.py 通过全部闸门并写出报告；
    uv run pytest tests/ 全绿；报告里 Section 5 只有一张表。

- id: T7
  title: 文档与出处更新
  file_path: sources/15-kmz-loop-track.md, PROJECT.md, PATTERNS.md, TECHSTACK.md, DEVFLOW.md, AGENTS.md
  functions:
    - name: sources/15
      behavioral_contract: |
        记 KMZ 出处：用户自有的两步路（2bulu）轨迹 2024.06 陆路 EBC 大环线，
        TrackId 56224568，抽出的 doc.kml 入库为 assets/ebc-loop.kml，
        20 条导航线的覆盖清单与逐段里程，63 个标注点里报告用到的那些的坐标与海拔。
        另记 OpenTopoData SRTM30m 与 Overpass 两个 API 的用法与抓取日期，
        以及 SRTM 与 KMZ 实测的偏差实测值。
    - name: 四份内容文档
      behavioral_contract: |
        PROJECT.md：CSV 清单从六张改为「route-segments 删除、day-track-stats 新增」的现状，
          Section 5 的描述改成一张表，模块地图补 geo/kmz_loop/gap_legs/day_tracks/tiles。
        PATTERNS.md：共用基础设施清单补 imgio；token 分工数字更新；
          文件粒度上限的「当前最大」实测值更新。
        TECHSTACK.md：补 OpenTopoData 与 Overpass 两个外部服务、
          assets/ebc-loop.kml 与三个新 data 产物、目录结构。
        DEVFLOW.md：图件重生成命令链更新为
          gap_legs.py → day_tracks.py → make_profile.py → make_map.py → build_report.py，
          「换 GPX 流程」改写为「换轨迹来源流程」。
        AGENTS.md：「要改 X 就动哪个文件」表里剖面图与地图两行的入口函数名更新。
  dependencies: [T6]
  acceptance: 每份文档只写当前事实，不出现「原来是 X 现在改成 Y」的对照叙事。

- id: T8
  title: gap_legs 按领域拆分到 150 行上限内
  file_path: scripts/osm_graph.py, scripts/gap_legs.py
  functions:
    - name: osm_graph.build_graph / shortest_path / nearest_node
      inputs: 同 gap_legs 里现有的三个同名函数
      outputs: 同上
      behavioral_contract: |
        把 OSM 图论部分整块搬进 scripts/osm_graph.py：从 Overpass way 元素建无向图、
        Dijkstra 求最短路、取距某坐标最近的图节点。行为逐字不变。
    - name: gap_legs 瘦身
      behavioral_contract: |
        gap_legs.py 保留 LEGS 常量、fetch_elevations、build_leg、main，
        图论部分改为 from osm_graph import ...，HTTP 部分改用 http_fetch，
        自带的 _haversine_m 改用 geo.haversine_m。
        两个模块各自落在 150 行以内。
  dependencies: [T5]
  reuse_candidates: |
    http_fetch.py 由 T5 建立，本单元复用它替换 gap_legs 里的两处 curl 调用。
  acceptance: |
    gaplegs 的 hidden 测试仍然全绿（28/28）；
    scripts/ 下每个模块的行数都 ≤150；
    data/gap-legs.json 不需要重新生成（行为不变，不打网络）。
```

## Dependency Graph

```
T1 ─┐
    ├─→ T3 ─┬─→ T4 ─┐
T2 ─┘       │        ├─→ T6 ─→ T7
            └─→ T5 ──┘         T8
T1 ──────────────────→ T5 ─────→ T8
```

## Execution Waves

- **Wave 1**（无依赖，可并行）：T1 ✅、T2 ✅
- **Wave 2**：T3
- **Wave 3**（可并行，目标文件不重叠）：T4、T5
- **Wave 4**：T6
- **Wave 5**（可并行，目标文件不重叠）：T7、T8

## 已确认的实测结果

四段缺口全部在 OSM 步道图里连通，没有一段回退成直线采样（plan 开头那个 medium
confidence 的 Unknown 到此关闭）：

| leg_id | 点数 | 距离 km | 爬升/下降 m | 海拔区间 m |
|---|---:|---:|---|---|
| namche-everest-view | 341 | 2.75 | 353 / 353 | 3,487–3,840 |
| dingboche-nangkartshang | 219 | 4.58 | 742 / 742 | 4,297–5,039 |
| lobuche-pheriche | 193 | 6.93 | 23 / 684 | 4,259–4,920 |
| pheriche-pangboche | 313 | 6.08 | 224 / 561 | 3,922–4,288 |

两个适应日支线与文献口径吻合：Nangkartshang 文献 4–6 km、爬升约 670 m、山脊约 5,080 m，
实测 4.58 km、742 m、最高 5,039 m；Everest View 文献约 3,880 m，实测最高 3,840 m。

## Status

Completed —— 八个 work unit 全部交付并通过架构师验收。构建 `wrote report/EBC-report.html (12.7 MB)`，
`uv run --with pytest pytest tests/ -q` 143 passed，三个数据单元的 hidden 测试
45/45 + 28/28 + 33/33。11 张逐日剖面图与全程剖面图零虚线，徒步详图三层叠加经逐块目检。
合进 main 由用户看过渲染效果后决定。
