# -*- coding: utf-8 -*-
from __future__ import absolute_import


def to_int(value):
    try:
        return int(value)
    except Exception:
        return None


def league_latest_season(league):
    seasons = league.get("seasons", []) if isinstance(league, dict) else []
    numeric = [s for s in [to_int(x) for x in seasons] if s is not None]
    if not numeric:
        return None
    return max(numeric)


def season_subscribable(selected_season, latest_season):
    season_value = to_int(selected_season)
    if season_value is None or latest_season is None:
        return (False, season_value)
    return (season_value >= latest_season, season_value)


def matchday_subscribable(selected_matchday, season, latest_season, current_group_id):
    season_value = to_int(season)
    matchday_value = to_int(selected_matchday)
    if season_value is None or latest_season is None or matchday_value is None:
        return (False, season_value, matchday_value)

    if season_value < latest_season:
        return (False, season_value, matchday_value)

    if season_value == latest_season and current_group_id is not None and matchday_value < current_group_id:
        return (False, season_value, matchday_value)

    return (True, season_value, matchday_value)


def matchday_status_suffix(matchday_id, season, latest_season, current_group_id):
    day_id = to_int(matchday_id)
    season_value = to_int(season)
    if day_id is None or season_value is None:
        return ""

    if latest_season is not None and season_value > latest_season:
        return " (ausstehend)"

    if latest_season is not None and season_value == latest_season and current_group_id is not None:
        if day_id == current_group_id:
            return " (aktuell)"
        if day_id > current_group_id:
            return " (ausstehend)"

    return ""


def build_table_row(item, fallback_rank):
    rank = item.get("Position")
    if rank is None:
        rank = item.get("Place")
    if rank is None:
        rank = fallback_rank

    team = item.get("TeamName") or item.get("ShortName") or "?"
    points = item.get("Points", 0)
    goals = item.get("Goals", 0)
    opp = item.get("OpponentGoals", 0)
    wins = item.get("Won", 0)
    draws = item.get("Draw", 0)
    lost = item.get("Lost", 0)

    return "%s. %s | P:%s | T:%s:%s | W/D/L:%s/%s/%s" % (
        rank,
        team,
        points,
        goals,
        opp,
        wins,
        draws,
        lost,
    )


def make_league_subscription(sport, league, season):
    return {
        "type": "league",
        "sport": sport,
        "leagueName": league.get("name"),
        "leagueShortcut": league.get("shortcut"),
        "season": season,
    }


def make_season_subscription(sport, league, season):
    return {
        "type": "season",
        "sport": sport,
        "leagueName": league.get("name"),
        "leagueShortcut": league.get("shortcut"),
        "season": season,
    }


def make_matchday_subscription(sport, league, season, matchday):
    return {
        "type": "matchday",
        "sport": sport,
        "leagueName": league.get("name"),
        "leagueShortcut": league.get("shortcut"),
        "season": season,
        "matchday": matchday,
    }


def make_team_subscription(sport, league, season, team_id, team_name):
    return {
        "type": "team",
        "sport": sport,
        "leagueName": league.get("name"),
        "leagueShortcut": league.get("shortcut"),
        "season": season,
        "teamId": team_id,
        "teamName": team_name,
    }
