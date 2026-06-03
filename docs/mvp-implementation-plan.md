# Rink Rat MVP Implementation Plan

This document tracks the concrete implementation work for the first Rink Rat MVP. It should be updated as milestones are completed, blocked, or intentionally descoped.

## MVP Goal

Build a public-first Swiss National League fan experience for the 2025/2026 season using the National League app API as the first source adapter.

The MVP should let users browse:

- Home summary
- Scores and schedule/results
- Standings
- Teams
- Team rosters
- Game detail pages
- Basic search for teams, players, and competitions

No account system is required for MVP.

## Source Strategy

Primary source:

- `https://www.nationalleague.ch/api`

Secondary/reference source:

- SIHF Game Center endpoints documented in `docs/sihf-national-league-endpoints.md`

MVP rule:

- Build `NationalLeagueAdapter` first.
- Do not mix SIHF into the first importer unless the National League API is missing a required MVP field.
- Keep external ID mapping from day one so SIHF or other providers can be added later.

## Current Progress

- [x] Product and technical plan created in `docs/product-tech-plan.md`
- [x] Endpoint research documented in `docs/sihf-national-league-endpoints.md`
- [x] National League selected as primary MVP source
- [x] National League fixture payloads saved under `tests/fixtures/sources/national_league/`
- [x] Initial normalized National League adapter added in `rink_rat/adapters/national_league.py`
- [x] Fixture-based adapter tests added in `tests/test_national_league_adapter.py`
- [x] Adapter tests pass with `python3 -m unittest discover -s tests`

## Phase 1: Backend Foundation

Purpose:

Create the minimal backend project structure needed to persist and serve normalized hockey data.

Tasks:

- [ ] Add `pyproject.toml` with backend dependencies and test config
- [ ] Add FastAPI app package structure
- [ ] Add environment-driven settings
- [ ] Add structured logging basics
- [ ] Add database engine/session setup
- [ ] Add Alembic setup
- [ ] Add `/api/v1/health` endpoint
- [ ] Add basic backend app tests

Acceptance criteria:

- [ ] `python3 -m unittest discover -s tests` still passes
- [ ] Backend app imports cleanly
- [ ] Health endpoint test passes
- [ ] Required env vars are documented with safe local defaults where practical

## Phase 2: Persistence Model And Migration

Purpose:

Create the initial database schema for stable identity, external IDs, games, roster membership, standings, and import observability.

Tables:

- [ ] `data_sources`
- [ ] `competitions`
- [ ] `seasons`
- [ ] `phases`
- [ ] `teams`
- [ ] `players`
- [ ] `roster_memberships`
- [ ] `venues`
- [ ] `games`
- [ ] `standings`
- [ ] `standing_rows`
- [ ] `external_ids`
- [ ] `import_runs`

Tasks:

- [ ] Define SQLAlchemy 2.0 models
- [ ] Define enums/check constraints for controlled values
- [ ] Add useful uniqueness constraints and indexes
- [ ] Add Alembic initial migration
- [ ] Add migration smoke test or documented migration command

Acceptance criteria:

- [ ] Migration creates the initial schema from an empty database
- [ ] Models support internal IDs plus source-specific external IDs
- [ ] Games store canonical UTC start time and source-local context
- [ ] Import runs can record success, partial success, and failure

## Phase 3: National League Importer

Purpose:

Import National League fixture/live payloads into the database through normalized adapter outputs.

Import jobs:

- [ ] `sync_national_league_teams`
- [ ] `sync_national_league_standings`
- [ ] `sync_national_league_players`
- [ ] `sync_national_league_rosters`
- [ ] `sync_national_league_games`
- [ ] `sync_national_league_game_detail`
- [ ] `sync_national_league_playoffs`

Tasks:

- [ ] Add National League API client with timeout and user-agent settings
- [ ] Add fixture-backed importer tests before live fetch integration
- [ ] Upsert `DataSource`, `Competition`, and `Season`
- [ ] Upsert teams and team external IDs
- [ ] Upsert players and player external IDs
- [ ] Upsert roster memberships
- [ ] Upsert games and game external IDs
- [ ] Upsert venues when arena names are present
- [ ] Persist standings and standing rows
- [ ] Record import runs with counts and errors
- [ ] Ensure imports are idempotent

Acceptance criteria:

- [ ] Fixture import creates expected teams, players, games, standings, and external IDs
- [ ] Running the same import twice does not create duplicates
- [ ] Failed imports produce an `ImportRun` record
- [ ] Importer does not hard-delete stable domain records

## Phase 4: Backend Public API

Purpose:

Expose stable normalized data to the frontend through `/api/v1` routes.

Endpoints:

