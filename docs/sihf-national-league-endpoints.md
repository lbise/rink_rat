# SIHF And National League Endpoint Research

This document records endpoint candidates confirmed from the public SIHF and National League pages during MVP discovery.

Confirmed with Playwright on 2026-06-03 against these pages:

- `https://www.sihf.ch/fr/game-center/national-league/#/teams/goalsFor/desc/page/0/`
- `https://www.nationalleague.ch/club/103138?tab=team`

The endpoints are publicly reachable, but public reachability is not approval for public or commercial reuse. Treat all data as `prototype_only` until usage rights, attribution, rate limits, and provider terms are reviewed.

## MVP Source Decision

Use the National League app API as the primary source for the first MVP adapter.

Primary base URL:

- `https://www.nationalleague.ch/api`

Reasoning:

- It returns plain JSON instead of SIHF JSONP.
- It exposes stable-looking `teamId`, `gameId`, and `playerId` values.
- It covers teams, standings, full-season games, team games, game detail, rosters, player stats, playoffs, playouts, and top scorers.
- Its game detail endpoint is already shaped closer to product use than the SIHF generic table payloads.
- The SIHF player-stat table observed through the Game Center did not expose stable player IDs in row data, while the National League roster and lineup payloads do.

Initial adapter direction:

- Build `NationalLeagueAdapter` first.
- Keep SIHF endpoints documented as secondary/reference candidates.
- Do not mix SIHF and National League data in the first importer unless a specific MVP field is missing from National League.
- Retain external ID mapping from day one so SIHF can be added later without reshaping internal entities.

Recommended MVP National League endpoint set:

| Need | Endpoint |
| --- | --- |
| Teams and standings | `GET /api/teams?season=2026&lang=de-CH` |
| Full season schedule/results | `GET /api/games?season=2026&lang=de-CH` |
| Current games | `GET /api/games/current?lang=de-CH` |
| Team schedule/results | `GET /api/games/team/{team_id}?lang=de-CH` |
| Game detail | `GET /api/games/{game_id}?isApp=false&lang=de-CH` |
| Team roster/player stats | `GET /api/player/team/{team_id}?season=2026&lang=de-CH` |
| Playoffs | `GET /api/games/playoffs?season=2026&lang=de-CH` |
| Playouts | `GET /api/games/playouts?season=2026&lang=de-CH` |
| Top scorers | `GET /api/player/topscorer?season=2026&lang=de-CH` |

## SIHF Game Center

Base hosts observed:

- `https://data.sihf.ch/Statistic/api/cms`
- `https://data.sihf.ch/statistic/api/cms`

Observed behavior:

- Most SIHF data endpoints return JSONP, not plain JSON.
- The callback used by the public page is `externalStatisticsCallback`.
- Typical content type is `text/javascript; charset=utf-8`.
- Responses use generic table payloads with `header` aliases and row arrays in `data`.
- Season aliases use the season end year, for example `2026` means `2025/26`.
- Team IDs observed here match National League API team IDs, for example `103138` for Fribourg-Gotteron.

### Team Stats

Source page:

- `https://www.sihf.ch/fr/game-center/national-league/#/teams/goalsFor/desc/page/0/`

Observed request:

```text
GET https://data.sihf.ch/Statistic/api/cms/cache300?alias=teamGoal&searchQuery=1//1&filterQuery=&filterBy=Season,Phase&orderBy=goalsFor&orderByDescending=true&callback=externalStatisticsCallback&skip=-1&language=fr
```

Observed response metadata:

| Field | Value |
| --- | --- |
| Status | `200` |
| Type | `script` |
| Content-Type | `text/javascript; charset=utf-8` |
| Cache-Control | `max-age=300` |
| Response alias | `teamGoal` |
| `updateDateTime` sample | `2026-05-01T13:10:26.318698+02:00` |

Important query parameters:

| Parameter | Meaning |
| --- | --- |
| `alias` | Stat table alias, for example `teamGoal` |
| `searchQuery` | Competition scope; observed `1//1` for National League |
| `filterBy` | Positional filter names, observed `Season,Phase` |
| `filterQuery` | Positional filter values, slash-separated |
| `orderBy` | Header alias used for sorting, for example `goalsFor` |
| `orderByDescending` | Sort direction |
| `skip` | Observed `-1` for this route |
| `language` | UI/data language, observed `fr` |

Response shape notes:

- Top-level fields include `title`, `description`, `pages`, `selectedPage`, `orderBy`, `orderByDescending`, `isLive`, `availableExports`, `updateDateTime`, `filters`, `secondaryMenu`, `header`, `data`, and `alias`.
- `filters` included `Season` and `Phase` with selected values.
- The observed selected season was `2026`.
- The observed selected phase for this page was `5297` / `Playoff Overall`.
- `secondaryMenu` lists related team-stat aliases such as `teamGoal`, `teamGoalPosNation`, `teamShotDetail`, `teamPp`, `teamPk`, `teamFoul`, `teamShootout`, `teamFaceoff`, and attendance.
- Team rows contain a team object in the second column with `id`, `name`, `acronym`, `signed`, and `type`.

Useful related image endpoint:

