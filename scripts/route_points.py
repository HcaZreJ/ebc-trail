"""路线关键点位（坐标与文献海拔）。

坐标出处：
- 徒步沿线村庄：公开坐标吸附 GPX 轨迹验证（吸附偏差见 data/route-track-stats.csv）
- Kathmandu TIA / Ramechhap Airport / Kala Patthar：Wikipedia（抓取 2026-07-31）
- 海拔取徒步文献口径（sources/06）；Kala Patthar 文献常用 5545m，
  2008 年 GPS 实测经幡顶为 5644.5m（Wikipedia）
"""

# (名称, 纬度, 经度, 海拔m)
TREK_VILLAGES = [
    ("Lukla",       27.6869, 86.7314, 2860),
    ("Phakding",    27.7433, 86.7133, 2610),
    ("Monjo",       27.7789, 86.7186, 2835),
    ("Namche",      27.8054, 86.7140, 3440),
    ("Tengboche",   27.8361, 86.7645, 3860),
    ("Pangboche",   27.8571, 86.7940, 3930),
    ("Dingboche",   27.8925, 86.8312, 4410),
    ("Pheriche",    27.8945, 86.8190, 4280),
    ("Lobuche",     27.9490, 86.8102, 4940),
    ("Gorak Shep",  27.9812, 86.8283, 5164),
    ("EBC",         28.0026, 86.8528, 5364),
]

KALA_PATTHAR = ("Kala Patthar", 27.9958, 86.8284, 5545)

KATHMANDU_TIA = ("Kathmandu (TIA)", 27.6978, 85.3592, 1338)
RAMECHHAP_AIRPORT = ("Manthali/Ramechhap", 27.3939, 86.0614, 474)
