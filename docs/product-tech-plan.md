# Rink Rat Product And Technical Plan

## Product Vision

Rink Rat is a fan-facing ice hockey web application focused on making live scores, schedules, standings, teams, rosters, tournaments, and game information easy to discover and enjoyable to follow.

Swiss hockey is the practical starting point because the current endpoint discovery work targets SIHF and National League data. The product itself should not be modeled as a Swiss-only app. It should be designed from the beginning to support any hockey league or competition, including domestic leagues like the NHL, SHL, Liiga, DEL, Czech Extraliga, and Swiss leagues, as well as international tournaments like the World Championship, World Juniors, U18 events, Olympics, and other national-team competitions.

The app should be public-first. Most of the core experience should be available without an account. Authentication should unlock personalization, not block access to basic hockey information.

## Target Experience

Rink Rat should feel like a clean, fast hockey companion for fans who want to answer questions like:

- Who is playing today?
- What is the current score?
- Where does my team sit in the standings?
- Who is on the roster?
- When is the next game?
- What happened in a specific game?
- Which players are leading in points, goals, assists, or goalie stats?

The primary product direction is fan-facing, not analyst-first. Advanced stats can exist later, but the initial product should emphasize clarity, speed, and team/player discovery.

## Competition Scope

The application should treat leagues and tournaments as first-class concepts.

Initial data source:

- Swiss National League / SIHF public data

MVP competition target:

- Swiss National League
- 2025/2026 season
- Completed season data, using the currently available SIHF / National League public data
- English interface copy
- Official team and player names preserved as provided by the source or official naming conventions

The MVP should be Swiss National League-focused for delivery clarity, but the domain model, adapters, IDs, and API routes should still be designed so future leagues and tournaments can be added without reshaping the application around Swiss-only assumptions.

Long-term supported competition types:

- Domestic club leagues
- Playoffs and cup competitions
- International senior tournaments
- Junior international tournaments
- National-team events
- Preseason or exhibition competitions if data is available

Examples of future competitions:

- NHL
- Swiss National League
- Swiss League
- SHL
- Liiga
- DEL
- Czech Extraliga
- IIHF World Championship
- World Junior Championship
- U18 World Championship
- Olympic hockey tournament

This means the domain model should avoid hard-coding Swiss-specific assumptions into core entities. Teams, players, games, standings, seasons, phases, and stats should all belong to a generic competition context.

Useful high-level model terms:

- `competition`: NHL, National League, World Championship, U18 World Championship
- `competition_type`: domestic_league, international_tournament, cup, exhibition
- `season`: 2025/2026, 2026, or tournament year
- `phase`: regular season, playoffs, group stage, quarterfinal, semifinal, final
- `team_type`: club or national_team
- `data_source`: SIHF, National League, NHL API, IIHF source, custom importer

## Data Usage And Legal Risk

Publicly reachable sports endpoints may be useful for private development, prototyping, and technical discovery, but public availability does not automatically mean the data is approved for public, commercial, or redistributed use.

Before public launch, each data source should be reviewed for terms, licensing, attribution requirements, rate limits, and allowed usage.

Guidelines:

- Public endpoints may be used for private development and prototyping.
- Before public launch, verify SIHF, National League, NHL, IIHF, Elite Prospects, and other provider terms as applicable.
- Avoid presenting unofficially sourced data as official.
- Store source attribution per competition and data source.
- Track source usage status, such as `prototype_only`, `approved`, `restricted`, or `unknown`.
- Avoid excessive polling, scraping-like behavior, or behavior that violates published terms or robots policies.
- Prepare to replace public endpoint usage with approved API access if needed.
- Treat logos, player images, league marks, team marks, and trademarks as separate rights concerns from statistics data.

This should be reflected in source adapter metadata. Each adapter should know the source name, attribution text, usage status, and any operational limits that affect imports, caching, or display.

## Tech Stack

### Frontend

Recommended stack:

- React Router v7 framework mode
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- TanStack Query

Rationale:

- React Router v7 framework mode preserves the React + TypeScript development model while adding route modules, data loading, server rendering, and a modern full-stack React routing model.
- React + TypeScript gives a strong component model and type safety.
- Tailwind enables fast styling while keeping the UI flexible.
- shadcn/ui provides accessible, composable components without locking the app into a heavy design system.
- TanStack Query remains useful for client-side interactive sections, live-ish data, refetching, stale states, and authenticated personalization.

Frontend decision:

- Use React Router v7 in framework mode instead of a client-only React SPA because the app is public-first and many pages should be discoverable, shareable, and previewable.
- Keep FastAPI as the main backend API. React Router should not replace the backend domain API.
- Public pages should support server rendering or pre-rendering depending on freshness needs.
- Live game widgets and highly interactive sections can hydrate on the client and use polling, SSE, WebSockets, or TanStack Query as needed.

### Service And Route Ownership

Because the frontend uses React Router framework mode and the backend uses FastAPI, route ownership should be explicit from the start.

Frontend service responsibilities:

- React Router application shell
- Public page routes
- Server rendering or pre-rendering for public pages when used
- Page metadata, canonical URLs, and shareability
- UI composition and client-side interactivity
- Calling the FastAPI backend for normalized data

Frontend-owned routes:

- `/`
- `/scores`
- `/schedule`
- `/standings`
- `/competitions/...`
- `/teams/...`
- `/players/...`
- `/games/...`
- `/search`

Backend service responsibilities:

- FastAPI domain API
- Source adapters and normalized data access
- Import jobs and sync orchestration
- Admin/import endpoints
- Auth API when account features are added
- API freshness metadata and source health

Backend-owned routes:

- `/api/v1/*`
- `/api/v1/admin/*`
- `/api/v1/auth/*` when auth is added
- Internal importer/sync endpoints or worker entry points

Deployment boundary:

- Public traffic should route page requests to the React Router service.
- Public API requests under `/api/*` should route to FastAPI, with normalized application routes versioned under `/api/v1/*`.
- A reverse proxy or platform routing layer can own this split in production.
- Local development can use separate ports with proxying, for example frontend on `localhost:5173` and FastAPI on `localhost:8000`.
- React Router loaders may call FastAPI server-side, but they should not duplicate FastAPI domain logic.
- FastAPI remains the source of truth for normalized hockey data.

Frontend data-loading boundary:

- All domain data should come from FastAPI.
- React Router loaders may call FastAPI for page-level server-side data loading, SSR, and pre-rendered public pages.
- TanStack Query may call FastAPI for client-side refresh, polling, live widgets, mutations, and browser-side cache behavior.
- React Router loaders should not contain hockey domain rules.
- TanStack Query hooks should not contain hockey domain rules.
- Frontend code may compose page data, such as team plus roster plus recent games, but should not normalize upstream payloads, map source statuses, derive standings, resolve external IDs, or enforce cache/freshness rules.
- Prefer a shared or generated TypeScript API client from FastAPI OpenAPI so React Router loaders and TanStack Query hooks call the same typed backend API functions.

### Configuration And Environment Variables

Configuration should be explicit and environment-driven from the beginning. The app will have multiple services, external data sources, caches, import jobs, and protected admin endpoints, so configuration should not be hard-coded.