```text
GET https://www.sihf.ch/Image/Club/{team_id}.png?w=60&h=60&scale=canvas
```

### Live Status Probe

Observed on the SIHF Game Center page:

```text
GET https://data.sihf.ch/statistic/api/cms/haslive?searchQuery=1,2,4,8,10,11&callback=externalStatisticsCallback&language=fr
```

This likely checks whether selected leagues or competitions currently have live games. It should be documented further before using it for product behavior.

### Standings

Verified through `scripts/sihf_demo.py`:

```text
GET https://data.sihf.ch/Statistic/api/cms/cache30?alias=standing&searchQuery=1//1&filterBy=Season,Phase,ContentType&filterQuery=2026//&orderBy=rank&orderByDescending=false&callback=externalStatisticsCallback&language=fr
```

Observed response notes:

- Response alias is `standing`.
- `Season` selected `2026` / `2025/26`.
- `Phase` selected `4940` / `Regular Season` when only season was supplied.
- `ContentType` selected `All`.
- Header aliases include `rank`, `team`, `gamesPlayed`, `points`, `gamesWonInTime`, `gamesWonExtraTime`, `gamesWonPenalty`, `gamesLostPenalty`, `gamesLostExtraTime`, `gamesLostInTime`, `goalsFor`, `goalsAgainst`, `goalsDifference`, and `streak`.
- Rows include team objects with SIHF/National League team IDs.

### Schedule And Results

Verified through `scripts/sihf_demo.py`:

```text
GET https://data.sihf.ch/Statistic/api/cms/cache300?alias=results&searchQuery=1,10//1&filterBy=season,phase,date,deferredState,team1,team2&filterQuery=2026/////&orderBy=date&orderByDescending=false&take=3&callback=externalStatisticsCallback&language=fr
```

Observed response notes:

- Response alias is `results`.
- `filterBy` order is important because `filterQuery` is positional.
- Filters include `Season`, `Phase`, `Date`, `DeferredState`, `team1`, and `team2`.
- `Phase` entries include `all`, `5318` / `Playoff Final`, `5317` / `Playoff 1/2 Final`, `5295` / `Playoff 1/4 Final`, `5307` / `Play-In Round 2`, `5293` / `Play-In Round 1`, `4940` / `Regular Season`, and `5294` / `Playout Final`.
- Row fields include day, local date, local start time, home team, away team, score, period score, OT/SO decision, game status, game detail link, and broadcasts.
- Game detail links expose SIHF game IDs, for example `20261105000421`.
- Game status objects include `id`, `updateDateTime`, `startDateTime`, `endDateTime`, `percent`, `name`, `canceled`, and `type`.

### Game Detail

Verified through `scripts/sihf_demo.py`:

```text
GET https://data.sihf.ch/statistic/api/cms/gameoverview?alias=gameDetail&searchQuery={game_id}&callback=externalStatisticsCallback&language=fr
```

Example:

```text
GET https://data.sihf.ch/statistic/api/cms/gameoverview?alias=gameDetail&searchQuery=20261105000421&callback=externalStatisticsCallback&language=fr
```

Observed response notes:

- Response alias is `gameDetail`.
- Top-level fields include `gameId`, `season`, `league`, `region`, `group`, `tournament`, `qualification`, `phase`, `broadcasts`, `result`, `details`, `status`, `startDateTime`, `endDateTime`, and `tables`.
- `result` includes final score, period scores, and shots-on-goal by period.
- `details` includes venue, spectators, referees, linesmen, home team, away team, and absentees.
- Tables include player stats, goalie stats, and team stats for both teams.

### Export Endpoints

Known from the existing discovery script, not re-confirmed through Playwright in this pass:

```text
GET https://data.sihf.ch/statistic/api/cms/export/gamedetails?searchQuery={game_id}&language={language}
GET https://data.sihf.ch/statistic/api/cms/export/teamrosters?searchQuery={team_id}&language={language}
```

These may return binary exports such as PDFs and should not be treated as primary normalized data unless needed for fallback/debugging.

## National League App API

Base host observed:

- `https://www.nationalleague.ch/api`

Observed behavior:

- Endpoints return plain JSON except image/logo endpoints.
- The club deep link document request returned `404`, but the SPA still loaded and made API calls.
- The club page used `lang=de-CH` and request header `accept-language: de-CH`.
- JSON responses observed `vary: accept-language` and `content-language: en-US`.
- Team IDs match SIHF Game Center team IDs in observed examples.

### Teams

Verified through `scripts/sihf_demo.py`:

```text
GET https://www.nationalleague.ch/api/teams
```

Observed response notes:

- Response is a JSON array.
- Important fields include `teamId`, `name`, `shortName`, `rank`, and `website`.
- This is a good candidate for the MVP team identity fixture.

### Team Logo

Observed on the National League club page:

```text
GET https://www.nationalleague.ch/api/teams/{team_id}/logo
```

Example:

```text
GET https://www.nationalleague.ch/api/teams/103138/logo
```

This returns image data. Logo and team mark usage needs separate rights review before public launch.

### Team Roster And Player Stats

Source page:

- `https://www.nationalleague.ch/club/103138?tab=team`

