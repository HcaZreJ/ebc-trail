"""tests/visible/citations_test.py

样例测试（work unit「citation 引擎」）：只覆盖 source_index / expand /
references_layer 的主 happy path，作为实现时的形状参考。完整的错误用例、
边界条件与 cite_sites 见 tests/hidden/citations_test.py。
"""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from reportgen import citations  # noqa: E402


def _write_source(tmp_path, filename, content):
    """在 tmp_path 下建一个 sources 目录并写一份出处 md 文件。"""
    target = tmp_path / "sources" / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target.parent


def test_citations_source_index_happy_path(tmp_path):
    """扫一份格式规整的出处 md，取出 title / outlets / date / stem / num。"""
    sources_dir = _write_source(
        tmp_path,
        "07-costs-lodging-food.md",
        (
            "# 沿途食宿与杂项价格\n"
            "\n"
            "抓取日期：2026-07-31\n"
            "\n"
            "## 来源 1：Himalayan Hero《徒步尼泊尔全指南》\n"
            "\n"
            "正文引用 https://himalayanhero.example.com/costs 一个链接。\n"
        ),
    )

    index = citations.source_index(sources_dir)

    assert index["07"]["num"] == 7
    assert index["07"]["stem"] == "07-costs-lodging-food"
    assert index["07"]["title"] == "沿途食宿与杂项价格"
    assert index["07"]["outlets"] == ["Himalayan Hero《徒步尼泊尔全指南》"]
    assert index["07"]["urls"] == ["https://himalayanhero.example.com/costs"]
    assert index["07"]["date"] == "2026-07-31"


def test_citations_expand_single_source_marker():
    """单源标记展开为 sup/a 结构，编号去前导零，K 从 1 起计。"""
    index = {"07": {"num": 7}}

    result = citations.expand("结论落地[[07]]。", index=index)

    assert result == (
        '结论落地<sup class="cite">'
        '<a id="cite-07-1" href="#ref-07">7</a>'
        "</sup>。"
    )


def test_citations_references_layer_happy_path(tmp_path):
    """一份出处被正文引用一次时，references_layer 产出该条目并带 citedby 回链。"""
    sources_dir = _write_source(
        tmp_path,
        "07-costs-lodging-food.md",
        (
            "# 沿途食宿与杂项价格\n"
            "\n"
            "抓取日期：2026-07-31\n"
            "\n"
            "## 要点\n"
            "\n"
            "- 茶屋双人间旺季 NPR 800 一间。\n"
            "\n"
            "## 来源 1：Himalayan Hero《徒步尼泊尔全指南》\n"
            "\n"
            "正文内容。\n"
        ),
    )
    text = (
        '<section class="sec" id="s1-deal">\n'
        '<h3>1 · Majestic Trails 的套餐值不值<a class="back" href="#summary">↑ 摘要</a></h3>\n'
        "<p>结论句[[07]]。</p>\n"
        "</section>\n"
    )

    refs = citations.references_layer(text, sources_dir)

    assert '<li id="ref-07">' in refs
    assert '<span class="refnum">[7]</span>' in refs
    assert "沿途食宿与杂项价格" in refs
    assert '<a href="#s1-deal">§1</a>' in refs
    assert "<summary>要点</summary>" in refs


# --------------------------------------------------------------------------
# `## 要点` 摘录
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


def test_excerpt_extract_happy_path():
    """`## 要点` 到下一个二级标题之间的正文原样返回，首尾空行去掉。"""
    assert citations._extract_excerpt(_EXCERPT_SOURCE) == _EXCERPT_EXPECTED


def test_excerpt_source_index_exposes_excerpt_key(tmp_path):
    """每个条目新增 excerpt 键取 `## 要点` 段，body_md 仍是整份文件全文。"""
    sources_dir = _write_source(tmp_path, "19-insurance-rescue.md", _EXCERPT_SOURCE)

    entry = citations.source_index(sources_dir)["19"]

    assert entry["excerpt"] == _EXCERPT_EXPECTED
    assert entry["body_md"] == _EXCERPT_SOURCE


def test_excerpt_references_layer_details_shows_excerpt(tmp_path):
    """References 条目折叠的是要点摘录，不是一手记录全文。"""
    sources_dir = _write_source(tmp_path, "19-insurance-rescue.md", _EXCERPT_SOURCE)
    text = (
        '<section class="sec" id="s3-insurance">\n'
        '<h3>3 · 保险买哪个<a class="back" href="#summary">↑ 摘要</a></h3>\n'
        "<p>结论句[[19]]。</p>\n"
        "</section>\n"
    )

    refs = citations.references_layer(text, sources_dir)

    assert "<summary>要点</summary>" in refs
    assert "ÖAV 会籍年费 EUR 96，山地救援不限海拔。" in refs
    assert "这一整段一手记录只留在仓库里供核对" not in refs
