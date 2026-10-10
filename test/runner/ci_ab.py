"""Run a nonempty, explicitly covered A/B acceptance shard in CI."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import run_all
import run_all_otelc


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--family", choices=("otelc", "skywalking"), required=True)
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--shards", type=int, default=1)
    args = parser.parse_args()
    if not 0 <= args.shard < args.shards:
        parser.error("shard must belong to the declared nonempty shard range")
    here = Path(__file__).resolve().parent
    names = run_all_otelc.ORDER if args.family == "otelc" else run_all.ORDER
    if not args.full:
        names = ["httpserver", "grpcserver"] if args.family == "otelc" else ["http", "cross-goroutine"]
    names = names[args.shard::args.shards]
    if not names:
        raise SystemExit("an empty acceptance shard cannot pass")
    directory = "scenarios-otelc" if args.family == "otelc" else "scenarios"
    runner = "run_ab_otelc.py" if args.family == "otelc" else "run_ab.py"
    results = []
    for name in names:
        scenario = here.parent / directory / name
        if not (scenario / "plugin.yml").is_file():
            raise SystemExit(f"declared scenario is missing: {name}")
        command = [sys.executable, "-u", str(here / runner), "--scenario", str(scenario)]
        if not args.full:
            command += ["--go", "1.27" if args.family == "otelc" else "1.26"]
        elif args.family == "skywalking":
            command += ["--min-go", "1.25"]
        result = subprocess.run(command, check=False)
        results.append({"scenario": name, "passed": result.returncode == 0})
    report = here / f"ci-{args.family}-{args.shard}.json"
    report.write_text(json.dumps({"family": args.family, "full": args.full, "results": results}, indent=2) + "\n")
    if any(not result["passed"] for result in results):
        raise SystemExit("A/B acceptance failed; see scenario output and shard report")


if __name__ == "__main__":
    main()