Configuration principles:

- Use environment variables for deployment-specific settings.
- Keep secrets out of source control.
- Provide safe local development defaults where possible.
- Document required variables in an example environment file.
- Validate required configuration at service startup.
- Use separate settings for local, test, staging, and production environments.

Expected backend configuration:

- `DATABASE_URL`
- `REDIS_URL`
- `ADMIN_API_TOKEN`
- `ALLOWED_ORIGINS`
- `PUBLIC_BASE_URL`
- `API_BASE_URL`
- `LOG_LEVEL`
- `ENVIRONMENT`: local, test, staging, production
- `SIHF_BASE_URL`
- `NATIONAL_LEAGUE_BASE_URL`
- Source-specific timeout and retry settings
- Import scheduling enable/disable flags

Expected frontend configuration:

- `PUBLIC_API_BASE_URL`
- `PUBLIC_SITE_URL`
- `PUBLIC_ENVIRONMENT`

Configuration that may be needed later:

- Sentry DSN
- Slack or Discord webhook URL for admin alerts
- Email provider settings
- Auth provider settings
- Feature flags for live updates, brackets, or additional data sources

Do not log secret values. Startup diagnostics can log whether a required value is present, but not the value itself.

### API Versioning

The normalized backend API should be versioned from day one using path-based versioning.

Use:

- `/api/v1/...`

Avoid unversioned public API routes such as:

- `/api/...`

Versioning early costs little and gives room to change normalized response shapes as the app learns more from SIHF / National League data and future providers.

Examples:

- `GET /api/v1/competitions`
- `GET /api/v1/games`
- `GET /api/v1/teams/{team_id}`
- `GET /api/v1/teams/{team_id}/players`
- `GET /api/v1/admin/import-runs`

The first public API version should be `v1`. Breaking response-shape changes should create a new version instead of silently changing existing clients.

### Backend

Recommended stack:

- FastAPI
- PostgreSQL
- Redis
- SQLAlchemy 2.0
- Pydantic v2
- Alembic database migrations
- Background worker or scheduled polling process

Rationale:

- The current endpoint discovery and scripting work is already in Python.
- FastAPI is a strong fit for typed API development and data normalization.
- Python is practical for handling inconsistent upstream sports data from multiple leagues, federations, and tournament providers.
- PostgreSQL gives durable storage for teams, players, games, users, favorites, and historical snapshots.
- Redis supports caching, rate limiting, pub/sub, and future live update fanout.
- SQLAlchemy 2.0 should be used for persistence models because Rink Rat will need mature relational modeling for competitions, seasons, phases, teams, players, games, venues, external IDs, import runs, roster memberships, standings rows, brackets, and future stat/event tables.
- Pydantic v2 should be used for API schemas, validation, adapter outputs, and response models.
- Alembic should be used from day one because sports domain models, external ID mappings, import records, and game-related schema will evolve quickly.

ORM/API model decision:

- Use SQLAlchemy 2.0 instead of SQLModel.
- Keep database persistence models separate from API schemas.
- Use Pydantic v2 models for request/response validation and normalized adapter outputs.
- Avoid coupling database shape directly to frontend API shape.

Database migration guidance:

- Use Alembic for all schema changes.
- Include migrations as part of MVP infrastructure.
- Avoid ad hoc manual schema changes outside migrations.
- Keep migrations reviewable and tied to model changes.
- Make local development and deployment run migrations predictably.

### Live Updates

Live game support does not require changing the backend choice.

Recommended live update pieces:

- Redis for cache and pub/sub
- Background worker polling upstream game endpoints
- WebSocket or Server-Sent Events endpoint
- Frontend subscriptions for live games

Preferred starting point:

- Use normal REST endpoints first.
- Add polling/refetching on the frontend for active games.
- Later introduce SSE or WebSockets when true push updates are needed.

## Public Features

These should be accessible without authentication.

### Home Page

The home page should focus on what fans care about immediately:

- Today's games
- Live games
- Recent final scores
- Upcoming games
- Standings snapshot
- Featured teams or followed league context

### Scores

Public score views should include:

- Today's games
- Previous/future date navigation
- Live, scheduled, final, postponed states
- Team names, logos, score, period, clock if available
- Link to game detail page

### Schedule

The schedule should support:

- Date-based browsing
- Team filtering
- Season filtering
- Competition filtering
- Phase filtering if useful
- Clear game status labels

### Standings

Standings should include:

- Rank
- Team
- Games played
- Points
- Wins/losses
- Goal differential
- Streak if available
- Qualification or playoff indicators if available

### Playoff And Final-Phase Brackets

Playoffs, final phases, elimination rounds, and medal rounds should have special bracket-style views instead of being shown only as flat schedules or standings.

Bracket views should support:

- Quarterfinals, semifinals, finals, bronze games, relegation rounds, and placement games
- Best-of series for club playoffs
- Single-elimination tournament rounds
- Aggregate series state such as games won, series lead, clinched status, and next game
- Team logos, seeds, records, and current series score
- Links from each matchup to game detail pages
- Clear visual distinction between upcoming, live, completed, and clinched matchups

This should apply across competition types. A Swiss National League playoff bracket, NHL Stanley Cup playoff bracket, SHL playoff bracket, World Championship knockout bracket, and U18 medal-round bracket should all use the same core bracket model with competition-specific labels and rules.

The frontend should make bracket views feel like a dedicated fan experience, not just a table. Brackets should work on desktop and mobile, with mobile using a horizontally scrollable or round-by-round layout.

### Teams

Team pages should include:

- Team name
- Logo
- Short name/acronym
- Website link
- Current standings position
- Recent results
- Upcoming games
- Roster
- Team stats summary

### Rosters

Roster pages should include:

- Player number
- Player name
- Position
- Player profile link
- Optional basic stats
- Grouping by goalkeeper, defender, forward

### Player Pages

Player pages can start simple:

- Name
- Number
- Position
- Team
- Birth date if available
- Season stats
- Link back to team

### Game Detail Pages

Game detail pages should eventually include:

- Score summary
- Period-by-period scoring
- Lineups if available
- Penalties if available
- Team stats if available
- Player stats if available
- Game status and venue if available

### Search

Public search should support:

- Teams
- Players
- Competitions
- Games

MVP search can be simple and database-backed. It should prioritize teams, players, and competitions using normalized names, aliases, and basic Postgres `ILIKE` matching. Advanced ranking, fuzzy matching, and richer game search can come later.

### SEO And Shareability

Because Rink Rat is public-first, public pages should be clean, shareable, and friendly to search engines and social previews.

Important public pages:

- Competition pages
- Team pages
- Player pages
- Game pages
- Standings pages
- Bracket pages

URL principles:

- Use clean, human-readable URLs.
- Keep canonical identity stable with internal IDs where collisions or future renames are possible.
- Do not rely only on provider IDs or mutable source-specific slugs.

Example URL patterns:

- `/competitions/national-league`
- `/teams/fribourg-gotteron`
- `/players/{player_id}/{player_slug}`
- `/games/{game_id}/{game_slug}`
- `/competitions/{competition_slug}/standings`
- `/competitions/{competition_slug}/bracket`

