"""Normalizers for the public National League app API payloads."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Mapping


SOURCE = "national_league"


@dataclass(frozen=True, slots=True)
class NormalizedTeam:
    source: str
    source_id: str
    name: str
    short_name: str | None
    website_url: str | None
    rank: int | None
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class NormalizedStandingRow:
    source: str
    team_source_id: str
    rank: int | None
    games_played: int | None
    points: int | None
    wins: int | None
    losses: int | None
    regulation_wins: int | None
    overtime_wins: int | None
    shootout_wins: int | None
    regulation_losses: int | None
    overtime_losses: int | None
    shootout_losses: int | None
    goals_for: int | None
    goals_against: int | None
    goal_difference: int | None
    streak: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class NormalizedPlayer:
    source: str
    source_id: str
    first_name: str
    last_name: str
    display_name: str
    birth_date: date | None
    nationality_country_code: str | None
    position: str
    shoots: str | None
    height_cm: int | None
    weight_kg: int | None
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class NormalizedRosterMembership:
    source: str
    player_source_id: str
    team_source_id: str
    season: str | None
    jersey_number: str | None
    position: str
    is_captain: bool
    first_goalkeeper: bool


@dataclass(frozen=True, slots=True)
class NormalizedGame:
    source: str
    source_id: str
    starts_at_utc: datetime | None
    home_team_source_id: str
    away_team_source_id: str
    home_team_name: str
    away_team_name: str
    home_team_short_name: str | None
    away_team_short_name: str | None
    status: str
    source_status: str | None
    is_live: bool
    is_final: bool
    ended_in: str
    home_score: int | None
    away_score: int | None
    arena: str | None
    spectators: int | None


@dataclass(frozen=True, slots=True)
class NormalizedLineupPlayer:
    source: str
    player_source_id: str
    team_side: str
    line: int | None
    first_name: str
    last_name: str
    display_name: str
    jersey_number: str | None
    position: str
    is_topscorer: bool
    is_captain: bool
    first_goalkeeper: bool


@dataclass(frozen=True, slots=True)
class NormalizedGameAction:
    source: str
    action_type: str
    team_source_id: str | None
    is_home_team: bool | None
    period: int | None
    overtime: int | None
    elapsed_seconds: int | None
    player_name: str | None
    player_number: str | None
    home_score: int | None
    away_score: int | None
    situation: str | None


@dataclass(frozen=True, slots=True)
class NormalizedPlayerGameStats:
    source: str
    team_side: str
    first_name: str
    last_name: str
    display_name: str
    jersey_number: str | None
    position: str
    goals: int | None
    assists: int | None
    points: int | None
    penalty_minutes: int | None
    shots_on_goal: int | None
    time_on_ice_seconds: int | None


@dataclass(frozen=True, slots=True)
class NormalizedGameDetail:
    source: str
    game: NormalizedGame
    home_lineup: tuple[NormalizedLineupPlayer, ...]
    away_lineup: tuple[NormalizedLineupPlayer, ...]
    actions: tuple[NormalizedGameAction, ...]
    home_player_stats: tuple[NormalizedPlayerGameStats, ...]
    away_player_stats: tuple[NormalizedPlayerGameStats, ...]
    home_team_stats: Mapping[str, Any]
    away_team_stats: Mapping[str, Any]
    home_shots: tuple[Mapping[str, Any], ...]
    away_shots: tuple[Mapping[str, Any], ...]


@dataclass(frozen=True, slots=True)
class NormalizedRoundSeries:
    source: str
    round_name: str
    group: int | None
    home_team_source_id: str
    away_team_source_id: str
    home_team_short_name: str | None
    away_team_short_name: str | None
    home_series_wins: int | None
    away_series_wins: int | None
    best_of: int | None
    title: str | None
    games: tuple[NormalizedGame, ...]


@dataclass(frozen=True, slots=True)
class NormalizedPlayerStatLine:
    source: str
    player_source_id: str
    team_source_id: str
    first_name: str
    last_name: str
    display_name: str
    position: str
    games_played: int | None
    goals: int | None
    assists: int | None
    points: int | None


def map_team(payload: Mapping[str, Any]) -> NormalizedTeam:
    return NormalizedTeam(
        source=SOURCE,
        source_id=_required_str(payload, "teamId"),
        name=_clean_str(payload.get("name")) or "",
        short_name=_clean_str(payload.get("shortName")),
        website_url=_clean_str(payload.get("website")),
        rank=_int_or_none(payload.get("rank")),
    )


def map_teams(payload: list[Mapping[str, Any]]) -> list[NormalizedTeam]:
    return [map_team(item) for item in payload]


def map_standing_row(payload: Mapping[str, Any]) -> NormalizedStandingRow:
    goals_for = _int_or_none(payload.get("g"))
    goals_against = _int_or_none(payload.get("ga"))
    goal_difference = None
    if goals_for is not None and goals_against is not None:
        goal_difference = goals_for - goals_against

    return NormalizedStandingRow(
        source=SOURCE,
        team_source_id=_required_str(payload, "teamId"),
        rank=_int_or_none(payload.get("rank")),
        games_played=_int_or_none(payload.get("gp")),
        points=_int_or_none(payload.get("po")),
        wins=_int_or_none(payload.get("gw")),
        losses=_int_or_none(payload.get("gl")),
        regulation_wins=_int_or_none(payload.get("gwit")),
        overtime_wins=_int_or_none(payload.get("gwo")),
        shootout_wins=_int_or_none(payload.get("gwpe")),
        regulation_losses=_int_or_none(payload.get("glit")),
        overtime_losses=_int_or_none(payload.get("glo")),
        shootout_losses=_int_or_none(payload.get("glpe")),
        goals_for=goals_for,
        goals_against=goals_against,
        goal_difference=goal_difference,
        streak=_string_tuple(payload.get("streak")),
    )


def map_standings(payload: list[Mapping[str, Any]]) -> list[NormalizedStandingRow]:
    return [map_standing_row(item) for item in payload]


def map_player(payload: Mapping[str, Any]) -> NormalizedPlayer:
    first_name = _clean_str(payload.get("firstName")) or ""
    last_name = _clean_str(payload.get("lastName")) or ""

    return NormalizedPlayer(
        source=SOURCE,
        source_id=_required_str(payload, "playerId"),
        first_name=first_name,
        last_name=last_name,
        display_name=_join_name(first_name, last_name),
        birth_date=_date_or_none(payload.get("birth")),
        nationality_country_code=_clean_str(payload.get("nationality")),
        position=normalize_position(payload.get("position")),
        shoots=_clean_str(payload.get("hand")),
        height_cm=_int_or_none(payload.get("height")),
        weight_kg=_int_or_none(payload.get("weight")),
    )


def map_players(payload: list[Mapping[str, Any]]) -> list[NormalizedPlayer]:
    return [map_player(item) for item in payload]


def map_roster_membership(
    payload: Mapping[str, Any], *, season: str | None = None
) -> NormalizedRosterMembership:
    return NormalizedRosterMembership(
        source=SOURCE,
        player_source_id=_required_str(payload, "playerId"),
        team_source_id=_required_str(payload, "teamId"),
        season=season,
        jersey_number=_clean_str(payload.get("number")),
        position=normalize_position(payload.get("position")),
        is_captain=bool(payload.get("isCaptain")),
        first_goalkeeper=bool(payload.get("firstGoalkeeper")),
    )


def map_roster_memberships(
    payload: list[Mapping[str, Any]], *, season: str | None = None
) -> list[NormalizedRosterMembership]:
    return [map_roster_membership(item, season=season) for item in payload]


def map_game(payload: Mapping[str, Any]) -> NormalizedGame:
    source_status = _clean_str(payload.get("status") or payload.get("baseStatus"))
    status = normalize_game_status(payload)

    return NormalizedGame(
        source=SOURCE,
        source_id=_required_str(payload, "gameId"),
        starts_at_utc=_datetime_or_none(payload.get("date")),
        home_team_source_id=_required_str(payload, "homeTeamId"),
        away_team_source_id=_required_str(payload, "awayTeamId"),
        home_team_name=_clean_str(payload.get("homeTeamName")) or "",
        away_team_name=_clean_str(payload.get("awayTeamName")) or "",
        home_team_short_name=_clean_str(payload.get("homeTeamShortName")),
        away_team_short_name=_clean_str(payload.get("awayTeamShortName")),
        status=status,
        source_status=source_status,
        is_live=status in {"live", "intermission"},
        is_final=status in {"final", "final_ot", "final_so"},
        ended_in=normalize_ended_in(payload, status),
        home_score=_int_or_none(payload.get("homeTeamResult")),
        away_score=_int_or_none(payload.get("awayTeamResult")),
        arena=_clean_str(payload.get("arena")),
        spectators=_int_or_none(payload.get("spectators")),
    )


def map_games(payload: list[Mapping[str, Any]]) -> list[NormalizedGame]:
    return [map_game(item) for item in payload]


def map_game_detail(payload: Mapping[str, Any]) -> NormalizedGameDetail:
    overview = payload.get("overview")
    if not isinstance(overview, Mapping):
        raise ValueError("Game detail payload is missing an overview object.")

    return NormalizedGameDetail(
        source=SOURCE,
        game=map_game(overview),
        home_lineup=tuple(_map_lineup(payload.get("lineupHome"), team_side="home")),
        away_lineup=tuple(_map_lineup(payload.get("lineupAway"), team_side="away")),
        actions=tuple(_map_actions(payload.get("actions"))),
        home_player_stats=tuple(
            _map_player_game_stats(payload.get("playerStatsHome"), team_side="home")
        ),
        away_player_stats=tuple(
            _map_player_game_stats(payload.get("playerStatsAway"), team_side="away")
        ),
        home_team_stats=_mapping_or_empty(payload.get("teamStatsHome")),
        away_team_stats=_mapping_or_empty(payload.get("teamStatsAway")),
        home_shots=tuple(_mapping_items(payload.get("shotsHome"))),
        away_shots=tuple(_mapping_items(payload.get("shotsAway"))),
    )


def map_round_series(payload: list[Mapping[str, Any]]) -> list[NormalizedRoundSeries]:
    series_rows: list[NormalizedRoundSeries] = []

    for round_payload in payload:
        round_name = _clean_str(round_payload.get("round")) or "unknown"
        matchups = round_payload.get("games")
        if not isinstance(matchups, list):
            continue

        for matchup in matchups:
            if not isinstance(matchup, Mapping):
                continue

            games = matchup.get("games")
            normalized_games = tuple(
                map_game(game) for game in games if isinstance(game, Mapping)
            ) if isinstance(games, list) else ()

            series_rows.append(
                NormalizedRoundSeries(
                    source=SOURCE,
                    round_name=round_name,
                    group=_int_or_none(matchup.get("group")),
                    home_team_source_id=_required_str(matchup, "homeTeamId"),
                    away_team_source_id=_required_str(matchup, "awayTeamId"),
                    home_team_short_name=_clean_str(matchup.get("homeTeamShortName")),
                    away_team_short_name=_clean_str(matchup.get("awayTeamShortName")),
                    home_series_wins=_int_or_none(matchup.get("homeTeamResult")),
                    away_series_wins=_int_or_none(matchup.get("awayTeamResult")),
                    best_of=_int_or_none(matchup.get("bestOf")),
                    title=_clean_str(matchup.get("title")),
                    games=normalized_games,
                )
            )

    return series_rows


def map_player_stat_line(payload: Mapping[str, Any]) -> NormalizedPlayerStatLine:
    first_name = _clean_str(payload.get("firstName")) or ""
    last_name = _clean_str(payload.get("lastName")) or ""

    return NormalizedPlayerStatLine(
        source=SOURCE,
        player_source_id=_required_str(payload, "playerId"),
        team_source_id=_required_str(payload, "teamId"),
        first_name=first_name,
        last_name=last_name,
        display_name=_join_name(first_name, last_name),
        position=normalize_position(payload.get("position")),
        games_played=_int_or_none(payload.get("gp")),
        goals=_int_or_none(payload.get("g")),
        assists=_int_or_none(payload.get("assists")),
        points=_int_or_none(payload.get("points")),
    )


def map_player_stat_lines(payload: list[Mapping[str, Any]]) -> list[NormalizedPlayerStatLine]:
    return [map_player_stat_line(item) for item in payload]


def normalize_position(value: Any) -> str:
    position = (_clean_str(value) or "").lower()
    return {
        "goalie": "goalkeeper",
        "goalkeeper": "goalkeeper",
        "defenseman": "defender",
        "defender": "defender",
        "forward": "forward",
        "forwarder": "forward",
    }.get(position, "unknown")


def normalize_game_status(payload: Mapping[str, Any]) -> str:
    status = (_clean_str(payload.get("status") or payload.get("baseStatus")) or "").lower()

    if status in {"finished", "final"}:
        if payload.get("isShootout"):
            return "final_so"
        if payload.get("isOvertime"):
            return "final_ot"
        return "final"

    return {
        "planned": "scheduled",
        "scheduled": "scheduled",
        "upcoming": "scheduled",
        "live": "live",
        "running": "live",
        "intermission": "intermission",
        "postponed": "postponed",
        "cancelled": "cancelled",
        "canceled": "cancelled",
    }.get(status, "unknown")


def normalize_ended_in(payload: Mapping[str, Any], status: str) -> str:
    if payload.get("isShootout"):
        return "shootout"
    if payload.get("isOvertime"):
        return "overtime"
    if status in {"final", "final_ot", "final_so"}:
        return "regulation"
    return "unknown"


def _map_lineup(payload: Any, *, team_side: str) -> list[NormalizedLineupPlayer]:
    lineups: list[NormalizedLineupPlayer] = []
    if not isinstance(payload, list):
        return lineups

    for line_payload in payload:
        if not isinstance(line_payload, Mapping):
            continue
        line = _int_or_none(line_payload.get("line"))
        players = line_payload.get("players")
        if not isinstance(players, list):
            continue

        for player in players:
            if not isinstance(player, Mapping):
                continue

            first_name = _clean_str(player.get("firstName")) or ""
            last_name = _clean_str(player.get("lastName")) or ""
            lineups.append(
                NormalizedLineupPlayer(
                    source=SOURCE,
                    player_source_id=_required_str(player, "playerId"),
                    team_side=team_side,
                    line=line,
                    first_name=first_name,
                    last_name=last_name,
                    display_name=_join_name(first_name, last_name),
                    jersey_number=_clean_str(player.get("number")),
                    position=normalize_position(player.get("position")),
                    is_topscorer=bool(player.get("isTopscorer")),
                    is_captain=bool(player.get("isCaptain")),
                    first_goalkeeper=bool(player.get("firstGoalkeeper")),
                )
            )

    return lineups


def _map_actions(payload: Any) -> list[NormalizedGameAction]:
    actions: list[NormalizedGameAction] = []
    if not isinstance(payload, list):
        return actions

    for period_payload in payload:
        if not isinstance(period_payload, Mapping):
            continue
        period = _int_or_none(period_payload.get("third"))
        period_actions = period_payload.get("actions")
        if not isinstance(period_actions, list):
            continue

        for action in period_actions:
            if not isinstance(action, Mapping):
                continue

            first_name = _clean_str(action.get("playerFirstName"))
            last_name = _clean_str(action.get("playerLastName"))
            actions.append(
                NormalizedGameAction(
                    source=SOURCE,
                    action_type=_clean_str(action.get("action")) or "unknown",
                    team_source_id=_clean_str(action.get("teamId")),
                    is_home_team=_bool_or_none(action.get("homeTeam")),
                    period=_int_or_none(action.get("third")) or period,
                    overtime=_int_or_none(action.get("overtime")),
                    elapsed_seconds=_int_or_none(action.get("time")),
                    player_name=_join_name(first_name, last_name) if first_name or last_name else None,
                    player_number=_clean_str(action.get("playerNumber")),
                    home_score=_int_or_none(action.get("homeTeamResult")),
                    away_score=_int_or_none(action.get("awayTeamResult")),
                    situation=_clean_str(action.get("situation")),
                )
            )

    return actions


def _map_player_game_stats(payload: Any, *, team_side: str) -> list[NormalizedPlayerGameStats]:
    stats: list[NormalizedPlayerGameStats] = []
    if not isinstance(payload, list):
        return stats

    for player in payload:
        if not isinstance(player, Mapping):
            continue

        first_name = _clean_str(player.get("firstName")) or ""
        last_name = _clean_str(player.get("lastName")) or ""
        stats.append(
            NormalizedPlayerGameStats(
                source=SOURCE,
                team_side=team_side,
                first_name=first_name,
                last_name=last_name,
                display_name=_join_name(first_name, last_name),
                jersey_number=_clean_str(player.get("number")),
                position=normalize_position(player.get("position")),
                goals=_int_or_none(player.get("g")),
                assists=_int_or_none(player.get("a")),
                points=_int_or_none(player.get("pts")),
                penalty_minutes=_int_or_none(player.get("pim")),
                shots_on_goal=_int_or_none(player.get("sog")),
                time_on_ice_seconds=_int_or_none(player.get("toi")),
            )
        )

    return stats


def _clean_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text == "None":
        return None
    return text


def _required_str(payload: Mapping[str, Any], key: str) -> str:
    value = _clean_str(payload.get(key))
    if value is None:
        raise ValueError(f"Missing required field: {key}")
    return value


def _int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _bool_or_none(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)


def _date_or_none(value: Any) -> date | None:
    text = _clean_str(value)
    if text is None:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _datetime_or_none(value: Any) -> datetime | None:
    text = _clean_str(value)
    if text is None:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _join_name(first_name: str | None, last_name: str | None) -> str:
    return " ".join(part for part in (first_name, last_name) if part)


def _string_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    text = _clean_str(value)
    return (text,) if text else ()


def _mapping_or_empty(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _mapping_items(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]
