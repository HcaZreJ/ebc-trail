"""附录 A 六张 CSV 全量表 + 附录 B sources/*.md 全文。"""
import markdown

from .config import SOURCES_DIR
from .csvio import blocks, read_csv
from .tables import table


def sources_appendix():
    md = markdown.Markdown(extensions=["tables"])
    out = []
    for f in sorted(SOURCES_DIR.glob("*.md")):
        out.append(f'<section class="src" id="{f.stem}">')
        out.append(f'<p class="meta">sources/{f.name}</p>')
        out.append(md.reset().convert(f.read_text()))
        out.append("</section>")
    return "\n".join(out)


def tokens():
    return {
        "TBL_ITINERARY_FULL": table(read_csv("itinerary.csv")),
        "TBL_COSTS_FULL": table(read_csv("cost-breakdown.csv")),
        "TBL_PACKING_FULL": table(read_csv("packing-list.csv")),
        "TBL_TRACKSTATS_FULL": "\n".join(table(b) for b in blocks(read_csv("route-track-stats.csv"))),
        "TBL_ROUTE_SEGMENTS_FULL": table(read_csv("route-segments.csv")),
        "TBL_QUOTE_CMP_FULL": table(read_csv("quote-comparison.csv")),
        "APPENDIX_SOURCES": sources_appendix(),
    }
