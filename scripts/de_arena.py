#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
去除课程网页中一切 Arena 网站的标识（品牌横幅、favicon、og/twitter 元信息、
PostHog 埋点脚本、Cloudflare beacon 等），把每节课变成干净、可独立打开的单页。

原始结构（Arena 的 "code preview" 保存页）:
    <课程>.html                     -> Arena 外壳: 悬浮 "Built with Arena" 横幅 + PostHog + iframe
    <课程>_files/saved_resource.html -> 真正的课程内容 (React 单页)
    <课程>_files/css2                -> 外壳横幅用字体 (Inter)
    <课程>_files/css2(1)             -> 课程内容用字体
    <课程>_files/array.js|config.js|surveys.js|... -> PostHog 埋点
    <课程>_files/v4513226...         -> Cloudflare Insights beacon

处理后:
    <课程>.html                     -> 课程内容本身（无任何 Arena 痕迹）
    <课程>_files/                    -> 只保留字体 css 与图片等真正需要的资源
"""

from __future__ import annotations

import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 课程页所在目录
COURSE_DIRS = ["御风记14节", "时间有余拓展"]

# 只服务于 Arena 外壳 / 埋点的资源，直接删除
JUNK_FILES = [
    "array.js.下载",                    # PostHog SDK
    "config.js.下载",                   # PostHog 远端配置（含 Arena 问卷文案）
    "dead-clicks-autocapture.js.下载",   # PostHog
    "exception-autocapture.js.下载",     # PostHog
    "surveys.js.下载",                  # PostHog 问卷（"Built with Arena" 举报表单）
    "web-vitals.js.下载",               # PostHog
    "css2",                            # Arena 横幅字体
    "v4513226cdae34746b4dedf0b4dfa099e1781791509496",  # Cloudflare beacon
    "saved_resource.html",             # 内容已内联进课程页
]

# 需要保留但要重写为 <课程>_files/ 前缀的相对资源
ASSET_RE = re.compile(r'(?P<attr>\b(?:href|src)=")\./(?P<path>[^"]+)"')

# 页内锚点在保存时被浏览器序列化成了绝对地址：
#   https://<uuid>.arena.site/?embed=true#intro  ->  #intro
ARENA_ANCHOR_RE = re.compile(
    r'https?://[0-9a-zA-Z-]+\.arena\.site/[^"\'\s]*?(#[^"\'\s]*)?(?=["\'\s])'
)

SAVED_FROM_RE = re.compile(r"<!--\s*saved from url=\(\d+\)[^>]*?-->\s*\n?", re.I)
CF_BEACON_RE = re.compile(
    r'\s*<script[^>]*src="\./v4513226[^"]*"[^>]*>\s*</script>', re.I
)
IMMERSIVE_ATTR_RE = re.compile(r'\s+data-immersive-translate-[a-z-]+="[^"]*"', re.I)

# 原来的 favicon 指向 arena.site，已删除；换成内联的中性图标，避免页面无图标 / 404
FAVICON = (
    '<link rel="icon" href="data:image/svg+xml,'
    "<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22>"
    "<text y=%22.9em%22 font-size=%2288%22>%E2%9C%88%EF%B8%8F</text></svg>\">"
)
TITLE_RE = re.compile(r"(<title>.*?</title>)", re.I | re.S)



def collect_pages():
    pages = []
    for d in COURSE_DIRS:
        root = os.path.join(REPO, d)
        if not os.path.isdir(root):
            continue
        for name in sorted(os.listdir(root)):
            if not name.endswith(".html"):
                continue
            html = os.path.join(root, name)
            files_dir = os.path.join(root, name[:-5] + "_files")
            if os.path.isdir(files_dir):
                pages.append((html, files_dir))
    return pages


def build_page(page_html: str, files_dir: str) -> str:
    """用课程真实内容重建页面，路径改写为 <课程>_files/ 前缀。

    首次运行读取 <课程>_files/saved_resource.html；若该文件已被清理（脚本重复运行），
    则直接在已生成的课程页上再跑一遍清洗规则，保证幂等。
    """
    src = os.path.join(files_dir, "saved_resource.html")
    if not os.path.exists(src):
        src = page_html
    with open(src, encoding="utf-8") as fh:
        content = fh.read()

    prefix = "./" + os.path.basename(files_dir) + "/"

    # 1. 删除 "saved from url=(...)....arena.site/?embed=true" 注释
    content = SAVED_FROM_RE.sub("", content, count=1)

    # 2. 删除 Cloudflare Insights beacon（外部追踪，且非课程所需）
    content = CF_BEACON_RE.sub("", content)

    # 3. 页内锚点从 arena.site 绝对地址还原为纯 fragment
    content = ARENA_ANCHOR_RE.sub(lambda m: m.group(1) or "#", content)

    # 4. 相对资源改写：./css2(1) -> ./<课程>_files/css2(1)
    def fix(m: re.Match) -> str:
        path = m.group("path")
        if path.startswith(os.path.basename(files_dir) + "/"):
            return m.group(0)
        return f'{m.group("attr")}{prefix}{path}"'

    content = ASSET_RE.sub(fix, content)

    # 5. 清掉翻译插件遗留属性
    content = IMMERSIVE_ATTR_RE.sub("", content)

    # 6. 补一个中性 favicon（原 favicon 指向 arena.site，已删除）
    if 'rel="icon"' not in content:
        content = TITLE_RE.sub(lambda m: m.group(1) + "\n    " + FAVICON, content, count=1)

    if not content.startswith("<!DOCTYPE"):
        content = "<!DOCTYPE html>\n" + content.lstrip()

    return content


def main() -> int:
    pages = collect_pages()
    if not pages:
        print("没有找到课程页面", file=sys.stderr)
        return 1

    for page_html, files_dir in pages:
        rebuilt = build_page(page_html, files_dir)
        with open(page_html, "w", encoding="utf-8") as fh:
            fh.write(rebuilt)

        for junk in JUNK_FILES:
            p = os.path.join(files_dir, junk)
            if os.path.exists(p):
                os.remove(p)

        kept = sorted(os.listdir(files_dir))
        rel = os.path.relpath(page_html, REPO)
        print(f"[ok] {rel}  (保留资源: {', '.join(kept) if kept else '无'})")

    print(f"\n共处理 {len(pages)} 个课程页面。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
