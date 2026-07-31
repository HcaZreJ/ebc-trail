"""从 report/shell.html + report/{styles,sections}/ + data/*.csv + sources/*.md + assets/*.png
生成自包含的 report/EBC-report.html（图片以 base64 内嵌，可直接分享/打印成 PDF）。

Run:  uv run --with markdown scripts/build_report.py
"""
from reportgen.assemble import build


def main():
    out = build()
    print(f"wrote {out}  ({out.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
