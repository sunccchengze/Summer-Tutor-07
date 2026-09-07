#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成一个干净的课程目录页 index.html（无任何第三方品牌标识）。"""

import html
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECTIONS = [
    ("御风记 · 14 节正课", "御风记14节", "从牛顿第三定律到 AI 优化，一条主线讲透航空发动机"),
    ("时间有余拓展", "时间有余拓展", "课堂节奏宽裕时的加餐内容"),
]

FIRST = {"御风记14节": ["御风记 — 开场.html"]}


def entries(folder):
    names = sorted(n for n in os.listdir(os.path.join(REPO, folder)) if n.endswith(".html"))
    head = [n for n in FIRST.get(folder, []) if n in names]
    return head + [n for n in names if n not in head]


def main():
    cards = []
    for title, folder, desc in SECTIONS:
        items = []
        for i, name in enumerate(entries(folder), 1):
            label = html.escape(name[:-5])
            href = html.escape(f"./{folder}/{name}")
            items.append(
                f'        <a class="card" href="{href}">'
                f'<span class="num">{i:02d}</span>'
                f'<span class="name">{label}</span></a>'
            )
        cards.append(
            f'    <section>\n      <h2>{html.escape(title)}</h2>\n'
            f'      <p class="desc">{html.escape(desc)}</p>\n'
            f'      <div class="grid">\n' + "\n".join(items) + "\n      </div>\n    </section>"
        )

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>御风记 · 航空发动机科普课程</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2288%22>%E2%9C%88%EF%B8%8F</text></svg>">
    <style>
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        padding: 56px 24px 80px;
        background: #faf9f5;
        color: #141413;
        font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei",
          "Helvetica Neue", Arial, sans-serif;
        line-height: 1.6;
      }}
      main {{ max-width: 960px; margin: 0 auto; }}
      header h1 {{ font-size: 32px; margin: 0 0 8px; letter-spacing: 0.5px; }}
      header p {{ margin: 0 0 40px; color: #6b6a65; }}
      h2 {{ font-size: 20px; margin: 40px 0 4px; }}
      h2::before {{
        content: ""; display: inline-block; width: 22px; height: 2px;
        background: #d97757; vertical-align: middle; margin-right: 10px;
      }}
      .desc {{ margin: 0 0 18px 32px; color: #8a8880; font-size: 14px; }}
      .grid {{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); }}
      .card {{
        display: flex; align-items: center; gap: 12px;
        padding: 16px 18px; background: #fff; border: 1px solid #eae7de;
        border-radius: 12px; text-decoration: none; color: inherit;
        transition: border-color .2s, transform .2s, box-shadow .2s;
      }}
      .card:hover {{
        border-color: #d97757; transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(20, 20, 19, .07);
      }}
      .num {{ font-size: 13px; color: #d97757; font-variant-numeric: tabular-nums; }}
      .name {{ font-size: 15px; }}
      footer {{ margin-top: 56px; color: #b1ada1; font-size: 13px; text-align: center; }}
    </style>
  </head>
  <body>
    <main>
      <header>
        <h1>御风记 · 航空发动机科普课程</h1>
        <p>点击任意一节即可在浏览器中打开，全部为可离线浏览的交互式网页。</p>
      </header>
{chr(10).join(cards)}
      <footer>共 {sum(len(entries(f)) for _, f, _ in SECTIONS)} 节 · 交互式课件</footer>
    </main>
  </body>
</html>
"""
    out = os.path.join(REPO, "index.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(page)
    print("已生成", out)


if __name__ == "__main__":
    main()
