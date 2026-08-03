"""tests/hidden/citations_test.py

scripts/reportgen/citations.py 的全面契约测试：覆盖 source_index / expand /
cite_sites / references_layer 四个函数的 happy path、每个 error_case、边界
条件（空文本、空目录、重复编号、多源标记、编号去前导零、K 计数递增、
落在 sec 块外的标记）。每个用例自建 tmp_path 下的 sources 目录，不读取
仓库里真实的 sources/ 内容。
"""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from reportgen import citations  # noqa: E402


def _write_source(tmp_path, filename, content):
    """在 tmp_path/sources 下写一份出处 md 文件，返回该 sources 目录路径。"""
    target = tmp_path / "sources" / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target.parent


def _entry_slice(refs, num):
    """截出编号 num 那一条 li 的文本，按下一条 li 的起点（或全文结尾）收尾。

    不按 `</li>` 收尾：details 里的 markdown 正文含列表时会先撞上列表项的 `</li>`。
    """
    start = refs.index(f'<li id="ref-{num}">')
    nxt = refs.find('<li id="ref-', start + 1)
    return refs[start:] if nxt == -1 else refs[start:nxt]


# --------------------------------------------------------------------------
# source_index
# --------------------------------------------------------------------------


def test_citations_source_index_extracts_all_fields(tmp_path):
    """title / outlets（多个）/ urls（去重保序）/ date / stem / num / body_md 全部按契约取值。"""
    content = (
        "# 沿途食宿与杂项价格\n"
        "\n"
        "抓取日期：2026-07-31\n"
        "\n"
        "## 来源 1：Himalayan Hero《徒步尼泊尔全指南》\n"
        "\n"
        "第一次出现 https://himalayanhero.example.com/costs 这里。\n"
        "再次出现同一个链接 https://himalayanhero.example.com/costs 应该去重。\n"
        "\n"
        "## 来源 2：Trekking Nepal 官网\n"
        "\n"
        "另一个链接 https://trekkingnepal.example.com/prices 结尾。\n"
    )
    sources_dir = _write_source(tmp_path, "07-costs-lodging-food.md", content)

    index = citations.source_index(sources_dir)

    entry = index["07"]
    assert entry["num"] == 7
    assert entry["stem"] == "07-costs-lodging-food"
    assert entry["title"] == "沿途食宿与杂项价格"
    assert entry["outlets"] == [
        "Himalayan Hero《徒步尼泊尔全指南》",
        "Trekking Nepal 官网",
    ]
    assert entry["urls"] == [
        "https://himalayanhero.example.com/costs",
        "https://trekkingnepal.example.com/prices",
    ]
    assert entry["date"] == "2026-07-31"
    assert entry["body_md"] == content


def test_citations_source_index_reads_outlets_from_level_three_headings(tmp_path):
    """三级 `### 来源 N：` 也算来源标题——sources/05 与 sources/14 把 `##` 留给主题分节。

    同一文件里二级与三级混用时，两级都收，按出现顺序排列。
    """
    content = (
        "# 小红书中文徒步者实地情报\n"
        "\n"
        "抓取日期：2026-07-31\n"
        "\n"
        "## 进山航班\n"
        "\n"
        "### 来源 1：《EBC 旺季能不能从加都飞卢卡拉》（甲，2026-03-04）\n"
        "\n"
        "正文。\n"
        "\n"
        "### 来源 2：《卢卡拉航班取消免费改直升机》（乙，2025-03-31）\n"
        "\n"
        "正文。\n"
        "\n"
        "## 来源 3：某攻略站聚合\n"
        "\n"
        "正文。\n"
    )
    sources_dir = _write_source(tmp_path, "14-xiaohongshu-field-intel.md", content)

    assert citations.source_index(sources_dir)["14"]["outlets"] == [
        "《EBC 旺季能不能从加都飞卢卡拉》（甲，2026-03-04）",
        "《卢卡拉航班取消免费改直升机》（乙，2025-03-31）",
        "某攻略站聚合",
    ]


def test_citations_source_index_outlets_empty_without_source_headings(tmp_path):
    """文件没有 `## 来源` 标题时 outlets 为空列表，其余字段仍正常解析。"""
    content = (
        "# 无来源标题的文件\n"
        "\n"
        "抓取日期：2026-07-20\n"
        "\n"
        "就是没有来源小标题这一段正文。\n"
    )
    sources_dir = _write_source(tmp_path, "12-kathmandu-city.md", content)

    index = citations.source_index(sources_dir)

    assert index["12"]["outlets"] == []
    assert index["12"]["title"] == "无来源标题的文件"


def test_citations_source_index_date_empty_without_date_line(tmp_path):
    """没有匹配 `(抓取|记录|收到|下载)日期` 的行时 date 为空字符串。"""
    content = "# 没有日期字段的文件\n\n## 来源 1：某处\n\n正文没有提日期信息。\n"
    sources_dir = _write_source(tmp_path, "13-map-apis.md", content)

    index = citations.source_index(sources_dir)

    assert index["13"]["date"] == ""


@pytest.mark.parametrize(
    "date_line",
    [
        "抓取日期：2026-07-31",
        "抓取日期: 2026-07-31",
        "- 记录日期：2026-07-31",
        "- 收到日期: 2026-07-31",
        "- 下载日期: 2026-07-31",
    ],
    ids=["fetch-fullwidth", "fetch-halfwidth", "record", "received", "downloaded"],
)
def test_citations_source_index_accepts_every_date_prefix_and_colon(tmp_path, date_line):
    """四种日期前缀与两种冒号都能取到日期——真实 sources/ 里这几种写法混用。"""
    content = f"# 某份出处\n\n{date_line}\n\n## 来源 1：某处\n\n正文。\n"
    sources_dir = _write_source(tmp_path, "05-guide-porter.md", content)

    assert citations.source_index(sources_dir)["05"]["date"] == "2026-07-31"


