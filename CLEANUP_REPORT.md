# Cleanup / optimisation report

Branch `claude/django-cleanup-optimize-7tym6i`. Bug list: [BUGS_FIXED.md](BUGS_FIXED.md).

## Done criteria

| Criterion                  | Result                                                                                                                                                                                                       |
|----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| One command for everything | `make test` (migration check, SQLite run, PostgreSQL run, coverage gate)                                                                                                                                     |
| Tests                      | 518 tests, all green on **SQLite** and on **PostgreSQL 16**                                                                                                                                                  |
| Coverage                   | **100 %** line + branch of the project code on both databases (migrations, `manage.py`, `wsgi/asgi`, the three settings entry points and generated files are excluded)                                       |
| Linter                     | `ruff check` and `ruff format --check` clean (`make lint`)                                                                                                                                                   |
| `makemigrations --check`   | clean for all project apps. The third-party app `webpush` reports a missing migration that ships with the library, not with this project; it is outside our control (baseline and final state are identical) |
| `check --deploy`           | production settings: only `security.W004` (HSTS, a decision for you, see below). Before: the check crashed because the log directory was missing; development settings: 7 → 6 warnings                       |

Baseline (before any change): `check --deploy` 7 warnings (dev), crash on production settings; `makemigrations --check`
only the `webpush` drift; `ruff` default rules 328 findings; **no tests**. `requirements.txt` was missing six imported
packages (`django-allauth`, `django-modeltranslation`, `httpx`, `Pillow`, `PyJWT`, `json5`, `psycopg2`) and contained
~50 unused tools/transitive packages: it is now a pinned list of direct runtime dependencies; dev tools are in
`requirements-dev.txt`.

## What changed and why

* **Repository hygiene** – removed committed `__pycache__`, `.DS_Store`, `.idea`, an empty file `changed`, an unused
  copy of the settings (`settings_backup_test.py`), dead code (`ifs.py`, `tags.py`, two templates, `html_range`, three
  unused template filters, three unused sitemap classes, ~600 lines of commented-out code).
* **Settings** – dev-only apps moved to `settings.py`; production keeps secrets in environment variables, gets
  `CONN_MAX_AGE=60` with health checks (persistent connections), `X-Frame-Options`; `settingstest.py` selects
  SQLite/PostgreSQL through `TEST_DB`; unused settings removed.
* **Structure** – business logic moved out of the fat views: `aktionen/services.py` (action validation and period rules,
  shared by add *and* edit which had two diverging copies), `utils/periods.py`, `utils/action_feedback.py`,
  `utils/groups.py`, `hall_of_fame/services.py`, `core/models.py` (`HashPasswordsOnSaveMixin` replaces two copies).
  Dispatch tables instead of 300-line `if` ladders in the family, community and settings views. Magic numbers/strings
  are named constants.
* **Security / bugs** – 60+ items, see BUGS_FIXED.md (open redirect, stored XSS, missing permission checks,
  race conditions, crashes).
* **Tests** – `tests/` (pytest-django): models, all views, forms/POST flows, permissions, admin (every registered
  model: list/add/change pages), management commands, cron entry points, signals, social adapter, template tags,
  middleware, sitemaps, error pages, `assertNumQueries`-style limits for the key pages, translation catalogs.
* **Tooling** – `Makefile`, `pyproject.toml` (pytest, coverage, ruff), `.github/workflows/ci.yml` (PostgreSQL service).

## Performance (PostgreSQL 16, generated data, same machine)

Data set A: 300 users, 30,000 actions. Data set B: 3,000 users, 300,000 actions. Time of one request through the
Django test client (includes template rendering).

| Page                                 | Before (A)                                     | After (A)                                           | After (B)          |
|--------------------------------------|------------------------------------------------|-----------------------------------------------------|--------------------|
| Landing page (global statistics)     | 19,391 ms, > 9,000 queries (capture limit hit) | 107 ms (first request, includes warm-up), 9 queries | 56 ms, 9 queries   |
| Dashboard                            | 267 ms                                         | 35 ms, 16 queries                                   | 185 ms, 16 queries |
| User profile                         | 190 ms                                         | 43 ms, 15 queries                                   | 162 ms, 15 queries |
| Family page (all users of the group) | 18,028 ms                                      | 70 ms, 9 queries                                    | 476 ms, 9 queries  |
| History (100 actions)                | 99 ms                                          | 34 ms, 5 queries                                    | –                  |
| Climate points page                  | 52 ms                                          | 12 ms, 7 queries                                    | –                  |

The old landing page and family page grow linearly with users × actions (one query per action *and* per user), so on
data set B the old code would need roughly 190 s per request (extrapolated, not measured). The query count of the old
code could not be captured beyond 9,000 queries. Main causes fixed: `Aktion.impact` loading the related row per action,
per-user loops for totals/ranking, per-row `.count()`/`exists()` in templates (prefetching), unordered queries.
Memory: the landing page no longer instantiates every user and action.

Not measurable here / not done: no HTTP caching headers or page/fragment cache were added (all numbers above are
without cache); static files were already compressed + hashed by `servestatic` (left unchanged); front-end libraries and
images in `static/` were not audited.