Page metadata should include:

- Descriptive page titles
- Meta descriptions
- Canonical URLs
- Open Graph metadata
- Shareable game/team/player summaries

Open Graph images can come later, but the URL and metadata model should be considered from the beginning.

React Router v7 framework mode is preferred over a client-only SPA for this reason. A pure SPA can still provide a good app experience, but SEO and social previews are weaker unless server rendering or pre-rendering are handled deliberately.

### Accessibility Requirements

Accessibility should be part of the public fan experience from the MVP. The app should be usable on desktop and mobile, with keyboard navigation, screen reader support, and readable visual states.

MVP accessibility requirements:

- Use semantic HTML for navigation, tables, headings, buttons, and links.
- Ensure all interactive controls are keyboard accessible.
- Provide visible focus states.
- Use sufficient color contrast for text, score states, badges, and game statuses.
- Do not rely on color alone to communicate live, final, postponed, or qualified states.
- Provide accessible labels for team logos, icons, search controls, and date navigation.
- Make standings, roster, and schedule tables readable on mobile without losing context.
- Support reduced-motion preferences where animations are used.
- Keep loading, empty, error, stale, and degraded states understandable to assistive technology.

Testing expectations:

- Include basic accessibility checks in component and E2E tests.
- Use React Testing Library patterns that encourage accessible queries.
- Use Playwright and `axe-core` where practical for critical public flows.

Accessibility should not be treated as a later visual polish task. It affects component choices, color system, table design, score badges, and live-update behavior.

### Localization Readiness

Full localization does not need to be part of the MVP, but the architecture should avoid choices that make localization difficult later.

MVP should start with one primary language, while keeping the app ready for future languages such as English, German, French, and Italian.

Do from the start:

- Keep user-facing UI strings easy to extract into translation files later.
- Use locale-aware date, time, and number formatting.
- Store canonical values separately from display labels where useful.
- Avoid hard-coding phase names, status labels, and competition labels directly into frontend logic.
- Preserve official team, player, and competition names without blindly translating proper names.
- Allow aliases and display labels to become locale-specific later.
- Design API responses so localized labels can be added later without breaking clients.
- Keep cache keys and API design compatible with a future `locale` parameter or `Accept-Language` handling.

Can wait until after MVP:

- Actual translated UI copy
- Locale switcher
- Locale-prefixed routes
- Localized slugs
- Localized Open Graph images
- `hreflang` metadata
- User account locale preferences

URL strategy should be revisited before full localization. If multilingual SEO becomes important, public routes may need locale prefixes such as `/en/teams/...`, `/de/teams/...`, and `/fr/teams/...`. For MVP, clean non-localized URLs are acceptable as long as future redirects and canonical URL handling remain possible.

## Authenticated Features

Authentication should add value without being required for the main browsing experience.

### User Accounts

Auth enables:

- Favorite teams
- Favorite players
- Personalized homepage
- Notification preferences
- Saved filters
- Recently viewed teams/games/players

### Favorite Teams

Favorite teams should power:

- Personalized home dashboard
- Quick access navigation
- Upcoming game reminders
- Live score alerts
- Final score alerts

### Favorite Players

Favorite players can support:

- Player watchlist
- Player stat shortcuts
- Goal/assist notifications later

### Notifications

Future notification types:

- Game starting soon
- Game started
- Goal scored
- Period ended
- Final score
- Favorite player scored
- Favorite team lineup published

## Backend Responsibilities

The backend should not simply expose third-party APIs directly. It should act as a stable application API across multiple upstream data sources.

Responsibilities:

- Fetch upstream league, federation, and tournament data
- Normalize payloads
- Cache responses
- Persist important entities
- Provide stable frontend-facing routes
- Handle retries and upstream failures
- Prepare data for live updates
- Protect the frontend from brittle upstream API changes
- Keep competition-specific mapping code isolated from the core domain model

## Data Source Adapters

Each upstream data source should be implemented through a source adapter. This keeps SIHF, NHL, IIHF, and other provider-specific details out of the core Rink Rat domain model and frontend API.

This is important because different sources will not share the same IDs, naming conventions, season formats, phase structures, roster shapes, game states, standings models, or tournament formats.

Examples of adapters:

- `SIHFAdapter`
- `NationalLeagueAdapter`
- `NHLAdapter`
- `IIHFAdapter`
- `SHLAdapter`
- `ManualAdapter`

Each adapter should implement a common importer interface where possible:

- `fetch_competitions()`
- `fetch_seasons()`
- `fetch_teams()`
- `fetch_rosters()`
- `fetch_schedule()`
- `fetch_game_detail()`
- `fetch_standings()`
- `fetch_bracket()`

The backend should have a clear data flow:

```text
Upstream API payloads
        |
        v
Source adapter / mapper
        |
        v
Normalized Rink Rat domain models
        |
        v
Frontend API
```

Adapter responsibilities:

- Fetch data from one upstream provider
- Translate provider-specific IDs into internal IDs or source mappings
- Normalize names, teams, players, seasons, phases, games, standings, and brackets
- Preserve useful raw payload references for debugging
- Report source-specific failures without leaking provider details into the frontend
- Avoid shaping core application models around the first implemented data source

The frontend should never need to know whether a payload came from SIHF, NHL, IIHF, or a manual source. It should only consume normalized Rink Rat API responses.

### MVP Endpoint Research

Before implementing the MVP backend, the SIHF / National League endpoint surface should be researched and documented more rigorously. The current working script proves that useful endpoints exist, but parts of it were reverse engineered from public site behavior.

MVP endpoint research should document:

- Teams endpoint
- Team roster/player endpoint
- Schedule/results endpoint
- Standings endpoint
- Game detail endpoint
- Season and phase/filter discovery
- Team/player logo or image behavior if used
- Export endpoints if useful for debugging or fallback behavior

For each endpoint, record:

- URL and host
- Required and optional query parameters
- Response content type and JSON/JSONP behavior
- Payload shape and important fields
- Language parameter behavior
- Season and phase semantics
- Cache behavior if known
- Failure behavior and common errors
- Legal/usage uncertainty
- Example request and saved fixture payload

This research should feed the initial `SIHFAdapter` / `NationalLeagueAdapter` implementation and the fixture-based adapter tests.

## Raw Payload Retention Policy

Raw upstream payloads are useful for debugging, adapter tests, endpoint research, import failure analysis, and detecting provider shape changes. They should be retained deliberately, not indefinitely by default.

Raw payload policy:

- Keep representative fixture payloads in the test suite for adapter mapping tests.
- Store raw payload references or hashes on import runs when useful.
- Store full raw payloads only when needed for debugging, fixture generation, or source-change analysis.
- Redact secrets, tokens, private headers, and any sensitive request metadata before storing payloads.
- Avoid storing personal data beyond what is already necessary for the sports domain model.
- Prefer compressed object storage or filesystem storage for large raw payloads if database storage becomes too heavy.
- Keep payload retention source-specific because provider rules and legal terms may differ.

Suggested MVP retention:

