# GPX 轨迹文件

## 来源：Real World Adventures 免费 GPS 轨迹库
- 页面 URL: https://realworldadventures.com/ebc-maps-facts/
- 文件直链: https://realworldadventures.com/wp-content/uploads/2023/03/EBC.gpx_.zip
- 下载日期: 2026-07-31
- 落盘位置: `assets/Everest_Base_Camp.gpx`
- 文件事实：
  - GPX 1.1，由 Locus Map 导出（2023-02-17），轨迹原始出处为 outdooractive（https://www.outdooractive.com/r/240405054）。
  - 3,291 个轨迹点，全部带海拔（`<ele>`），无独立 waypoint。
  - 起点位于 Lukla（27.687, 86.732，2,855m）。
- 用途：`scripts/` 下的脚本用它计算逐村累计里程并生成海拔剖面图（`assets/elevation-profile.png`、`data/route-track-stats.csv`）。村庄点位是把公开坐标吸附到最近轨迹点得到的，吸附点海拔与文献海拔的偏差在脚本输出里可核对。
