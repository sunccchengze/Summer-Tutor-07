#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验：新课程页与原始课程内容（git 中的 saved_resource.html）之间的差异，
只应包含"去 Arena 标识"相关的改动。"""
import difflib
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
COURSE_DIRS = ["御风记14节", "时间有余拓展"]

TOKEN = re.compile(r"\s+|[^\s]+")


def tokens(s):
    return re.findall(r"\S+|\s+", s)


def main():
    total = 0
    for d in COURSE_DIRS:
        root = os.path.join(REPO, d)
        for name in sorted(os.listdir(root)):
            if not name.endswith(".html"):
                continue
            orig_path = f"{d}/{name[:-5]}_files/saved_resource.html"
            try:
                orig = subprocess.run(
                    ["git", "show", f"{BASE}:{orig_path}"],
                    cwd=REPO, capture_output=True, check=True,
                ).stdout.decode("utf-8")
            except subprocess.CalledProcessError:
                print(f"!! 找不到原始内容: {orig_path}")
                continue
            with open(os.path.join(root, name), encoding="utf-8") as fh:
                new = fh.read()

            a, b = tokens(orig), tokens(new)
            sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
            changes = [op for op in sm.get_opcodes() if op[0] != "equal"]
            total += len(changes)
            print(f"\n=== {d}/{name}  差异块 {len(changes)}")
            for tag, i1, i2, j1, j2 in changes:
                old = "".join(a[i1:i2]).strip()
                new_ = "".join(b[j1:j2]).strip()
                print(f"  [{tag}] - {old[:160]!r}")
                print(f"        + {new_[:160]!r}")
    print(f"\n总差异块: {total}")


if __name__ == "__main__":
    main()
