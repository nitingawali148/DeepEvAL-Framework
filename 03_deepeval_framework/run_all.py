"""One-command runner for the entire DeepEval suite.

Usage:
    python run_all.py                         # all metrics
    python run_all.py --only chatbot          # only -m chatbot
    python run_all.py --only "rag and quality"
    python run_all.py --provider groq         # override JUDGE_PROVIDER
    python run_all.py --max-goldens 2         # cap golden cases per metric
    python run_all.py --html my-report.html
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="pytest -m expression (e.g. 'chatbot and quality')")
    ap.add_argument("--provider", default=None, choices=["openai", "groq", "ollama"])
    ap.add_argument("--judge-model", default=None)
    ap.add_argument("--max-goldens", type=int, default=None)
    ap.add_argument("--html", default=str(REPORTS / "report.html"))
    ap.add_argument("--keyword", default=None, help="pytest -k expression")
    ap.add_argument("extra", nargs=argparse.REMAINDER)
    args = ap.parse_args()

    env = os.environ.copy()
    if args.provider:
        env["JUDGE_PROVIDER"] = args.provider
    if args.judge_model:
        if env.get("JUDGE_PROVIDER") == "groq":
            env["JUDGE_MODEL_GROQ"] = args.judge_model
        elif env.get("JUDGE_PROVIDER") == "ollama":
            env["JUDGE_MODEL_OLLAMA"] = args.judge_model
        else:
            env["JUDGE_MODEL_OPENAI"] = args.judge_model
    if args.max_goldens:
        env["MAX_GOLDENS"] = str(args.max_goldens)

    cmd = ["pytest", "tests", f"--html={args.html}", "--self-contained-html", "-v"]
    if args.only:
        cmd += ["-m", args.only]
    if args.keyword:
        cmd += ["-k", args.keyword]
    if args.extra and args.extra[0] == "--":
        cmd += args.extra[1:]
    print(f"[run_all] {' '.join(cmd)}")
    print(f"[run_all] JUDGE_PROVIDER={env.get('JUDGE_PROVIDER', 'openai')}")
    proc = subprocess.run(cmd, cwd=ROOT, env=env)
    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
