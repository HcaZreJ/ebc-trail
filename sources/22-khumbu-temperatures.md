# Khumbu 沿线气温（9 月下旬至 10 月上旬）

## 要点

- 9/25–10/6 这个窗口正卡在季风撤退的转折点上，Pyramid 站（5,035m）的三十年气候图显示日最低均值在 9 月到 10 月这一个月内从 0°C 掉到 −10.5°C，同一海拔在窗口前后半段差别很大。
- 白天行进时段的气温沿海拔从加德满都（1,400m）的 24–28°C 降到 Gorak Shep（5,164m）的 −2–6°C；夜间最低从 15–19°C 降到 −15–−10°C。
- Kala Patthar（5,545m）凌晨气温在 −15°C 上下，山脊在 10–11 月持续风速常到 30–50 km/h，顶风时体感可到 −25°C 以下，风速是当天赌概率的变量，不写单一数字。
- 这个窗口的雨雪分界大致在 3,900–4,400m 之间：Tengboche（3,860m）夜间在零度线附近徘徊，Dingboche（4,410m）已明确转负；这是按本文各点夜间温度做的推算，不是某篇文献直接给出的数字。
- 典型日周期是上午晴朗、能见度最好，12:00–14:00 起谷风增强、云开始堆积，4,500m 以上再叠加午后到傍晚的冰川下坡风，这是 Namche 以上下午风特别大的物理成因。
- 紫外线每升高 1,000m 增强约 10%，5,000m 处约为海平面的 1.5 倍，所以高海拔段长袖是缺省选择，作用是防晒而不是保暖。

## 逐点取值（写进 data/clothing-by-day.csv 的依据）

| 地点 | 海拔 | 白天 9:00–16:00 | 夜间/清晨最低 | 取值依据 |
|---|---|---|---|---|
| 加德满都 | 1,400m | 24–28°C | 15–19°C | 多源聚合，跨源 F/C 换算有 1–2°C 内部不一致 |
| Phakding | 2,610m | 13–18°C | 6–11°C | 无直接月值，按 Lukla 加 0.5°C/100m 递减率推算 |
| Lukla | 2,860m | 12–17°C | 5–10°C | 运营商月度表；Pyramid 网络 AWS3 站即设在 Lukla 2,660m |
| Namche Bazaar | 3,440m | 8–13°C | −3–2°C | 取 climate-data.org 独立气候常模（10 月日最低均值 1.2°C）为中心 |
| Tengboche | 3,860m | 8–12°C | −3–2°C | 运营商月度表 |
| Pheriche | 4,280m | 3–7°C | −8–−3°C | 按 Pyramid 站基准加 0.5°C/100m 推算，用 Dingboche 运营商数据校核量级 |
| Dingboche | 4,410m | 5–10°C | −8–0°C | 取 Himalayan Recreation 表 |
| Lobuche | 4,940m | 0–7°C | −12–−6°C | 取 Himalayan Recreation 表 |
| Gorak Shep | 5,164m | −2–6°C | −15–−10°C | 取 Nepal Hiking Team 的「早 10 月 −10–−15°C」，与 Pyramid 站 10 月日最低均值 −10.5°C 量级一致 |
| Kala Patthar | 5,545m | 凌晨 −15°C 上下 | 顶风体感 −25°C 以下 | 徒步记录与预报站共识区间 −10–−20°C，叠加 30–50 km/h 山脊风的风寒修正 |

行程表里的白天一列取当天行进路线跨过的海拔落差所对应的区间（早上在谷底暖、下午爬到高处冷），因此是上表相邻两点的并集，不是单点值。

## 来源 1：Pyramid 气象站网三十年数据集（最硬的一份）

