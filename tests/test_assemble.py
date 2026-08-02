"""scripts/reportgen/assemble.py 的契约测试。

覆盖 include 指令解析 / 展开、孤儿文件检查、token 使用率检查与 token 替换。
每个用例自建 tmp_path 下的 base_dir，不读取仓库里真实的 report/ 内容。
"""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from reportgen import assemble  # noqa: E402


def _write(base_dir, rel_path, content):
    """在 base_dir 下写一个文件（自动建父目录），返回该文件路径。"""
    target = pathlib.Path(base_dir) / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


# --------------------------------------------------------------------------
# parse_includes
# --------------------------------------------------------------------------


def test_assemble_parse_includes_both_syntaxes_in_order():
    """两种等价写法都识别，返回 (1 起行号, 路径) 且顺序 = 出现顺序。

    同时覆盖：指令在首行、指令在末行、指令前后允许空白、非指令行忽略。
    """
    shell = (
        "/* include: styles/base.css */\n"
        "<body>\n"
        "  <!-- include: sections/s1-visa.html -->  \n"
        "<p>plain line</p>\n"
        "<!-- include: sections/s2-route.html -->"
    )

    assert assemble.parse_includes(shell) == [
        (1, "styles/base.css"),
        (3, "sections/s1-visa.html"),
        (5, "sections/s2-route.html"),
    ]


def test_assemble_parse_includes_no_directives_returns_empty():
    """空字符串与完全没有 include 指令的文本都返回空列表。"""
    assert assemble.parse_includes("") == []
    assert assemble.parse_includes("<html>\n  <p>no directives here</p>\n</html>") == []
    assert assemble.parse_includes("   \n\t\n") == []


@pytest.mark.parametrize(
    "line",
    [
        "text before <!-- include: sections/s1.html -->",
        "<!-- include: sections/s1.html --> text after",
        "<!-- include: sections/s1.html sections/s2.html -->",
        "<!-- include sections/s1.html -->",
    ],
    ids=["leading-content", "trailing-content", "path-with-space", "missing-colon"],
)
def test_assemble_parse_includes_rejects_lines_that_are_not_pure_directives(line):
    """正则锚定整行：行内还有别的内容、路径含空白、缺 `include:` 都不算指令。"""
    assert assemble.parse_includes(line) == []


# --------------------------------------------------------------------------
# resolve_includes
# --------------------------------------------------------------------------


def test_assemble_resolve_includes_replaces_whole_line_with_file_body(tmp_path):
    """整行（含缩进）被目标文件内容替换，文件末尾一个换行被去掉，其余行逐字不动。"""
    _write(tmp_path, "styles/base.css", "body{margin:0}\n")
    _write(tmp_path, "sections/s1.html", "<h1>S1</h1>\n")
    _write(tmp_path, "sections/s2.html", "<h2>S2</h2>\n")

    shell = (
        "/* include: styles/base.css */\n"
        "<body>\n"
        "  <!-- include: sections/s1.html -->\n"
        "<!-- include: sections/s2.html -->"
    )

    result = assemble.resolve_includes(shell, tmp_path)

    assert result == "body{margin:0}\n<body>\n<h1>S1</h1>\n<h2>S2</h2>"
    assert "include:" not in result


def test_assemble_resolve_includes_text_without_directives_is_unchanged(tmp_path):
    """空字符串与无指令文本原样返回。"""
    assert assemble.resolve_includes("", tmp_path) == ""

    plain = "<html>\n  <p>no directives</p>\n</html>"
    assert assemble.resolve_includes(plain, tmp_path) == plain


@pytest.mark.parametrize(
    "file_body, inserted",
    [
        ("X\n", "X"),
        ("X", "X"),
        ("X\n\n", "X\n"),
        ("", ""),
    ],
    ids=["one-trailing-newline", "no-trailing-newline", "two-trailing-newlines", "empty-file"],
)
def test_assemble_resolve_includes_strips_exactly_one_trailing_newline(
    tmp_path, file_body, inserted
):
    """只去掉目标文件末尾的一个换行：无换行不动、两个换行留一个、空文件插空行。"""
    _write(tmp_path, "sections/s.html", file_body)
    shell = "before\n<!-- include: sections/s.html -->\nafter"

    assert assemble.resolve_includes(shell, tmp_path) == "before\n" + inserted + "\nafter"


