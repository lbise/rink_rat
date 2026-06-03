#!/usr/bin/env python3
"""Proof-of-concept client for public National League endpoints.

This version is intentionally focused on the Swiss National League MVP data.
It uses the National League app API as the primary source:

    https://www.nationalleague.ch/api

Examples:
    python3 scripts/sihf_demo.py standings
    python3 scripts/sihf_demo.py results --take 10
    python3 scripts/sihf_demo.py teams
    python3 scripts/sihf_demo.py teamplayers 103138
    python3 scripts/sihf_demo.py teamgames 103138 --take 10
    python3 scripts/sihf_demo.py gameoverview 20261105000421
    python3 scripts/sihf_demo.py playoffs
    python3 scripts/sihf_demo.py topscorer

Notes:
- The script name is historical from the first SIHF discovery pass.
- The core commands now use National League JSON endpoints instead of SIHF
  JSONP table endpoints because these responses expose stable team, game, and
  player identifiers that are better suited to the MVP adapter.
- Public reachability is not usage approval. Treat these endpoints as
  prototype-only until provider terms, attribution, and rate limits are reviewed.
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

NL_API_BASE = "https://www.nationalleague.ch/api"
DEFAULT_LANGUAGE = "de-CH"
DEFAULT_SEASON = "2026"
USER_AGENT = "RinkRatEndpointDiscovery/0.4"

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
        default=DEFAULT_LANGUAGE,
        help=f"Request language passed to the National League API (default: {DEFAULT_LANGUAGE})",
    )



def add_common_season_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--season",
        default=DEFAULT_SEASON,
        help=f"Season alias or display value, for example 2026 or 2025/2026 (default: {DEFAULT_SEASON})",
    )



def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch data from public National League endpoints.",
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
        help="Fetch full-season National League schedule / results.",
    )
    add_common_season_argument(results_parser)
    add_common_language_argument(results_parser)
    results_parser.add_argument(
        "--take",
        type=int,
        default=20,
        help="Number of games to show in table output (default: 20). Use 0 for all.",
    )
    results_parser.add_argument(
        "--team-id",
        help="Optional team ID filter applied client-side.",
    )
    results_parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format (default: table).",
    )

    standings_parser = subparsers.add_parser(
        "standings",
        help="Fetch National League standings from the season teams endpoint.",
    )
    add_common_season_argument(standings_parser)
    add_common_language_argument(standings_parser)
    standings_parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format (default: table).",
    )

    teams_parser = subparsers.add_parser(
        "teams",
        help="List National League teams.",
    )
    add_common_season_argument(teams_parser)
    add_common_language_argument(teams_parser)
    teams_parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format for the extracted team list (default: table).",
    )

    teamplayers_parser = subparsers.add_parser(
        "teamplayers",
        help="List players for a National League team.",
    )
    teamplayers_parser.add_argument("team_id", help="National League team ID")
    add_common_season_argument(teamplayers_parser)
    add_common_language_argument(teamplayers_parser)
    teamplayers_parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format for the extracted player list (default: table).",
    )

    teamgames_parser = subparsers.add_parser(
        "teamgames",
        help="Fetch schedule / results for a single National League team.",
    )
    teamgames_parser.add_argument("team_id", help="National League team ID")
    add_common_language_argument(teamgames_parser)
    teamgames_parser.add_argument(
        "--take",
        type=int,
        default=20,
        help="Number of games to show in table output (default: 20). Use 0 for all.",
    )
    teamgames_parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format (default: table).",
    )

    current_parser = subparsers.add_parser(
        "current",
        help="Fetch current National League games.",
    )
    add_common_language_argument(current_parser)
    current_parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format (default: table).",
    )

    gameoverview_parser = subparsers.add_parser(
        "gameoverview",
        help="Fetch detailed information for a single National League game.",
    )
    gameoverview_parser.add_argument("game_id", help="National League game ID")
    add_common_language_argument(gameoverview_parser)
    gameoverview_parser.add_argument(
        "--format",
        choices=("summary", "json"),
        default="summary",
        help="Output format (default: summary).",
    )

    game_parser = subparsers.add_parser(
        "game",
        help="Alias for gameoverview.",
    )
    game_parser.add_argument("game_id", help="National League game ID")
    add_common_language_argument(game_parser)
    game_parser.add_argument(
        "--format",
        choices=("summary", "json"),
        default="summary",
        help="Output format (default: summary).",
    )

    playoffs_parser = subparsers.add_parser(
        "playoffs",
        help="Fetch National League playoff rounds.",
    )
    add_common_season_argument(playoffs_parser)
    add_common_language_argument(playoffs_parser)
    playoffs_parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format (default: table).",
    )

    playouts_parser = subparsers.add_parser(
        "playouts",
        help="Fetch National League playout rounds.",
    )
    add_common_season_argument(playouts_parser)
    add_common_language_argument(playouts_parser)
    playouts_parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format (default: table).",
    )

    topscorer_parser = subparsers.add_parser(
        "topscorer",
        help="Fetch National League top scorers.",
    )
    add_common_season_argument(topscorer_parser)
    add_common_language_argument(topscorer_parser)
    topscorer_parser.add_argument(
        "--take",
        type=int,
        default=20,
        help="Number of players to show in table output (default: 20). Use 0 for all.",
    )
    topscorer_parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format (default: table).",
    )

    return parser



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
        games_played = str(item.get("gp", "")).strip()
        points = str(item.get("po", "")).strip()

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
                "gp": games_played,
                "points": points,
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
        ("GP", "gp"),
        ("Pts", "points"),
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
        number_value = item.get("number")
        number = "" if number_value is None else str(number_value).strip()
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



def format_score(game: dict[str, Any]) -> str:
    home_score = game.get("homeTeamResult")
    away_score = game.get("awayTeamResult")
    if home_score is None or away_score is None:
        return "-"

    decision = ""
    if game.get("isOvertime"):
        decision = " OT"
    elif game.get("isShootout"):
        decision = " SO"

    return f"{home_score}-{away_score}{decision}"



def format_streak(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value or "")



def print_standings_table(rows: list[dict[str, Any]]) -> None:
    if not rows:
        print("No standings rows found.")
        return

    table: list[dict[str, str]] = []
    for item in rows:
        goals_for = item.get("g")
        goals_against = item.get("ga")
        goal_diff = ""
        if isinstance(goals_for, int) and isinstance(goals_against, int):
            goal_diff = str(goals_for - goals_against)

        table.append(
            {
                "rank": str(item.get("rank", "")),
                "team": str(item.get("name", "")),
                "gp": str(item.get("gp", "")),
                "pts": str(item.get("po", "")),
                "w": str(item.get("gw", "")),
                "l": str(item.get("gl", "")),
                "gf": str(goals_for if goals_for is not None else ""),
                "ga": str(goals_against if goals_against is not None else ""),
                "gd": goal_diff,
                "streak": format_streak(item.get("streak")),
            }
        )

    columns = [
        ("Rank", "rank"),
        ("Team", "team"),
        ("GP", "gp"),
        ("Pts", "pts"),
        ("W", "w"),
        ("L", "l"),
        ("GF", "gf"),
        ("GA", "ga"),
        ("GD", "gd"),
        ("Streak", "streak"),
    ]
    print_table(table, columns)



def game_to_row(game: dict[str, Any]) -> dict[str, str]:
    return {
        "date": str(game.get("date", "")),
        "id": str(game.get("gameId", "")),
        "home": str(game.get("homeTeamShortName") or game.get("homeTeamName") or ""),
        "away": str(game.get("awayTeamShortName") or game.get("awayTeamName") or ""),
        "score": format_score(game),
        "status": str(game.get("status") or game.get("baseStatus") or ""),
        "arena": str(game.get("arena", "")),
    }



def limit_items(items: list[Any], take: int | None) -> list[Any]:
    if take is None or take == 0:
        return items
    return items[:take]



def filter_games(games: list[dict[str, Any]], team_id: str | None) -> list[dict[str, Any]]:
    if not team_id:
        return games

    return [
        game
        for game in games
        if str(game.get("homeTeamId", "")) == team_id
        or str(game.get("awayTeamId", "")) == team_id
    ]



def print_games_table(games: list[dict[str, Any]], *, take: int | None = None) -> None:
    games = limit_items(games, take)
    if not games:
        print("No games found.")
        return

    rows = [game_to_row(game) for game in games]
    columns = [
        ("Date", "date"),
        ("Game", "id"),
        ("Home", "home"),
        ("Away", "away"),
        ("Score", "score"),
        ("Status", "status"),
        ("Arena", "arena"),
    ]
    print_table(rows, columns)



def print_round_games_table(rounds: list[dict[str, Any]]) -> None:
    rows: list[dict[str, str]] = []
    for round_item in rounds:
        round_name = str(round_item.get("round", ""))
        games = round_item.get("games")
        if not isinstance(games, list):
            continue

        for game in games:
            if not isinstance(game, dict):
                continue

            row = game_to_row(game)
            row["round"] = round_name
            rows.append(row)

    if not rows:
        print("No round games found.")
        return

    columns = [
        ("Round", "round"),
        ("Date", "date"),
        ("Game", "id"),
        ("Home", "home"),
        ("Away", "away"),
        ("Score", "score"),
        ("Status", "status"),
    ]
    print_table(rows, columns)



def print_topscorers_table(players: list[dict[str, Any]], *, take: int | None = None) -> None:
    players = limit_items(players, take)
    if not players:
        print("No players found.")
        return

    rows = []
    for index, player in enumerate(players, start=1):
        rows.append(
            {
                "rank": str(index),
                "player": " ".join(
                    part
                    for part in (
                        str(player.get("firstName", "")).strip(),
                        str(player.get("lastName", "")).strip(),
                    )
                    if part
                ),
                "team": str(player.get("teamShortName") or player.get("teamName") or ""),
                "pos": str(player.get("position", "")),
                "gp": str(player.get("gp", "")),
                "g": str(player.get("g", "")),
                "a": str(player.get("assists", "")),
                "pts": str(player.get("points", "")),
            }
        )

    columns = [
        ("Rank", "rank"),
        ("Player", "player"),
        ("Team", "team"),
        ("Pos", "pos"),
        ("GP", "gp"),
        ("G", "g"),
        ("A", "a"),
        ("Pts", "pts"),
    ]
    print_table(rows, columns)



def print_game_summary(payload: dict[str, Any]) -> None:
    overview = payload.get("overview")
    result = payload.get("result")

    if not isinstance(overview, dict):
        print("Unexpected game detail payload: missing overview.")
        return

    game_id = overview.get("gameId", "")
    home = overview.get("homeTeamName", "")
    away = overview.get("awayTeamName", "")
    date = overview.get("date", "")
    status = overview.get("status", "")
    arena = overview.get("arena", "")
    score = format_score(overview)

    print(f"Game: {game_id}")
    print(f"Date: {date}")
    print(f"Matchup: {home} vs {away}")
    print(f"Score: {score}")
    print(f"Status: {status}")
    if arena:
        print(f"Arena: {arena}")

    if isinstance(result, dict):
        periods = [
            (
                "1P",
                result.get("homeTeamFirstResult"),
                result.get("awayTeamFirstResult"),
            ),
            (
                "2P",
                result.get("homeTeamSecondResult"),
                result.get("awayTeamSecondResult"),
            ),
            (
                "3P",
                result.get("homeTeamThirdResult"),
                result.get("awayTeamThirdResult"),
            ),
        ]
        overtime_home = result.get("homeTeamOvertimeResult")
        overtime_away = result.get("awayTeamOvertimeResult")
        if overtime_home or overtime_away:
            periods.append(("OT", overtime_home, overtime_away))

        print("Periods:")
        for label, home_score, away_score in periods:
            print(f"  {label}: {home_score}-{away_score}")

    actions = payload.get("actions")
    if isinstance(actions, list):
        action_count = sum(
            len(item.get("actions", [])) for item in actions if isinstance(item, dict)
        )
        print(f"Actions: {action_count}")

    for key, label in (
        ("lineupHome", "Home lineup"),
        ("lineupAway", "Away lineup"),
        ("playerStatsHome", "Home player stats"),
        ("playerStatsAway", "Away player stats"),
    ):
        value = payload.get(key)
        if isinstance(value, list):
            print(f"{label}: {len(value)} rows")



def print_table(rows: list[dict[str, str]], columns: list[tuple[str, str]]) -> None:
    widths = {
        key: max(len(title), *(len(row.get(key, "")) for row in rows))
        for title, key in columns
    }

    header_line = "  ".join(title.ljust(widths[key]) for title, key in columns)
    separator_line = "  ".join("-" * widths[key] for _, key in columns)

    print(header_line)
    print(separator_line)
    for row in rows:
        print("  ".join(row.get(key, "").ljust(widths[key]) for _, key in columns))



def resolve_endpoint(args: argparse.Namespace) -> tuple[str, dict[str, str]]:
    if args.command == "results":
        return f"{NL_API_BASE}/games", {
            "season": normalize_season_alias(args.season),
            "lang": args.language,
        }

    if args.command in {"standings", "teams"}:
        return f"{NL_API_BASE}/teams", {
            "season": normalize_season_alias(args.season),
            "lang": args.language,
        }

    if args.command == "teamplayers":
        params: dict[str, str] = {"lang": args.language}

        season = normalize_season_alias(args.season)
        if season:
            params["season"] = season

        return f"{NL_API_BASE}/player/team/{args.team_id}", params

    if args.command == "teamgames":
        return f"{NL_API_BASE}/games/team/{args.team_id}", {
            "lang": args.language,
        }

    if args.command == "current":
        return f"{NL_API_BASE}/games/current", {
            "lang": args.language,
        }

    if args.command in {"gameoverview", "game"}:
        return f"{NL_API_BASE}/games/{args.game_id}", {
            "isApp": "false",
            "lang": args.language,
        }

    if args.command == "playoffs":
        return f"{NL_API_BASE}/games/playoffs", {
            "season": normalize_season_alias(args.season),
            "lang": args.language,
        }

    if args.command == "playouts":
        return f"{NL_API_BASE}/games/playouts", {
            "season": normalize_season_alias(args.season),
            "lang": args.language,
        }

    if args.command == "topscorer":
        return f"{NL_API_BASE}/player/topscorer", {
            "season": normalize_season_alias(args.season),
            "lang": args.language,
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

    payload = try_parse_json(body, content_type)
    if payload is None:
        pretty_print(content_type, body)
    elif getattr(args, "format", None) == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    elif args.command == "teams":
        try:
            print_team_table(extract_teams_from_nl_api(payload))
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    elif args.command == "standings":
        if not isinstance(payload, list):
            print("Unexpected standings payload: expected a JSON array.", file=sys.stderr)
            return 1
        print_standings_table(payload)
    elif args.command == "teamplayers":
        try:
            print_team_players_table(extract_team_players_from_nl_api(payload))
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    elif args.command == "results":
        if not isinstance(payload, list):
            print("Unexpected results payload: expected a JSON array.", file=sys.stderr)
            return 1
        print_games_table(
            filter_games(payload, args.team_id),
            take=args.take,
        )
    elif args.command in {"teamgames", "current"}:
        if not isinstance(payload, list):
            print("Unexpected games payload: expected a JSON array.", file=sys.stderr)
            return 1
        print_games_table(payload, take=getattr(args, "take", None))
    elif args.command in {"gameoverview", "game"}:
        if not isinstance(payload, dict):
            print("Unexpected game detail payload: expected a JSON object.", file=sys.stderr)
            return 1
        print_game_summary(payload)
    elif args.command in {"playoffs", "playouts"}:
        if not isinstance(payload, list):
            print("Unexpected round payload: expected a JSON array.", file=sys.stderr)
            return 1
        print_round_games_table(payload)
    elif args.command == "topscorer":
        if not isinstance(payload, list):
            print("Unexpected top scorer payload: expected a JSON array.", file=sys.stderr)
            return 1
        print_topscorers_table(payload, take=args.take)
    else:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    if args.output:
        print()
        save_output(args.output, body)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
