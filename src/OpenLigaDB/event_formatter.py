# -*- coding: utf-8 -*-
from __future__ import absolute_import


def team_short(team):
    if not isinstance(team, dict):
        return "?"
    return (
        team.get("ShortName")
        or team.get("TeamShortcut")
        or team.get("TeamName")
        or "?"
    )



def score_from_match_results(match):
    results = match.get("MatchResults") or []
    if not isinstance(results, list) or not results:
        return (0, 0)

    current = None
    current_id = -1
    for result in results:
        result_type = result.get("ResultTypeID")
        if result_type is None:
            result_type = -1
        if result_type >= current_id:
            current_id = result_type
            current = result

    if not current:
        return (0, 0)

    return (current.get("PointsTeam1", 0), current.get("PointsTeam2", 0))



def event_kind(goal):
    if goal.get("IsOwnGoal"):
        return "own goal"
    if goal.get("IsPenalty"):
        return "penalty"
    return "regular goal"



def render_popup_event(match, goal):
    t1 = team_short(match.get("Team1") or {})
    t2 = team_short(match.get("Team2") or {})
    minute = goal.get("MatchMinute") or "?"
    scorer = goal.get("GoalGetterName") or "Unknown"
    kind = event_kind(goal)

    score_a = goal.get("ScoreTeam1")
    score_b = goal.get("ScoreTeam2")
    if score_a is None or score_b is None:
        score_a, score_b = score_from_match_results(match)

    return "%s' %s (%s)\\n%s %s:%s %s" % (
        minute,
        scorer,
        kind,
        t1,
        score_a,
        score_b,
        t2,
    )



def render_event_row(match, goal):
    minute = goal.get("MatchMinute") or "?"
    scorer = goal.get("GoalGetterName") or "Unknown"
    kind = event_kind(goal)

    score_a = goal.get("ScoreTeam1")
    score_b = goal.get("ScoreTeam2")
    if score_a is None or score_b is None:
        score_a, score_b = score_from_match_results(match)

    return "%s'  %s  | %s | %s:%s" % (minute, scorer, kind, score_a, score_b)