def test_citations_source_index_sorted_ascending_by_number(tmp_path):
    """返回的 dict 按编号数字升序排列，与文件写入顺序 / 文件系统遍历顺序无关。"""
    _write_source(tmp_path, "16-a.md", "# Sixteen\n")
    _write_source(tmp_path, "02-b.md", "# Two\n")
    _write_source(tmp_path, "07-c.md", "# Seven\n")
    sources_dir = tmp_path / "sources"

    index = citations.source_index(sources_dir)

    assert list(index.keys()) == ["02", "07", "16"]


def test_citations_source_index_skips_files_with_invalid_filename_prefix(tmp_path):
    """文件名不以两位数字加短横线开头 → 跳过该文件，不进索引（error_case）。"""
    _write_source(tmp_path, "readme.md", "# Readme\n")
    _write_source(tmp_path, "1-single.md", "# Single digit prefix\n")
    _write_source(tmp_path, "ab-notes.md", "# Letters prefix\n")
    _write_source(tmp_path, "07-valid.md", "# 有效文件\n")
    sources_dir = tmp_path / "sources"

    index = citations.source_index(sources_dir)

    assert list(index.keys()) == ["07"]
    assert index["07"]["title"] == "有效文件"


# --------------------------------------------------------------------------
# expand
# --------------------------------------------------------------------------


def test_citations_expand_empty_text_returns_empty():
    """空字符串没有标记可展开，原样返回空字符串。"""
    assert citations.expand("", index={}) == ""


def test_citations_expand_strips_leading_zero_and_counts_occurrences_across_document():
    """N 去前导零；K 按该编号在全文出现的先后独立计数；多源标记共用一个 sup、
    每个条目各自是一个 a；逗号后带空格的写法（`[[16, 07]]`）与不带空格等价。
    """
    index = {"07": {"num": 7}, "16": {"num": 16}}
    text = "A[[07]]B[[16]]C[[07]]D[[16, 07]]E"

    result = citations.expand(text, index=index)

    expected = (
        "A"
        '<sup class="cite"><a id="cite-07-1" href="#ref-07">7</a></sup>'
        "B"
        '<sup class="cite"><a id="cite-16-1" href="#ref-16">16</a></sup>'
        "C"
        '<sup class="cite"><a id="cite-07-2" href="#ref-07">7</a></sup>'
        "D"
        '<sup class="cite">'
        '<a id="cite-16-2" href="#ref-16">16</a>,'
        '<a id="cite-07-3" href="#ref-07">7</a>'
        "</sup>"
        "E"
    )
    assert result == expected


def test_citations_expand_dedups_repeated_number_within_single_marker():
    """同一个 `[[..]]` 里重复的编号只渲染一次（保序去重），K 也只计一次。"""
    index = {"07": {"num": 7}}

    result = citations.expand("重复[[07,07]]结束。", index=index)

    assert result == (
        '重复<sup class="cite"><a id="cite-07-1" href="#ref-07">7</a></sup>结束。'
    )


def test_citations_expand_missing_source_exits():
    """标记里的编号在 source_index 里不存在 → SystemExit，消息形如
    `正文引用了不存在的出处：sources/99`（error_case）。
    """
    index = {"07": {"num": 7}}

    with pytest.raises(SystemExit) as excinfo:
        citations.expand("参见[[99]]。", index=index)

    message = str(excinfo.value)
    assert "正文引用了不存在的出处" in message
    assert "sources/99" in message


@pytest.mark.parametrize(
    "marker",
    ["[[7]]", "[[abc]]"],
    ids=["single-digit", "non-numeric"],
)
def test_citations_expand_malformed_marker_exits(marker):
    """展开后文本里仍有 `[[` 残留（语法写错）→ SystemExit，消息形如
    `citation 标记语法不合法：[[7]]`（error_case）。
    """
    index = {"07": {"num": 7}}
    text = f"前文{marker}后文"

    with pytest.raises(SystemExit) as excinfo:
        citations.expand(text, index=index)

    message = str(excinfo.value)
    assert "citation 标记语法不合法" in message
    assert marker in message


# --------------------------------------------------------------------------
# cite_sites
# --------------------------------------------------------------------------


def test_citations_cite_sites_happy_path_multiple_sections():
    """按 sec 块切分，h3 去标签与回链得标题；同节内重复引用只记一次；
    同一编号在不同节各记一条，按节在文档中出现的顺序排列；sec 块外的标记不计入。
    """
    text = (
        '<section class="sec" id="s1-deal">\n'
        '<h3>1 · Majestic Trails 的套餐值不值<a class="back" href="#summary">↑ 摘要</a></h3>\n'
        "<p>结论句[[07]]，又提一次[[07]]同节内重复只记一次。</p>\n"
        "</section>\n"
        '<section class="sec" id="s2-prep">\n'
        '<h3>2 · 行前准备<a class="back" href="#summary">↑ 摘要</a></h3>\n'
        "<p>装备清单参考[[16]]。</p>\n"
        "</section>\n"
        '<section class="sec" id="s4-route">\n'
        '<h3>4 · 12 天行程与强度<a class="back" href="#summary">↑ 摘要</a></h3>\n'
        "<p>强度参照同一份出处[[07]]。</p>\n"
        "</section>\n"
        "<p>游离在 sec 块之外的标记[[99]]不应计入。</p>\n"
    )

    result = citations.cite_sites(text)

    assert result == {
        "07": [
            ("s1-deal", "1 · Majestic Trails 的套餐值不值"),
            ("s4-route", "4 · 12 天行程与强度"),
        ],
        "16": [("s2-prep", "2 · 行前准备")],
    }


