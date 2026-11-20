# -*- coding: utf-8 -*-
"""生成可复现的知识库测试语料（synthetic corpus）。

用途：压测并验证 kb.py doctor 的体检能力。
语料完全合成，不含任何真实业务内容。

设计要点：
- 页面总数可参数化；n=4000 时的缺陷配额是本期公开内容引用的那一份。
- 缺陷按互不重叠的页面集合注入，每类的期望条数由下方配额决定。
- 语料同时带真实双链与故意断链，使入链计数非零、可被独立复算。

用法:
    python build_case.py <目标目录> [页数]
"""
import os
import re
import shutil
import sys

# n=4000 时的缺陷配额（公开内容引用的口径）
BASE_QUOTA = {
    "缺少frontmatter": 120,   # 严重
    "AUTO区块缺失": 40,       # 严重
    "摘要不足20字": 60,       # 严重
    "断链": 30,               # 严重
    "核心观点不足3条": 50,    # 警告
    "sources为空": 60,        # 警告
    "type越界": 40,           # 警告
    "缺少created字段": 50,    # 警告
    "未注册索引": 100,        # 提示
}
BASE_N = 4000

SUMMARY = "这是一段完全合成的示例摘要，用于验证体检脚本的判定逻辑，不代表任何真实内容。"
SHORT_SUMMARY = "太短了。"
BROKEN_TARGET = "不存在的页面"


def sname(i): return f"来源{i + 1:04d}"
def cname(i): return f"概念{i + 1:04d}"
def ename(i): return f"实体{i + 1:04d}"
def tname(i): return f"主题{i + 1:04d}"


def quota_for(n):
    """按规模等比缩放缺陷配额（n=4000 时与 BASE_QUOTA 完全一致）。"""
    if n == BASE_N:
        return dict(BASE_QUOTA)
    return {k: max(1, round(v * n / BASE_N)) for k, v in BASE_QUOTA.items()}


def page_text(kind, i, n, defect):
    if kind == "source":
        name, sub = sname(i), "sources"
        body = ["---", f'title: "{name}"', "type: source-summary",
                "created: 2026-11-18", "updated: 2026-11-18",
                "sources: []", "tags: []", "---", "", f"# {name}", "",
                "## 来源", "| 字段 | 值 |", "|---|---|",
                "| 链接 | https://example.invalid/synthetic |",
                "| raw 路径 | raw/web/synthetic.md |", "",
                "## 内容摘要", "",
                SHORT_SUMMARY if "CS" in defect else SUMMARY, "",
                "## 核心观点", ""]
        pts = ["1. 观点一。", "2. 观点二。", "3. 观点三。"]
        if "CP" in defect:
            pts = pts[:2]
        body += pts
        if "CA" not in defect:
            body += ["", "<!-- AUTO:START summary -->", "合成摘要内容。", "<!-- AUTO:END summary -->"]
        else:
            body += ["", "（本页故意删除 AUTO 区块，用于验证严重项判定）"]
        body += ["", f"关联 [[{cname(i % n)}]]"]
        return sub, name, "\n".join(body) + "\n"

    if kind == "concept":
        name, sub = cname(i), "concepts"
        src_field = "sources: []" if "ES" in defect else f'sources: ["wiki/sources/{sname(i % n)}.md"]'
        fields = ["---", f'title: "{name}"', "type: concept"]
        if "NC" in defect:
            fields.append("updated: 2026-11-18")            # 故意缺 created
        else:
            fields += ["created: 2026-11-18", "updated: 2026-11-18"]
        fields += [src_field, "tags: []", "---"]
        body = fields + ["", f"# {name}", "",
                         f"关联 [[{sname(i % n)}]] [[{ename(i % n)}]] [[{cname((i + 1) % n)}]]"]
        if "BL" in defect:
            body.append(f"坏链 [[{BROKEN_TARGET}]]")
        return sub, name, "\n".join(body) + "\n"

    if kind == "entity":
        name, sub = ename(i), "entities"
        fields = ["---", f'title: "{name}"', "type: entity"]
        if "NC" in defect:
            fields.append("updated: 2026-11-18")            # 故意缺 created
        else:
            fields += ["created: 2026-11-18", "updated: 2026-11-18"]
        fields += ['sources: ["wiki/sources/%s.md"]' % sname(i % n), "tags: []", "---"]
        body = fields + ["", f"# {name}", "", f"关联 [[{cname((i - 1) % n)}]] [[{sname(i % n)}]]"]
        if "BL" in defect:
            body.append(f"坏链 [[{BROKEN_TARGET}]]")
        return sub, name, "\n".join(body) + "\n"

    name, sub = tname(i), "topics"
    ttype = "essay" if "TY" in defect else "topic"
    fields = ["---", f'title: "{name}"', f"type: {ttype}",
              "created: 2026-11-18", "updated: 2026-11-18",
              'sources: ["wiki/sources/%s.md"]' % sname(i % n), "tags: []", "---"]
    body = fields + ["", f"# {name}", "", f"关联 [[{tname((i + 1) % n)}]] [[{sname(i % n)}]]"]
    if "MF" in defect:
        return sub, name, f"# {name}\n\n这一页故意没有 frontmatter，用于验证严重项判定。\n"
    return sub, name, "\n".join(body) + "\n"