- Test fixtures: keep indefinitely in source control when legally safe and reasonably small.
- Failed import payloads: retain for 7-30 days.
- Successful import debug payloads: retain for a short period, such as 1-7 days, or only retain hashes/references.
- Live game raw payloads: retain only when needed for debugging or tests because they can be noisy.

Raw payloads should not be exposed to the public API. Admin/debug access should be protected and should avoid leaking sensitive provider details.

## External ID Mapping

External ID mapping should exist from day one. Rink Rat should use its own internal IDs for core entities, while separately storing provider-specific IDs from each upstream data source.

This is necessary because the same real-world team, player, game, competition, or season may appear in multiple systems with different identifiers, names, and formats.

Example:

- Fribourg-Gotteron internal Rink Rat team ID
- SIHF team ID
- National League team ID
- Elite Prospects team ID
- Future IIHF or NHL-related references if applicable

The app should have an `external_ids` concept or table.

Suggested fields:

- `entity_type`: controlled enum such as competition, season, phase, team, player, game, venue
- `entity_id`: internal Rink Rat ID
- `source`: sihf, national_league, nhl, iihf, eliteprospects, shl, manual
- `external_id`: provider-specific ID
- `external_slug`: provider-specific slug if available
- `source_scope`: optional provider-specific scope when IDs are not globally unique
- `competition_id`: optional scope when provider IDs are unique only within a competition
- `season_id`: optional scope when provider IDs are unique only within a season
- `source_url`: provider URL if useful for debugging
- `metadata`: optional provider-specific context

The combination of `entity_type`, `source`, and `external_id` should be unique when a provider's IDs are globally unique. Some providers may only guarantee uniqueness within a league, competition, season, endpoint, or other context. In those cases, `source_scope`, `competition_id`, or `season_id` should be included in the uniqueness rule.

`entity_type` should not be arbitrary free text. Use an application enum and, if practical, a database check constraint. This keeps external ID mappings consistent without making future migrations unnecessarily painful.

External ID mapping responsibilities:

- Resolve upstream payloads to existing internal entities
- Prevent duplicate teams or players when adding new data sources
- Support cross-source enrichment later
- Preserve provider-specific IDs for debugging and reconciliation
- Allow source adapters to stay provider-specific while the core API stays normalized

This is especially important for players and teams because names can vary between providers, include accents or abbreviations, change over time, or collide with other entities.

## Identity Resolution And Player Matching

External IDs solve many cross-source identity problems, but they do not make player matching automatic or safe. Player identity matching is difficult because names, metadata, and source behavior can vary significantly.

Player matching risks:

- Accents and transliteration differences
- Duplicate names
- Missing birth dates
- Nationality changes or multiple nationalities
- Junior players with sparse data
- Inconsistent first-name/last-name ordering
- Spelling variants and abbreviations
- Source-specific display names

MVP rule:

- Do not auto-merge players across sources unless there is a reliable external ID or strong verified match.
- Prefer manual reconciliation over risky automatic merges.
- If a match is uncertain, keep players separate rather than corrupting a shared identity.
- Treat possible matches as suggestions, not automatic writes.

Future reconciliation tooling may include:

- `PlayerIdentityCandidate`
- `confidence_score`
- `match_reason`
- `review_status`: pending, approved, rejected
- `reviewed_by`
- `reviewed_at`

Potential matching signals:

- Shared external IDs
- Normalized full name
- Birth date
- Nationality
- Position
- Team history
- Source profile URL

No single weak signal should be enough to automatically merge players. Incorrect merges are worse than temporary duplicates.

## Import Jobs And Observability

Import jobs should be treated as first-class backend features. The largest operational risk in Rink Rat is not the React frontend or FastAPI itself. It is upstream data changing, failing, returning partial data, or returning unexpected payloads.

Initial import jobs:

- `sync_competitions`
- `sync_seasons`
- `sync_teams`
- `sync_players`
- `sync_rosters`
- `sync_schedule`
- `sync_standings`

Future import jobs:

- `sync_game_detail`
- `sync_bracket`
- `sync_live_games`

Each import run should be recorded.

Suggested fields:

- `job_type`: sync_competitions, sync_teams, sync_live_games, etc.
- `source`: sihf, national_league, nhl, iihf, shl, manual
- `competition_id`
- `season_id`
- `phase_id`
- `started_at`
- `finished_at`
- `status`: success, partial_success, failed
- `records_created`
- `records_updated`
- `records_deactivated`
- `records_missing_from_source`
- `records_skipped`
- `error_message`
- `upstream_endpoint`
- `adapter_version`
- `metadata`

Imports should be conservative about deletes. Upstream sports data can temporarily omit records because of provider outages, filter issues, season/phase changes, delayed corrections, or partial payloads. Normal imports should not hard-delete competitions, seasons, teams, players, games, venues, or external ID mappings.

Deletion guidance:

- Prefer soft deletes or `is_active = false` for identity records.
- Track when records were last seen from a source.
- Use `records_missing_from_source` when an import expected a record but did not receive it.
- Use `records_deactivated` when the system intentionally marks a record inactive.
- Only deactivate after repeated missing imports or an explicit upstream signal when possible.
- Preserve historical games and player/team identities even if no longer active.
- Reserve hard deletes for manual admin maintenance, test data cleanup, or clearly safe dependent/cache records.

Import jobs should be:

- Idempotent
- Safe to retry
- Observable through logs and import run records
- Manually triggerable for debugging
- Able to report partial success instead of only success or failure

### Import Scheduling Rules

Import schedules should vary by data volatility and season/game context. These rules can start rough and be refined as endpoint behavior becomes better understood.

Recommended schedules:

- Competitions, seasons, and phases: daily, plus manual refresh when configuring a new source
- Teams: daily, plus manual refresh when source metadata changes
- Players and roster identities: daily during the season, less frequently outside the season
- Rosters: daily during the season, plus before game days if possible
- Schedule/results: hourly during the active season, daily outside the season
- Standings: every 5-15 minutes during game windows, hourly otherwise during the active season
- Live games: every 10-30 seconds during active games only
- Game detail before/during live game: every 15-60 seconds if the detail endpoint contains live state
- Game detail after final: sync shortly after final, then recheck once later to catch official corrections
- Brackets/playoff series: every 5-15 minutes during playoff or tournament game windows, hourly otherwise during active final phases

Scheduling rules should account for:

- Active season vs offseason
- Game day vs non-game day
- Active live games vs no live games
- Completed season MVP mode, where live-game jobs can be disabled or run manually
- Source-specific rate limits or usage restrictions
- Admin manual syncs that bypass the normal schedule for debugging

The worker should avoid aggressive polling when no games are active. Live-game polling should start shortly before scheduled puck drop and stop after final game detail has been confirmed.

Admin notifications should exist for important import failures.

Notify admins when:

- A scheduled import fails
- An import partially succeeds with missing critical data
- A live game sync falls behind or stops updating
- An upstream payload shape changes unexpectedly
- A source adapter starts producing validation errors
- The same source fails repeatedly within a short time window

