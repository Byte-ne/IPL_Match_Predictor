from __future__ import annotations

import argparse
import json
import sys
from datetime import date as Date
from pathlib import Path

from rich import print
from rich.table import Table

from .config import get_paths
from .data.download import download_default_dataset
from .data.info import dataset_report
from .api.cricapi import list_fixtures
from .models.predict import predict_matchday, predict_prematch
from .models.train import train_mode


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ipl_predictor",
        description="IPL match predictor (pre-match + match-day).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    dl = sub.add_parser("download-data", help="Download IPL matches CSV (2008-2024)")
    dl.add_argument("--force", action="store_true", help="Re-download even if exists")

    sub.add_parser("data-info", help="Show dataset season range and row count")

    lf = sub.add_parser("list-fixtures", help="List live/upcoming matches from CricAPI")
    lf.add_argument("--offset", type=int, default=0)
    lf.add_argument("--all", action="store_true", help="Show all cricket, not only IPL")

    tr = sub.add_parser("train", help="Train a model")
    tr.add_argument("mode", choices=["pre", "prematch", "matchday", "md"])
    tr.add_argument("--raw-csv", type=Path, default=None)

    pr = sub.add_parser("predict", help="Predict win probabilities")
    pr.add_argument("mode", choices=["pre", "prematch", "matchday", "md"])
    pr.add_argument("--team1", default=None)
    pr.add_argument("--team2", default=None)
    pr.add_argument("--venue", default=None)
    pr.add_argument("--date", dest="match_date", default=None, help="YYYY-MM-DD")
    pr.add_argument("--fixture-id", default=None)
    pr.add_argument("--toss-winner", default=None)
    pr.add_argument("--toss-decision", default=None)
    pr.add_argument("--team1-xi", default=None)
    pr.add_argument("--team2-xi", default=None)

    return parser


def main(argv: list[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)
    paths = get_paths()

    if args.command == "download-data":
        out_path = download_default_dataset(paths.raw_dir, force=args.force)
        print(f"[bold green]Downloaded:[/bold green] {out_path}")
        print(json.dumps(dataset_report(paths), indent=2, default=str))
        return

    if args.command == "data-info":
        print(json.dumps(dataset_report(paths), indent=2, default=str))
        return

    if args.command == "list-fixtures":
        try:
            fixtures = list_fixtures(paths, offset=args.offset, ipl_only=not args.all)
        except RuntimeError as exc:
            print(f"[bold red]API error:[/bold red] {exc}", file=sys.stderr)
            sys.exit(1)
        if not fixtures:
            print("No fixtures found. Try --all or set CRICAPI_KEY.")
            return
        table = Table(title="Fixtures")
        table.add_column("fixture_id", style="cyan")
        table.add_column("match")
        table.add_column("status")
        table.add_column("venue")
        table.add_column("date")
        for f in fixtures:
            table.add_row(
                f.fixture_id,
                f"{f.team1} vs {f.team2}".strip() or f.name,
                f.status,
                f.venue,
                str(f.date) if f.date else "",
            )
        print(table)
        return

    if args.command == "train":
        result = train_mode(mode=args.mode, paths=paths, raw_csv=args.raw_csv)
        print("[bold green]Training complete[/bold green]")
        print(json.dumps(result, indent=2, default=str))
        return

    if args.command == "predict":
        mode = args.mode.lower()
        if mode in {"pre", "prematch"}:
            if not (args.team1 and args.team2 and args.venue and args.match_date):
                print("Error: pre requires --team1 --team2 --venue --date", file=sys.stderr)
                sys.exit(2)
            print(json.dumps(
                predict_prematch(
                    paths=paths,
                    team1=args.team1,
                    team2=args.team2,
                    venue=args.venue,
                    date=Date.fromisoformat(args.match_date),
                ),
                indent=2,
            ))
            return
        if mode in {"matchday", "md"}:
            print(json.dumps(
                predict_matchday(
                    paths=paths,
                    fixture_id=args.fixture_id,
                    team1=args.team1,
                    team2=args.team2,
                    venue=args.venue,
                    date=(Date.fromisoformat(args.match_date) if args.match_date else None),
                    toss_winner=args.toss_winner,
                    toss_decision=args.toss_decision,
                    team1_xi=args.team1_xi,
                    team2_xi=args.team2_xi,
                ),
                indent=2,
            ))
            return

    print(f"Unknown command: {args.command}", file=sys.stderr)
    sys.exit(2)


app = main