def test_citations_cite_sites_multi_source_marker_records_each_number():
    """一个多源标记 `[[07,16]]` 在同一节内出现时，两个编号各记一条该节。"""
    text = (
        '<section class="sec" id="s3-insurance">\n'
        '<h3>3 · 保险买哪个<a class="back" href="#summary">↑ 摘要</a></h3>\n'
        "<p>结论[[07,16]]。</p>\n"
        "</section>\n"
    )

    result = citations.cite_sites(text)

    assert result == {
        "07": [("s3-insurance", "3 · 保险买哪个")],
        "16": [("s3-insurance", "3 · 保险买哪个")],
    }


@pytest.mark.parametrize(
    "text",
    ["", "<p>没有 section 块，标记[[07]]也不算</p>"],
    ids=["empty-text", "no-sec-block-with-marker"],
)
def test_citations_cite_sites_no_sec_blocks_returns_empty_dict(text):
    """文档里没有任何 sec 块 → 返回空 dict（error_case），空文本同理。"""
    assert citations.cite_sites(text) == {}


# --------------------------------------------------------------------------
# references_layer
# --------------------------------------------------------------------------


def test_citations_references_layer_empty_sources_dir_returns_empty_string(tmp_path):
    """sources 目录为空 → 返回空字符串（error_case）。"""
    sources_dir = tmp_path / "sources"
    sources_dir.mkdir()
    text = (
        '<section class="sec" id="s1-deal">\n'
        "<h3>1 · 标题<a class=\"back\" href=\"#summary\">↑ 摘要</a></h3>\n"
        "<p>正文[[07]]。</p>\n"
        "</section>\n"
    )

    assert citations.references_layer(text, sources_dir) == ""


def test_citations_references_layer_groups_cited_and_uncited(tmp_path):
    """被引用过的编号进第一组；零引用的编号进「数据与方法来源」第二组；
    被引用的条目带 citedby 回链，未被引用的不带。
    """
    _write_source(
        tmp_path,
        "07-costs-lodging-food.md",
        (
            "# 沿途食宿与杂项价格\n"
            "\n"
            "抓取日期：2026-07-31\n"
            "\n"
            "## 来源 1：Himalayan Hero《徒步尼泊尔全指南》\n"
            "\n"
            "正文 https://himalayanhero.example.com/costs 一处链接。\n"
        ),
    )
    _write_source(
        tmp_path,
        "16-agency-quote-majestic-trails.md",
        (
            "# Majestic Trails 报价单\n"
            "\n"
            "记录日期：2026-07-20\n"
            "\n"
            "## 来源 1：Majestic Trails Nepal 官方报价邮件\n"
            "\n"
            "未被正文引用的一份出处。\n"
        ),
    )
    sources_dir = tmp_path / "sources"
    text = (
        '<section class="sec" id="s1-deal">\n'
        '<h3>1 · Majestic Trails 的套餐值不值<a class="back" href="#summary">↑ 摘要</a></h3>\n'
        "<p>结论句[[07]]。</p>\n"
        "</section>\n"
    )

    refs = citations.references_layer(text, sources_dir)

    assert '<li id="ref-07">' in refs
    assert '<li id="ref-16">' in refs
    assert "数据与方法来源" in refs

    slice07 = _entry_slice(refs, "07")
    assert "citedby" in slice07
    assert '<a href="#s1-deal">§1</a>' in slice07

    slice16 = _entry_slice(refs, "16")
    assert "citedby" not in slice16


def test_citations_references_layer_all_cited_sorted_ascending_no_second_group(tmp_path):
    """全部编号都被引用过时不输出「数据与方法来源」组；条目按编号升序排列。"""
    for filename, title in [
        ("02-lukla-flight-fixed-wing.md", "卢卡拉定翼机"),
        ("07-costs-lodging-food.md", "沿途食宿与杂项价格"),
        ("16-agency-quote-majestic-trails.md", "Majestic Trails 报价单"),
    ]:
        _write_source(tmp_path, filename, f"# {title}\n\n抓取日期：2026-07-31\n\n正文。\n")
    sources_dir = tmp_path / "sources"
    text = (
        '<section class="sec" id="s1-deal">\n'
        "<h3>1 · 标题<a class=\"back\" href=\"#summary\">↑ 摘要</a></h3>\n"
        "<p>全部引用一遍[[02,07,16]]。</p>\n"
        "</section>\n"
    )

    refs = citations.references_layer(text, sources_dir)

    assert "数据与方法来源" not in refs
    assert refs.index('id="ref-02"') < refs.index('id="ref-07"') < refs.index('id="ref-16"')


