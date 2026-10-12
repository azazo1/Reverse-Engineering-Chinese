#!/usr/bin/env python3
"""书稿的共用编排定义.

build_book.py (电子书) 与 build_site.py (阅读站点) 共用这里的卷序,
标题与内容清洗规则. 加一门课只需改这一处, 两边的目录就同步了.

注意: 这两个脚本的调用方 (.github/workflows/ 下) 都把这个文件列进了
paths, 改它也会触发重建.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
BOOK = DOCS / "book"

TITLE = "逆向工程中文教程"
SUBTITLE = "mytechnotalent/Reverse-Engineering 中文版"
REPO_URL = "https://github.com/azazo1/Reverse-Engineering-Chinese"

# 书稿编排顺序: (目录名, 卷标题). 电子书与阅读站点都按这个次序展开.
COURSES = [
    ("rp2350-rust", "RP2350 Rust 课程"),
    ("rp2350-arm-asm", "RP2350 ARM 汇编课程"),
    ("rp2350-riscv-asm", "RP2350 RISC-V 汇编课程"),
    ("avr-assembler", "AVR 汇编课程"),
    ("wasm", "Wasm 课程"),
    ("embedded-wasm-uart", "嵌入式 Wasm UART 回显课程"),
    ("embedded-wasm-blinky", "嵌入式 Wasm 闪烁课程"),
    ("embedded-wasm-button", "嵌入式 Wasm 按键课程"),
    ("embedded-wasm-servo", "嵌入式 Wasm 舵机课程"),
]

# 需要保留的 HTML 标签, 其余尖括号按伪代码占位符处理
HTML_TAGS = {
    "br", "img", "a", "p", "div", "span", "em", "strong", "code", "pre",
    "table", "tr", "td", "th", "thead", "tbody", "ul", "ol", "li",
    "h1", "h2", "h3", "h4", "h5", "h6", "hr", "sup", "sub", "kbd",
    "blockquote", "details", "summary", "video", "source", "iframe", "input",
}

_ANCHOR = re.compile(r"\[([^\]]+)\]\(#[^)]*\)")
_TAG = re.compile(r"<([^<>\n]{1,40})>")


def _walk(text: str, sub) -> str:
    """按行应用替换, 跳过围栏代码块内部."""
    out, fenced = [], False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            out.append(line)
            continue
        out.append(line if fenced else sub(line))
    return "\n".join(out)


def strip_anchor_links(text: str) -> str:
    """把 `[文字](#锚点)` 还原成纯文字.

    各篇自带的目录在合订本 (或合订站) 里没有意义, 因为书本身就有总目录,
    站点也有侧边栏; 而锚点合并后会重名或失配.
    """
    return _walk(text, lambda line: _ANCHOR.sub(r"\1", line))


def escape_placeholders(text: str) -> str:
    """转义 `<frame>` `<u8>` 这类伪代码占位符.

    markdown 会把尖括号当 HTML 标签: 轻则内容被吞掉不显示, 重则 mdBook
    报 unclosed tag 直接中止渲染. 只转义白名单外的标签名, 保留 <br>.
    """
    def repl(m: re.Match) -> str:
        inner = m.group(1)
        name = inner.lstrip("/").split()[0].lower() if inner.split() else ""
        if name.rstrip("/") in HTML_TAGS:
            return m.group(0)
        return "&lt;" + inner + "&gt;"

    return _walk(text, lambda line: _TAG.sub(repl, line))


def clean(text: str) -> str:
    """合订前的统一清洗. 只作用于生成物, 不改动 docs/ 下的原稿."""
    return escape_placeholders(strip_anchor_links(text))


def chapter_sort_key(path: Path):
    """按文件名里的数字排序, 没有数字时退回文件名."""
    m = re.search(r"(\d+)", path.stem)
    return (int(m.group(1)) if m else 10**6, path.stem)


def first_heading(path: Path) -> str:
    """取文件第一个一级标题, 用作目录项文字."""
    for line in path.read_text(encoding="utf-8").split("\n"):
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def iter_courses():
    """展开卷序, 产出 (目录名, 卷标题, 正文文件, 附录文件).

    正文按章号排序, `re.md` 这类逆向分析篇单独归到附录, 排在正文之后.
    """
    for dirname, volume in COURSES:
        d = BOOK / dirname
        if not d.is_dir():
            continue
        main = sorted((p for p in d.glob("*.md") if not p.name.startswith("re.")),
                      key=chapter_sort_key)
        extra = sorted(d.glob("re.md"))
        if main or extra:
            yield dirname, volume, main, extra
