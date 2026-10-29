#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kb.py — 知识库零依赖体检/统计工具（Python 3.8+，仅标准库）

用法：
    python scripts/kb.py doctor     # 质量门体检：frontmatter / 断链 / 空摘要 / AUTO 块 / 孤立页 / 索引覆盖
    python scripts/kb.py stats      # 各层页面与 raw 数量
    python scripts/kb.py todo       # 列出 raw/ 中 needs_ingest: true 的待编译资料

退出码：doctor 发现严重问题返回 1（可接 CI / 定时任务告警），否则 0。
"""
import datetime as _dt
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIKI = os.path.join(ROOT, "wiki")
RAW = os.path.join(ROOT, "raw")

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
WIKILINK_RE = re.compile(r"\[\[([^\[\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
AUTO_RE = re.compile(r"<!--\s*AUTO:START.*?-->(.*?)<!--\s*AUTO:END.*?-->", re.S)
REQUIRED_FIELDS = ("title", "type", "created", "updated", "sources")
PAGE_TYPES = {"source-summary", "concept", "entity", "topic", "comparison"}
SEVERITY = {"严重": 0, "警告": 1, "提示": 2}


def md_files(base):
    out = []
    if not os.path.isdir(base):
        return out
    for dp, _dn, fns in os.walk(base):
        for fn in fns:
            if fn.endswith(".md"):
                out.append(os.path.join(dp, fn))
    return out


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


def parse_frontmatter(text):
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        mm = re.match(r"^([A-Za-z_]+)\s*:\s*(.*)$", line)
        if mm:
            fm[mm.group(1)] = mm.group(2).strip()
    return fm


def page_name(path):
    return os.path.splitext(os.path.basename(path))[0]


def collect():
    pages = md_files(WIKI)
    index = os.path.join(WIKI, "index.md")
    log = os.path.join(WIKI, "log.md")
    names = {page_name(p): p for p in pages}
    links = {}          # page -> set(target basename)
    inbound = {page_name(p): 0 for p in pages}
    issues = []

    def add(sev, where, msg):
        issues.append((sev, rel(where) if isinstance(where, str) else where, msg))

    for p in sorted(pages):
        text = open(p, encoding="utf-8").read()
        stem = page_name(p)
        is_nav = p in (index, log)

        fm = parse_frontmatter(text)
        if not fm and not is_nav:
            add("严重", p, "缺少 YAML frontmatter")
        elif fm and not is_nav:
            for f in REQUIRED_FIELDS:
                if not fm.get(f):
                    add("严重" if f in ("title", "type") else "警告", p, f"frontmatter 缺少字段: {f}")
            t = (fm.get("type") or "").strip()
            if t and t not in PAGE_TYPES:
                add("警告", p, f"type 不在约定范围: {t}")
            if os.path.dirname(p).endswith("sources"):
                body = text
                sec = re.search(r"##\s*(?:内容摘要|摘要)\s*\n(.*?)(?:\n##\s|$)", body, re.S)
                if not sec or len(sec.group(1).strip()) < 20:
                    add("严重", p, "来源摘要为空或不足 20 字")
                pts = re.search(r"##\s*核心观点\s*\n(.*?)(?:\n##\s|$)", body, re.S)
                if not pts or len(re.findall(r"^\s*(?:\d+[.、)]|[-*])\s+\S", pts.group(1), re.M)) < 3:
                    add("警告", p, "核心观点少于 3 条")
                autos = AUTO_RE.findall(body)
                if not autos or any(len(a.strip()) < 5 for a in autos):
                    add("严重", p, "AUTO 区块缺失、未成对或为空")
            if t in ("concept", "entity", "topic"):
                src = fm.get("sources", "[]")
                if src in ("", "[]"):
                    add("警告", p, f"{t} 页面 sources 为空（应链回至少 1 个来源页）")

        targets = set()
        for raw_link in WIKILINK_RE.findall(text):
            targets.add(os.path.basename(raw_link.strip()))
        links[stem] = targets
        for t in targets:
            if t in inbound:
                inbound[t] += 1
            elif t not in names:
                add("严重", p, f"断链: [[{t}]]")

    # 孤立页：没有任何入链（index/log 除外）
    for p in pages:
        stem = page_name(p)
        if p in (index, log):
            continue
        if inbound.get(stem, 0) == 0 and not links.get(stem):
            add("提示", p, "孤立页：无入链也无出链")
        elif inbound.get(stem, 0) == 0:
            add("提示", p, "无入链（只能从索引到达）")

    # 索引覆盖
    if os.path.isfile(index):
        idx = open(index, encoding="utf-8").read()
        for p in pages:
            if p in (index, log):
                continue
            stem = page_name(p)
            if stem not in idx and f"({rel(p).split('wiki/')[-1]})" not in idx:
                add("提示", p, "未在 wiki/index.md 注册")
    else:
        add("严重", index, "wiki/index.md 不存在")

    return pages, issues


def cmd_doctor():
    pages, issues = collect()
    issues.sort(key=lambda x: SEVERITY[x[0]])
    counts = {"严重": 0, "警告": 0, "提示": 0}
    for sev, where, msg in issues:
        counts[sev] += 1
        print(f"[{sev}] {where}  ->  {msg}")
    print("-" * 60)
    print(f"体检页面: {len(pages)} | 严重 {counts['严重']} | 警告 {counts['警告']} | 提示 {counts['提示']}")
    if counts["严重"]:
        print("结论: 未通过质量门，请先修复严重项。")
        return 1
    print("结论: 通过质量门。" + ("（有提示项可择机处理）" if counts["提示"] or counts["警告"] else ""))
    return 0


def cmd_stats():
    rows = []
    for sub in ("sources", "concepts", "entities", "topics"):
        d = os.path.join(WIKI, sub)
        rows.append((f"wiki/{sub}", len(md_files(d))))
    rows.append(("raw（原始证据，含子目录）", len(md_files(RAW))))
    inbox = os.path.join(ROOT, "inbox")
    rows.append(("inbox（待处理）", len(md_files(inbox))))
    w = max(len(a) for a, _ in rows)
    for a, b in rows:
        print(f"{a.ljust(w)}  {b}")
    return 0


def cmd_todo():
    n = 0
    for p in md_files(RAW):
        text = open(p, encoding="utf-8").read()
        fm = parse_frontmatter(text)
        if fm and str(fm.get("needs_ingest", "")).lower() in ("true", "yes"):
            print(rel(p))
            n += 1
    print("-" * 60)
    print(f"待编译资料: {n} 篇（单批评译 ≤ 10 篇）")
    return 0


def cmd_log():
    # 便捷追加日志：python scripts/kb.py log "新增来源摘要 3 篇"
    if len(sys.argv) < 3:
        print("用法: python scripts/kb.py log \"<做了什么>\"")
        return 2
    os.makedirs(WIKI, exist_ok=True)
    line = f"| {_dt.date.today()} | {sys.argv[2]} |  |  |\n"
    with open(os.path.join(WIKI, "log.md"), "a", encoding="utf-8") as f:
        f.write(line)
    print("已追加 wiki/log.md")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "doctor"
    sys.exit({"doctor": cmd_doctor, "stats": cmd_stats,
              "todo": cmd_todo, "log": cmd_log}.get(cmd, lambda: (print(__doc__) or 2))())
