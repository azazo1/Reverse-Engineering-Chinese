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
