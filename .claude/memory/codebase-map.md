# Codebase map (onboarding 2026-07-08)

**enigma2-openliga-db** — Enigma2 (OpenATV 7.6) plugin: Bundesliga football
(tables, matchday, results via the OpenLigaDB API) on the TV. Python. ~1900 LOC.

## Layout
- `src/OpenLigaDB/plugin.py` — entry.
- `src/OpenLigaDB/api.py` (~331 LOC) — OpenLigaDB REST client. **Data layer.**
- `src/OpenLigaDB/services.py` (~153) — orchestration/caching.
- `src/OpenLigaDB/screens.py` (~876) — enigma2 GUI (tables/fixtures).
- `res/`, `control/`, `build/` (gitignored ipk).

## Conventions
- Enigma2 Py3; timeouts on all API calls (main reactor thread).

## Kodi portability: **monolithic (data layer already separate)**
4 files import enigma2 (screens/plugin). `api.py`+`services.py` are the
portable data layer. Port = move them into `core/` (verify enigma2-free,
abstract config), add `platform/kodi/`. Target shape: lotto/stocks/weather.
