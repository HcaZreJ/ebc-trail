"""表格内嵌用的逐日剖面小图：无坐标轴、无标题，只画实线加同色填充。

11 张共用同一 x_max 与 y_range（由调用方传入），格与格之间的高矮胖瘦
因此可以直接比较当天路程的强度，不为填满格子各自缩放坐标轴。

由 scripts/make_profile.py 调用，不单独执行。
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import geo
from day_colors import hex_color

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"


def day_thumbnail(day, pts, x_max, y_range):
    """写 assets/day-profile-NN.png：实线 + 同色半透明填充，四周留白压到最小。"""
    xs = geo.cum_km(pts)
    ys = [p[2] for p in pts]
    color = hex_color(day)

    fig, ax = plt.subplots(figsize=(5.2, 1.9), dpi=200)
    ax.fill_between(xs, ys, y_range[0], color=color, alpha=0.28, linewidth=0)
    ax.plot(xs, ys, color=color, linewidth=1.6)
    ax.set_xlim(0, x_max)
    ax.set_ylim(*y_range)
    ax.axis("off")
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(ASSETS / f"day-profile-{day:02d}.png", facecolor="white")
    plt.close(fig)