def build(root, n=BASE_N):
    if os.path.isdir(root):
        shutil.rmtree(root)
    wiki = os.path.join(root, "wiki")
    for sub in ("sources", "concepts", "entities", "topics"):
        os.makedirs(os.path.join(wiki, sub), exist_ok=True)
    os.makedirs(os.path.join(root, "raw", "web"), exist_ok=True)

    body_n = n - 2                                    # 预留 index.md 与 log.md
    per = body_n // 4
    counts = {"source": per, "concept": per, "entity": per, "topic": body_n - 3 * per}

    q = quota_for(n)
    plan = []
    plan += [("source", i, {"CS"}) for i in range(q["摘要不足20字"])]
    plan += [("source", counts["source"] - 1 - i, {"CA"}) for i in range(q["AUTO区块缺失"])]
    plan += [("source", counts["source"] - 1 - q["AUTO区块缺失"] - i, {"CP"})
             for i in range(q["核心观点不足3条"])]
    plan += [("concept", i, {"ES"}) for i in range(q["sources为空"])]
    plan += [("concept", counts["concept"] - 1 - i, {"NC"}) for i in range(q["缺少created字段"])]
    plan += [("entity", i, {"BL"}) for i in range(q["断链"])]
    plan += [("entity", counts["entity"] - 1 - i, {"NC"}) for i in range(q["缺少created字段"])]
    plan += [("topic", i, {"TY"}) for i in range(q["type越界"])]
    plan += [("topic", counts["topic"] - 1 - i, {"MF"}) for i in range(q["缺少frontmatter"])]

    defects = {(k, i): set(d) for k, i, d in plan}

    # 未注册索引的页面（与上面集合不重叠）
    unregistered = set()
    ni = q["未注册索引"]
    for i in range(ni):
        if i < ni // 2:
            unregistered.add(("concept", counts["concept"] - 1 - ni // 2 - i))
        else:
            unregistered.add(("entity", counts["entity"] - 1 - ni + i - ni // 2))

    entries = []
    for kind, count in (("source", counts["source"]), ("concept", counts["concept"]),
                        ("entity", counts["entity"]), ("topic", counts["topic"])):
        for i in range(count):
            sub, name, text = page_text(kind, i, count, defects.get((kind, i), set()))
            with open(os.path.join(wiki, sub, name + ".md"), "w", encoding="utf-8") as fh:
                fh.write(text)
            if (kind, i) not in unregistered:
                entries.append(f"- [{name}](wiki/{sub}/{name}.md)")

    with open(os.path.join(wiki, "index.md"), "w", encoding="utf-8") as fh:
        fh.write("# 合成索引\n\n" + "\n".join(entries) + "\n")
    with open(os.path.join(wiki, "log.md"), "w", encoding="utf-8") as fh:
        fh.write("# 日志\n\n| 2026-11-18 | 合成语料 | | |\n")
    with open(os.path.join(root, "raw", "web", "synthetic.md"), "w", encoding="utf-8") as fh:
        fh.write("# 合成原始证据\n")
    return {"页数": n, "缺陷配额": q}


# ---------- 独立重写判定逻辑，作为体检器的交叉校验 ----------
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
WIKILINK_RE = re.compile(r"\[\[([^\[\]|#]+)(?:#[^\]|]*)?(?:[^\]]*)?\]\]")
AUTO_RE = re.compile(r"<!--\s*AUTO:START.*?-->(.*?)<!--\s*AUTO:END.*?-->", re.S)
REQUIRED_FIELDS = ("title", "type", "created", "updated", "sources")
PAGE_TYPES = {"source-summary", "concept", "entity", "topic", "comparison"}


def expected_counts(root):
    wiki = os.path.join(root, "wiki")
    pages = []
    for dp, _dn, fns in os.walk(wiki):
        for fn in fns:
            if fn.endswith(".md"):
                pages.append(os.path.join(dp, fn))
    index = os.path.join(wiki, "index.md")
    log = os.path.join(wiki, "log.md")
    names = {os.path.splitext(os.path.basename(p))[0] for p in pages}
    inbound = {os.path.splitext(os.path.basename(p))[0]: 0 for p in pages}
    c = {"严重": 0, "警告": 0, "提示": 0}
    for p in pages:
        with open(p, encoding="utf-8") as fh:
            text = fh.read()
        stem = os.path.splitext(os.path.basename(p))[0]
        is_nav = p in (index, log)
        m = FRONTMATTER_RE.match(text)
        fm = {}
        if m:
            for line in m.group(1).splitlines():
                mm = re.match(r"^([A-Za-z_]+)\s*:\s*(.*)$", line)
                if mm:
                    fm[mm.group(1)] = mm.group(2).strip()
        if not fm and not is_nav:
            c["严重"] += 1
        elif fm and not is_nav:
            for f in REQUIRED_FIELDS:
                if not fm.get(f):
                    c["严重" if f in ("title", "type") else "警告"] += 1
            t = (fm.get("type") or "").strip()
            if t and t not in PAGE_TYPES:
                c["警告"] += 1
            if os.path.dirname(p).endswith("sources"):
                sec = re.search(r"##\s*(?:内容摘要|摘要)\s*\n(.*?)(?:\n##\s|$)", text, re.S)
                if not sec or len(sec.group(1).strip()) < 20:
                    c["严重"] += 1
                pts = re.search(r"##\s*核心观点\s*\n(.*?)(?:\n##\s|$)", text, re.S)
                if not pts or len(re.findall(r"^\s*(?:\d+[.、)]|[-*])\s+\S", pts.group(1), re.M)) < 3:
                    c["警告"] += 1
                autos = AUTO_RE.findall(text)
                if not autos or any(len(a.strip()) < 5 for a in autos):
                    c["严重"] += 1
            if t in ("concept", "entity", "topic"):
                src = fm.get("sources", "[]")
                if src in ("", "[]"):
                    c["警告"] += 1
        targets = set()
        for raw_link in WIKILINK_RE.findall(text):
            targets.add(os.path.basename(raw_link.strip()))
        for t in targets:
            if t in inbound:
                inbound[t] += 1
            elif t not in names:
                c["严重"] += 1
    for p in pages:
        stem = os.path.splitext(os.path.basename(p))[0]
        if p in (index, log):
            continue
        if inbound.get(stem, 0) == 0:
            c["提示"] += 1
    with open(index, encoding="utf-8") as fh:
        idx = fh.read()
    for p in pages:
        if p in (index, log):
            continue
        stem = os.path.splitext(os.path.basename(p))[0]
        rel = os.path.relpath(p, root).replace("\\", "/").split("wiki/")[-1]
        if stem not in idx and f"({rel})" not in idx:
            c["提示"] += 1
    return len(pages), c


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "case"
    pages = int(sys.argv[2]) if len(sys.argv) > 2 else BASE_N
    info = build(target, pages)
    n, exp = expected_counts(target)
    info["独立复算期望"] = exp
    info["实际文件数"] = n
    import json
    print(json.dumps(info, ensure_ascii=False, indent=2))