def test_citations_references_layer_citedby_lists_multiple_sections(tmp_path):
    """同一出处被多个节引用时，citedby 回链列出全部被引用的节。"""
    _write_source(
        tmp_path,
        "07-costs-lodging-food.md",
        "# 沿途食宿与杂项价格\n\n抓取日期：2026-07-31\n\n正文。\n",
    )
    sources_dir = tmp_path / "sources"
    text = (
        '<section class="sec" id="s1-deal">\n'
        '<h3>1 · Majestic Trails 的套餐值不值<a class="back" href="#summary">↑ 摘要</a></h3>\n'
        "<p>结论[[07]]。</p>\n"
        "</section>\n"
        '<section class="sec" id="s2-prep">\n'
        '<h3>2 · 行前准备<a class="back" href="#summary">↑ 摘要</a></h3>\n'
        "<p>再次引用同一出处[[07]]。</p>\n"
        "</section>\n"
    )

    refs = citations.references_layer(text, sources_dir)

    assert '<a href="#s1-deal">§1</a>' in refs
    assert '<a href="#s2-prep">§2</a>' in refs


def test_citations_references_layer_entry_format_matches_template(tmp_path):
    """条目字面格式：refnum · 标题 · outlets 以 ` · ` 连接 · 抓取日期 · urls 渲染成 a 链接。"""
    _write_source(
        tmp_path,
        "07-costs-lodging-food.md",
        (
            "# 沿途食宿与杂项价格\n"
            "\n"
            "抓取日期：2026-07-31\n"
            "\n"
            "## 来源 1：Himalayan Hero《徒步尼泊尔全指南》\n"
            "\n"
            "正文。\n"
            "\n"
            "## 来源 2：Trekking Nepal 官网\n"
            "\n"
            "更多正文 https://trekkingnepal.example.com/prices 一处链接。\n"
        ),
    )
    sources_dir = tmp_path / "sources"
    text = (
        '<section class="sec" id="s1-deal">\n'
        "<h3>1 · 标题<a class=\"back\" href=\"#summary\">↑ 摘要</a></h3>\n"
        "<p>结论[[07]]。</p>\n"
        "</section>\n"
    )

    refs = citations.references_layer(text, sources_dir)

    expected_prefix = (
        '<li id="ref-07"><span class="refnum">[7]</span> '
        "<b>沿途食宿与杂项价格</b> · "
        "Himalayan Hero《徒步尼泊尔全指南》 · Trekking Nepal 官网 · "
        "2026-07-31 · "
        '<a href="https://trekkingnepal.example.com/prices">trekkingnepal.example.com</a>'
    )
    assert expected_prefix in refs


def test_citations_references_layer_joins_multiple_urls_with_separator(tmp_path):
    """一份出处有多个链接时，urls 之间同样用 ` · ` 连接，每个各自是一个 a 标签。"""
    _write_source(
        tmp_path,
        "09-packing-gear-rental.md",
        (
            "# 装备清单与加德满都租赁\n"
            "\n"
            "抓取日期：2026-07-31\n"
            "\n"
            "## 来源 1：三个装备清单聚合\n"
            "\n"
            "- https://a.example.com/list\n"
            "- https://b.example.com/list\n"
        ),
    )
    sources_dir = tmp_path / "sources"
    text = (
        '<section class="sec" id="s2-prep">\n'
        '<h3>2 · 行前准备<a class="back" href="#summary">↑ 摘要</a></h3>\n'
        "<p>装备结论[[09]]。</p>\n"
        "</section>\n"
    )

    refs = citations.references_layer(text, sources_dir)

    assert (
        '<a href="https://a.example.com/list">a.example.com</a> · '
        '<a href="https://b.example.com/list">b.example.com</a>'
    ) in refs


def test_citations_references_layer_dedups_urls_by_domain(tmp_path):
    """同一站点的多条链接按域名折成一条，链到该域名首次出现的那个 URL。

    sources/14 的 19 条小红书链接同属一个站点，这条规则让它的条目从一长串压成一条。
    """
    _write_source(
        tmp_path,
        "14-xiaohongshu-field-intel.md",
        (
            "# 小红书中文徒步者实地情报\n"
            "\n"
            "抓取日期：2026-07-31\n"
            "\n"
            "## 来源 1：笔记甲\n"
            "\n"
            "https://www.xiaohongshu.com/note/aaa\n"
            "https://www.xiaohongshu.com/note/bbb\n"
            "https://www.xiaohongshu.com/note/ccc\n"
        ),
    )
    sources_dir = tmp_path / "sources"
    text = (
        '<section class="sec" id="s5-cost">\n'
        '<h3>5 · 花多少钱<a class="back" href="#summary">↑ 摘要</a></h3>\n'
        "<p>实付价[[14]]。</p>\n"
        "</section>\n"
    )

    refs = citations.references_layer(text, sources_dir)

    assert refs.count("www.xiaohongshu.com</a>") == 1
    assert '<a href="https://www.xiaohongshu.com/note/aaa">www.xiaohongshu.com</a>' in refs
    assert "note/bbb" not in refs.split("<details>")[0]


def test_citations_references_layer_truncates_outlets_beyond_three(tmp_path):
    """outlets 超过 3 个时只列前 3 个，后面接「等 N 个来源」，N 是总数。"""
    heads = "".join(f"## 来源 {i}：出处方 {i}\n\n正文。\n\n" for i in range(1, 6))
    _write_source(
        tmp_path,
        "07-costs-lodging-food.md",
        f"# 沿途食宿与杂项价格\n\n抓取日期：2026-07-31\n\n{heads}",
    )
    sources_dir = tmp_path / "sources"
    text = (
        '<section class="sec" id="s5-cost">\n'
        '<h3>5 · 花多少钱<a class="back" href="#summary">↑ 摘要</a></h3>\n'
        "<p>价格[[07]]。</p>\n"
        "</section>\n"
    )

    head = citations.references_layer(text, sources_dir).split("<details>")[0]

    assert "出处方 1 · 出处方 2 · 出处方 3 · 等 5 个来源" in head
    assert "出处方 4" not in head


