# -*- coding: utf-8 -*-
from __future__ import absolute_import

import json
import re
from datetime import datetime

try:
    from urllib2 import urlopen
except Exception:
    from urllib.request import urlopen


class OpenLigaDbClient(object):
    BASE_URL = "https://api.openligadb.de"

    SPORT_NAME_MAP = {
        "football": "Fußball",
        "soccer": "Fußball",
        "womens football": "Frauenfußball",
        "women football": "Frauenfußball",
        "women's football": "Frauenfußball",
        "fussball": "Fußball",
    }

    def _safe_text(self, value, fallback):
        if isinstance(value, (str, int, float)):
            text = str(value).strip()
            if text:
                return text
        return fallback

    def _safe_season(self, value):
        if isinstance(value, bool) or value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None
            try:
                return int(text)
            except Exception:
                return text
        return None

    def _extract_sport_name(self, league):
        raw = league.get("leagueSport")
        if raw is None:
            raw = league.get("sport")

        if isinstance(raw, dict):
            candidate = raw.get("sportName") or raw.get("name") or raw.get("Name")
            return self._safe_text(candidate, "Football")

        return self._safe_text(raw, "Football")

    def _normalize_sport_name(self, name):
        base = self._safe_text(name, "Football")
        mapped = self.SPORT_NAME_MAP.get(base.strip().lower())
        if mapped:
            return mapped
        return base

    def _normalize_shortcut_key(self, shortcut):
        key = self._safe_text(shortcut, "").strip().lower()
        key = key.strip("'\" ")
        if key.endswith("alt") and len(key) > 3:
            key = key[:-3]
        return key

    def _choose_better_shortcut(self, current_shortcut, candidate_shortcut):
        current = self._safe_text(current_shortcut, "")
        candidate = self._safe_text(candidate_shortcut, "")
        if not current:
            return candidate
        if not candidate:
            return current

        def rank(value):
            lower = value.lower()
            is_alt = 1 if lower.endswith("alt") else 0
            return (is_alt, len(lower), lower)

        if rank(candidate) < rank(current):
            return candidate
        return current

    def _normalize_league_name(self, value, fallback):
        text = self._safe_text(value, fallback)
        # Strip trailing season parts like "2004/2005", "09/10", "2025/2026" or "...alt/old".
        text = re.sub(
            r"\s+(?:\d{2,4})(?:\s*/\s*\d{2,4})?(?:\s*(?:alt|old))?$",
            "",
            text,
            flags=re.IGNORECASE,
        )
        text = text.replace("Fussball", "Fußball")
        text = re.sub(r"\s+", " ", text).strip()
        return text or fallback

    def _as_dict(self, value):
        if isinstance(value, dict):
            return value
        return None

    def _as_list_of_dicts(self, value):
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, dict)]

    def _season_sort_key(self, value):
        try:
            return (0, int(value))
        except Exception:
            return (1, str(value))

    def _needs_season_refresh(self, seasons):
        numeric = []
        for value in seasons or []:
            try:
                numeric.append(int(value))
            except Exception:
                continue

        if not numeric:
            return True

        now_year = datetime.utcnow().year
        latest = max(numeric)
        if latest < (now_year - 1):
            return True

        return False

    def refresh_league_seasons(self, league):
        if not isinstance(league, dict):
            return {}

        result = dict(league)
        seasons = list(result.get("seasons") or [])
        season_shortcuts = dict(result.get("seasonShortcuts") or {})

        if not self._needs_season_refresh(seasons):
            seasons.sort(key=self._season_sort_key, reverse=True)
            result["seasons"] = seasons
            result["seasonShortcuts"] = season_shortcuts
            return result

        shortcut_candidates = []
        base_shortcut = self._safe_text(result.get("shortcut"), "")
        if base_shortcut:
            shortcut_candidates.append(base_shortcut)

        for mapped in season_shortcuts.values():
            mapped_shortcut = self._safe_text(mapped, "")
            if mapped_shortcut and mapped_shortcut not in shortcut_candidates:
                shortcut_candidates.append(mapped_shortcut)

        now_year = datetime.utcnow().year
        # Probe a bounded recent window to avoid excessive API calls.
        for probe_year in range(now_year + 1, now_year - 20, -1):
            for candidate in shortcut_candidates:
                groups = self.get_available_groups(candidate, probe_year)
                if groups:
                    if probe_year not in seasons:
                        seasons.append(probe_year)
                    season_shortcuts[str(probe_year)] = self._choose_better_shortcut(
                        season_shortcuts.get(str(probe_year)),
                        candidate,
                    )

        seasons.sort(key=self._season_sort_key, reverse=True)
        result["seasons"] = seasons
        result["seasonShortcuts"] = season_shortcuts
        return result

    def _fetch_json(self, path):
        url = "%s/%s" % (self.BASE_URL, path.lstrip("/"))
        try:
            response = urlopen(url, timeout=12)
            payload = response.read()
        except Exception:
            return None
        if not payload:
            return None
        try:
            text = payload.decode("utf-8")
        except Exception:
            text = payload
        try:
            return json.loads(text)
        except Exception:
            return None

    def get_available_leagues(self):
        data = self._fetch_json("getavailableleagues")
        return self._as_list_of_dicts(data)

    def get_sports_tree(self):
        sports = {}
        for league in self.get_available_leagues():
            sport = self._normalize_sport_name(self._extract_sport_name(league))
            # Skip test/dummy leagues (sport "Test" in API)
            raw_sport = league.get("sport") or {}
            if isinstance(raw_sport, dict) and (raw_sport.get("sportName") or "").strip().lower() == "test":
                continue
            shortcut = self._safe_text(league.get("leagueShortcut"), "")
            shortcut_key = self._normalize_shortcut_key(shortcut)
            if not shortcut_key:
                continue
            season = self._safe_season(league.get("leagueSeason"))
            league_name = self._normalize_league_name(league.get("leagueName"), shortcut)
            if sport not in sports:
                sports[sport] = {}

            if shortcut_key not in sports[sport]:
                sports[sport][shortcut_key] = {
                    "name": league_name,
                    "shortcut": shortcut,
                    "sport": sport,
                    "seasons": [],
                    "seasonShortcuts": {},
                }
            else:
                sports[sport][shortcut_key]["name"] = self._normalize_league_name(
                    sports[sport][shortcut_key].get("name"),
                    league_name,
                )
                sports[sport][shortcut_key]["shortcut"] = self._choose_better_shortcut(
                    sports[sport][shortcut_key].get("shortcut"),
                    shortcut,
                )

            if season is not None and season not in sports[sport][shortcut_key]["seasons"]:
                sports[sport][shortcut_key]["seasons"].append(season)

            if season is not None:
                season_map = sports[sport][shortcut_key].setdefault("seasonShortcuts", {})
                season_key = str(season)
                season_map[season_key] = self._choose_better_shortcut(
                    season_map.get(season_key),
                    shortcut,
                )

        for sport in sports.keys():
            for shortcut_key in sports[sport].keys():
                seasons = sports[sport][shortcut_key]["seasons"]
                seasons.sort(key=self._season_sort_key, reverse=True)
        return sports

    def get_current_group(self, league_shortcut):
        data = self._fetch_json("getcurrentgroup/%s" % league_shortcut)
        as_dict = self._as_dict(data)
        if as_dict is not None:
            return as_dict
        return {}

    def get_matchday_matches(self, league_shortcut, season, matchday):
        data = self._fetch_json(
            "getmatchdata/%s/%s/%s" % (league_shortcut, season, matchday)
        )
        return self._as_list_of_dicts(data)

    def get_matchdays(self, league_shortcut, season):
        groups = self.get_available_groups(league_shortcut, season)
        if groups:
            return groups

        data = self._fetch_json("getmatchdata/%s/%s" % (league_shortcut, season))
        days = []
        if not isinstance(data, list):
            return days
        for match in self._as_list_of_dicts(data):
            group = match.get("Group") or {}
            if not isinstance(group, dict):
                continue
            group_order = group.get("GroupOrderID")
            group_name = group.get("GroupName") or ("Matchday %s" % group_order)
            if group_order is None:
                continue
            found = [d for d in days if d["id"] == group_order]
            if not found:
                days.append({"id": group_order, "name": group_name})
        days.sort(key=lambda x: x["id"])
        return days

    def get_available_groups(self, league_shortcut, season):
        data = self._fetch_json("getavailablegroups/%s/%s" % (league_shortcut, season))
        days = []
        if not isinstance(data, list):
            return days

        for group in self._as_list_of_dicts(data):
            group_id = group.get("GroupOrderID")
            group_name = group.get("GroupName") or ("Matchday %s" % group_id)
            if group_id is None:
                continue
            days.append({"id": group_id, "name": group_name})

        days.sort(key=lambda x: x["id"])
        return days

    def get_match(self, match_id):
        data = self._fetch_json("getmatchdata/%s" % match_id)
        as_dict = self._as_dict(data)
        if as_dict is not None:
            return as_dict
        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict):
                return first
        return {}

    def get_match_events(self, match_id):
        match = self.get_match(match_id)
        events = match.get("Goals") or []
        if isinstance(events, list):
            return events
        return []

    def get_available_teams(self, league_shortcut, season):
        data = self._fetch_json("getavailableteams/%s/%s" % (league_shortcut, season))
        return self._as_list_of_dicts(data)

    def get_table(self, league_shortcut, season):
        data = self._fetch_json("getbltable/%s/%s" % (league_shortcut, season))
        return self._as_list_of_dicts(data)
