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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from book_layout import (  # noqa: E402
    BOOK, DOCS, REPO_URL, ROOT, TITLE,
    clean, first_heading, iter_courses,
)

STAGE = ROOT / ".tmp" / "site"
OUT = ROOT / "site"


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
    for dirname, volume, main, extra in iter_courses():
        summary.append(f"# {volume}")
        summary.append("")

        # 各篇内容拷进 src, 用课程目录名分层, 避免同名文件互相覆盖
        for f in main + extra:
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
git-repository-url = "{REPO_URL}"
edit-url-template = "{REPO_URL}/edit/main/{{{{ path }}}}"

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