def test_citations_references_layer_omits_cited_group_when_nothing_referenced(tmp_path):
    """正文一个标记都没有时，第一组连列表一起不输出，只留「数据与方法来源」一组。"""
    _write_source(
        tmp_path,
        "11-gpx-track.md",
        "# GPX 轨迹文件\n\n- 下载日期: 2026-07-31\n\n正文。\n",
    )
    sources_dir = tmp_path / "sources"
    text = (
        '<section class="sec" id="s4-route">\n'
        '<h3>4 · 12 天行程与强度<a class="back" href="#summary">↑ 摘要</a></h3>\n'
        "<p>这一节没有放任何角标。</p>\n"
        "</section>\n"
    )

    refs = citations.references_layer(text, sources_dir)

    assert refs.count('<ol class="refs">') == 1
    assert "数据与方法来源" in refs
    assert '<li id="ref-11">' in refs
    assert "citedby" not in refs


def test_citations_references_layer_details_contains_rendered_markdown_body(tmp_path):
    """`<details><summary>要点</summary>` 包裹要点段转换后的 HTML，
    markdown 语法（如行首 `- `）被转换掉，要点内容仍可读到。
    """
    _write_source(
        tmp_path,
        "07-x.md",
        "# 出处标题\n\n抓取日期：2026-07-31\n\n## 要点\n\n- 正文一段说明。\n\n## 来源 1：某处\n\n一手记录。\n",
    )
    sources_dir = tmp_path / "sources"
    text = (
        '<section class="sec" id="s1-deal">\n'
        "<h3>1 · 标题<a class=\"back\" href=\"#summary\">↑ 摘要</a></h3>\n"
        "<p>结论[[07]]。</p>\n"
        "</section>\n"
    )

    refs = citations.references_layer(text, sources_dir)

    assert "<details>" in refs
    assert "<summary>要点</summary>" in refs
    assert "- 正文一段说明" not in refs
    assert "正文一段说明" in refs
    assert "一手记录" not in refs


# --------------------------------------------------------------------------
# _extract_excerpt
# --------------------------------------------------------------------------


_EXCERPT_SOURCE = (
    "# 保险与高山救援\n"
    "\n"
    "抓取日期：2026-07-31\n"
    "\n"
    "## 要点\n"
    "\n"
    "- 保游尊享覆盖 6000 m 以下徒步，含直升机搜救。\n"
    "- ÖAV 会籍年费 EUR 96，山地救援不限海拔。\n"
    "\n"
    "## 来源 1：保游官网\n"
    "\n"
    "这一整段一手记录只留在仓库里供核对。\n"
)

_EXCERPT_EXPECTED = (
    "- 保游尊享覆盖 6000 m 以下徒步，含直升机搜救。\n"
    "- ÖAV 会籍年费 EUR 96，山地救援不限海拔。"
)

_EXCERPT_TEXT = (
    '<section class="sec" id="s3-insurance">\n'
    '<h3>3 · 保险买哪个<a class="back" href="#summary">↑ 摘要</a></h3>\n'
    "<p>结论句[[19]]。</p>\n"
    "</section>\n"
)


def test_excerpt_extract_happy_path_between_headings():
    """`## 要点` 与下一个二级标题之间的正文原样返回，首尾空行去掉。"""
    assert citations._extract_excerpt(_EXCERPT_SOURCE) == _EXCERPT_EXPECTED


@pytest.mark.parametrize(
    "next_heading",
    ["# 另起的一级标题", "## 来源 1：某处"],
    ids=["level-one", "level-two"],
)
def test_excerpt_extract_terminates_at_same_or_higher_heading(next_heading):
    """同级（`## `）与更高级（`# `）的标题都收尾，标题之后的内容不进摘录。"""
    text = (
        "# 出处标题\n"
        "\n"
        "## 要点\n"
        "\n"
        "- 唯一一条要点。\n"
        "\n"
        f"{next_heading}\n"
        "\n"
        "标题之后的内容不进摘录。\n"
    )

    assert citations._extract_excerpt(text) == "- 唯一一条要点。"


def test_excerpt_extract_runs_to_end_of_file():
    """`## 要点` 是文件最后一节时取到文件末尾，末尾的空行去掉（error_case）。"""
    text = (
        "# 出处标题\n"
        "\n"
        "抓取日期：2026-07-31\n"
        "\n"
        "## 要点\n"
        "\n"
        "- 全文最后一节就是要点。\n"
        "- 第二条要点。\n"
        "\n"
        "\n"
    )

    assert citations._extract_excerpt(text) == (
        "- 全文最后一节就是要点。\n- 第二条要点。"
    )


def test_excerpt_extract_preserves_bullets_bold_and_inline_links():
    """小节里的 bullet、粗体、行内链接原样返回，交给 markdown 渲染。"""
    body = (
        "- **必买**：[保游尊享](https://example.com/baoyou) 覆盖 6000 m 以下。\n"
        "- 直升机救援赔付上限 USD 100,000，**先垫付后理赔**。\n"
        "- 普通旅游险把徒步列为除外责任，见 [条款页](https://example.com/terms)。\n"
    )
    text = f"# 保险\n\n## 要点\n\n{body}\n## 来源 1：某处\n\n一手记录全文。\n"

    assert citations._extract_excerpt(text) == body.rstrip("\n")


