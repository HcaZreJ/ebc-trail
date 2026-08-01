"""路线关键点位（坐标与文献海拔）。

坐标出处：
- 徒步沿线村庄：KMZ 实测轨迹的标注点坐标（sources/15「标注点坐标」小节），
  KMZ 没有标注点的 Tengboche / Pheriche 取该小节文末给出的坐标
- Kathmandu TIA / Ramechhap Airport / Kala Patthar：Wikipedia（抓取 2026-07-31）
- 海拔取徒步文献口径（sources/06），村庄坐标校正后海拔口径不变；
  Kala Patthar 文献常用 5545m，2008 年 GPS 实测经幡顶为 5644.5m（Wikipedia）
"""

# (名称, 纬度, 经度, 海拔m)
TREK_VILLAGES = [
    ("Lukla",       27.6882, 86.7315, 2860),
    ("Phakding",    27.7392, 86.7122, 2610),
    ("Monjo",       27.7701, 86.7238, 2835),
    ("Namche",      27.8054, 86.7124, 3440),
    ("Tengboche",   27.8361, 86.7645, 3860),
    ("Pangboche",   27.8547, 86.7908, 3930),
    ("Dingboche",   27.8895, 86.8273, 4410),
    ("Pheriche",    27.8941, 86.8198, 4280),
    ("Lobuche",     27.9478, 86.8104, 4940),
    ("Gorak Shep",  27.9794, 86.8283, 5164),
    ("EBC",         27.9986, 86.8489, 5364),
]

KALA_PATTHAR = ("Kala Patthar", 27.9958, 86.8284, 5545)

KATHMANDU_TIA = ("Kathmandu (TIA)", 27.6978, 85.3592, 1338)
RAMECHHAP_AIRPORT = ("Manthali/Ramechhap", 27.3939, 86.0614, 474)

# 海拔适应点，供地图标注（sources/15）：往返支线的目标点坐标 + 文献常用海拔。
# 只在 Dingboche 安排一个适应日（见 sources/16、17）。
ACCLIMATIZE_POINTS = [
    ("Nangkartshang",     27.9055, 86.8355, 5080),
]

# 大环线支线上的关键节点，供地图标注（sources/15「标注点坐标」，海拔取报告文献值）
LOOP_LANDMARKS = [
    ("Kongma La",   27.9298, 86.8362, 5535),
    ("Cho La",      27.9617, 86.7517, 5368),
    ("Renjo La",    27.9474, 86.6585, 5411),
    ("Gokyo",       27.9533, 86.6946, 4790),
    ("Chukhung",    27.9040, 86.8702, 4740),
    ("Chukhung Ri", 27.9254, 86.8792, 5546),
    ("Dzongla",     27.9386, 86.7737, 4830),
    ("Thame",       27.8336, 86.6515, 3860),
]
