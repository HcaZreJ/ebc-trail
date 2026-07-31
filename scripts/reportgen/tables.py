"""把行列表渲染成报告用的 <table>。"""
import io

from .csvio import esc


def table(rows, header=True, total_marker=None):
    """total_marker：首列等于它的行加粗底色；可以是一个字符串，也可以是多个。"""
    if total_marker is None:
        marks = set()
    else:
        marks = {total_marker} if isinstance(total_marker, str) else set(total_marker)
    out = io.StringIO()
    out.write('<div class="table-scroll">\n<table>\n')
    for i, row in enumerate(rows):
        tag = "th" if (header and i == 0) else "td"
        cls = ' class="total"' if row and row[0] in marks else ""
        out.write(f"<tr{cls}>" + "".join(f"<{tag}>{esc(c)}</{tag}>" for c in row) + "</tr>\n")
    out.write("</table>\n</div>\n")
    return out.getvalue()