@pytest.mark.parametrize(
    "text",
    [
        "",
        "# 只有正文的文件\n\n抓取日期：2026-07-31\n\n## 来源 1：某处\n\n正文。\n",
        "# 出处标题\n\n正文里写到 ## 要点 三个字但不在行首。\n\n## 来源 1：某处\n\n正文。\n",
    ],
    ids=["empty-text", "no-section", "inline-mention-only"],
)
def test_excerpt_extract_returns_empty_when_section_absent(text):
    """文本没有 `## 要点` 行时返回空字符串，由调用方决定是否报错（error_case）。"""
    assert citations._extract_excerpt(text) == ""


def test_excerpt_extract_empty_when_next_heading_follows_immediately():
    """`## 要点` 后面紧跟另一个二级标题时小节为空，返回空字符串。"""
    text = "# 出处标题\n## 要点\n## 来源 1：某处\n\n正文。\n"

    assert citations._extract_excerpt(text) == ""


def test_excerpt_extract_section_above_top_level_title():
    """`## 要点` 出现在一级标题之前也能取到，取到那个一级标题为止。"""
    text = "## 要点\n\n- 要点写在一级标题之前也能取到。\n\n# 出处标题\n\n正文。\n"

    assert citations._extract_excerpt(text) == "- 要点写在一级标题之前也能取到。"


def test_excerpt_extract_keeps_inner_blank_lines_and_drops_outer():
    """小节内部的空行保留，标题之后与下一个标题之前的空行去掉。"""
    text = (
        "# 出处标题\n"
        "\n"
        "## 要点\n"
        "\n"
        "\n"
        "- 第一条要点。\n"
        "\n"
        "- 第二条要点。\n"
        "\n"
        "\n"
        "## 来源 1：某处\n"
        "\n"
        "正文。\n"
    )

    assert citations._extract_excerpt(text) == "- 第一条要点。\n\n- 第二条要点。"


def test_excerpt_extract_keeps_level_three_subheading_inside():
    """三级标题比 `## 要点` 低一级，不收尾，连同其后内容一起留在小节里。"""
    text = (
        "# 出处标题\n"
        "\n"
        "## 要点\n"
        "\n"
        "- 第一条要点。\n"
        "\n"
        "### 细分\n"
        "\n"
        "- 第二条要点。\n"
        "\n"
        "## 来源 1：某处\n"
        "\n"
        "正文。\n"
    )

    assert citations._extract_excerpt(text) == (
        "- 第一条要点。\n\n### 细分\n\n- 第二条要点。"
    )


def test_excerpt_extract_uses_first_section_when_repeated():
    """文件里出现多个 `## 要点` 时取首个小节。"""
    text = (
        "# 出处标题\n"
        "\n"
        "## 要点\n"
        "\n"
        "- 首个小节的要点。\n"
        "\n"
        "## 来源 1：某处\n"
        "\n"
        "正文。\n"
        "\n"
        "## 要点\n"
        "\n"
        "- 后面重复出现的小节。\n"
    )

    assert citations._extract_excerpt(text) == "- 首个小节的要点。"


@pytest.mark.parametrize(
    "heading",
    ["## 对话要点（原文摘录，中文概括）", "## 三、要点", "## 要点摘录", "## 要点与结论"],
    ids=["prefixed", "numbered", "suffixed", "extended"],
)
def test_excerpt_extract_requires_exact_heading(heading):
    """标题必须整行就是 `## 要点`。前后带别的字的二级标题都不算，返回空字符串。

    sources/17 里真实存在一个 `## 对话要点（原文摘录，中文概括）`，
    子串匹配会把那一整节当成摘录取走。
    """
    text = f"# 出处标题\n\n{heading}\n\n- 这一节不是要点摘录。\n\n## 来源 1：某处\n\n正文。\n"

    assert citations._extract_excerpt(text) == ""


def test_excerpt_extract_tolerates_trailing_whitespace_on_heading():
    """`## 要点` 行尾的空白不影响识别。"""
    text = "# 出处标题\n\n## 要点   \n\n- 行尾有空格也认。\n\n## 来源 1：某处\n\n正文。\n"

    assert citations._extract_excerpt(text) == "- 行尾有空格也认。"


# --------------------------------------------------------------------------
# source_index 的 excerpt 键与构建期闸门
# --------------------------------------------------------------------------


def test_excerpt_source_index_adds_excerpt_and_keeps_body_md(tmp_path):
    """条目新增 excerpt 键；body_md 仍是整份文件全文，其余字段照旧。"""
    sources_dir = _write_source(tmp_path, "19-insurance-rescue.md", _EXCERPT_SOURCE)

    entry = citations.source_index(sources_dir)["19"]

    assert entry["excerpt"] == _EXCERPT_EXPECTED
    assert entry["body_md"] == _EXCERPT_SOURCE
    assert entry["title"] == "保险与高山救援"
    assert entry["outlets"] == ["保游官网"]
    assert entry["date"] == "2026-07-31"


def test_excerpt_source_index_excerpt_equals_extract_helper(tmp_path):
    """excerpt 的值等于对该文件全文调用 _extract_excerpt 的结果。"""
    sources_dir = _write_source(tmp_path, "19-insurance-rescue.md", _EXCERPT_SOURCE)

    entry = citations.source_index(sources_dir)["19"]

    assert entry["excerpt"] == citations._extract_excerpt(entry["body_md"])