def test_assemble_resolve_includes_missing_target_exits_with_line_and_path(tmp_path):
    """目标文件不存在 → SystemExit，消息里同时出现 shell 行号与该路径。"""
    _write(tmp_path, "styles/base.css", "body{}\n")
    shell = (
        "/* include: styles/base.css */\n"
        "<body>\n"
        "<p>a</p>\n"
        "<p>b</p>\n"
        "<p>c</p>\n"
        "<p>d</p>\n"
        "<!-- include: sections/absent.html -->\n"
        "</body>"
    )

    with pytest.raises(SystemExit) as excinfo:
        assemble.resolve_includes(shell, tmp_path)

    message = str(excinfo.value)
    assert "sections/absent.html" in message
    assert "7" in message


def test_assemble_resolve_includes_duplicate_path_exits(tmp_path):
    """同一路径被 include 两次 → SystemExit，消息里出现该路径。"""
    _write(tmp_path, "styles/base.css", "body{}\n")
    _write(tmp_path, "sections/s1.html", "<h1>S1</h1>\n")
    shell = (
        "/* include: styles/base.css */\n"
        "<!-- include: sections/s1.html -->\n"
        "<!-- include: sections/s1.html -->"
    )

    with pytest.raises(SystemExit) as excinfo:
        assemble.resolve_includes(shell, tmp_path)

    assert "sections/s1.html" in str(excinfo.value)


def test_assemble_resolve_includes_does_not_expand_nested_directives(tmp_path):
    """被 include 的文件内容里的 include 指令按普通文本插入，不递归展开。"""
    _write(tmp_path, "styles/base.css", "BASE_CSS_BODY\n")
    _write(tmp_path, "sections/s1.html", "<!-- include: styles/base.css -->\n")
    shell = "<body>\n<!-- include: sections/s1.html -->\n</body>"

    result = assemble.resolve_includes(shell, tmp_path)

    assert result == "<body>\n<!-- include: styles/base.css -->\n</body>"
    assert "BASE_CSS_BODY" not in result


# --------------------------------------------------------------------------
# check_orphans
# --------------------------------------------------------------------------


def test_assemble_check_orphans_returns_none_when_all_files_loaded(tmp_path):
    """MANAGED_DIRS 下每个文件都被 include 装载时静默返回 None。"""
    _write(tmp_path, "styles/base.css", "body{}\n")
    _write(tmp_path, "styles/print.css", "@media print{}\n")
    _write(tmp_path, "sections/s1.html", "<h1>S1</h1>\n")
    shell = (
        "/* include: styles/base.css */\n"
        "/* include: styles/print.css */\n"
        "<!-- include: sections/s1.html -->"
    )

    assert assemble.check_orphans(shell, tmp_path) is None


def test_assemble_check_orphans_lists_unloaded_files(tmp_path):
    """styles/ 与 sections/ 里没被装载的文件 → SystemExit，消息里列出这些文件名。"""
    _write(tmp_path, "styles/base.css", "body{}\n")
    _write(tmp_path, "styles/forgotten.css", "a{}\n")
    _write(tmp_path, "sections/s1.html", "<h1>S1</h1>\n")
    _write(tmp_path, "sections/stale.html", "<h9>stale</h9>\n")
    shell = "/* include: styles/base.css */\n<!-- include: sections/s1.html -->"

    with pytest.raises(SystemExit) as excinfo:
        assemble.check_orphans(shell, tmp_path)

    message = str(excinfo.value)
    assert "forgotten.css" in message
    assert "stale.html" in message


def test_assemble_check_orphans_ignores_dotfiles(tmp_path):
    """点文件（.DS_Store 之类的系统产物）不算孤儿，只有正常文件参与覆盖率检查。"""
    _write(tmp_path, "styles/base.css", "body{}\n")
    _write(tmp_path, "styles/.DS_Store", "\x00binary junk\n")
    _write(tmp_path, "sections/s1.html", "<h1>S1</h1>\n")
    _write(tmp_path, "sections/.DS_Store", "\x00binary junk\n")
    shell = "/* include: styles/base.css */\n<!-- include: sections/s1.html -->"

    assert assemble.check_orphans(shell, tmp_path) is None