**Index**: I evaluated a composite index `Aktion(user, date)` with `EXPLAIN ANALYZE` on 300,000 rows (weekly sum query
0.134 ms without vs 0.212 ms with, the planner keeps using the existing `user_id` index; `ORDER BY date DESC` 0.114 vs
0.124 ms). No gain, so **no index was added**. Consequently the branch contains **no migrations**.

## Migrations

None added, none changed, none applied anywhere. No data migration was necessary, therefore there is nothing to roll
back or verify. All schema-relevant code changes (password mixin, query changes, templates) are neutral for the schema;
`makemigrations --check` proves it.

## Translations

Only English `.po` files exist (German is the source language); 15 catalogs were re-extracted with `makemessages -a`
(per app, as before) and recompiled with `compilemessages`.

* English – filled all empty and corrected all `fuzzy` entries (6 new strings: period labels "Total/Today/Seven days/…",
  duration/goal/reCAPTCHA/community messages; the 4 `fuzzy` entries carried the *neighbouring* entry's wrong text),
  removed 119 obsolete `#~` entries, replaced the acute accent `´` by `'` in 7 strings, fixed "Students werde enabled",
  "legal notice" → "privacy policy" in the privacy text, word order of the hall-of-fame sentence, missing full stops,
  `a action` → `an action`, `hast been` → `has been`, `with who` → `with whom`, "his / her" → "their", header
  `Language: en` and header `fuzzy` flag removed.
* German – source language; only the broken `climate-questde` URL (see below) was fixed in the source.
* New test `tests/test_translations.py` fails on empty, fuzzy or obsolete entries, differing placeholders, `´`, and on
  `.mo` files that are not compiled from the `.po`.
* **Not changed on purpose** (rule "do not change msgids"): German typos inside msgids – "Pflichfelder", "Interner
  Fehler Probiere es später erneut" (no punctuation), "geupdated", a few missing full stops. The only msgid change is
  the dead link `https://climate-questde/…` → `climate-quest.de` in two messages (functional bug).
* Confidence: English is idiomatic where I read it, but I did **not** proofread all ~1,100 entries (the long legal
  texts in `home` and `pages` were only checked with automatic checks for placeholders, tags, German leftovers, odd
  punctuation); a native review of the privacy policy / terms of use is recommended.

## Needs your decision (not changed because behaviour or data would change, or the intent is unclear)

1. **Password reset** e-mails a new password and sets it for anybody who knows the e-mail address (account lock-out by
   third parties, password in clear text in the mail). Recommended: token link flow like the e-mail verification.
2. **`POST /personals/api/devices/ios/register/`** is `csrf_exempt` and unauthenticated: anyone can bind a device token
   to
   any `user_id` (receive someone's notifications). Needs an auth scheme agreed with the iOS app.
3. **Password rules**: `AUTH_PASSWORD_VALIDATORS` are configured but never applied; I only reject empty passwords.
4. **No brute-force protection** for login and for joining families/communities by password.
5. **HSTS** (`SECURE_HSTS_SECONDS`) is not set; enabling it is hard to undo.
6. **Language prefix**: `{% url %}` and `redirect()` produce URLs without `/de|/en`, so every link/redirect costs an
   extra 302, and the target language is taken from the profile/browser rather than the current page. Setting the
   script prefix would fix this but changes all URLs in the HTML.
7. **State-changing GET** requests: logout, like/unlike, delete notification (CSRF-able). Changing to POST changes the
   templates.
8. **Hall of fame**: "vegetarian/vegan" is evaluated for *today* only although the text says "between Monday and today";
   action ids 19/20/22 are hard-coded (constants now, but still production primary keys).
9. **Community ranking** adds each member's bonus points for every period; the family page only for "total". Which is
   intended?
10. **Fan-out in the request**: family chat, delete family/account, petition updates, admin broadcast and the cron jobs
    send one mail + push per recipient synchronously. A task queue would fix it but changes timing semantics.
11. **`icontains` searches** (user search, article/event/forum filters) are ASCII-case-insensitive only on SQLite but
    fully
    case-insensitive on PostgreSQL (e.g. "Ä" vs "ä").
12. **Date defaults** `default=timezone.now` on `DateField`s (e.g. `Aktion.date`) yield a datetime in memory until
    reloaded;
    changing to `timezone.localdate` needs `AlterField` migrations (no DB change).
13. **Unpaginated lists** (history, users search, overviews). Pagination changes the visible output.
14. **Events** cannot be edited when they start within 24 h (same rule as on creation) – intended?
15. **Hard-coded user-visible strings** that are not translated through gettext: notification texts (stored in both
    languages by design), mail subjects/footers (German only), admin-only text; formal "Sie" in the legal pages vs "du"
    in the app.
16. About 40 keys of `core/all_messages.py` look unused (some are looked up dynamically) – not removed.
17. `CONN_MAX_AGE=60` is new: if PgBouncer in transaction mode is used, set it to 0.
18. Production settings (`settingsprod.py`) are not imported by the tests (only by `check --deploy`).
