# -*- coding: utf-8 -*-
from __future__ import absolute_import

from .event_formatter import render_popup_event, team_short


class PollingEngine(object):
    """Platform-neutral polling engine.

    Dependencies are injected to keep this class reusable in other runtimes.
    """

    def __init__(self, api):
        self.api = api

    def collect_new_events(self, subscriptions, seen_ids):
        seen = set(seen_ids or [])
        new_seen = []
        messages = []

        for sub in subscriptions or []:
            if not isinstance(sub, dict):
                continue
            try:
                events = self._load_subscription_events(sub)
            except Exception:
                continue

            for event in events:
                if not isinstance(event, dict):
                    continue
                event_id = event.get("event_id")
                if not event_id or event_id in seen:
                    continue
                seen.add(event_id)
                new_seen.append(event_id)
                messages.append(event.get("text", ""))

        return {
            "new_seen": new_seen,
            "messages": messages,
        }

    def _load_subscription_events(self, subscription):
        if not isinstance(subscription, dict):
            return []
        league = subscription.get("leagueShortcut")
        season = subscription.get("season")
        if not league or not season:
            return []

        mode = subscription.get("type", "league")
        matchday = None
        if mode == "matchday":
            matchday = subscription.get("matchday")
        else:
            current = self.api.get_current_group(league)
            matchday = current.get("GroupOrderID")

        if matchday is None:
            return []

        matches = self.api.get_matchday_matches(league, season, matchday)
        team_id = subscription.get("teamId")
        items = []

        for match in matches:
            if not isinstance(match, dict):
                continue
            if mode == "team" and team_id is not None:
                team1 = (match.get("Team1") or {}).get("TeamId")
                team2 = (match.get("Team2") or {}).get("TeamId")
                if team1 != team_id and team2 != team_id:
                    continue

            goals = match.get("GoalGetter") or []
            if not isinstance(goals, list):
                continue

            for goal in goals:
                if not isinstance(goal, dict):
                    continue
                event_id = self._event_id(match, goal)
                text = render_popup_event(match, goal)
                items.append({"event_id": event_id, "text": text})

        return items

    def _event_id(self, match, goal):
        match_id = match.get("MatchID")
        goal_id = goal.get("GoalGetterID")
        minute = goal.get("GoalGetterMinute")
        score1 = goal.get("ScoreTeam1")
        score2 = goal.get("ScoreTeam2")
        t1 = team_short(match.get("Team1") or {})
        t2 = team_short(match.get("Team2") or {})
        return "%s|%s|%s|%s|%s|%s|%s" % (
            match_id,
            goal_id,
            minute,
            score1,
            score2,
            t1,
            t2,
        )
