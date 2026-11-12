"""injectbench: red-team a tool-using agent with planted prompt injections and compare defenses.

  injectbench run    [options]          run all cases x defenses and write reports
  injectbench report results/<run>      re-render reports
  injectbench show   <case-id-prefix>   print the planted attack text for matching cases
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def main(argv=None):
    ap = argparse.ArgumentParser(prog="injectbench", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--backend", choices=["offline", "llm"], default="offline")
    r.add_argument("--model", default="anthropic:claude-sonnet-5-5")
    r.add_argument("--fallback-model", action="append", default=[])
    r.add_argument("--defenses", nargs="+", default=None)
    r.add_argument("--attacks", type=int, default=144, help="number of attacked cases (multiple of 48 is balanced)")
    r.add_argument("--limit", type=int, help="only the first N attacked cases (quick pilot)")
    r.add_argument("--classifier", default="heuristic", help="'heuristic' or 'hf:<local-path-or-hub-id>'")
    r.add_argument("--workers", type=int, default=8)
    r.add_argument("--seed", type=int, default=0)
    r.add_argument("--out", default="results/run")
    rp = sub.add_parser("report")
    rp.add_argument("run")
    sh = sub.add_parser("show")
    sh.add_argument("prefix")
    a = ap.parse_args(argv)

    from .bench import BenchConfig, run_bench, write_reports
    from .defenses import DEFENSES
    if a.cmd == "run":
        if a.backend == "llm" and not os.environ.get("ANTHROPIC_API_KEY"):
            sys.exit("set ANTHROPIC_API_KEY for --backend llm")
        cfg = BenchConfig(out=a.out, defenses=a.defenses or list(DEFENSES), backend=a.backend, model=a.model,
                          fallback_models=a.fallback_model, attacks=a.attacks, seed=a.seed, workers=a.workers,
                          classifier=a.classifier, limit=a.limit)
        print(write_reports(run_bench(cfg))["md"])
        print(f"reports: {Path(a.out) / 'report.md'}  {Path(a.out) / 'report.html'}")
    elif a.cmd == "report":
        print(write_reports(Path(a.run) / "results.jsonl")["md"])
    else:
        from .suite import build_cases
        for c in build_cases():
            if c.id.startswith(a.prefix) and c.attacked:
                print(f"== {c.id}\n{c.payload()}\n")


if __name__ == "__main__":
    main()
