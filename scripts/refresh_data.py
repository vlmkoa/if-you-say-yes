#!/usr/bin/env python3
"""
Refresh all integrated data: TripSit → Neo4j, PsychonautWiki + OpenFDA → core-api.

Run periodically (e.g. weekly via cron/Task Scheduler) so interaction and substance
data stay up to date. Requires Neo4j and core-api to be reachable (see RUN.md).

Usage:
  python scripts/refresh_data.py                    # full refresh (default substance list)
  python scripts/refresh_data.py --all-tripsit      # full refresh, sync every TripSit substance to core-api
  python scripts/refresh_data.py --neo4j            # Neo4j only
  python scripts/refresh_data.py --core-api         # core-api only (default list)
  python scripts/refresh_data.py --core-api --all-tripsit           # core-api only, every TripSit substance
  python scripts/refresh_data.py --core-api --from-psychonautwiki  # core-api only, many drugs from PsychonautWiki
"""

import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_script(name: str, *args: str) -> bool:
    """Run a Python script from scripts/ with project root as cwd. Return True on success."""
    script = os.path.join(ROOT, "scripts", name)
    env = os.environ.copy()
    if os.path.exists(os.path.join(ROOT, ".env")):
        with open(os.path.join(ROOT, ".env")) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    env[k.strip()] = v.strip()
    result = subprocess.run(
        [sys.executable, script] + list(args),
        cwd=ROOT,
        env=env,
    )
    return result.returncode == 0


def main_cli() -> None:
    parser = argparse.ArgumentParser(description="Refresh Neo4j and/or core-api data.")
    parser.add_argument("--neo4j", action="store_true", help="Only load TripSit into Neo4j")
    parser.add_argument("--core-api", action="store_true", help="Only sync substances to core-api")
    parser.add_argument("--all-tripsit", action="store_true", help="Sync every TripSit substance to core-api (use with --core-api or full refresh)")
    parser.add_argument("--from-psychonautwiki", action="store_true", help="Sync substances from PsychonautWiki list to core-api (use with --core-api or full refresh)")
    args = parser.parse_args()
    do_all = not (args.neo4j or args.core_api)
    do_neo4j = do_all or args.neo4j
    do_core = do_all or args.core_api

    ok = True
    if do_neo4j:
        if not run_script("load_tripsit_to_neo4j.py"):
            ok = False
    if do_core:
        sync_args = []
        if getattr(args, "from_psychonautwiki", False):
            sync_args.append("--from-psychonautwiki")
        elif getattr(args, "all_tripsit", False):
            sync_args.append("--all-tripsit")
        if not run_script("sync_substances_to_core_api.py", *sync_args):
            ok = False
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main_cli()