def test_excerpt_source_index_each_file_gets_its_own_excerpt(tmp_path):
    """多份出处各取各的要点段，互不串味。"""
    _write_source(
        tmp_path,
        "02-lukla-flight-fixed-wing.md",
        "# 卢卡拉定翼机\n\n## 要点\n\n- 加都直飞单程 USD 220。\n\n## 来源 1：某处\n\n正文。\n",
    )
    _write_source(
        tmp_path,
        "07-costs-lodging-food.md",
        "# 沿途食宿与杂项价格\n\n## 要点\n\n- 茶屋双人间 NPR 800 一间。\n",
    )
    sources_dir = tmp_path / "sources"

    index = citations.source_index(sources_dir)

    assert index["02"]["excerpt"] == "- 加都直飞单程 USD 220。"
    assert index["07"]["excerpt"] == "- 茶屋双人间 NPR 800 一间。"


def test_excerpt_source_index_missing_section_yields_empty_excerpt(tmp_path):
    """source_index 只做提取：缺 `## 要点` 的文件拿到空字符串，不在这里报错。"""
    sources_dir = _write_source(
        tmp_path,
        "07-costs-lodging-food.md",
        "# 沿途食宿与杂项价格\n\n抓取日期：2026-07-31\n\n## 来源 1：某处\n\n正文没有要点小节。\n",
    )

    assert citations.source_index(sources_dir)["07"]["excerpt"] == ""


def test_excerpt_check_excerpts_missing_section_exits(tmp_path):
    """某份 sources 缺 `## 要点` → check_excerpts SystemExit，消息点名是哪一份（error_case）。"""
    sources_dir = _write_source(
        tmp_path,
        "07-costs-lodging-food.md",
        "# 沿途食宿与杂项价格\n\n抓取日期：2026-07-31\n\n## 来源 1：某处\n\n正文没有要点小节。\n",
    )

    with pytest.raises(SystemExit) as excinfo:
        citations.check_excerpts(citations.source_index(sources_dir))

    message = str(excinfo.value)
    assert "sources/07" in message
    assert "## 要点" in message


def test_excerpt_check_excerpts_exits_when_any_one_of_many_lacks_section(tmp_path):
    """目录里只要有一份缺 `## 要点`，闸门就报错退出并点名那一份。"""
    _write_source(tmp_path, "02-a.md", "# A\n\n## 要点\n\n- 有要点。\n")
    _write_source(tmp_path, "07-b.md", "# B\n\n## 要点\n\n- 也有要点。\n")
    _write_source(tmp_path, "16-c.md", "# C\n\n## 来源 1：某处\n\n这一份没有要点小节。\n")
    sources_dir = tmp_path / "sources"

    with pytest.raises(SystemExit) as excinfo:
        citations.check_excerpts(citations.source_index(sources_dir))

    message = str(excinfo.value)
    assert "sources/16" in message
    assert "sources/02" not in message
    assert "sources/07" not in message


def test_excerpt_check_excerpts_empty_section_counts_as_missing(tmp_path):
    """`## 要点` 存在但小节为空，与完全没有该小节同等对待，闸门照样拦。"""
    sources_dir = _write_source(
        tmp_path,
        "07-costs-lodging-food.md",
        "# 沿途食宿与杂项价格\n\n## 要点\n\n## 来源 1：某处\n\n正文。\n",
    )

    with pytest.raises(SystemExit) as excinfo:
        citations.check_excerpts(citations.source_index(sources_dir))

    assert "sources/07" in str(excinfo.value)


def test_excerpt_check_excerpts_names_every_offending_file(tmp_path):
    """多份都缺要点时，消息把它们全部点名，一次跑完就能改齐。"""
    _write_source(tmp_path, "02-a.md", "# A\n\n## 要点\n\n- 有要点。\n")
    _write_source(tmp_path, "07-b.md", "# B\n\n## 来源 1：某处\n\n没有要点。\n")
    _write_source(tmp_path, "16-c.md", "# C\n\n## 来源 1：某处\n\n也没有要点。\n")
    sources_dir = tmp_path / "sources"

    with pytest.raises(SystemExit) as excinfo:
        citations.check_excerpts(citations.source_index(sources_dir))

    message = str(excinfo.value)
    assert "sources/07" in message
    assert "sources/16" in message


def test_excerpt_check_excerpts_passes_when_all_present(tmp_path):
    """全部条目都有非空要点时返回 None，不抛异常。"""
    _write_source(tmp_path, "02-a.md", "# A\n\n## 要点\n\n- 有要点。\n")
    _write_source(tmp_path, "07-b.md", "# B\n\n## 要点\n\n- 也有要点。\n")
    sources_dir = tmp_path / "sources"

    assert citations.check_excerpts(citations.source_index(sources_dir)) is None


def test_excerpt_check_excerpts_empty_index_passes(tmp_path):
    """空 index 没有可校验的条目，返回 None。"""
    assert citations.check_excerpts({}) is None


def test_excerpt_source_index_ignores_files_with_invalid_prefix(tmp_path):
    """文件名不带两位编号前缀的文件被跳过，它没有要点小节也不触发闸门。"""
    _write_source(tmp_path, "readme.md", "# 说明文件\n\n不带编号前缀，也没有要点小节。\n")
    _write_source(
        tmp_path,
        "07-costs-lodging-food.md",
        "# 沿途食宿与杂项价格\n\n## 要点\n\n- 茶屋双人间 NPR 800 一间。\n",
    )
    sources_dir = tmp_path / "sources"

    index = citations.source_index(sources_dir)

    assert list(index.keys()) == ["07"]
    assert index["07"]["excerpt"] == "- 茶屋双人间 NPR 800 一间。"


