"""仓库路径与全局换算口径。"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data"
SOURCES_DIR = ROOT / "sources"
ASSETS_DIR = ROOT / "assets"
REPORT_DIR = ROOT / "report"

NPR_PER_USD = 129.2   # 1 USD ≈ 129.2 NPR
PAX = 6               # 同行人数
