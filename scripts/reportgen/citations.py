"""citation 引擎：`[[NN]]` 标记解析、展开与 references 层渲染。

契约见 .claude/plans/report-slim-citations.md 的 T1 work-unit spec。
"""
import re
from pathlib import Path

import markdown

from . import config

FILENAME_RE = re.compile(r"^(\d{2})-")
TITLE_RE = re.compile(r"^#\s+(.+)")
OUTLET_HEADING_RE = re.compile(r"^#{2,3} 来源.*?[:：]\s*(.+)$", re.M)
DATE_RE = re.compile(r"(?:抓取|记录|收到|下载)日期[:：]\s*(\d{4}-\d{2}-\d{2})")
URL_RE = re.compile(r"https?://[^\s，。、；：！？（）\"'`」』》】]+")

EXCERPT_HEADING_RE = re.compile(r"^## 要点[^\S\n]*$", re.M)
NEXT_HEADING_RE = re.compile(r"^#{1,2} ", re.M)

MARKER_RE = re.compile(r"\[\[(\d{2}(?:\s*,\s*\d{2})*)\]\]")
LEFTOVER_RE = re.compile(r"\[\[[^\]]*\]\]")

SEC_RE = re.compile(r'<section class="sec" id="([\w-]+)">')
H3_RE = re.compile(r"<h3>(.*?)</h3>", re.S)
BACK_RE = re.compile(r'<a class="back".*?</a>', re.S)
TAG_RE = re.compile(r"<[^>]+>")
SEC_NUM_RE = re.compile(r"\d+")


def _split_numbers(group):
    """把 `07` / `07,16` / `07, 16` 拆成保序去重的编号列表。"""
    seen = []
    for num in re.split(r"\s*,\s*", group):
        if num not in seen:
            seen.append(num)
    return seen


def _extract_excerpt(text):
    """取首个整行为 `## 要点` 的小节正文，到下一个 `^#{1,2} ` 标题或文件末尾为止。

    标题行整行必须是 `## 要点`（行尾空白可以有）；找不到时返回空字符串。
    小节内的 bullet、粗体、行内链接原样返回，交给 markdown 渲染。
    """
    m = EXCERPT_HEADING_RE.search(text)
    if not m:
        return ""
    nxt = NEXT_HEADING_RE.search(text, m.end())
    body = text[m.end() : nxt.start()] if nxt else text[m.end() :]
    lines = body.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def check_excerpts(index):
    """任一条目缺 `## 要点` 摘录 → SystemExit，消息点名是哪几份文件。"""
    missing = [
        f"sources/{key}"
        for key, entry in index.items()
        if not (entry.get("excerpt") or "").strip()
    ]
    if missing:
        raise SystemExit("以下出处缺少 ## 要点 小节：" + "、".join(missing))
    return None


def source_index(sources_dir=None):
    directory = Path(sources_dir) if sources_dir is not None else config.SOURCES_DIR
    entries = {}
    for path in sorted(directory.glob("*.md")):
        m = FILENAME_RE.match(path.name)
        if not m:
            continue
        key = m.group(1)
        text = path.read_text(encoding="utf-8")
        title_m = TITLE_RE.match(text)
        title = title_m.group(1).strip() if title_m else ""
        outlets = [o.strip() for o in OUTLET_HEADING_RE.findall(text)]
        urls = []
        for found in URL_RE.findall(text):
            if found not in urls:
                urls.append(found)
        date_m = DATE_RE.search(text)
        date = date_m.group(1) if date_m else ""
        entries[key] = {
            "num": int(key),
            "stem": path.stem,
            "title": title,
            "outlets": outlets,
            "urls": urls,
            "date": date,
            "body_md": text,
            "excerpt": _extract_excerpt(text),
        }
    return dict(sorted(entries.items(), key=lambda kv: kv[1]["num"]))


