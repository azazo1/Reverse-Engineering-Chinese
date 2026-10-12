#!/usr/bin/env python3
"""把 docs/ 下的中文内容组装成电子书, 生成 PDF / EPUB / MOBI.

只用标准库, 通过子进程调用 pandoc / typst / ebook-convert.
入口: uv run --no-project python scripts/build_book.py [--no-mobi] [--skip-pdf]

产物落在 dist/, 命名为 reverse-engineering-chinese-<版本>.<ext>.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from book_layout import (  # noqa: E402
    BOOK, DOCS, ROOT, SUBTITLE, TITLE,
    chapter_sort_key, clean, iter_courses,
)

DIST = ROOT / "dist"

# 中文字体候选, 按平台常见情况排列
CJK_FONTS = [
    "Noto Sans CJK SC",
    "Noto Serif CJK SC",
    "Source Han Sans SC",
    "PingFang SC",
    "Heiti SC",
    "Songti SC",
    "WenQuanYi Zen Hei",
]


def configure_output_encoding() -> None:
    """中文日志在 Windows 控制台默认代码页下会抛 UnicodeEncodeError."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        except (AttributeError, OSError):
            pass


def log(msg: str) -> None:
    print(msg, flush=True)


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    """跑外部命令, 失败时把 stderr 一并抛出."""
    proc = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-15:]
        raise RuntimeError(
            "命令失败 (%d): %s\n%s" % (proc.returncode, " ".join(cmd), "\n".join(tail))
        )
    return proc


