"""把 report/shell.html 的 include 指令与 {{TOKEN}} 占位解析成自包含的报告 HTML。

装载顺序的唯一事实源是 shell.html 里 include 指令的出现顺序：
`<style>` 内的 CSS include 顺序即层叠顺序，`<main>` 内的 section include 顺序即章节顺序。
"""
import re
from datetime import date
from pathlib import Path

from .config import REPORT_DIR

SHELL = REPORT_DIR / "shell.html"
OUT = REPORT_DIR / "EBC-report.html"

# 两种写法等价，各自在宿主语言里是合法注释：
#   HTML 正文用   <!-- include: sections/s1-visa.html -->
#   <style> 内用  /* include: styles/base.css */
INCLUDE_RE = re.compile(r"^\s*(?:<!--|/\*)\s*include:\s*(\S+?)\s*(?:-->|\*/)\s*$")

# 被 include 覆盖率检查扫描的目录，相对 report/
MANAGED_DIRS = ("styles", "sections")

TOKEN_RE = re.compile(r"\{\{(\w+)\}\}")


def parse_includes(shell_text):
    """→ [(行号从 1 起, include 路径)]，按在 shell 里出现的顺序。"""
    found = []
    for lineno, line in enumerate(shell_text.split("\n"), start=1):
        m = INCLUDE_RE.match(line)
        if m:
            found.append((lineno, m.group(1)))
    return found


def resolve_includes(shell_text, base_dir):
    """把每条 include 指令所在的整行替换为目标文件内容（去掉文件末尾换行）。

    目标文件缺失或同一路径被 include 两次时 SystemExit。
    """
    directives = parse_includes(shell_text)

    seen = set()
    dupes = []
    for _, rel in directives:
        if rel in seen and rel not in dupes:
            dupes.append(rel)
        seen.add(rel)
    if dupes:
        raise SystemExit("include 指令重复装载同一文件：" + "、".join(dupes))

    lines = shell_text.split("\n")
    for lineno, rel in directives:
        target = Path(base_dir) / rel
        if not target.is_file():
            raise SystemExit(f"shell.html 第 {lineno} 行的 include 目标不存在：{rel}")
        body = target.read_text(encoding="utf-8")
        if body.endswith("\n"):
            body = body[:-1]
        lines[lineno - 1] = body
    return "\n".join(lines)


def check_orphans(shell_text, base_dir):
    """MANAGED_DIRS 下存在却没被任何 include 装载的文件 → SystemExit。

    点文件（.DS_Store 之类的系统产物）不算报告内容，跳过。
    """
    loaded = {rel for _, rel in parse_includes(shell_text)}
    orphans = []
    for sub in MANAGED_DIRS:
        directory = Path(base_dir) / sub
        if not directory.is_dir():
            continue
        for p in sorted(directory.iterdir()):
            if p.name.startswith("."):
                continue
            if p.is_file() and f"{sub}/{p.name}" not in loaded:
                orphans.append(f"{sub}/{p.name}")
    if orphans:
        raise SystemExit("以下文件没有被 shell.html 装载：" + "、".join(orphans))
    return None


def check_token_usage(text, tokens):
    """tokens 里存在却在 text 中没被引用的 token 名 → SystemExit。"""
    unused = [name for name in tokens if "{{" + name + "}}" not in text]
    if unused:
        raise SystemExit("以下 token 没有被任何章节引用：" + "、".join(unused))
    return None


def substitute(text, tokens):
    """把 {{NAME}} 替换为 tokens[NAME]；替换后仍有 {{...}} 残留 → SystemExit。"""
    out = TOKEN_RE.sub(lambda m: tokens[m.group(1)] if m.group(1) in tokens else m.group(0), text)
    if "{{" in out:
        left = TOKEN_RE.search(out)
        where = left.group(1) if left else out[out.find("{{"):out.find("{{") + 40]
        raise SystemExit(f"装配后仍有未解析的 token：{where!r}")
    return out


def collect_tokens():
    """合并全部 provider 的 tokens()，键为不带花括号的裸 token 名。"""
    from . import costs, figures, packing, quotes, route, sources

    merged = {"BUILD_DATE": date.today().isoformat()}
    for provider in (figures, costs, quotes, route, packing, sources):
        for name, value in provider.tokens().items():
            if name in merged:
                raise SystemExit(f"token 名冲突：{name} 同时由 {provider.__name__} 提供")
            merged[name] = value
    return merged


def build():
    """跑完整链路并写出 OUT，返回 OUT 路径。"""
    shell_text = SHELL.read_text(encoding="utf-8")
    text = resolve_includes(shell_text, REPORT_DIR)
    check_orphans(shell_text, REPORT_DIR)
    tokens = collect_tokens()
    check_token_usage(text, tokens)
    text = substitute(text, tokens)
    OUT.write_text(text, encoding="utf-8")
    return OUT