def expand(text, index=None):
    if index is None:
        index = source_index()
    counters = {}

    def repl(m):
        links = []
        for num in _split_numbers(m.group(1)):
            if num not in index:
                raise SystemExit(f"正文引用了不存在的出处：sources/{num}")
            counters[num] = counters.get(num, 0) + 1
            k = counters[num]
            n = str(int(num))
            links.append(f'<a id="cite-{num}-{k}" href="#ref-{num}">{n}</a>')
        return '<sup class="cite">' + ",".join(links) + "</sup>"

    result = MARKER_RE.sub(repl, text)
    if "[[" in result:
        m = LEFTOVER_RE.search(result)
        marker = m.group(0) if m else result[result.index("[[") :][:20]
        raise SystemExit(f"citation 标记语法不合法：{marker}")
    return result


def cite_sites(text):
    result = {}
    marks = list(SEC_RE.finditer(text))
    for m in marks:
        sec_id = m.group(1)
        close = text.find("</section>", m.end())
        end = close if close != -1 else len(text)
        block = text[m.end() : end]
        h3 = H3_RE.search(block)
        if h3:
            title = TAG_RE.sub("", BACK_RE.sub("", h3.group(1))).strip()
        else:
            title = sec_id
        nums_in_block = []
        for marker in MARKER_RE.finditer(block):
            for num in _split_numbers(marker.group(1)):
                if num not in nums_in_block:
                    nums_in_block.append(num)
        for num in nums_in_block:
            result.setdefault(num, []).append((sec_id, title))
    return result


def _outlets_segment(outlets):
    """呈现层压缩：最多列 3 个来源，超出时补一句「等 N 个来源」。"""
    if not outlets:
        return ""
    seg = " · ".join(outlets[:3])
    if len(outlets) > 3:
        seg += f" · 等 {len(outlets)} 个来源"
    return seg


def _url_domain(url):
    return re.sub(r"^https?://", "", url).split("/", 1)[0]


def _urls_segment(urls):
    """呈现层压缩：按域名去重，最多列 4 个站点，超出时补一句「等 N 个站点」。"""
    if not urls:
        return ""
    by_domain = {}
    for u in urls:
        domain = _url_domain(u)
        if domain not in by_domain:
            by_domain[domain] = u
    domains = list(by_domain.items())
    seg = " · ".join(f'<a href="{u}">{d}</a>' for d, u in domains[:4])
    if len(domains) > 4:
        seg += f" · 等 {len(domains)} 个站点"
    return seg


def _render_entry(key, entry, sites, md):
    num = str(entry["num"])
    parts = [f'<b>{entry["title"]}</b>']
    outlets_seg = _outlets_segment(entry["outlets"])
    if outlets_seg:
        parts.append(outlets_seg)
    if entry["date"]:
        parts.append(entry["date"])
    urls_seg = _urls_segment(entry["urls"])
    if urls_seg:
        parts.append(urls_seg)
    head = f'<li id="ref-{key}"><span class="refnum">[{num}]</span> ' + " · ".join(parts)
    cited = sites.get(key)
    citedby = ""
    if cited:
        links = " · ".join(
            f'<a href="#{sec_id}">§{SEC_NUM_RE.search(sec_id).group()}</a>'
            for sec_id, _ in cited
        )
        citedby = f'<p class="citedby">引用于 {links}</p>'
    excerpt = entry.get("excerpt") or ""
    details = ""
    if excerpt:
        details = (
            "<details><summary>要点</summary>"
            + md.reset().convert(excerpt)
            + "</details>"
        )
    return head + citedby + details + "</li>"


def references_layer(text, sources_dir=None):
    directory = sources_dir if sources_dir is not None else config.SOURCES_DIR
    index = source_index(directory)
    if not index:
        return ""
    sites = cite_sites(text)
    md = markdown.Markdown(extensions=["tables"])

    cited_keys = [k for k in index if k in sites]
    uncited_keys = [k for k in index if k not in sites]

    out = []
    if cited_keys:
        out.append('<ol class="refs">')
        out.extend(_render_entry(k, index[k], sites, md) for k in cited_keys)
        out.append("</ol>")
    if uncited_keys:
        out.append("<h4>数据与方法来源</h4>")
        out.append('<ol class="refs">')
        out.extend(_render_entry(k, index[k], sites, md) for k in uncited_keys)
        out.append("</ol>")
    return "\n".join(out)