def has(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def pick_cjk_font() -> str | None:
    """挑一个系统里可用的中文字体名."""
    if not has("typst"):
        return None
    try:
        out = run(["typst", "fonts"]).stdout
    except RuntimeError:
        return None
    available = {line.strip() for line in out.splitlines()}
    for font in CJK_FONTS:
        if font in available:
            return font
    return None


def shift_headings(text: str, levels: int = 1) -> str:
    """把标题层级整体下沉, 让各章标题挂在卷标题之下. 跳过围栏代码块."""
    out, fenced = [], False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            out.append(line)
            continue
        if not fenced and re.match(r"^#{1,6}\s", line):
            line = "#" * levels + line
        out.append(line)
    return "\n".join(out)


def assemble() -> Path:
    """把书稿拼成一个 markdown 文件, 返回其路径."""
    parts: list[str] = []

    # 封面与前言
    parts.append(f"---\ntitle: {TITLE}\nsubtitle: {SUBTITLE}\nlang: zh-CN\n---\n")
    intro = BOOK / "README.md"
    if intro.exists():
        parts.append(shift_headings(clean(intro.read_text(encoding="utf-8").strip())))

    chapters = 0
    for dirname, volume, main, extra in iter_courses():
        parts.append(f"\n# {volume}\n")
        for f in main:
            chapters += 1
            parts.append(shift_headings(clean(f.read_text(encoding="utf-8").strip())))
        # RE 分析篇另起一节, 不参与正文编号
        if extra:
            parts.append(f"\n## {volume} - 逆向分析\n")
            for f in extra:
                chapters += 1
                parts.append(shift_headings(clean(f.read_text(encoding="utf-8").strip())))

    # 课程总索引放最后当附录, 它主要是外链
    courses = DOCS / "courses.md"
    if courses.exists():
        parts.append("\n# 附录: 课程总索引\n")
        parts.append(shift_headings(clean(courses.read_text(encoding="utf-8").strip())))

    body = "\n\n".join(p for p in parts if p.strip()) + "\n"
    tmp = ROOT / ".tmp"
    tmp.mkdir(exist_ok=True)
    target = tmp / "book-combined.md"
    target.write_text(body, encoding="utf-8")
    log(f"  组装完成: {chapters} 篇, {len(body.splitlines())} 行 -> {target.relative_to(ROOT)}")
    return target


def build_version() -> str:
    """版本号取自 CI 环境变量, 本地回退到日期."""
    v = os.environ.get("PROJECT_BUILD_VERSION", "").strip()
    if v:
        return re.sub(r"[^0-9A-Za-z._-]", "", v.lstrip("v"))
    if has("git"):
        try:
            out = run(["git", "rev-parse", "--short", "HEAD"]).stdout.strip()
            if out:
                return f"0.0.0-{out}"
        except RuntimeError:
            pass
    return time.strftime("0.0.0-%Y%m%d")


def build_epub(src: Path, out: Path) -> None:
    run([
        "pandoc", "-f", "markdown-citations", str(src), "-o", str(out),
        "--toc", "--toc-depth=2",
        "--metadata", f"title={TITLE}",
        "--metadata", f"subtitle={SUBTITLE}",
        "--metadata", "lang=zh-CN",
        "--split-level=1",
        "--standalone",
    ])
    log(f"  EPUB -> {out.name} ({out.stat().st_size // 1024} KiB)")


def build_pdf(src: Path, out: Path, font: str | None) -> None:
    """优先 typst (快), 不可用时回退 xelatex."""
    if has("typst"):
        cmd = ["pandoc", "-f", "markdown-citations", str(src), "-o", str(out), "--pdf-engine=typst", "--toc", "--toc-depth=2"]
        if font:
            cmd += ["-V", f"mainfont={font}"]
        try:
            run(cmd)
            log(f"  PDF -> {out.name} ({out.stat().st_size // 1024} KiB, typst)")
            return
        except RuntimeError as e:
            log(f"  typst 失败, 回退 xelatex: {str(e).splitlines()[0]}")
    cmd = [
        "pandoc", "-f", "markdown-citations", str(src), "-o", str(out), "--pdf-engine=xelatex",
        "--toc", "--toc-depth=2", "-V", "geometry:margin=2.2cm",
    ]
    if font:
        cmd += ["-V", f"CJKmainfont={font}"]
    run(cmd)
    log(f"  PDF -> {out.name} ({out.stat().st_size // 1024} KiB, xelatex)")


# Calibre 的 ebook-convert 常见落点, 图形化安装时不一定在 PATH 里
CALIBRE_HINTS = [
    "/Applications/calibre.app/Contents/MacOS/ebook-convert",
    "/opt/calibre/ebook-convert",
    "/usr/bin/ebook-convert",
    "/usr/local/bin/ebook-convert",
]


def find_ebook_convert() -> str | None:
    """先查 PATH, 再查图形化安装的固定位置."""
    if has("ebook-convert"):
        return "ebook-convert"
    for hint in CALIBRE_HINTS:
        if Path(hint).is_file():
            return hint
    return None


def build_mobi(epub: Path, out: Path) -> None:
    converter = find_ebook_convert()
    if not converter:
        raise RuntimeError("找不到 ebook-convert (Calibre), 无法生成 MOBI")
    run([converter, str(epub), str(out)])
    log(f"  MOBI -> {out.name} ({out.stat().st_size // 1024} KiB)")


def main() -> int:
    configure_output_encoding()
    ap = argparse.ArgumentParser(description="构建中文电子书")
    ap.add_argument("--no-mobi", action="store_true", help="跳过 MOBI")
    ap.add_argument("--no-pdf", action="store_true", help="跳过 PDF")
    ap.add_argument("--no-epub", action="store_true", help="跳过 EPUB")
    args = ap.parse_args()

    # 只做 MOBI 时不需要 pandoc (EPUB 由上游 job 提供)
    if not (args.no_epub and args.no_pdf) and not has("pandoc"):
        log("错误: 找不到 pandoc")
        return 1

    log("组装书稿")
    src = assemble()
    version = build_version()
    font = pick_cjk_font()
    log(f"版本 {version}; 中文字体 {font or '(未指定, 用引擎默认)'}")

    DIST.mkdir(exist_ok=True)
    stem = f"reverse-engineering-chinese-{version}"
    built: list[Path] = []

    log("生成电子书")
    if not args.no_epub:
        epub = DIST / f"{stem}.epub"
        build_epub(src, epub)
        built.append(epub)

    if not args.no_pdf:
        pdf = DIST / f"{stem}.pdf"
        build_pdf(src, pdf, font)
        built.append(pdf)

    if not args.no_mobi:
        epub = DIST / f"{stem}.epub"
        if not epub.exists():
            # 单独跑 MOBI 时 EPUB 应当已由上游提供; 实在没有就现做一份.
            if not has("pandoc"):
                log(f"错误: 缺少 {epub.name}, 且没有 pandoc 可现做一份")
                return 1
            build_epub(src, epub)
        mobi = DIST / f"{stem}.mobi"
        try:
            build_mobi(epub, mobi)
            built.append(mobi)
        except RuntimeError as e:
            log(f"  跳过 MOBI: {e}")

    log(f"完成, 共 {len(built)} 个产物:")
    for p in built:
        log(f"  {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