- [ ] `GET /api/v1/competitions`
- [ ] `GET /api/v1/competitions/{competition_id}`
- [ ] `GET /api/v1/competitions/{competition_id}/standings`
- [ ] `GET /api/v1/teams`
- [ ] `GET /api/v1/teams/{team_id}`
- [ ] `GET /api/v1/teams/{team_id}/players`
- [ ] `GET /api/v1/games`
- [ ] `GET /api/v1/games/{game_id}`
- [ ] `GET /api/v1/search`
- [ ] `GET /api/v1/admin/import-runs`
- [ ] `GET /api/v1/admin/source-health`
- [ ] `POST /api/v1/admin/sync/competition/{competition_id}`

Tasks:

- [ ] Add Pydantic v2 response schemas
- [ ] Add consistent pagination/filter conventions
- [ ] Add freshness metadata to relevant responses
- [ ] Add consistent API error format
- [ ] Add admin token protection for admin/import routes
- [ ] Add route tests using imported fixture data

Acceptance criteria:

- [ ] Public endpoints return normalized data without upstream-specific table shapes
- [ ] Frontend does not need National League or SIHF-specific logic
- [ ] Admin routes are protected
- [ ] API route tests cover success, not found, validation, and protected-route behavior

## Phase 5: Frontend Foundation

Purpose:

Create the public React Router application shell and connect it to the FastAPI backend.

Tasks:

- [ ] Add React Router v7 framework-mode frontend
- [ ] Add TypeScript
- [ ] Add Tailwind CSS
- [ ] Add shadcn/ui setup if still desired after frontend scaffold
- [ ] Add API client wrapper for FastAPI routes
- [ ] Add shared layout, navigation, and responsive shell
- [ ] Add loading, empty, error, and stale states

Acceptance criteria:

- [ ] Frontend runs locally against backend API
- [ ] Public pages are mobile-friendly at the shell level
- [ ] Basic accessibility patterns are established early

## Phase 6: MVP Public Pages

Purpose:

Implement the fan-facing MVP page set.

Pages:

- [ ] `/`
- [ ] `/scores`
- [ ] `/schedule`
- [ ] `/standings`
- [ ] `/teams`
- [ ] `/teams/{team_slug}`
- [ ] `/games/{game_id}/{game_slug}`
- [ ] `/search`

Components:

- [ ] Game card/list item
- [ ] Score/status badge
- [ ] Date navigation
- [ ] Standings table
- [ ] Team card/list item
- [ ] Roster table
- [ ] Game detail summary
- [ ] Search result list

Acceptance criteria:

- [ ] A user can browse from home to scores, standings, team detail, roster, and game detail
- [ ] Tables are readable on mobile
- [ ] Game states are not communicated by color alone
- [ ] Public pages include basic metadata titles/descriptions

## Phase 7: MVP QA And Accessibility

Purpose:

Verify the core fan-facing flows and avoid preventable accessibility regressions.

Tasks:

- [ ] Add backend test coverage for importer and API routes
- [ ] Add frontend component tests for game cards, standings, roster, and search results
- [ ] Add Playwright smoke tests for key public flows
- [ ] Add basic accessibility checks for critical pages
- [ ] Confirm timezone display behavior
- [ ] Confirm source freshness/stale indicators

Acceptance criteria:

- [ ] Home to game detail smoke flow passes
- [ ] Team page to roster smoke flow passes
- [ ] Scores/schedule date browsing smoke flow passes
- [ ] Critical accessibility checks pass

## Phase 8: Local Dev And Deployment Readiness

Purpose:

Make the MVP runnable and maintainable outside one-off scripts.

Tasks:

- [ ] Add local development docs
- [ ] Add example environment file
- [ ] Add Docker Compose or equivalent local service setup
- [ ] Add migration command documentation
- [ ] Add import command documentation
- [ ] Add production/staging deployment notes
- [ ] Document provider usage/legal status before public launch

Acceptance criteria:

- [ ] A fresh checkout can run backend, database, importer, and frontend from documented commands
- [ ] Admin/import endpoints are not publicly exposed without protection
- [ ] Source usage status is clearly marked before public deployment

## MVP Non-Goals

Do not build these before the MVP public browsing loop works:

- User accounts
- Account-based favorites
- Push notifications
- SSE/WebSocket live updates
- Multi-league support
- Full localization
- Native mobile app
- Advanced analytics
- Full admin UI

## Suggested Immediate Next Task

Start Phase 1 with backend foundation:

- Add `pyproject.toml`
- Add FastAPI app skeleton
- Add settings module
- Add `/api/v1/health`
- Add a basic health endpoint test

This is the smallest next implementation step that moves toward persistence and API delivery without overbuilding.
