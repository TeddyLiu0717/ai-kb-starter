# -*- coding: utf-8 -*-
"""kb.py doctor 规模基准：独立进程计时 + 独立复算交叉校验。

为什么用独立进程：
  同一进程内连续调用 collect() 会受文件句柄缓存与 OS 缓存影响，
  首次与后续调用耗时可差 3 倍以上（实测 0.61s vs 2.18s，同一语料同一结果）。
  用户实际是每次敲一次命令，所以每个规模点起独立进程计时更接近真实体感。

用法:
    python run_bench.py --kb <kb.py 路径> --out <输出目录> [--sizes 1000,4000,8000]
"""
import argparse
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_case  # noqa: E402


def run_doctor(kb_path, case_dir, repeats=5):
    """独立进程跑 doctor，返回 (耗时列表, 解析出的问题分类, 退出码)。

    kb.py 用自身文件位置推导 ROOT（scripts/ 的上级），所以必须把 kb.py
    复制到用例目录下的 scripts/ 里，否则它会去体检它自己所在的仓库。
    """
    scripts_dir = os.path.join(case_dir, "scripts")
    os.makedirs(scripts_dir, exist_ok=True)
    local_kb = os.path.join(scripts_dir, "kb.py")
    if not os.path.exists(local_kb) or os.path.getmtime(local_kb) < os.path.getmtime(kb_path):
        shutil.copyfile(kb_path, local_kb)

    times, issues = [], None
    code = None
    for _ in range(repeats):
        t0 = time.perf_counter()
        r = subprocess.run([sys.executable, local_kb, "doctor"],
                           cwd=case_dir, capture_output=True, text=True, encoding="utf-8")
        times.append(time.perf_counter() - t0)
        code = r.returncode
        issues = parse_doctor_output(r.stdout)
    return times, issues, code


def parse_doctor_output(stdout):
    """从 doctor 输出解析出严重/警告/提示计数与逐类明细。"""
    res = {"严重": 0, "警告": 0, "提示": 0, "明细": {}, "页数": None, "结论": None}
    for line in stdout.splitlines():
        m = re.match(r"^\[(严重|警告|提示)\]\s+(.*?)\s*->\s*(.*)$", line)
        if m:
            sev, _where, msg = m.groups()
            res[sev] += 1
            key = re.sub(r":\s*(\[\[.*?\]\]|[\w]+)$", "", msg)
            res["明细"][f"{sev}|{key}"] = res["明细"].get(f"{sev}|{key}", 0) + 1
            continue
        m = re.match(r"^体检页面:\s*(\d+)\s*\|\s*严重\s*(\d+)\s*\|\s*警告\s*(\d+)\s*\|\s*提示\s*(\d+)", line)
        if m:
            res["页数"] = int(m.group(1))
            res["严重"], res["警告"], res["提示"] = int(m.group(2)), int(m.group(3)), int(m.group(4))
            continue
        if line.startswith("结论:"):
            res["结论"] = line.split("：", 1)[-1] if "：" in line else line
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kb", required=True, help="kb.py 绝对路径")
    ap.add_argument("--out", required=True, help="合成语料输出根目录")
    ap.add_argument("--sizes", default="1000,4000,8000")
    ap.add_argument("--repeats", type=int, default=5)
    args = ap.parse_args()

    sizes = [int(s) for s in args.sizes.split(",")]
    rows = []
    # 必须转绝对路径：脚本路径与 cwd 同时用相对路径时，子进程会按新 cwd 解析脚本路径而找不到文件
    kb_path = os.path.abspath(args.kb)
    out_root = os.path.abspath(args.out)
    print("kb.py doctor 规模基准（独立进程，每档 %d 次取中位数）" % args.repeats)
    print(f"{'页数':>6} {'中位秒':>8} {'最小':>7} {'最大':>7} {'严重':>6} {'警告':>6} {'提示':>6} {'交叉校验':>10}")
    for n in sizes:
        case_dir = os.path.join(out_root, f"case-{n}")
        build_case.build(case_dir, n)
        times, issues, code = run_doctor(kb_path, case_dir, args.repeats)

        # 独立复算：不依赖 kb.py 自己，重写判定逻辑核对严重/警告/提示
        _pages, exp = build_case.expected_counts(case_dir)
        match = (exp["严重"] == issues["严重"] and exp["警告"] == issues["警告"]
                 and exp["提示"] == issues["提示"])

        med = statistics.median(times)
        rows.append({
            "pages": n,
            "median_sec": round(med, 3),
            "min_sec": round(min(times), 3),
            "max_sec": round(max(times), 3),
            "exit_code": code,
            "doctor": {"严重": issues["严重"], "警告": issues["警告"], "提示": issues["提示"],
                       "页数": issues["页数"], "明细": issues["明细"]},
            "independent_recompute": exp,
            "cross_check_passed": match,
        })
        print(f"{n:>6} {med:>8.3f} {min(times):>7.3f} {max(times):>7.3f} "
              f"{issues['严重']:>6} {issues['警告']:>6} {issues['提示']:>6} "
              f"{'一致' if match else '不一致':>10}")

    print("\n翻倍比（中位数，线性应约 x2）：")
    for a, b in zip(rows, rows[1:]):
        print(f"  {a['pages']:>5} -> {b['pages']:<5} x{b['median_sec']/a['median_sec']:.2f}")

    with open(os.path.join(out_root, "bench-result.json"), "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=2)
    print("\n结果写入: " + os.path.join(out_root, "bench-result.json"))


if __name__ == "__main__":
    main()