def test_assemble_check_orphans_tolerates_missing_managed_dirs(tmp_path):
    """styles/ 与 sections/ 不存在时视为没有文件，不报错。"""
    assert assemble.check_orphans("", tmp_path) is None
    assert assemble.check_orphans("<html></html>", tmp_path) is None


# --------------------------------------------------------------------------
# check_token_usage
# --------------------------------------------------------------------------


def test_assemble_check_token_usage_returns_none_when_all_referenced(tmp_path):
    """每个 token 都以 {{NAME}} 出现在 text 里时静默返回 None；空 tokens 也返回 None。"""
    text = "cost {{TOTAL_COST}} / days {{DAY_COUNT}} / again {{TOTAL_COST}}"
    tokens = {"TOTAL_COST": "$1,200", "DAY_COUNT": "12"}

    assert assemble.check_token_usage(text, tokens) is None
    assert assemble.check_token_usage("", {}) is None


def test_assemble_check_token_usage_lists_unreferenced_tokens(tmp_path):
    """tokens 里存在但 text 里没被引用的 token → SystemExit，消息里列出这些名字。"""
    text = "only {{USED_TOKEN}} appears here"
    tokens = {"USED_TOKEN": "u", "LONELY_ONE": "a", "LONELY_TWO": ""}

    with pytest.raises(SystemExit) as excinfo:
        assemble.check_token_usage(text, tokens)

    message = str(excinfo.value)
    assert "LONELY_ONE" in message
    assert "LONELY_TWO" in message


# --------------------------------------------------------------------------
# substitute
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text, tokens, expected",
    [
        (
            "Total {{TOTAL_COST}} for {{DAY_COUNT}} days; total again {{TOTAL_COST}}",
            {"TOTAL_COST": "$1,200", "DAY_COUNT": "12"},
            "Total $1,200 for 12 days; total again $1,200",
        ),
        ("prefix{{EMPTY_NOTE}}suffix", {"EMPTY_NOTE": ""}, "prefixsuffix"),
        ("", {}, ""),
        ("no placeholders at all", {"UNUSED_TOKEN": "x"}, "no placeholders at all"),
    ],
    ids=["repeated-and-multiple", "empty-value", "empty-text", "no-placeholder"],
)
def test_assemble_substitute_replaces_every_occurrence(text, tokens, expected):
    """每个 {{NAME}} 都换成 tokens[NAME]，重复出现全部替换，空值合法。"""
    assert assemble.substitute(text, tokens) == expected


def test_assemble_substitute_unresolved_token_exits():
    """替换后仍残留 {{...}} → SystemExit，消息里出现第一个未解析的 token 名。"""
    text = "head {{MISSING_FIRST}} mid {{KNOWN}} tail {{MISSING_SECOND}}"

    with pytest.raises(SystemExit) as excinfo:
        assemble.substitute(text, {"KNOWN": "k"})

    assert "MISSING_FIRST" in str(excinfo.value)


def test_assemble_substitute_non_strict_leaves_unresolved_tokens_in_place():
    """strict=False 时未解析的 {{...}} 原样留在结果里、不报错。

    装配分两阶段：先替换六个 provider 的 token，此时 {{REFERENCES}} 还没有值，
    要等 citations 拿着这份文本建完引用图才能渲染，所以第一阶段必须容忍它残留。
    """
    text = "head {{KNOWN}} mid {{REFERENCES}} tail"

    out = assemble.substitute(text, {"KNOWN": "k"}, strict=False)

    assert out == "head k mid {{REFERENCES}} tail"


@pytest.mark.parametrize(
    "tokens",
    [
        {"OUTER": "left {{INNER_NAME}} right"},
        {"OUTER": "left {{INNER_NAME}} right", "INNER_NAME": "deep"},
    ],
    ids=["inner-not-a-token", "inner-is-a-token"],
)
def test_assemble_substitute_does_not_reexpand_token_values(tokens):
    """token 值里的 {{...}} 字样原样插入、不做二次替换，因此被残留检查报出。"""
    with pytest.raises(SystemExit) as excinfo:
        assemble.substitute("body {{OUTER}} end", tokens)

    assert "INNER_NAME" in str(excinfo.value)
