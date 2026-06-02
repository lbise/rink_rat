#!/usr/bin/env python3
"""Small proof-of-concept client for public SIHF / National League endpoints.

This version is intentionally focused on the Swiss National League (NL).
It uses the URLs currently referenced by the public SIHF Game Center pages.

Examples:
    python3 scripts/sihf_demo.py results

    python3 scripts/sihf_demo.py results \
        --filter Season=2025/2026 \
        --filter League="National League"

    python3 scripts/sihf_demo.py standings

    python3 scripts/sihf_demo.py teams

    python3 scripts/sihf_demo.py teamplayers 101151

    python3 scripts/sihf_demo.py gameoverview 20261105000421

    python3 scripts/sihf_demo.py gamedetails-export 20261105000421 \
        --output tmp/game_20261105000421.pdf

Notes:
- The older host dvdata.sihf.ch does not appear to be publicly resolvable.
  The current public SIHF pages reference data.sihf.ch instead.
- Many SIHF endpoints return JSONP rather than plain JSON. This script unwraps
  that automatically and prints the JSON payload.
- For schedule / standings filters, SIHF often expects internal alias values.
  This script translates seasons like 2025/2026 to 2026, and accepts a legacy
  --filter Season=... input for convenience.
- If you need exact filter aliases for advanced queries, first run the command
  without filters and inspect the returned "filters" section.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_BASE = "https://data.sihf.ch/statistic/api/cms"
CACHE_BASE = "https://data.sihf.ch/Statistic/api/cms"
EXPORT_BASE = f"{API_BASE}/export"
NL_API_BASE = "https://www.nationalleague.ch/api"
JSONP_CALLBACK = "externalStatisticsCallback"
USER_AGENT = "SwissHockeyHubPoC/0.3"

RESULTS_FILTER_ORDER = ["season", "phase", "date", "deferredstate", "team1", "team2"]
STANDINGS_FILTER_ORDER = ["season", "phase", "contenttype"]


class SupportedLegacyFilters:
    RESULTS = {"season", "phase", "deferredstate", "team1", "team2", "league"}
    STANDINGS = {"season", "phase", "contenttype", "league"}



def normalize_filter_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())



def normalize_season_alias(value: str | None) -> str:
    if value is None:
        return ""

    cleaned = value.strip()
    if not cleaned:
        return ""

    if cleaned.isdigit():
        return cleaned

    match = re.fullmatch(r"(\d{4})\s*[/\-]\s*(\d{2}|\d{4})", cleaned)
    if match:
        end_year = match.group(2)
        if len(end_year) == 2:
            century = match.group(1)[:2]
            return f"{century}{end_year}"
        return end_year

    return cleaned



def parse_legacy_filters(filters: list[str], *, allowed: set[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}

    for item in filters:
        if "=" not in item:
            raise ValueError(
                f"Invalid filter '{item}'. Expected KEY=VALUE, for example Season=2025/2026"
            )

        key, value = item.split("=", 1)
        key = normalize_filter_key(key)
        value = value.strip()

        if not key or not value:
            raise ValueError(
                f"Invalid filter '{item}'. Both key and value must be non-empty."
            )

        if key not in allowed:
            supported = ", ".join(sorted(allowed))
            raise ValueError(
                f"Unsupported filter '{item}'. Supported legacy filters: {supported}"
            )

        parsed[key] = value

    return parsed



def build_slash_filter_query(values: list[str]) -> str:
    return "/".join(value or "" for value in values)



def build_url(base_url: str, params: dict[str, str]) -> str:
    clean_params = {key: value for key, value in params.items() if value is not None}
    if not clean_params:
        return base_url
    return f"{base_url}?{urlencode(clean_params)}"



def fetch(base_url: str, params: dict[str, str], timeout: int) -> tuple[str, str, bytes]:
    url = build_url(base_url, params)
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/plain, application/javascript, */*",
        },
    )

    with urlopen(request, timeout=timeout) as response:
        body = response.read()
        content_type = response.headers.get("Content-Type", "")
        return url, content_type, body



def detect_charset(content_type: str) -> str:
    for part in content_type.split(";"):
        part = part.strip()
        if part.lower().startswith("charset="):
            return part.split("=", 1)[1].strip() or "utf-8"
    return "utf-8"



def try_parse_jsonp(text: str) -> Any | None:
    patterns = [
        r"&&\s*[A-Za-z0-9_$.]+\((.*)\);\s*$",
        r"^[A-Za-z0-9_$.]+\((.*)\);\s*$",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.S)
        if not match:
            continue

        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            continue

    return None



def try_parse_json(body: bytes, content_type: str = "") -> Any | None:
    charset = detect_charset(content_type)

    try:
        text = body.decode(charset)
    except (UnicodeDecodeError, LookupError):
        try:
            text = body.decode("utf-8")
        except UnicodeDecodeError:
            return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return try_parse_jsonp(text)



def is_probably_binary(content_type: str, body: bytes) -> bool:
    content_type = content_type.lower()
    if any(token in content_type for token in ("json", "javascript", "text/", "xml", "html")):
        return False

    if any(token in content_type for token in ("octet-stream", "pdf", "image/", "zip", "gzip")):
        return True

    if not body:
        return False

    if b"\x00" in body[:1024]:
        return True

    sample = body[:1024]
    non_printable = sum(byte < 9 or (13 < byte < 32) for byte in sample)
    return non_printable / max(len(sample), 1) > 0.15



def pretty_print(content_type: str, body: bytes) -> None:
    parsed_json = try_parse_json(body, content_type)
    if parsed_json is not None:
        print(json.dumps(parsed_json, indent=2, ensure_ascii=False))
        return

    if is_probably_binary(content_type, body):
        print(f"Binary response received ({len(body)} bytes). Use --output to save it.")
        return

    charset = detect_charset(content_type)
    try:
        print(body.decode(charset, errors="replace"))
    except LookupError:
        print(body.decode("utf-8", errors="replace"))



def save_output(path: str, body: bytes) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(body)
    print(f"Saved raw response to: {output_path}")



def add_common_language_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--language",
        default="de",
        help="Request language passed to SIHF (default: de)",
    )



def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch data from public SIHF / National League endpoints.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="HTTP timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--output",
        help="Optional file path to save the raw response body.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    results_parser = subparsers.add_parser(
        "results",
        help="Fetch National League schedule / results.",
    )
    results_parser.add_argument(
        "--season",
        help="Season alias or display value, for example 2026 or 2025/2026.",
    )
    results_parser.add_argument(
        "--phase",
        help="Optional SIHF phase alias (advanced).",
    )
    results_parser.add_argument(
        "--deferred-state",
        help="Optional SIHF deferredState alias (advanced).",
    )
    results_parser.add_argument(
        "--team1",
        help="Optional SIHF Team 1 alias (advanced).",
    )
    results_parser.add_argument(
        "--team2",
        help="Optional SIHF Team 2 alias (advanced).",
    )
    results_parser.add_argument(
        "--filter-query",
        help="Exact SIHF filterQuery override for advanced use.",
    )
    results_parser.add_argument(
        "--take",
        type=int,
        default=20,
        help="Number of rows to request (default: 20)",
    )
    results_parser.add_argument(
        "--filter",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help=(
            "Legacy convenience filter. Supported keys: Season, Phase, "
            "DeferredState, Team1, Team2, League. League is accepted but ignored "
            "because this command already targets National League."
        ),
    )
    add_common_language_argument(results_parser)

    standings_parser = subparsers.add_parser(
        "standings",
        help="Fetch National League standings.",
    )
    standings_parser.add_argument(
        "--season",
        help="Season alias or display value, for example 2026 or 2025/2026.",
    )
    standings_parser.add_argument(
        "--phase",
        help="Optional SIHF phase alias (advanced).",
    )
    standings_parser.add_argument(
        "--content-type",
        help="Optional SIHF ContentType alias (advanced).",
    )
    standings_parser.add_argument(
        "--filter-query",
        help="Exact SIHF filterQuery override for advanced use.",
    )
    standings_parser.add_argument(
        "--filter",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help=(
            "Legacy convenience filter. Supported keys: Season, Phase, "
            "ContentType, League. League is accepted but ignored because this "
            "command already targets National League."
        ),
    )
    add_common_language_argument(standings_parser)

    teams_parser = subparsers.add_parser(
        "teams",
        help="List National League teams via the public National League API.",
    )
    teams_parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format for the extracted team list (default: table).",
    )

    teamplayers_parser = subparsers.add_parser(
        "teamplayers",
        help="List players for a National League team via the public National League API.",
    )
    teamplayers_parser.add_argument("team_id", help="National League team ID")
    teamplayers_parser.add_argument(
        "--season",
        help="Optional season alias or display value, for example 2026 or 2025/2026.",
    )
    teamplayers_parser.add_argument(
        "--phase",
        help="Optional phase alias (advanced).",
    )
    teamplayers_parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format for the extracted player list (default: table).",
    )

    gameoverview_parser = subparsers.add_parser(
        "gameoverview",
        help="Fetch detailed information for a single game.",
    )
    gameoverview_parser.add_argument("game_id", help="SIHF game ID")
    add_common_language_argument(gameoverview_parser)

    gamedetails_parser = subparsers.add_parser(
        "gamedetails-export",
        help="Fetch the official exported game sheet for a single game.",
    )
    gamedetails_parser.add_argument("game_id", help="SIHF game ID")
    add_common_language_argument(gamedetails_parser)

    teamroster_parser = subparsers.add_parser(
        "teamroster-export",
        help="Fetch the official exported roster for a single team.",
    )
    teamroster_parser.add_argument("team_id", help="SIHF team ID / roster ID")
    add_common_language_argument(teamroster_parser)

    return parser



def build_results_filter_query(args: argparse.Namespace) -> str:
    legacy = parse_legacy_filters(args.filter, allowed=SupportedLegacyFilters.RESULTS)

    season = normalize_season_alias(args.season or legacy.get("season"))
    phase = args.phase or legacy.get("phase") or ""
    deferred_state = args.deferred_state or legacy.get("deferredstate") or ""
    team1 = args.team1 or legacy.get("team1") or ""
    team2 = args.team2 or legacy.get("team2") or ""

    league = legacy.get("league")
    if league and normalize_filter_key(league) not in {"nationleague", "nationalleague", "nl", "1"}:
        raise ValueError(
            "Only National League is supported by this script right now. "
            f"Received League={league!r}."
        )

    if args.filter_query is not None:
        return args.filter_query

    values = ["" for _ in RESULTS_FILTER_ORDER]
    mapping = {
        "season": season,
        "phase": phase,
        "deferredstate": deferred_state,
        "team1": team1,
        "team2": team2,
    }

    for index, name in enumerate(RESULTS_FILTER_ORDER):
        values[index] = mapping.get(name, "")

    if not any(values):
        return ""

    return build_slash_filter_query(values)



def build_standings_filter_query(args: argparse.Namespace) -> str:
    legacy = parse_legacy_filters(args.filter, allowed=SupportedLegacyFilters.STANDINGS)

    season = normalize_season_alias(args.season or legacy.get("season"))
    phase = args.phase or legacy.get("phase") or ""
    content_type = args.content_type or legacy.get("contenttype") or ""

    league = legacy.get("league")
    if league and normalize_filter_key(league) not in {"nationleague", "nationalleague", "nl", "1"}:
        raise ValueError(
            "Only National League is supported by this script right now. "
            f"Received League={league!r}."
        )

    if args.filter_query is not None:
        return args.filter_query

    values = [season, phase, content_type]
    if not any(values):
        return ""

    return build_slash_filter_query(values)



def extract_teams_from_nl_api(payload: Any) -> list[dict[str, str]]:
    if not isinstance(payload, list):
        raise ValueError("Unexpected teams payload: expected a JSON array.")

    teams: list[dict[str, str]] = []
    seen: set[str] = set()

    for item in payload:
        if not isinstance(item, dict):
            continue

        team_id = str(item.get("teamId", "")).strip()
        name = str(item.get("name", "")).strip()
        acronym = str(item.get("shortName", "")).strip()
        rank = str(item.get("rank", "")).strip()
        website = str(item.get("website", "")).strip()

        identity = team_id or name
        if not identity or identity in seen:
            continue

        seen.add(identity)
        teams.append(
            {
                "rank": rank,
                "id": team_id,
                "acronym": acronym,
                "name": name,
                "website": website,
                "logoUrl": f"{NL_API_BASE}/teams/{team_id}/logo" if team_id else "",
            }
        )

    def sort_key(team: dict[str, str]) -> tuple[int, str]:
        rank_value = team.get("rank", "")
        return (int(rank_value) if rank_value.isdigit() else 9999, team.get("name", ""))

    teams.sort(key=sort_key)
    return teams



def print_team_table(teams: list[dict[str, str]]) -> None:
    if not teams:
        print("No teams found.")
        return

    columns = [
        ("Rank", "rank"),
        ("ID", "id"),
        ("Acr", "acronym"),
        ("Team", "name"),
    ]
    widths = {
        key: max(len(title), *(len(team.get(key, "")) for team in teams))
        for title, key in columns
    }

    header_line = "  ".join(title.ljust(widths[key]) for title, key in columns)
    separator_line = "  ".join("-" * widths[key] for _, key in columns)

    print(header_line)
    print(separator_line)
    for team in teams:
        print(
            "  ".join(
                team.get(key, "").ljust(widths[key]) for _, key in columns
            )
        )



def extract_team_players_from_nl_api(payload: Any) -> list[dict[str, str]]:
    if not isinstance(payload, list):
        raise ValueError("Unexpected team players payload: expected a JSON array.")

    players: list[dict[str, str]] = []
    seen: set[str] = set()

    position_order = {"goalkeeper": 0, "defender": 1, "forwarder": 2}

    for item in payload:
        if not isinstance(item, dict):
            continue

        player_id = str(item.get("playerId", "")).strip()
        first_name = str(item.get("firstName", "")).strip()
        last_name = str(item.get("lastName", "")).strip()
        number = str(item.get("number", "")).strip()
        position = str(item.get("position", "")).strip()

        identity = player_id or f"{first_name} {last_name}".strip()
        if not identity or identity in seen:
            continue

        seen.add(identity)
        players.append(
            {
                "id": player_id,
                "number": number,
                "firstName": first_name,
                "lastName": last_name,
                "name": " ".join(part for part in (first_name, last_name) if part),
                "position": position,
                "teamId": str(item.get("teamId", "")).strip(),
                "teamName": str(item.get("teamName", "")).strip(),
            }
        )

    def sort_key(player: dict[str, str]) -> tuple[int, int, str, str]:
        number_value = player.get("number", "")
        return (
            position_order.get(player.get("position", ""), 99),
            int(number_value) if number_value.isdigit() else 999,
            player.get("lastName", ""),
            player.get("firstName", ""),
        )

    players.sort(key=sort_key)
    return players



def print_team_players_table(players: list[dict[str, str]]) -> None:
    if not players:
        print("No players found.")
        return

    columns = [
        ("No", "number"),
        ("Pos", "position"),
        ("Name", "name"),
        ("ID", "id"),
    ]
    widths = {
        key: max(len(title), *(len(player.get(key, "")) for player in players))
        for title, key in columns
    }

    header_line = "  ".join(title.ljust(widths[key]) for title, key in columns)
    separator_line = "  ".join("-" * widths[key] for _, key in columns)

    print(header_line)
    print(separator_line)
    for player in players:
        print(
            "  ".join(
                player.get(key, "").ljust(widths[key]) for _, key in columns
            )
        )



def resolve_endpoint(args: argparse.Namespace) -> tuple[str, dict[str, str]]:
    if args.command == "results":
        return f"{CACHE_BASE}/cache300", {
            "alias": "results",
            "searchQuery": "1,10//1",
            "filterBy": "season,phase,date,deferredState,team1,team2",
            "filterQuery": build_results_filter_query(args),
            "orderBy": "date",
            "orderByDescending": "false",
            "take": str(args.take),
            "callback": JSONP_CALLBACK,
            "language": args.language,
        }

    if args.command == "standings":
        return f"{CACHE_BASE}/cache30", {
            "alias": "standing",
            "searchQuery": "1//1",
            "filterBy": "Season,Phase,ContentType",
            "filterQuery": build_standings_filter_query(args),
            "orderBy": "rank",
            "orderByDescending": "false",
            "callback": JSONP_CALLBACK,
            "language": args.language,
        }

    if args.command == "teams":
        return f"{NL_API_BASE}/teams", {}

    if args.command == "teamplayers":
        params: dict[str, str] = {}

        season = normalize_season_alias(args.season)
        if season:
            params["season"] = season

        if args.phase:
            params["phase"] = args.phase

        return f"{NL_API_BASE}/player/team/{args.team_id}", params

    if args.command == "gameoverview":
        return f"{API_BASE}/gameoverview", {
            "alias": "gameDetail",
            "searchQuery": args.game_id,
            "callback": JSONP_CALLBACK,
            "language": args.language,
        }

    if args.command == "gamedetails-export":
        return f"{EXPORT_BASE}/gamedetails", {
            "searchQuery": args.game_id,
            "language": args.language,
        }

    if args.command == "teamroster-export":
        return f"{EXPORT_BASE}/teamrosters", {
            "searchQuery": args.team_id,
            "language": args.language,
        }

    raise ValueError(f"Unsupported command: {args.command}")



def print_http_error(exc: HTTPError) -> None:
    print(f"HTTP error: {exc.code} {exc.reason}", file=sys.stderr)
    try:
        body = exc.read(600)
    except Exception:
        return

    if not body:
        return

    detail = body.decode("utf-8", errors="replace").strip()
    if detail:
        print(detail[:600], file=sys.stderr)



def main() -> int:
    parser = make_parser()
    args = parser.parse_args()

    try:
        base_url, params = resolve_endpoint(args)
        url, content_type, body = fetch(base_url, params, timeout=args.timeout)
    except ValueError as exc:
        parser.error(str(exc))
    except HTTPError as exc:
        print_http_error(exc)
        return 1
    except URLError as exc:
        print(f"Network error: {exc.reason}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - defensive for a quick PoC script
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1

    print(f"URL: {url}")
    if content_type:
        print(f"Content-Type: {content_type}")
    print()

    if args.command in {"teams", "teamplayers"}:
        payload = try_parse_json(body, content_type)
        if payload is None:
            message = (
                "Could not parse the teams response as JSON."
                if args.command == "teams"
                else "Could not parse the team players response as JSON."
            )
            print(message, file=sys.stderr)
            return 1

        try:
            if args.command == "teams":
                items = extract_teams_from_nl_api(payload)
            else:
                items = extract_team_players_from_nl_api(payload)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1

        if args.format == "json":
            print(json.dumps(items, indent=2, ensure_ascii=False))
        else:
            if args.command == "teams":
                print_team_table(items)
            else:
                print_team_players_table(items)
    else:
        pretty_print(content_type, body)

    if args.output:
        print()
        save_output(args.output, body)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