- Salerno, Guyennon 等 (2025), "What is climate change doing in Himalaya? Thirty years of the Pyramid Meteorological Network (Nepal)", *Earth System Science Data*
- URL: https://essd.copernicus.org/articles/17/4293/2025/
- 抓取日期：2026-09-19
- 这个站网几乎是照着 EBC 行程点位建的：AWS3 设在 Lukla 2,660m、AWS5 设在 Namche 3,570m、AWS2 设在 Pheriche 4,260m、AWS4 设在 Kala Patthar 5,600m，Pyramid 主站 5,035m。
- Pyramid 站年均温 −2.5°C；降水 90% 集中在 6–9 月，10 月降水占比很低。
- Figure 4（1994–2023 逐月气候图，目视读图，误差约 ±1°C）：Pyramid 站 10 月日最高均值约 0°C、日均温约 −5°C、日最低均值约 −10.5°C；9 月明显更暖，日最高约 6°C、日均温约 2.5°C、日最低约 0°C。
- 正文写明白天全年为谷风（up-valley wind），4,500m 以上另有强烈的日循环冰川下坡风（katabatic wind）。
- 站网 6–9 月监测期内 5,035m 处日最低温始终高于 0°C，说明季风季即便在 5,000m 降水也主要以雨的形式落下，进入 10 月夜间转负后同海拔才转雪。

## 来源 2：运营商月度气温表

- Nepal Hiking Team, EBC October guide — https://www.nepalhikingteam.com/everest-base-camp-trek-in-october — 抓取 2026-09-19。Gorak Shep 月均 max 5.4°C / min −8.9°C，明确区分「早 10 月 −10–−15°C、晚 10 月 −15–−22°C」，是唯一按上下旬拆开报数字的来源。
- Himalayan Recreation — https://www.himalayanrecreation.com/blog/trek-to-everest-base-camp-in-october — 抓取 2026-09-19。给出 Lukla 到 EBC 全程一张表，海拔标注与本行程精确对上（Dingboche 4,410m、Lobuche 4,940m）。
- MountainKick — https://mountainkick.com/ebc-trek-in-october/ — 抓取 2026-09-19。完整梯度表与「下午 2 点后起云、月末风变强」的日周期描述。
- The Everest Holiday — https://theeverestholiday.com/blog/everest-base-camp-weather-month-by-month-what-the-temperature-actually-feels-lik — 抓取 2026-09-19。唯一给出风寒量化例子的来源：−5°C 无风尚可，−5°C 叠加 20 km/h 逆风体感 −15°C。
- Life Happens Outdoors — https://lifehappensoutdoors.com/everest-base-camp-trek-in-october/ — 抓取 2026-09-19。「早 10 月更暖、带残余季风水汽」这一判断的主要来源。

## 来源 3：气温递减率

- 中喜马拉雅（尼泊尔中部，涵盖 Khumbu）年均递减率 −0.52°C/100m，西喜马拉雅 −0.66、东喜马拉雅 −0.50（Biodiversity and Conservation 分区研究）。
- Khumbu Himal 多年冻土研究给出 5,200–5,300m 以下实测递减率约 0.5°C/100m，此高度以上递减率明显更大。
- 5,300m 以上的确切系数没有查到，只有定性表述。凡涉及 Kala Patthar 与 Gorak Shep 高值区的推算都用 0.5–0.8°C/100m 的区间做，基准点是 Pyramid 站 10 月气候图。

## 来源 4：紫外线

- 常引用系数为每升高 1,000m 紫外线增强约 10%，5,000m 处约为海平面的 1.5 倍，多个来源独立给出同一量级。
- EBC 高海拔段 UV 指数可到 10 以上，雪面反射使暴露量再翻倍；建议 SPF50+ 每两小时补涂、UV400 墨镜从第一天起用。

## 源间分歧与取舍

- **Namche 夜间低温**跨度近 9°C：MountainKick 报 −5°C，The Everest Holiday 报 +4°C（标注 9 月）。climate-data.org 的独立气候常模给 10 月日最低均值 1.2°C。取 −3–2°C 为区间中心，营销页的 −5°C 更像极端夜或月末数字。
- **Dingboche / Lobuche / Gorak Shep 夜间低温**三个信源之间差 4–7°C。偏向 Himalayan Recreation 的表，因为它标注的海拔与本行程点位精确对上；其余两源的海拔标注有偏差（4,360m / 4,483m / 4,910m），提示它们引用的是别处行程的数字后改了海拔标签。
- **Pheriche** 虽有实测站（AWS2, 4,260m），但论文只公开了 Pyramid 主站的月度图，Pheriche 的数字是推算值。
