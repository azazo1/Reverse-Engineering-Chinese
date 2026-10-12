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
    clean_for_render, first_heading, iter_courses,
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


def write_volume_index(d: Path, volume: str, entries: list, appendix: list) -> None:
    """给每卷生成一个导览页, 作为该卷在目录树里的节点.

    mdBook 的折叠只作用于有子项的章节, `# 卷名` 那种 part 标题不能折叠, 于是
    291 篇会一次性铺满侧栏. 改成"卷节点 + 篇为子项"之后, 侧栏默认只列 14 个卷.
    """
    total = len(entries) + len(appendix)
    lines = [f"# {volume}", "", f"本卷共 {total} 篇.", ""]
    if entries:
        lines += ["## 正文", ""]
        lines += [f"- [{title}]({f.name})" for f, title in entries]
        lines += [""]
    if appendix:
        lines += ["## 逆向分析", ""]
        lines += [f"- [{title}]({f.name})" for f, title in appendix]
        lines += [""]
    (d / "index.md").write_text("\n".join(lines), encoding="utf-8")


def assemble() -> list[str]:
    """铺内容到 STAGE/src, 返回 SUMMARY.md 的行."""
    if STAGE.exists():
        shutil.rmtree(STAGE)
    src = STAGE / "src"
    src.mkdir(parents=True)

    # 配图统一放在 src/imgs/, 各卷文件在下一层, 因此引用前缀是 ../imgs/,
    # 而根目录的 README 与 courses 用 imgs/.
    imgs = BOOK / "imgs"
    n_img = 0
    if imgs.is_dir():
        shutil.copytree(imgs, src / "imgs")
        n_img = sum(1 for _ in (src / "imgs").iterdir())

    summary: list[str] = ["# 目录", ""]

    # 翻译规范在 docs/ 下, 不属于书稿, README 里用 ../translation-guide.md 指向它.
    # 站点根只有书稿, 这个相对路径出不去, 因此单独铺一份并把链接拉平.
    # 这份文件里有 `<pre>` 这类字面示例, 不能过 clean_for_render (它会把
    # 反引号里的 `<pre>` 当成真标签替换掉), 原样拷过去.
    guide = DOCS / "translation-guide.md"
    if guide.exists():
        # 它里面的 [book/README.md](book/README.md) 是相对 docs/ 写的,
        # 铺到站点根之后要指向根上的首页 (源文件是 README.md, 页名是 index.html).
        text = guide.read_text(encoding="utf-8").replace(
            "](book/README.md)", "](index.html)")
        (src / "translation-guide.md").write_text(text, encoding="utf-8")

    # 首页
    intro = BOOK / "README.md"
    if intro.exists():
        text = clean_for_render(intro.read_text(encoding="utf-8"), "imgs/")
        text = text.replace("(../translation-guide.md)", "(translation-guide.md)")
        (src / "README.md").write_text(text, encoding="utf-8")
    else:
        (src / "README.md").write_text(f"# {TITLE}\n", encoding="utf-8")
    summary += ["# 总览", "", "- [书稿目录](README.md)", ""]

    chapters = 0
    summary += ["# 课程", ""]
    for dirname, volume, main, extra in iter_courses():
        # 各篇内容拷进 src, 用课程目录名分层, 避免同名文件互相覆盖
        for f in main + extra:
            rel = f"{dirname}/{f.name}"
            (src / dirname).mkdir(exist_ok=True)
            text = clean_for_render(f.read_text(encoding="utf-8"), "../imgs/")
            (src / rel).write_text(text, encoding="utf-8")

        entries = [(f, first_heading(f)) for f in main]
        appendix = [(f, first_heading(f)) for f in extra]
        write_volume_index(src / dirname, volume, entries, appendix)

        # 卷节点挂在导览页上, 各篇缩进一级, 侧栏即可按卷折叠
        summary.append(f"- [{volume}]({dirname}/index.md)")
        for f, title in entries + appendix:
            summary.append(f"  - [{title}]({dirname}/{f.name})")
        summary.append("")
        chapters += len(entries) + len(appendix)

    courses = DOCS / "courses.md"
    if courses.exists():
        text = clean_for_render(courses.read_text(encoding="utf-8"), "imgs/")
        (src / "courses.md").write_text(text, encoding="utf-8")
        summary += ["# 附录", ""]
        if guide.exists():
            summary.append("- [翻译规范](translation-guide.md)")
        summary += ["- [课程总索引](courses.md)", ""]

    (src / "SUMMARY.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    log(f"  铺开 {chapters} 篇, 配图 {n_img} 张 -> {src.relative_to(ROOT)}")
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
# 0 表示各卷默认收起, 只列卷名; 打开某篇时它所在的卷会自行展开.
# 取 1 的话 291 篇会一次性铺满侧栏.
level = 0
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
