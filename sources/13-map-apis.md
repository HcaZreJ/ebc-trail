# 带地形静态地图的选型（路线图底图）

需求：为纯静态 HTML 报告生成带地形（等高线/山体阴影）的路线图 PNG，叠加 GPX 轨迹与地点标记，覆盖尼泊尔 Khumbu 地区，离线嵌入、可打印。

## 要点

- 报告的地形底图采用 OpenTopoMap 瓦片离线拼合，它免费、无需 API key，渲染自带等高线与山体阴影，出图尺寸不受接口上限约束。
- OpenTopoMap 的许可是 CC-BY-SA 3.0，图上必须保留署名「© OpenStreetMap contributors, SRTM | map style © OpenTopoMap CC-BY-SA」。
- 实测珠峰地区 z10–z13 的瓦片可正常获取，约 100 张量级的一次性抓取符合它的公平使用要求，偶发的 SSL 中断用 HTTP/1.1 加重试解决。
- Google Static Maps 支持 `maptype=terrain`，但要求 Google Cloud 账号绑卡开 billing，单图上限 1280×1280，只作备选。
- 高德静态地图没有任何切换地形底图的参数，单图上限 1024×1024、折线最多 4 条，只能作无地形的 fallback。

## 来源 1：高德静态地图 API 官方文档
- URL: https://lbs.amap.com/api/webservice/guide/api/staticmaps
- 抓取日期: 2026-07-31
- 要点：
  - 参数集里**没有任何切换地形/等高线/山体阴影底图的选项**，只有标准底图样式。
  - 限制：图片最大 1024×1024；折线/多边形最多 4 条；标注最多 10 个；坐标经纬度小数点后最多 6 位。
  - 文档未说明尼泊尔等境外区域的底图覆盖质量。
  - 高德「地形图」产品（https://lbs.amap.com/product/terrain）是 JS API 的动态 3D 地形能力，输出网页应用，没有静态图片接口。
- 结论：高德只能作为无地形的 fallback（paths 画轨迹 + markers 标点，需用户的 key）。

## 来源 2：Google Maps Static API 官方文档
- URL: https://developers.google.com/maps/documentation/maps-static/start
- 抓取日期: 2026-07-31
- 要点：
  - 支持 `maptype=terrain`（"physical relief map image, showing terrain and vegetation"），另有 roadmap/satellite/hybrid。
  - **必须有 API key 且项目开通 billing（绑卡）**。
  - 图片上限 640×640（scale=1）或 1280×1280（scale=2）。
  - 该文档页未写明免费额度数字。
- 结论：可行但要 Google Cloud 账号绑卡，且单图尺寸上限低于本报告想要的大图。

## 来源 3：OpenTopoMap 官方说明
- URL: https://opentopomap.org/about
- 抓取日期: 2026-07-31
- 要点：
  - 免费使用，许可 CC-BY-SA 3.0，署名要求原文："Kartendaten: © OpenStreetMap-Mitwirkende, SRTM | Kartendarstellung: © OpenTopoMap (CC-BY-SA)"（英文等价：© OpenStreetMap contributors, SRTM | map style © OpenTopoMap CC-BY-SA）。
  - 数据源：OpenStreetMap + SRTM 高程，渲染含等高线与山体阴影。
  - 瓦片地址 `https://{a|b|c}.tile.opentopomap.org/{z}/{x}/{y}.png`，**无需 API key**。
  - 公平使用：欢迎集成，但要求避免大规模批量下载压垮服务器；无可用性保证。
- 实测（2026-07-31，本 repo）：珠峰地区 z10–z13 瓦片可正常获取，约 100 张量级的一次性抓取符合公平使用；个别请求偶发 SSL/HTTP2 中断，用 HTTP/1.1 + 重试解决（见 scripts/make_map.py）。

## 选型结论

1. **采用 OpenTopoMap 瓦片离线合成**（本 repo 方案）：无需 key、真等高线+山体阴影、尺寸不受 API 上限约束（自行拼瓦），符合"静态展示、导出 PDF"的场景。图上保留署名。
2. 备选：Google Static Maps `maptype=terrain`（需绑卡开 billing，单图 ≤1280px）。
3. Fallback：高德静态图（用户已有 key，但无地形、境外底图细节未知、单图 ≤1024px、折线 ≤4 条）。
