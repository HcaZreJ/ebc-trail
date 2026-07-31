"""仓库路径与全局换算口径。"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data"
SOURCES_DIR = ROOT / "sources"
ASSETS_DIR = ROOT / "assets"
REPORT_DIR = ROOT / "report"

RATE = 6.8   # 1 USD ≈ 6.8 CNY（2026-07 参考价，见 AGENTS.md）
PAX = 6      # 同行人数