Not every transient retry should alert admins. Minor retryable failures should be logged first, then escalated if they repeat or affect user-visible data. This avoids alert fatigue while still making data problems visible quickly.

Possible notification channels:

- Email
- Slack or Discord webhook
- Admin dashboard alert
- Error tracking service integration

If an upstream source later requires authentication, import logs must avoid storing sensitive tokens or private request headers.

### MVP Admin Import Support

The MVP does not need a polished admin UI, but it should include minimal protected admin/import observability because upstream data reliability is a core operational risk.

MVP admin support should include:

- Import run records persisted in Postgres
- Source health summary
- Manual sync trigger for a competition
- Basic logs/errors for failed and partial imports
- A simple admin token or private deployment boundary to protect admin endpoints before full user auth exists

Suggested MVP admin routes:

- `GET /api/v1/admin/import-runs`
- `GET /api/v1/admin/source-health`
- `POST /api/v1/admin/sync/competition/{competition_id}`

Optional early admin route:

- `POST /api/v1/admin/sync/game/{game_id}`

These endpoints should be internal-only or protected. They should not be exposed publicly without authentication or an admin secret.

## Observability

Basic observability should be part of the backend from the beginning. This is especially important because upstream sports data can fail, change shape, become stale, or behave differently across providers.

MVP observability should include:

- Structured backend logs
- Structured import job logs
- Failed upstream request logging
- Source adapter validation error logging
- Slow backend endpoint logging
- Slow upstream endpoint logging
- Import run records in Postgres
- Request IDs or correlation IDs for tracing issues across API calls and import jobs

Useful structured log fields:

- `request_id`
- `source`
- `adapter`
- `competition_id`
- `season_id`
- `phase_id`
- `game_id`
- `job_type`
- `duration_ms`
- `status`
- `upstream_endpoint`
- `error_type`

Later observability improvements:

- Sentry or another error tracking service
- Prometheus/Grafana metrics
- Uptime checks
- Alert routing and escalation
- Dashboards for API latency, failed imports, data freshness, stale responses, and live-game lag

Sentry or similar error tracking can be added earlier if deployment setup makes it cheap, but Prometheus/Grafana-level monitoring can wait until the app has more production traffic and operational needs.

## Testing Strategy

Testing should focus heavily on source adapters, importer mapping, and data normalization. Frontend bugs are usually visible to users quickly, but bad upstream mapping can silently create incorrect teams, players, games, standings, brackets, or live states.

Highest-priority test path:

```text
Saved upstream fixture
        |
        v
Source adapter mapper
        |
        v
Expected normalized Rink Rat model
```

Backend testing priorities:

- Unit tests for source adapter mapping and parsing
- Fixture-based tests using saved upstream payloads
- Explicit expected normalized-output tests
- Snapshot tests for upstream sample payloads where useful
- Integration tests for public API routes
- Integration tests for protected admin/import routes
- Import idempotency tests
- External ID mapping tests
- Game status normalization tests
- Timezone parsing tests
- Freshness metadata tests
- Failure tests for missing fields, malformed payloads, unexpected payload shapes, and partial upstream responses

Frontend testing priorities:

- Component tests for game cards
- Component tests for standings tables
- Component tests for roster tables
- Component tests for search results
- Component tests for bracket views once brackets enter scope
- E2E smoke test for home/scores to game detail flow
- E2E smoke test for team page to roster flow
- Basic accessibility checks for public pages

Live upstream tests should not run in normal CI because they can be flaky and dependent on third-party availability. Live endpoint checks should be separate manual smoke tests, scheduled checks, or admin/source-health checks.

Recommended testing tech stack:

- Backend unit/integration tests: `pytest`
- Async backend tests: `pytest-asyncio` or `anyio`
- FastAPI route tests: `httpx` or FastAPI `TestClient`
- HTTP mocking: `respx` or `pytest-httpx`
- Database tests: test Postgres container or isolated test database
- Frontend unit/component tests: `Vitest`
- React component tests: React Testing Library
- E2E tests: Playwright
- Accessibility checks: Playwright accessibility checks or `axe-core`
- Type checks: `mypy` or `pyright` for Python, `tsc` for TypeScript

Snapshot tests can help detect upstream payload changes, but they should not be the only protection. The most valuable tests assert normalized Rink Rat models explicitly.

## API Data Freshness

Relevant API responses should include freshness metadata so users and developers can understand whether sports data is current.

This is especially important for:

- Scores
- Live games
- Standings
- Rosters
- Game details
- Brackets
- Schedule/results

Recommended response shape:

```json
{
  "data": {},
  "meta": {
    "sources": ["sihf"],
    "last_synced_at": "2026-06-03T18:42:00Z",
    "served_at": "2026-06-03T18:42:08Z",
    "is_stale": false,
    "stale_after_seconds": 300,
    "status": "fresh"
  }
}
```

Possible freshness statuses:

- `fresh`
- `stale`
- `degraded`
- `partial`
- `unknown`

Freshness thresholds should depend on the data type. Live game state may become stale after seconds, while rosters or standings may remain acceptable for much longer.

The API should allow multiple sources in metadata because future responses may combine data from several providers, such as league data, tournament data, player enrichment, and internal cached state.

Freshness metadata responsibilities:

- Communicate whether user-visible data is current
- Support frontend stale/degraded indicators
- Help debug upstream sync issues
- Make import delays visible without exposing sensitive provider details
- Avoid pretending cached data is live when upstream sync has stopped

## Cache Strategy And Invalidation

Redis cache usage should have clear TTL defaults from the beginning. These defaults do not need to be perfect, but they should guide implementation and prevent stale sports data from being served accidentally for too long.

Rough TTL classes:

- Live game state: 5-15 seconds
- Today scores during game windows: 30-60 seconds
- Upcoming schedule/results: 5-15 minutes
- Standings: 5-15 minutes
- Roster payloads: 6-24 hours
- Teams and competition reference data: 24 hours or manual refresh
- Game detail before/during live game: 15-60 seconds
- Game detail after final: long TTL, such as 24 hours or more
- Static source metadata and external ID mappings: long TTL or manual invalidation

Cache key guidance:

- Include API version where relevant, such as `v1`.
- Include source, competition, season, phase, team, player, date, date context, and timezone when they affect the response.
- Include locale in cache keys once localized responses are introduced.
- Avoid sharing cache entries across different freshness or date-context semantics.

Invalidation guidance:

- Successful import jobs should invalidate or refresh affected cache keys.
- Manual admin syncs should invalidate affected competition, team, game, standings, roster, and source-health caches.
- Live game updates should refresh game and scoreboard caches aggressively while the game is active.
- Final games can move to longer TTLs once status is final and game detail has been synced.
- If an upstream source fails, the API may serve stale cached data with `meta.status = stale` or `degraded` when the data is still useful.

Cache freshness should align with API freshness metadata. If cached data is returned beyond its ideal freshness window, the response should make that visible through `last_synced_at`, `served_at`, `is_stale`, and `status` metadata.

## API Pagination And Filtering Conventions

API endpoints that can grow over time should use consistent pagination and filtering conventions from the beginning.

Pagination parameters:

