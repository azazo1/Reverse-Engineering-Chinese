# 逆向工程中文教程 - 常用任务

[private]
default:
    @just --list

# 构建 PDF 与 EPUB (本机需装 pandoc 与 typst)
# 产物落在 dist/, 文件名带当前提交的短 hash.
book:
    uv run --no-project python scripts/build_book.py --no-mobi

# 构建全部格式, 含 MOBI (本机还需装 Calibre)
book-all:
    uv run --no-project python scripts/build_book.py

# 只构建 EPUB, 最快, 用来快速看排版效果
book-epub:
    uv run --no-project python scripts/build_book.py --no-pdf --no-mobi

# 构建在线阅读站点 (本机需装 mdbook, 或用 .tmp/tools/mdbook)
# 产物落在 site/, 可用 just site-serve 预览.
site:
    uv run --no-project python scripts/build_site.py

# 本地起服务预览阅读站点, 改动文档会自动重建
site-serve:
    uv run --no-project python scripts/build_site.py --serve