Observed request:

```text
GET https://www.nationalleague.ch/api/player/team/103138?lang=de-CH
```

Observed response metadata:

| Field | Value |
| --- | --- |
| Status | `200` |
| Type | `fetch` |
| Content-Type | `application/json; charset=utf-8` |
| Cache-Control | `public,max-age=600` |
| Vary | `accept-language` |
| Content-Language | `en-US` |

Observed response notes:

- Response is a JSON array.
- Important identity fields include `playerId`, `firstName`, `lastName`, `teamId`, `teamShortName`, `teamName`, `number`, `position`, `birth`, `height`, `weight`, and `hand`.
- The payload also includes many season/stat fields such as `gp`, `g`, `a1`, `a2`, `assists`, `points`, goalie stats, faceoff stats, shot stats, topscorer fields, captain flags, and per-game derived values.
- Position values observed include `goalkeeper`, `defender`, and `forwarder`.
- Some fields may be `null`, `None` as a string, `0`, or derived percentages. Adapter validation should be conservative.

### Player Image

Observed on the National League club page:

```text
GET https://www.nationalleague.ch/api/player/{player_id}/image
```

Example:

```text
GET https://www.nationalleague.ch/api/player/101791/image
```

Player image usage needs separate rights review before public launch.

### Team Games

Observed on the National League club page:

```text
GET https://www.nationalleague.ch/api/games/team/103138?lang=de-CH
```

Observed response metadata:

| Field | Value |
| --- | --- |
| Status | `200` |
| Type | `fetch` |
| Content-Type | `application/json; charset=utf-8` |
| Cache-Control | `public,max-age=10` |
| Vary | `accept-language` |
| Content-Language | `en-US` |

Observed response notes:

- Response is a JSON array.
- Important fields include `gameId`, `homeTeamShortName`, `homeTeamName`, `awayTeamShortName`, `awayTeamName`, `homeTeamId`, `awayTeamId`, `date`, `status`, `baseStatus`, `homeTeamResult`, `awayTeamResult`, `isOvertime`, `isShootout`, `isCurrent`, `isCurrentForTeam`, `spectators`, `referees`, `arena`, and broadcast/video fields.
- Example `date` value used UTC offset format, such as `2025-09-09T17:45:00+00:00`.
- Cache TTL is short, so this endpoint may be intended to support live-ish team schedule/results views.

### Content Endpoints

Observed on the National League club page but not core MVP data:

```text
GET https://www.nationalleague.ch/api/content/metadata?lang=de-CH
GET https://www.nationalleague.ch/api/content/news?tags=&lang=de-CH
GET https://www.nationalleague.ch/api/content/news?tags=Fribourg-Gott%C3%A9ron&lang=de-CH
```

These are news/content endpoints and should stay out of the initial normalized hockey data path unless the product scope changes.

## Fixture Targets

Recommended first National League fixtures, pending rights review:

| Fixture | Endpoint |
| --- | --- |
| `national_league_teams_2026_de_ch.json` | National League `/api/teams?season=2026&lang=de-CH` |
| `national_league_games_2026_de_ch.json` | National League `/api/games?season=2026&lang=de-CH` |
| `national_league_game_20261105000421_de_ch.json` | National League `/api/games/20261105000421?isApp=false&lang=de-CH` |
| `national_league_team_103138_players_2026_de_ch.json` | National League `/api/player/team/103138?season=2026&lang=de-CH` |
| `national_league_team_103138_games_de_ch.json` | National League `/api/games/team/103138?lang=de-CH` |
| `national_league_playoffs_2026_de_ch.json` | National League `/api/games/playoffs?season=2026&lang=de-CH` |
| `national_league_topscorer_2026_de_ch.json` | National League `/api/player/topscorer?season=2026&lang=de-CH` |

Optional secondary SIHF fixtures can be collected later if a specific field needs comparison or fallback coverage:

- `sihf_team_goal_2026_fr.jsonp`
- `sihf_standing_2026_regular_fr.jsonp`
- `sihf_results_2026_fr.jsonp`
- `sihf_game_detail_20261105000421_fr.jsonp`

Suggested fixture directory when we are ready to keep payloads:

```text
tests/fixtures/sources/national_league/
tests/fixtures/sources/sihf/  # Optional secondary fixtures only.
```

## Open Questions

- Confirm provider terms, attribution requirements, and rate limits before public use.
- Confirm whether `data.sihf.ch/Statistic` and `data.sihf.ch/statistic` are equivalent and stable.
- Test language behavior for `language=de`, `language=fr`, `language=en`, `lang=de-CH`, and possible English variants.
- Confirm whether SIHF `searchQuery=1//1` and `searchQuery=1,10//1` are stable National League scope values.
- Confirm whether National League `lang=de-CH` has an English equivalent suitable for MVP fixtures, or whether the adapter should fetch `de-CH` and normalize labels internally.
- Verify how SIHF date filters should be generated for arbitrary dates instead of consuming only returned filter aliases.
- Normalize time zones carefully because SIHF returns local `+01:00` or `+02:00` timestamps while the National League team-games endpoint observed UTC-style timestamps.