- `page`: 1-indexed page number, default `1`
- `page_size`: number of records per page, default `25`
- Maximum `page_size`: `100`

Recommended paginated response shape:

```json
{
  "data": [],
  "meta": {
    "page": 1,
    "page_size": 25,
    "total_count": 250,
    "total_pages": 10
  }
}
```

Common filter parameters:

- `competition_id`
- `season_id`
- `phase_id`
- `team_id`
- `player_id`
- `date`
- `date_context`: user, competition, venue
- `timezone`: IANA timezone used when `date_context=user`
- `status`: canonical game status
- `source_id`
- `q`: search query

Date filtering rules:

- `date` should use ISO date format, for example `2026-01-12`.
- `date_context=user` means the date is interpreted in the user's selected/browser timezone.
- `date_context=competition` means the date is interpreted in the competition default timezone.
- `date_context=venue` means the date is interpreted in each game's venue timezone.
- If `date_context=user` is used, the request should include an IANA `timezone` value when possible.

Endpoints that should support pagination and filters early:

- `GET /api/v1/games`
- `GET /api/v1/teams`
- `GET /api/v1/players`
- `GET /api/v1/players/{player_id}` only if returning related lists or stats history
- `GET /api/v1/search`
- `GET /api/v1/admin/import-runs`

Suggested endpoint-specific filters:

- `GET /api/v1/games`: `competition_id`, `season_id`, `phase_id`, `team_id`, `date`, `date_context`, `timezone`, `status`
- `GET /api/v1/teams`: `competition_id`, `season_id`, `q`
- `GET /api/v1/players`: `competition_id`, `season_id`, `team_id`, `position`, `q`
- `GET /api/v1/search`: `q`, `competition_id`, `season_id`, `type`
- `GET /api/v1/admin/import-runs`: `source_id`, `competition_id`, `season_id`, `job_type`, `status`, `page`, `page_size`

Small reference endpoints can return full lists without pagination when the result set is bounded and small, but the API should be designed so pagination can be added without changing response conventions.

## API Error Format

The backend API should return consistent error responses so the frontend, Python test client, and admin tools can handle failures predictably.

Recommended error response shape:

```json
{
  "error": {
    "code": "SOURCE_UNAVAILABLE",
    "message": "SIHF data source is temporarily unavailable.",
    "request_id": "req_123456789",
    "details": {}
  }
}
```

Recommended error codes:

- `VALIDATION_ERROR`
- `NOT_FOUND`
- `SOURCE_UNAVAILABLE`
- `SOURCE_STALE`
- `IMPORT_FAILED`
- `UNAUTHORIZED`
- `FORBIDDEN`
- `RATE_LIMITED`
- `INTERNAL_ERROR`

Error response rules:

- Every error should include a stable machine-readable `code`.
- Every error should include a human-readable `message` suitable for logs and simple UI display.
- Every error should include `request_id` when available so issues can be traced through logs.
- `details` can include field validation errors, source names, retry hints, or admin-only debugging context when safe.
- Do not expose secrets, private upstream credentials, stack traces, or sensitive provider request headers.

Suggested HTTP status mapping:

- `VALIDATION_ERROR`: `400` or `422`
- `NOT_FOUND`: `404`
- `SOURCE_UNAVAILABLE`: `502` or `503`
- `SOURCE_STALE`: `200` with stale metadata when data can still be shown, or `503` when no usable data exists
- `IMPORT_FAILED`: `500` or `503` depending on whether cached data is available
- `UNAUTHORIZED`: `401`
- `FORBIDDEN`: `403`
- `RATE_LIMITED`: `429`
- `INTERNAL_ERROR`: `500`

Frontend behavior should distinguish between user-fixable errors, missing data, stale/degraded source data, and true internal failures. Admin tools should show `request_id`, source context, and import run links when available.

## Security Basics

Security should be handled pragmatically from the MVP, even though the first public product is mostly read-only and account-free.

MVP security requirements:

- Serve production traffic over HTTPS.
- Keep public read-only endpoints separate from protected admin/import endpoints.
- Protect admin endpoints with an admin token, private network boundary, or equivalent mechanism before full user auth exists.
- Store secrets only in environment variables or a deployment secret manager.
- Never commit secrets, API tokens, private keys, or provider credentials.
- Redact secrets, tokens, private headers, and sensitive provider request data from logs and import records.
- Configure CORS explicitly for the frontend origin instead of allowing all origins in production.
- Add basic rate limiting or abuse protection for public API endpoints if traffic or scraping becomes a concern.
- Add stricter rate limiting for admin endpoints.
- Validate all API inputs with Pydantic models or explicit query parameter validation.
- Use dependency pinning and keep backend/frontend dependencies updated.
- Avoid exposing raw upstream payloads through public endpoints.
- Make error responses useful but avoid stack traces or sensitive internals.

Future security requirements:

- Full authentication and authorization for account features.
- Role-based admin access.
- CSRF protection if cookie-based authenticated sessions are used.
- Audit logs for admin actions and manual sync triggers.
- More robust bot/rate-limit controls if public endpoints are abused.
- Security headers managed by the frontend service or reverse proxy.

Example backend routes:

- `GET /api/v1/competitions`
- `GET /api/v1/competitions/{competition_id}`
- `GET /api/v1/competitions/{competition_id}/standings`
- `GET /api/v1/competitions/{competition_id}/games`
- `GET /api/v1/competitions/{competition_id}/bracket`
- `GET /api/v1/competitions/{competition_id}/phases/{phase_id}/bracket`
- `GET /api/v1/teams`
- `GET /api/v1/teams/{team_id}`
- `GET /api/v1/teams/{team_id}/players`
- `GET /api/v1/games`
- `GET /api/v1/games/{game_id}`
- `GET /api/v1/standings`
- `GET /api/v1/players`
- `GET /api/v1/players/{player_id}`
- `GET /api/v1/search`
- `GET /api/v1/me`
- `GET /api/v1/me/favorites`
- `GET /api/v1/admin/import-runs`
- `GET /api/v1/admin/source-health`
- `POST /api/v1/admin/sync/competition/{competition_id}`

## API Prototyping And Test Client

The same backend API used by the React frontend should also be easy to test through a Python CLI script.

This is useful for:

- Prototyping backend endpoints before frontend screens exist
- Smoke testing local, staging, and production environments
- Validating normalized app API payloads
- Debugging data-source differences across leagues and tournaments
- Comparing upstream raw responses against the app's stable API responses

The current `scripts/sihf_demo.py` should remain an upstream discovery tool for SIHF and National League endpoints. A future script, such as `scripts/rink_rat_api.py`, should act as a client of the app backend itself.

Example commands:

- `python3 scripts/rink_rat_api.py teams`
- `python3 scripts/rink_rat_api.py teamplayers 101151`
- `python3 scripts/rink_rat_api.py games --date 2026-01-10`
- `python3 scripts/rink_rat_api.py standings --competition national-league`
- `python3 scripts/rink_rat_api.py bracket --competition national-league --season 2026`

Those commands should call the same frontend-facing API routes that the web app uses, for example:

