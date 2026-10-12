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
#
# 卷标题用上游的课程原名, 结构词 Course 按翻译规范保留英文, 与
# docs/book/README.md 的课程一览表保持一致.
COURSES = [
    # 经典教程系列, 正文取自上游 GitBook 的 pages/ 目录
    ("x86-course", "x86 Course"),
    ("arm32-course-1", "ARM-32 Course 1"),
    ("arm32-course-2", "ARM-32 Course 2"),
    ("x64-course", "x64 Course"),
    ("arm64-course", "ARM-64 Course"),
    # 嵌入式系列, 正文取自上游各自独立的仓库
    ("rp2350-rust", "RP2350 Rust Course"),
    ("rp2350-arm-asm", "RP2350 ARM Assembler Course"),
    ("rp2350-riscv-asm", "RP2350 RISC-V Assembler Course"),
    ("avr-assembler", "AVR Assembler Course"),
    ("wasm", "Wasm Course"),
    ("embedded-wasm-uart", "Embedded Wasm UART Echo Course"),
    ("embedded-wasm-blinky", "Embedded Wasm Blinky Course"),
    ("embedded-wasm-button", "Embedded Wasm Button Course"),
    ("embedded-wasm-servo", "Embedded Wasm Servo Course"),
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


# ---------------------------------------------------------------------------
# 原生 HTML 归一化
#
# 经典教程那 5 个卷是从 GitBook 抓下来的, 正文里有大量原生 HTML:
# 代码装在 <pre> 里 (内含 highlight.js 的 <span>), 配图是 <img>, 还有
# src="about:blank" 的失效 <iframe> 嵌入. pandoc 遇到原生 HTML 会整段
# 丢弃, 出电子书会直接少掉代码与插图, 所以渲染前必须先归一成 markdown.
# ---------------------------------------------------------------------------

_SPAN = re.compile(r"</?span\b[^>]*>")
_PRE_OPEN = re.compile(r"<pre\b[^>]*>")
_PRE_CLOSE = re.compile(r"</pre\s*>")
# 带 slate 包裹的图片, 允许 div 与 img 之间有换行
_IMG_DIV = re.compile(
    r'<div[^>]*class="[^"]*slate[^"]*"[^>]*>\s*<img[^>]*src="([^"]+)"[^>]*/?>\s*</div>',
    re.S | re.I)
_IMG_ANY = re.compile(r'<img\b[^>]*src="([^"]+)"[^>]*/?>', re.I)
# 原文里本来就用 markdown 图片语法的少量图片, 路径同样是 /imgs/ 开头
_MD_IMG = re.compile(r"!\[([^\]]*)\]\((/imgs/[^)]+)\)")
_IFRAME = re.compile(r"<iframe\b([^>]*)>(.*?)</iframe\s*>", re.S | re.I)
_IFRAME_SELF = re.compile(r"<iframe\b([^>]*)/>", re.I)


def _img_markdown(src: str, img_prefix: str) -> str:
    """把本地图片地址改成可用的相对路径, 并转成 markdown 图片.

    绝对 URL (http/https, 或 protocol-relative) 原样保留, 不能改成本地文件.
    """
    if src.startswith(("http://", "https://", "//", "data:")):
        name = src.rsplit("/", 1)[-1]
        return f"![{name}]({src})"
    name = src.rsplit("/", 1)[-1]
    return f"![{name}]({img_prefix}{name})"


def _iframe_repl(m: re.Match, img_prefix: str) -> str:
    """失效嵌入换成普通链接, 保留标题与真实地址."""
    attrs = m.group(1)
    url = re.search(r'data-delayed-url="([^"]+)"', attrs)
    title = re.search(r'title="([^"]*)"', attrs)
    if not url:
        return ""
    text = title.group(1) if title and title.group(1).strip() else "嵌入内容"
    return f"[{text}]({html_unescape(url.group(1))})"


def html_unescape(s: str) -> str:
    return (s.replace("&amp;", "&").replace("&lt;", "<")
             .replace("&gt;", ">").replace("&quot;", '"'))


def normalize_html(text: str, img_prefix: str) -> str:
    """把抓取页里的原生 HTML 归一成 markdown.

    img_prefix 是图片目录相对当前文件的路径前缀, 电子书与站点取值不同.
    """
    # 1. <pre> 代码块换成围栏代码块, 并去掉 highlight.js 的 span
    text = _PRE_OPEN.sub("```\n", text)
    text = _PRE_CLOSE.sub("\n```", text)
    text = _SPAN.sub("", text)

    # 2. 图片: 先处理带 slate 包裹的整行形式, 再兜底处理裸 img,
    #    最后处理原本就是 markdown 语法的少量图片
    text = _IMG_DIV.sub(lambda m: _img_markdown(m.group(1), img_prefix), text)
    text = _IMG_ANY.sub(lambda m: _img_markdown(m.group(1), img_prefix), text)
    text = _MD_IMG.sub(
        lambda m: f"![{m.group(1)}]({img_prefix}{m.group(2).rsplit('/', 1)[-1]})", text)

    # 3. 失效嵌入换成链接
    text = _IFRAME.sub(lambda m: _iframe_repl(m, img_prefix), text)
    text = _IFRAME_SELF.sub(lambda m: _iframe_repl(m, img_prefix), text)
    return text


def clean_for_render(text: str, img_prefix: str) -> str:
    """渲染前的完整清洗: 先去 HTML, 再剥锚点, 最后转义占位符."""
    return clean(normalize_html(text, img_prefix))


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
