from __future__ import annotations

import json
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

from rink_rat.adapters import national_league as nl


FIXTURES = Path(__file__).parent / "fixtures" / "sources" / "national_league"


def load_fixture(name: str):
    with (FIXTURES / name).open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


class NationalLeagueAdapterTests(unittest.TestCase):
    def test_maps_teams_and_standings_from_season_teams_fixture(self) -> None:
        payload = load_fixture("teams_2026_de_ch.json")

        teams = nl.map_teams(payload)
        standings = nl.map_standings(payload)

        self.assertEqual(len(teams), 14)
        self.assertEqual(len(standings), 14)

        fribourg = next(team for team in teams if team.source_id == "103138")
        self.assertEqual(fribourg.source, "national_league")
        self.assertEqual(fribourg.name, "Fribourg-Gottéron")
        self.assertEqual(fribourg.short_name, "FRI")
        self.assertEqual(fribourg.rank, 2)
        self.assertEqual(fribourg.website_url, "https://www.gotteron.ch/")

        row = next(row for row in standings if row.team_source_id == "103138")
        self.assertEqual(row.rank, 2)
        self.assertEqual(row.games_played, 52)
        self.assertEqual(row.points, 100)
        self.assertEqual(row.wins, 37)
        self.assertEqual(row.losses, 15)
        self.assertEqual(row.regulation_wins, 24)
        self.assertEqual(row.overtime_wins, 5)
        self.assertEqual(row.shootout_wins, 8)
        self.assertEqual(row.goals_for, 172)
        self.assertEqual(row.goals_against, 126)
        self.assertEqual(row.goal_difference, 46)
        self.assertEqual(row.streak[:4], ("SW", "OW", "W", "OW"))

    def test_maps_full_season_games_fixture(self) -> None:
        payload = load_fixture("games_2026_de_ch.json")

        games = nl.map_games(payload)

        self.assertGreaterEqual(len(games), 400)

        final_game = next(game for game in games if game.source_id == "20261105000421")
        self.assertEqual(final_game.home_team_source_id, "101151")
        self.assertEqual(final_game.away_team_source_id, "103138")
        self.assertEqual(final_game.home_team_short_name, "HCD")
        self.assertEqual(final_game.away_team_short_name, "FRI")
        self.assertEqual(
            final_game.starts_at_utc,
            datetime(2026, 4, 30, 18, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(final_game.status, "final_ot")
        self.assertIs(final_game.is_final, True)
        self.assertEqual(final_game.ended_in, "overtime")
        self.assertEqual(final_game.home_score, 2)
        self.assertEqual(final_game.away_score, 3)
        self.assertEqual(final_game.arena, "zondacrypto-Arena")

    def test_maps_team_roster_players_and_memberships_fixture(self) -> None:
        payload = load_fixture("team_103138_players_2026_de_ch.json")

        players = nl.map_players(payload)
        memberships = nl.map_roster_memberships(payload, season="2026")

        self.assertEqual(len(players), 34)
        self.assertEqual(len(memberships), 34)

        berra = next(player for player in players if player.source_id == "101791")
        self.assertEqual(berra.display_name, "Reto Berra")
        self.assertEqual(berra.position, "goalkeeper")
        self.assertEqual(berra.birth_date, date(1987, 1, 3))

        berra_membership = next(
            membership for membership in memberships if membership.player_source_id == "101791"
        )
        self.assertEqual(berra_membership.team_source_id, "103138")
        self.assertEqual(berra_membership.season, "2026")
        self.assertEqual(berra_membership.jersey_number, "20")
        self.assertEqual(berra_membership.position, "goalkeeper")

        dandois_membership = next(
            membership for membership in memberships if membership.player_source_id == "320627"
        )
        self.assertIsNone(dandois_membership.jersey_number)
        self.assertEqual(dandois_membership.position, "forward")

    def test_maps_team_games_fixture(self) -> None:
        payload = load_fixture("team_103138_games_de_ch.json")

        games = nl.map_games(payload)

        self.assertGreaterEqual(len(games), 70)
        self.assertTrue(
            all(
                game.home_team_source_id == "103138" or game.away_team_source_id == "103138"
                for game in games
            )
        )

    def test_maps_game_detail_fixture(self) -> None:
        payload = load_fixture("game_20261105000421_de_ch.json")

        detail = nl.map_game_detail(payload)

        self.assertEqual(detail.game.source_id, "20261105000421")
        self.assertEqual(detail.game.status, "final_ot")
        self.assertEqual(len(detail.actions), 15)
        self.assertEqual(len(detail.home_lineup), 22)
        self.assertEqual(len(detail.away_lineup), 22)
        self.assertEqual(len(detail.home_player_stats), 22)
        self.assertEqual(len(detail.away_player_stats), 22)
        self.assertEqual(len(detail.home_shots), 86)
        self.assertEqual(len(detail.away_shots), 42)

        first_goal = next(action for action in detail.actions if action.action_type == "goal")
        self.assertEqual(first_goal.team_source_id, "103138")
        self.assertEqual(first_goal.player_name, "Henrik Borgström")
        self.assertEqual(first_goal.away_score, 1)
        self.assertEqual(first_goal.situation, "PP1")

        away_goalie = next(
            player for player in detail.away_lineup if player.player_source_id == "101791"
        )
        self.assertEqual(away_goalie.display_name, "Reto Berra")
        self.assertIs(away_goalie.first_goalkeeper, True)

        home_stats = next(
            stat for stat in detail.home_player_stats if stat.display_name == "Enzo Corvi"
        )
        self.assertEqual(home_stats.position, "forward")
        self.assertEqual(home_stats.time_on_ice_seconds, 998)

    def test_maps_playoff_round_series_fixture(self) -> None:
        payload = load_fixture("playoffs_2026_de_ch.json")

        series = nl.map_round_series(payload)

        self.assertEqual(len(series), 10)

        final = next(row for row in series if row.round_name == "final")
        self.assertEqual(final.home_team_source_id, "101151")
        self.assertEqual(final.away_team_source_id, "103138")
        self.assertEqual(final.home_series_wins, 3)
        self.assertEqual(final.away_series_wins, 4)
        self.assertEqual(final.best_of, 7)
        self.assertEqual(len(final.games), 7)

    def test_maps_top_scorer_fixture(self) -> None:
        payload = load_fixture("topscorer_2026_de_ch.json")

        scorers = nl.map_player_stat_lines(payload)

        self.assertEqual(len(scorers), 14)
        leader = scorers[0]
        self.assertEqual(leader.display_name, "Markus Granlund")
        self.assertEqual(leader.position, "forward")
        self.assertEqual(leader.games_played, 49)
        self.assertEqual(leader.goals, 22)
        self.assertEqual(leader.assists, 32)
        self.assertEqual(leader.points, 54)


if __name__ == "__main__":
    unittest.main()