- `GET /api/v1/teams`
- `GET /api/v1/teams/{team_id}/players`
- `GET /api/v1/games?date=2026-01-10`
- `GET /api/v1/competitions/{competition_id}/standings`
- `GET /api/v1/competitions/{competition_id}/bracket`

The Python test client should not duplicate backend business logic. It should only send requests, display responses, and optionally validate response shapes.

## Time Zones And Game Times

Time zones should be handled deliberately from the beginning. Sports schedules, live games, notifications, and date-based browsing all depend on correct time handling.

Core rules:

- Store canonical game start times in UTC.
- Use IANA time zone names, such as `Europe/Zurich` or `America/New_York`.
- Avoid naive datetimes.
- Display times in the user's local timezone by default.
- Preserve venue-local and source-local context for debugging and display.

Important timezone concepts:

- `starts_at_utc`: canonical game start timestamp
- `venue_timezone`: timezone where the game is played
- `competition_default_timezone`: default timezone for the competition or tournament
- `source_local_start_time`: local start time as reported by the provider, if useful
- `source_local_date`: local date as reported by the provider, if useful
- `starts_at_confirmed`: whether the scheduled time is confirmed

Examples:

- Swiss National League can usually default to `Europe/Zurich`.
- IIHF tournaments can default to the host city or venue timezone.
- NHL cannot rely on one competition timezone because games are played across multiple North American time zones.
- Neutral-site games may differ from both teams' home timezones.

API responses for games should expose UTC plus timezone metadata:

```json
{
  "starts_at_utc": "2026-01-12T18:45:00Z",
  "venue_timezone": "Europe/Zurich",
  "competition_default_timezone": "Europe/Zurich",
  "source_local_date": "2026-01-12"
}
```

Schedule grouping needs special care. "Today's games" can mean user-local date, competition-local date, or venue-local date. The API should make the selected date context explicit when returning date-based game lists.

Implementation notes:

- Use Postgres `timestamptz` for canonical timestamps.
- Use Python `zoneinfo` for timezone conversion.
- Keep source adapters responsible for interpreting provider-local dates and times.
- Avoid storing fixed UTC offsets as the primary timezone representation because daylight saving rules change.

## Game Status State Machine

Game statuses should be normalized into a canonical Rink Rat state machine. Upstream sources will use different labels, codes, and lifecycle models, so source adapters should map provider-specific statuses into internal statuses.

Canonical statuses:

- `scheduled`
- `pre_game`
- `live`
- `intermission`
- `final`
- `final_ot`
- `final_so`
- `postponed`
- `cancelled`
- `suspended`
- `delayed`
- `forfeit`

Recommended game status fields:

- `status`: canonical Rink Rat status
- `source_status`: raw upstream status string or code
- `period`: current or final period when available
- `clock`: current game clock when live
- `is_live`: derived convenience boolean
- `is_final`: derived convenience boolean
- `ended_in`: regulation, overtime, shootout, forfeit, or unknown
- `status_reason`: postponement, suspension, delay, or cancellation reason if available

Final status nuance:

- `final_ot` and `final_so` are useful for frontend display and fan readability.
- Internally, the app may also store `status = final` plus `ended_in = overtime` or `ended_in = shootout` for cleaner logic.
- The frontend API should make it easy to show final labels like `Final`, `Final/OT`, and `Final/SO` without source-specific logic.

Adapters should preserve raw source status values for debugging, but the frontend should only depend on canonical Rink Rat statuses.

## Data Strategy

The backend should distinguish canonical persisted data from cached volatile data.

Guiding principle:

- Persist stable identity and backbone data.
- Cache volatile display data and rich upstream payloads.

### MVP Data Strategy

For the MVP, source adapters should fetch upstream data, map provider IDs through external ID mappings, persist stable domain entities, and cache volatile display payloads.

Stable identity data should be persisted from the beginning because it forms the backbone of routing, search, history, game pages, favorites, notifications, and future cross-source enrichment.

Persist early:

- Competitions
- Seasons
- Phases
- Teams
- Players
- Games
- Venues
- External IDs
- Import runs / sync logs

Games should be persisted early. They should not be treated as temporary schedule/result cache entries. A game record should store canonical fields such as competition, season, phase, `starts_at_utc`, venue timezone, home team, away team, venue, status, score, and external ID mappings.

Players should be persisted as identities, but detailed player stats can be cached initially. Roster payloads can be cached, but discovered player identities should still be persisted.

Cache early:

- Standings
- Roster payloads
- Game detail payloads
- Live game state
- Bracket payloads
- Rich upstream response payloads used for debugging

### Later Data Strategy

As the product grows, persist richer historical and derived data:

- Bracket rounds
- Bracket matchups
- Playoff series state
- Standings snapshots
- Detailed game events
- Player stats snapshots
- Team stats snapshots
- User favorites
- Notification preferences
- Historical game results

This allows the app to support history, analytics, notifications, richer search, and improved reliability when upstream APIs are slow or unavailable.

## MVP Data Model Draft

This is a minimum viable schema draft, not the final SQLAlchemy implementation. It should guide the first backend implementation and migrations while leaving room for refinement.

All persisted domain entities should use internal Rink Rat IDs as primary identifiers. Provider-specific IDs belong in `ExternalId`, not in frontend-facing URLs or core relationships.

Common fields for most persisted tables:

- `id`
- `created_at`
- `updated_at`

### DataSource

Represents an upstream provider or manually maintained source.

- `id`
- `key`: sihf, national_league, nhl, iihf, manual
- `name`
- `base_url`
- `attribution_text`
- `usage_status`: prototype_only, approved, restricted, unknown
- `metadata`
- `created_at`
- `updated_at`

### Competition

Represents a league or tournament.

- `id`
- `name`
- `slug`
- `competition_type`: domestic_league, international_tournament, cup, exhibition
- `country_code`
- `default_timezone`
- `primary_data_source_id`
- `is_active`
- `created_at`
- `updated_at`

### Season

Represents a season or tournament year within a competition.

- `id`
- `competition_id`
- `name`: 2025/2026, 2026, etc.
- `slug`
- `starts_on`
- `ends_on`
- `is_current`
- `created_at`
- `updated_at`

### Phase

Represents a season phase or tournament round context.

- `id`
- `competition_id`
- `season_id`
- `name`: regular season, playoffs, group stage, final, etc.
- `slug`
- `phase_type`: regular_season, playoffs, group_stage, knockout, final, placement, unknown
- `sort_order`
- `starts_on`
- `ends_on`
- `created_at`
- `updated_at`

### Team

Represents a club or national team.

- `id`
- `name`
- `slug`
- `short_name`
- `team_type`: club, national_team
- `country_code`
- `primary_color`
- `secondary_color`
- `website_url`
- `logo_url`
- `is_active`
- `created_at`
- `updated_at`

### Player

Represents a player identity, not a season-specific stat line.

- `id`
- `first_name`
- `last_name`
- `display_name`
- `slug`
- `birth_date`
- `nationality_country_code`
- `position`: goalkeeper, defender, forward, unknown
- `shoots`
- `height_cm`
- `weight_kg`
- `is_active`
- `created_at`
- `updated_at`

### RosterMembership

