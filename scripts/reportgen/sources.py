"""出处层：sources/*.md 全文渲染，每份开头列出引用它的问题、可跳回详解块。"""
import re

import markdown

from .config import REPORT_DIR, SOURCES_DIR

EXT_BLOCK_RE = re.compile(r'<section class="ext" id="(q-[\w-]+)">')
H3_RE = re.compile(r"<h3>(.*?)</h3>", re.S)
BACKLINK_RE = re.compile(r'<a class="back".*?</a>', re.S)
CITE_RE = re.compile(r'href="#(\d{2}-[\w-]+)"')
TAG_RE = re.compile(r"<[^>]+>")
QNUM_RE = re.compile(r"Q(\d+)")


def cite_map():
    """→ {source 文件 stem: [(问题锚点 id, 问题标题), ...]}，去重后按问题编号排序。"""
    cited = {}
    for f in sorted((REPORT_DIR / "sections").glob("*.html")):
        text = f.read_text(encoding="utf-8")
        marks = list(EXT_BLOCK_RE.finditer(text))
        for i, m in enumerate(marks):
            end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
            block = text[m.end():end]
            h3 = H3_RE.search(block)
            title = TAG_RE.sub("", BACKLINK_RE.sub("", h3.group(1))).strip() if h3 else m.group(1)
            for stem in CITE_RE.findall(block):
                entry = (m.group(1), title)
                if entry not in cited.setdefault(stem, []):
                    cited[stem].append(entry)
    for entries in cited.values():
        entries.sort(key=lambda e: int(QNUM_RE.match(e[1]).group(1)) if QNUM_RE.match(e[1]) else 99)
    return cited


def sources_layer():
    md = markdown.Markdown(extensions=["tables"])
    cited = cite_map()
    out = []
    for f in sorted(SOURCES_DIR.glob("*.md")):
        out.append(f'<section class="src" id="{f.stem}">')
        out.append(f'<p class="meta">sources/{f.name}</p>')
        entries = cited.get(f.stem)
        if entries:
            refs = " · ".join(f'<a href="#{qid}">{title}</a>' for qid, title in entries)
            out.append(f'<p class="meta">被引用于：{refs}</p>')
        out.append(md.reset().convert(f.read_text()))
        out.append("</section>")
    return "\n".join(out)


def tokens():
    return {"SOURCES_LINKED": sources_layer()}