def test_excerpt_source_index_empty_dir_returns_empty_dict(tmp_path):
    """空的 sources 目录没有可校验的文件，返回空 dict 而不是报错。"""
    sources_dir = tmp_path / "sources"
    sources_dir.mkdir()

    assert citations.source_index(sources_dir) == {}


# --------------------------------------------------------------------------
# _render_entry 渲染要点摘录
# --------------------------------------------------------------------------


def test_excerpt_render_entry_details_summary_is_excerpt_label(tmp_path):
    """折叠块的 summary 文案是「要点」。"""
    sources_dir = _write_source(tmp_path, "19-insurance-rescue.md", _EXCERPT_SOURCE)

    refs = citations.references_layer(_EXCERPT_TEXT, sources_dir)

    assert "<details>" in refs
    assert "<summary>要点</summary>" in refs


def test_excerpt_render_entry_renders_excerpt_markdown(tmp_path):
    """要点段经 markdown 渲染进 details：bullet 成 li、粗体成 strong、行内链接成 a。"""
    content = (
        "# 保险与高山救援\n"
        "\n"
        "抓取日期：2026-07-31\n"
        "\n"
        "## 要点\n"
        "\n"
        "- **必买**：[保游尊享](https://example.com/baoyou) 覆盖 6000 m 以下。\n"
        "- 直升机救援赔付上限 USD 100,000。\n"
        "\n"
        "## 来源 1：保游官网\n"
        "\n"
        "要点之外的这段一手记录不进 details。\n"
    )
    sources_dir = _write_source(tmp_path, "19-insurance-rescue.md", content)

    entry = _entry_slice(citations.references_layer(_EXCERPT_TEXT, sources_dir), "19")

    assert "<li><strong>必买</strong>" in entry
    assert '<a href="https://example.com/baoyou">保游尊享</a>' in entry
    assert "直升机救援赔付上限 USD 100,000。" in entry
    assert "- **必买**" not in entry
    assert "要点之外的这段一手记录不进 details。" not in entry


def test_excerpt_render_entry_omits_raw_body_outside_excerpt(tmp_path):
    """要点之外的一手记录正文不进报告。"""
    sources_dir = _write_source(tmp_path, "19-insurance-rescue.md", _EXCERPT_SOURCE)

    refs = citations.references_layer(_EXCERPT_TEXT, sources_dir)

    assert "ÖAV 会籍年费 EUR 96，山地救援不限海拔。" in refs
    assert "这一整段一手记录只留在仓库里供核对" not in refs


def test_excerpt_render_entry_keeps_header_and_citedby(tmp_path):
    """头部信息（编号、标题、来源方、日期）与「引用于 §N」回链保持现状不变。"""
    sources_dir = _write_source(tmp_path, "19-insurance-rescue.md", _EXCERPT_SOURCE)

    refs = citations.references_layer(_EXCERPT_TEXT, sources_dir)

    assert (
        '<li id="ref-19"><span class="refnum">[19]</span> '
        "<b>保险与高山救援</b> · 保游官网 · 2026-07-31"
    ) in refs
    assert "citedby" in refs
    assert '<a href="#s3-insurance">§3</a>' in refs


def test_excerpt_render_entry_uncited_entry_also_shows_excerpt(tmp_path):
    """零引用的条目同样折叠要点摘录，只是不带 citedby 回链。"""
    _write_source(tmp_path, "19-insurance-rescue.md", _EXCERPT_SOURCE)
    _write_source(
        tmp_path,
        "11-gpx-track.md",
        (
            "# GPX 轨迹文件\n"
            "\n"
            "- 下载日期: 2026-07-31\n"
            "\n"
            "## 要点\n"
            "\n"
            "- 轨迹 3,291 个点，单程 58.3 km。\n"
            "\n"
            "## 来源 1：Real World Adventures\n"
            "\n"
            "一手记录全文。\n"
        ),
    )
    sources_dir = tmp_path / "sources"

    refs = citations.references_layer(_EXCERPT_TEXT, sources_dir)
    slice11 = _entry_slice(refs, "11")

    assert "citedby" not in slice11
    assert "<summary>要点</summary>" in slice11
    assert "轨迹 3,291 个点，单程 58.3 km。" in slice11


def test_excerpt_render_entry_omits_details_when_excerpt_empty(tmp_path):
    """excerpt 为空的条目不输出折叠块，头部信息照常渲染。

    闸门在 build() 拦住这种文件，渲染层遇到时给出干净的降级：没有内容就不给折叠块。
    """
    sources_dir = _write_source(
        tmp_path,
        "07-costs-lodging-food.md",
        "# 沿途食宿与杂项价格\n\n抓取日期：2026-07-31\n\n## 来源 1：某处\n\n没有要点小节。\n",
    )
    text = (
        '<section class="sec" id="s1-deal">\n'
        '<h3>1 · 标题<a class="back" href="#summary">↑ 摘要</a></h3>\n'
        "<p>结论[[07]]。</p>\n"
        "</section>\n"
    )

    entry = _entry_slice(citations.references_layer(text, sources_dir), "07")

    assert "<details>" not in entry
    assert "沿途食宿与杂项价格" in entry
    assert '<a href="#s1-deal">§1</a>' in entry