Connects a player to a team in a competition season.

- `id`
- `competition_id`
- `season_id`
- `team_id`
- `player_id`
- `jersey_number`
- `position`
- `is_captain`
- `is_alternate_captain`
- `starts_on`
- `ends_on`
- `created_at`
- `updated_at`

### Venue

Represents a game venue or arena.

- `id`
- `name`
- `slug`
- `city`
- `country_code`
- `timezone`
- `capacity`
- `created_at`
- `updated_at`

### Game

Represents a scheduled, live, or completed game.

- `id`
- `competition_id`
- `season_id`
- `phase_id`
- `home_team_id`
- `away_team_id`
- `venue_id`
- `starts_at_utc`
- `venue_timezone`
- `source_local_date`
- `starts_at_confirmed`
- `status`: scheduled, pre_game, live, intermission, final, final_ot, final_so, postponed, cancelled, suspended, delayed, forfeit
- `source_status`
- `status_reason`
- `period`
- `clock`
- `home_score`
- `away_score`
- `ended_in`: regulation, overtime, shootout, forfeit, unknown
- `slug`
- `created_at`
- `updated_at`

### Standing

Represents a standings table for a competition, season, and phase.

- `id`
- `competition_id`
- `season_id`
- `phase_id`
- `name`
- `last_synced_at`
- `created_at`
- `updated_at`

### StandingRow

Represents one team row in a standings table.

- `id`
- `standing_id`
- `team_id`
- `rank`
- `games_played`
- `wins`
- `losses`
- `overtime_wins`
- `overtime_losses`
- `shootout_wins`
- `shootout_losses`
- `points`
- `goals_for`
- `goals_against`
- `goal_difference`
- `streak`
- `qualification_status`
- `created_at`
- `updated_at`

### ExternalId

Maps internal Rink Rat entities to provider-specific identifiers.

- `id`
- `entity_type`: controlled enum for competition, season, phase, team, player, game, venue
- `entity_id`
- `source_id`
- `external_id`
- `external_slug`
- `source_scope`
- `competition_id`
- `season_id`
- `source_url`
- `metadata`
- `created_at`
- `updated_at`

The combination of `entity_type`, `source_id`, and `external_id` should be unique when the provider ID is globally unique. If the provider ID is scoped, include `source_scope`, `competition_id`, or `season_id` in the uniqueness rule.

### ImportRun

Records each import or sync attempt.

- `id`
- `job_type`
- `source_id`
- `competition_id`
- `season_id`
- `phase_id`
- `started_at`
- `finished_at`
- `status`: success, partial_success, failed
- `records_created`
- `records_updated`
- `records_deactivated`
- `records_missing_from_source`
- `records_skipped`
- `upstream_endpoint`
- `adapter_version`
- `error_type`
- `error_message`
- `metadata`
- `created_at`
- `updated_at`

Implementation details such as exact SQLAlchemy relationship definitions, indexes, constraints, enum implementations, and loading strategies should be handled in the implementation plan and migrations.

## Live Game Strategy

Initial implementation:

- Frontend uses TanStack Query refetching for live games.
- Active game views poll more frequently.
- Non-live views poll less frequently or not at all.

Future implementation:

- Background worker polls upstream live game endpoints.
- Worker detects state changes.
- Updates are written to Redis/Postgres.
- Redis pub/sub broadcasts changes.
- FastAPI pushes changes over SSE or WebSockets.
- Frontend updates game cards and detail pages in realtime.

Recommended transport:

- Use SSE if updates are only server-to-client.
- Use WebSockets if the app later needs richer bidirectional interactions.

## MVP Scope

The first useful version should prove the public fan experience without requiring accounts.

MVP target:

- Swiss National League only
- 2025/2026 season only
- Completed season data first, with live-game architecture considered but not required for the first MVP release
- English UI copy
- Official team and player names preserved
- Endpoint research and fixture collection completed before backend implementation

MVP should include:

- Public home page
- Public scores page
- Public schedule/results page
- Public standings page
- Public competition selector
- Public basic search for teams, players, and competitions
- Clean shareable public URLs with basic metadata
- Public teams page
- Public team detail page
- Public roster list
- Basic game detail page
- Optional local-only favorite team stored in the browser without an account
- Minimal protected admin/import observability endpoints or CLI support

This gives the app a complete public fan-facing loop without overbuilding. Account-based personalization can wait until the core browsing experience is stable.

## MVP Non-Goals

The MVP should stay focused on proving the public Swiss National League fan experience for the 2025/2026 season. The following are intentionally out of scope for MVP unless they become trivial side effects of the core work.

MVP non-goals:

- Multi-league support beyond Swiss National League
- International tournaments
- Live game push updates through SSE or WebSockets
- Public playoff/final-phase bracket views
- User accounts and full authentication
- Account-based favorite teams or players
- Push notifications or email notifications
- Full admin dashboard UI
- Advanced player, team, or game analytics
- Player/team comparison tools
- Fantasy or prediction features
- Commenting, discussion, or social features
- Full localization and locale-prefixed routes
- Localized Open Graph images
- Native mobile app
- Polished historical archive beyond the MVP season

Optional local-only favorite team support is acceptable in MVP because it does not require account infrastructure.

## V2 Scope

After MVP:

- Public playoff/final-phase bracket views
- Authentication
- Account-based favorite teams
- Account-based favorite players
- Personalized homepage
- Saved preferences
- Live game refetching improvements
- Player detail pages
- Stat leaders
- Notifications foundation
- Better game detail pages
- Bracket view refinements for playoffs and tournament final phases
- Advanced search
- Open Graph images and richer share previews
- Full admin/status UI for upstream data health

## V3 Scope

Longer-term features:

- Push notifications
- True realtime SSE/WebSocket updates
- Rich game center
- Live bracket updates during playoff and tournament final phases
- Player comparisons
- Team comparisons
- Historical results
- Additional league and tournament data sources
- Mobile app or PWA enhancements

## Admin And Operations

The app should have minimal admin/import observability in MVP and richer internal tooling later.

Minimal MVP support:

- Protected import run listing
- Protected source health endpoint
- Protected manual competition sync trigger
- Import failure and partial-success logs

Expanded internal tooling:

- Upstream endpoint health
- Last sync timestamps
- Failed request logs
- Cache inspection
- Manual refresh for teams/games
- Data mismatch detection
- Known upstream API issues
- Per-source importer status
- Admin notifications for failed, partial, or repeatedly degraded imports
- Competition/team/player ID mapping

This is especially important because the app depends on public endpoints that may change.

## Design Principles

- Public-first
- Fast loading
- Mobile-friendly
- Clear game status labels
- Team identity matters: logos, colors, names
- Competition context should always be clear
- Avoid forcing accounts for basic browsing
- Make authenticated features feel useful, not mandatory
- Optimize for fans before analysts

## Key Product Decision

Rink Rat should start as a fan-facing scores and team hub.

The best initial differentiator is not deep analytics. It is a clean, reliable, easy-to-use interface for scores, standings, teams, rosters, and favorite-team tracking.

Advanced stats and live notifications can grow naturally from that base.
