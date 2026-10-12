#!/usr/bin/env python3
"""把 docs/ 下的中文内容组装成 mdBook 站点, 供在线阅读.

产出 .tmp/site/ (mdBook 源) 与 site/ (渲染后的静态站).
入口: uv run --no-project python scripts/build_site.py

mdBook 需要一份 SUMMARY.md 描述目录树, 所以先把内容铺到 .tmp/site/src/,
再调用 mdbook build. 站点布局与上游那个 GitBook 站点一致: 左侧目录,
全文搜索, 章节内上一页/下一页.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
BOOK = DOCS / "book"
STAGE = ROOT / ".tmp" / "site"
OUT = ROOT / "site"

TITLE = "逆向工程中文教程"

# 与 build_book.py 保持同一编排顺序
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

CALIBRE_HINTS = [
    "/Applications/calibre.app/Contents/MacOS/ebook-convert",
    "/opt/calibre/ebook-convert",
]


def configure_output_encoding() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        except (AttributeError, OSError):
            pass


def log(msg: str) -> None:
    print(msg, flush=True)


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-20:]
        raise RuntimeError("命令失败 (%d): %s\n%s" % (proc.returncode, " ".join(cmd), "\n".join(tail)))
    return proc


def has(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def find_mdbook() -> str | None:
    """优先 PATH, 其次 .tmp/tools (本地测试时下载的)."""
    if has("mdbook"):
        return "mdbook"
    local = ROOT / ".tmp" / "tools" / "mdbook"
    if local.is_file():
        return str(local)
    return None


def chapter_sort_key(path: Path):
    m = re.search(r"(\d+)", path.stem)
    return (int(m.group(1)) if m else 10**6, path.stem)


def first_heading(path: Path) -> str:
    """取文件第一个一级标题作为目录项文字."""
    for line in path.read_text(encoding="utf-8").split("\n"):
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def strip_anchor_links(text: str) -> str:
    """把 `[文字](#锚点)` 还原成纯文字.

    各篇自带的目录锚点在合订站里会重名或失配, 而 mdBook 自带侧边栏与搜索,
    这些手写目录没有意义.
    """
    out, fenced = [], False
    pat = re.compile(r"\[([^\]]+)\]\(#[^)]*\)")
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            out.append(line)
            continue
        out.append(line if fenced else pat.sub(r"\1", line))
    return "\n".join(out)


# 需要保留的 HTML 标签, 其余尖括号按占位符处理
HTML_TAGS = {
    "br", "img", "a", "p", "div", "span", "em", "strong", "code", "pre",
    "table", "tr", "td", "th", "thead", "tbody", "ul", "ol", "li",
    "h1", "h2", "h3", "h4", "h5", "h6", "hr", "sup", "sub", "kbd",
    "blockquote", "details", "summary", "video", "source", "iframe", "input",
}


def escape_placeholders(text: str) -> str:
    """转义 `<frame>` `<u8>` 这类伪代码占位符.

    上游代码里用尖括号表示占位, 但 markdown 会把它们当成 HTML 标签:
    轻则被吞掉不显示, 重则像 mdBook 那样报 unclosed tag 并中止渲染.
    只转义白名单外的标签名, 保留 <br> 这类真正的 HTML.
    """
    def repl(m: re.Match) -> str:
        inner = m.group(1)
        name = inner.lstrip("/").split()[0].lower() if inner.split() else ""
        if name.rstrip("/") in HTML_TAGS:
            return m.group(0)
        return "&lt;" + inner + "&gt;"

    out, fenced = [], False
    pat = re.compile(r"<([^<>\n]{1,40})>")
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            out.append(line)
            continue
        out.append(line if fenced else pat.sub(repl, line))
    return "\n".join(out)


def clean(text: str) -> str:
    """站点专用的内容清洗, 不改动 docs/ 下的原稿."""
    return escape_placeholders(strip_anchor_links(text))


def assemble() -> list[str]:
    """铺内容到 STAGE/src, 返回 SUMMARY.md 的行."""
    if STAGE.exists():
        shutil.rmtree(STAGE)
    src = STAGE / "src"
    src.mkdir(parents=True)

    summary: list[str] = ["# 目录", ""]

    # 首页
    intro = BOOK / "README.md"
    if intro.exists():
        (src / "README.md").write_text(
            clean(intro.read_text(encoding="utf-8")), encoding="utf-8"
        )
    else:
        (src / "README.md").write_text(f"# {TITLE}\n", encoding="utf-8")
    summary += ["# 总览", "", "- [书稿目录](README.md)", ""]

    chapters = 0
    for dirname, volume in COURSES:
        d = BOOK / dirname
        if not d.is_dir():
            continue
        files = sorted((p for p in d.glob("*.md") if not p.name.startswith("re.")),
                       key=chapter_sort_key)
        res = sorted(d.glob("re.md"))
        if not files and not res:
            continue

        summary.append(f"# {volume}")
        summary.append("")

        # 各篇内容拷进 src, 用课程目录名分层, 避免同名文件互相覆盖
        for f in files + res:
            rel = f"{dirname}/{f.name}"
            (src / dirname).mkdir(exist_ok=True)
            (src / rel).write_text(
                clean(f.read_text(encoding="utf-8")), encoding="utf-8"
            )
            summary.append(f"- [{first_heading(f)}]({rel})")
            chapters += 1
        summary.append("")

    courses = DOCS / "courses.md"
    if courses.exists():
        (src / "courses.md").write_text(
            clean(courses.read_text(encoding="utf-8")), encoding="utf-8"
        )
        summary += ["# 附录", "", "- [课程总索引](courses.md)", ""]

    (src / "SUMMARY.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    log(f"  铺开 {chapters} 篇 -> {src.relative_to(ROOT)}")
    return summary


def write_config() -> None:
    (STAGE / "book.toml").write_text(
        f"""[book]
title = "{TITLE}"
description = "mytechnotalent/Reverse-Engineering 的中文版"
language = "zh-CN"
src = "src"

[output.html]
default-theme = "light"
preferred-dark-theme = "navy"
no-section-label = true
git-repository-url = "https://github.com/azazo1/Reverse-Engineering-Chinese"
edit-url-template = "https://github.com/azazo1/Reverse-Engineering-Chinese/edit/main/{{{{ path }}}}"

[output.html.search]
enable = true
limit-results = 30

[output.html.fold]
enable = true
level = 1
""",
        encoding="utf-8",
    )


def main() -> int:
    configure_output_encoding()
    ap = argparse.ArgumentParser(description="构建在线阅读站点")
    ap.add_argument("--serve", action="store_true", help="本地起服务预览")
    args = ap.parse_args()

    mdbook = find_mdbook()
    if not mdbook:
        log("错误: 找不到 mdbook")
        return 1

    log("组装站点内容")
    assemble()
    write_config()

    if args.serve:
        log(f"启动预览: {mdbook} serve")
        os.execv(mdbook, [mdbook, "serve", str(STAGE)])

    log("渲染站点")
    run([mdbook, "build", str(STAGE)])
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(STAGE / "book", OUT)
    log(f"  站点 -> {OUT.relative_to(ROOT)} ({sum(1 for _ in OUT.rglob('*'))} 个文件)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
