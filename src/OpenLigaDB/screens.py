# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Components.ScrollLabel import ScrollLabel
from Components.Sources.StaticText import StaticText
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.Directories import SCOPE_PLUGINS, resolveFilename

from . import _
from .core import (
    build_table_row,
    league_latest_season,
    make_league_subscription,
    make_matchday_subscription,
    make_season_subscription,
    make_team_subscription,
    matchday_status_suffix,
    matchday_subscribable,
    season_subscribable,
    to_int,
)
from .event_formatter import render_event_row, score_from_match_results, team_short


def _choice_data(choice):
    if isinstance(choice, (list, tuple)) and len(choice) > 1:
        return choice[1]
    return None


def _league_shortcut_for_season(league, season):
    if not isinstance(league, dict):
        return None

    season_map = league.get("seasonShortcuts") or {}
    if isinstance(season_map, dict):
        resolved = season_map.get(str(season))
        if resolved:
            return resolved

    return league.get("shortcut")


def _league_for_season(league, season):
    if not isinstance(league, dict):
        return {}
    copy = dict(league)
    resolved = _league_shortcut_for_season(league, season)
    if resolved:
        copy["shortcut"] = resolved
    return copy


def _subscribe_team_all_leagues(app, sport, all_leagues, team_id, team_name):
    """Subscribe a team in every league (of this sport) where it participates."""
    added = 0
    for league in (all_leagues or {}).values():
        if not isinstance(league, dict):
            continue
        season = league_latest_season(league)
        if season is None:
            continue
        try:
            league_teams = app.api.get_available_teams(league.get("shortcut", ""), season)
        except Exception:
            continue
        for lt in league_teams:
            if not isinstance(lt, dict):
                continue
            lt_id = lt.get("teamId") or lt.get("TeamId")
            if str(lt_id) == str(team_id):
                created = app.store.add_subscription(
                    make_team_subscription(
                        sport,
                        _league_for_season(league, season),
                        season,
                        team_id,
                        team_name,
                    )
                )
                if created:
                    added += 1
                break
    return added


class BaseListScreen(Screen):
    skin = """
        <screen name="BaseListScreen" position="center,120" size="1000,560" title="OpenLigaDB">
            <widget source="title" render="Label" position="20,10" size="960,35" font="Regular;30" />
            <widget name="list" position="20,55" size="960,420" scrollbarMode="showOnDemand" />
            <widget name="hint" position="20,472" size="960,30" font="Regular;22" />
            <widget source="support" render="Label" position="20,500" size="960,24" font="Regular;18" foregroundColor="#666666" />
            <ePixmap pixmap="skin_default/buttons/red.png" position="20,525" size="220,30" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/green.png" position="250,525" size="220,30" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/yellow.png" position="480,525" size="220,30" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/blue.png" position="710,525" size="270,30" alphatest="on" />
            <widget source="key_red" render="Label" position="20,525" size="220,30" font="Regular;22" halign="center" valign="center" transparent="1" />
            <widget source="key_green" render="Label" position="250,525" size="220,30" font="Regular;22" halign="center" valign="center" transparent="1" />
            <widget source="key_yellow" render="Label" position="480,525" size="220,30" font="Regular;22" halign="center" valign="center" transparent="1" />
            <widget source="key_blue" render="Label" position="710,525" size="270,30" font="Regular;22" halign="center" valign="center" transparent="1" />
        </screen>
    """

    def __init__(self, session, title, hint):
        Screen.__init__(self, session)
        self["title"] = StaticText(title)
        self["list"] = MenuList([])
        self["hint"] = Label(hint)
        self["support"] = StaticText("Support this plugin: https://buymeacoffee.com/madoe21")
        self["key_red"] = StaticText(_("Close"))
        self["key_green"] = StaticText("")
        self["key_yellow"] = StaticText("")
        self["key_blue"] = StaticText("")
        self._rows = []

        self["actions"] = ActionMap(
            ["ColorActions", "OkCancelActions", "DirectionActions"],
            {
                "ok": self.key_ok,
                "cancel": self.close,
                "red": self.close,
                "green": self.key_green,
                "yellow": self.key_yellow,
                "blue": self.key_blue,
                "left": self.key_left,
                "right": self.key_right,
            },
            -1,
        )

    def set_rows(self, rows):
        self._rows = rows or []
        labels = [row[0] for row in self._rows]
        if not labels:
            labels = [_("No entries available")]
        self["list"].setList(labels)

    def current_data(self):
        index = self["list"].getSelectionIndex()
        if index is None or index < 0 or index >= len(self._rows):
            return None
        return self._rows[index][1]

    def key_ok(self):
        pass

    def key_green(self):
        pass

    def key_yellow(self):
        pass

    def key_blue(self):
        pass

    def key_left(self):
        pass

    def key_right(self):
        pass


class OpenLigaMainScreen(BaseListScreen):
    def __init__(self, session, app):
        BaseListScreen.__init__(
            self,
            session,
            _("OpenLigaDB Browser"),
            _("OK to open"),
        )
        self.app = app
        self["key_red"] = StaticText(_("Close"))
        self["key_green"] = StaticText("")
        self["key_yellow"] = StaticText(_("Settings"))
        self["key_blue"] = StaticText(_("Information"))
        self.set_rows(
            [
                (_("Browse events"), "browse"),
                (_("Subscriptions"), "subscriptions"),
            ]
        )

    def key_ok(self):
        action = self.current_data()
        if action == "browse":
            self.session.open(SportsScreen, self.app)
        elif action == "subscriptions":
            self.session.open(SubscriptionsScreen, self.app)

    def key_yellow(self):
        self.session.open(SettingsScreen, self.app)

    def key_blue(self):
        self.session.open(InfoScreen)


class SportsScreen(BaseListScreen):
    def __init__(self, session, app):
        BaseListScreen.__init__(self, session, _("Sports"), _("Loading..."))
        self.app = app
        self.tree = {}
        self._loaded = False
        self.onShow.append(self._load)

    def _load(self):
        if self._loaded:
            return
        self._loaded = True
        import threading
        self._worker = threading.Thread(target=self._fetch)
        self._worker.daemon = True
        self._worker.start()
        from enigma import eTimer
        self._check_timer = eTimer()
        try:
            self._check_timer.timeout.connect(self._check_result)
        except Exception:
            self._check_timer.callback.append(self._check_result)
        self._check_timer.start(500, True)

    def _fetch(self):
        try:
            self._fetch_result = self.app.api.get_sports_tree()
        except Exception:
            self._fetch_result = {}

    def _check_result(self):
        if self._worker.is_alive():
            self._check_timer.start(500, True)
            return
        self.tree = self._fetch_result if isinstance(self._fetch_result, dict) else {}
        rows = []
        for sport in sorted(self.tree.keys()):
            rows.append((sport, sport))
        self.set_rows(rows)
        self["hint"].setText(_("Select a sport"))

    def key_ok(self):
        sport = self.current_data()
        if sport and sport in self.tree:
            self.session.open(LeaguesScreen, self.app, sport, self.tree.get(sport, {}))


class LeaguesScreen(BaseListScreen):
    def __init__(self, session, app, sport, leagues):
        BaseListScreen.__init__(
            self,
            session,
            _("Leagues"),
            _("Select a league") + " | " + _("Blue") + " = " + _("Add") + " " + _("League"),
        )
        self.app = app
        self.sport = sport
        self.leagues = leagues if isinstance(leagues, dict) else {}
        self["key_blue"] = StaticText(_("Add") + " " + _("League"))
        rows = []
        def _league_sort_key(sk):
            lg = self.leagues.get(sk) or {}
            return (-len(lg.get("seasons") or []), (lg.get("name") or sk).lower())
        for shortcut in sorted(self.leagues.keys(), key=_league_sort_key):
            league = self.leagues.get(shortcut) or {}
            if not isinstance(league, dict):
                continue
            rows.append(("%s (%s)" % (league.get("name", shortcut), shortcut), league))
        self.set_rows(rows)

    def key_ok(self):
        league = self.current_data()
        if league:
            self.session.open(SeasonsScreen, self.app, self.sport, league)

    def key_blue(self):
        league = self.current_data()
        if not league:
            return

        season = league_latest_season(league)
        if season is None:
            self.session.open(MessageBox, _("No season available for this league"), MessageBox.TYPE_INFO, timeout=4)
            return

        created = self.app.store.add_subscription(
            make_league_subscription(self.sport, _league_for_season(league, season), season)
        )
        text = _("League subscription added") if created else _("Already subscribed")
        self.session.open(MessageBox, text, MessageBox.TYPE_INFO, timeout=4)


class SeasonsScreen(BaseListScreen):
    def __init__(self, session, app, sport, league):
        BaseListScreen.__init__(
            self,
            session,
            _("Seasons"),
            _("Current season") + " first" + " | " + _("Blue") + " = " + _("Add") + " " + _("Season"),
        )
        self.app = app
        self.sport = sport
        self.league = self.app.api.refresh_league_seasons(league)
        self["key_blue"] = StaticText(_("Add") + " " + _("Season"))
        rows = []
        latest = league_latest_season(self.league)
        for season in self.league.get("seasons", []):
            suffix = ""
            s_val = to_int(season)
            if latest is not None and s_val == latest:
                suffix = " (aktuell)"
            rows.append((str(season) + suffix, season))
        self.set_rows(rows)

    def key_ok(self):
        season = self.current_data()
        if season:
            self.session.open(SeasonOverviewScreen, self.app, self.sport, self.league, season)

    def key_blue(self):
        season = self.current_data()
        if not season:
            return

        latest = league_latest_season(self.league)
        is_allowed, season_value = season_subscribable(season, latest)
        if season_value is None or latest is None:
            self.session.open(MessageBox, _("Could not validate season"), MessageBox.TYPE_INFO, timeout=4)
            return

        if not is_allowed:
            self.session.open(
                MessageBox,
                _("Only current or future seasons can be subscribed"),
                MessageBox.TYPE_INFO,
                timeout=5,
            )
            return

        created = self.app.store.add_subscription(
            make_season_subscription(self.sport, _league_for_season(self.league, season_value), season_value)
        )
        text = _("Season subscription added") if created else _("Already subscribed")
        self.session.open(MessageBox, text, MessageBox.TYPE_INFO, timeout=4)


class SeasonOverviewScreen(BaseListScreen):
    def __init__(self, session, app, sport, league, season):
        title = _("Season") + ": %s %s" % (league.get("shortcut", ""), season)
        BaseListScreen.__init__(
            self,
            session,
            title,
            _("Choose") + ": " + _("Table") + " / " + _("Matchdays"),
        )
        self.app = app
        self.sport = sport
        self.league = league
        self.season = season
        self.set_rows(
            [
                (_("Table"), "table"),
                (_("Matchdays"), "matchdays"),
            ]
        )

    def key_ok(self):
        action = self.current_data()
        if action == "table":
            self.session.open(TableScreen, self.app, self.sport, self.league, self.season)
        elif action == "matchdays":
            self.session.open(MatchdaysScreen, self.app, self.sport, self.league, self.season)


class MatchdaysScreen(BaseListScreen):
    def __init__(self, session, app, sport, league, season):
        BaseListScreen.__init__(
            self,
            session,
            _("Matchdays"),
            _("Select a matchday") + " | " + _("Blue") + " = " + _("Add") + " " + _("Matchday"),
        )
        self.app = app
        self.sport = sport
        self.league = league
        self.season = season
        self.league_shortcut = _league_shortcut_for_season(league, season)
        self["key_blue"] = StaticText(_("Add") + " " + _("Matchday"))
        self.current_group_id = to_int((self.app.api.get_current_group(self.league_shortcut) or {}).get("GroupOrderID"))
        self.latest_season = league_latest_season(league)
        rows = []
        for matchday in self.app.api.get_matchdays(self.league_shortcut, season):
            if not isinstance(matchday, dict):
                continue
            day_id = to_int(matchday.get("id"))
            if day_id is None:
                continue
            status = matchday_status_suffix(day_id, season, self.latest_season, self.current_group_id)
            rows.append((matchday.get("name", str(matchday.get("id"))) + status, day_id))
        self.set_rows(rows)

    def key_ok(self):
        matchday = self.current_data()
        if matchday is not None:
            self.session.open(
                MatchScreen,
                self.app,
                self.sport,
                self.league,
                self.season,
                matchday,
            )

    def key_blue(self):
        matchday = self.current_data()
        if matchday is None:
            return

        is_allowed, season_value, matchday_value = matchday_subscribable(
            matchday,
            self.season,
            self.latest_season,
            self.current_group_id,
        )

        if season_value is None or self.latest_season is None or matchday_value is None:
            self.session.open(MessageBox, _("Could not validate matchday"), MessageBox.TYPE_INFO, timeout=4)
            return

        if not is_allowed:
            self.session.open(
                MessageBox,
                _("Only current or future matchdays can be subscribed"),
                MessageBox.TYPE_INFO,
                timeout=5,
            )
            return

        created = self.app.store.add_subscription(
            make_matchday_subscription(self.sport, _league_for_season(self.league, season_value), season_value, matchday_value)
        )
        text = _("Matchday subscription added") if created else _("Already subscribed")
        self.session.open(MessageBox, text, MessageBox.TYPE_INFO, timeout=4)


class TableScreen(BaseListScreen):
    def __init__(self, session, app, sport, league, season):
        BaseListScreen.__init__(
            self,
            session,
            _("Table"),
            _("Data may be delayed by OpenLigaDB providers."),
        )
        self.app = app
        self.sport = sport
        self.league = league
        self.season = season
        self.league_shortcut = _league_shortcut_for_season(league, season)

        table = self.app.api.get_table(self.league_shortcut, season)
        rows = []
        for index, item in enumerate(table, 1):
            if not isinstance(item, dict):
                continue
            row = build_table_row(item, index)
            rows.append((row, item))

        if not rows:
            rows = [(_("No table data available"), None)]
        self.set_rows(rows)


class MatchScreen(BaseListScreen):
    def __init__(self, session, app, sport, league, season, matchday):
        BaseListScreen.__init__(self, session, _("Matches"), _("OK") + " = " + _("Events"))
        self.app = app
        self.sport = sport
        self.league = league
        self.season = season
        self.matchday = matchday
        self.league_shortcut = _league_shortcut_for_season(league, season)
        self["key_blue"] = StaticText(_("Add") + " " + _("Team"))
        rows = []
        self.matches = self.app.api.get_matchday_matches(self.league_shortcut, season, matchday)
        for match in self.matches:
            if not isinstance(match, dict):
                continue
            t1 = team_short(match.get("Team1") or {})
            t2 = team_short(match.get("Team2") or {})
            p1, p2 = score_from_match_results(match)
            row = "%s  %s %s:%s %s" % (
                match.get("MatchDateTime", ""),
                t1,
                p1,
                p2,
                t2,
            )
            rows.append((row, match))
        self.set_rows(rows)

    def key_ok(self):
        match = self.current_data()
        if match:
            self.session.open(EventScreen, self.app, match)

    def key_blue(self):
        match = self.current_data()
        if not match:
            return
        team1 = match.get("Team1") or {}
        team2 = match.get("Team2") or {}
        choices = [
            (team_short(team1), team1),
            (team_short(team2), team2),
        ]
        self.session.openWithCallback(
            self._on_team_subscription_choice,
            ChoiceBox,
            title=_("Select a team"),
            list=choices,
        )

    def _on_team_subscription_choice(self, choice):
        team = _choice_data(choice)
        if not isinstance(team, dict):
            return
        team_id = team.get("teamId") or team.get("TeamId")
        team_name = team.get("teamName") or team.get("TeamName") or team_short(team)
        try:
            tree = self.app.api.get_sports_tree()
            all_leagues = (tree or {}).get(self.sport) or {}
        except Exception:
            all_leagues = {}
        added = _subscribe_team_all_leagues(self.app, self.sport, all_leagues, team_id, team_name)
        if added > 0:
            text = _("%d leagues subscribed for %s") % (added, team_name)
        else:
            # Fallback: subscribe in the current league only
            season = self.season
            created = self.app.store.add_subscription(
                make_team_subscription(
                    self.sport,
                    _league_for_season(self.league, season),
                    season,
                    team_id,
                    team_name,
                )
            )
            text = _("Team subscription added") if created else _("Already subscribed")
        self.session.open(MessageBox, text, MessageBox.TYPE_INFO, timeout=4)


class EventScreen(BaseListScreen):
    def __init__(self, session, app, match):
        BaseListScreen.__init__(self, session, _("Events"), _("Data may be delayed by OpenLigaDB providers."))
        self.app = app
        self.match = match

        match_id = match.get("MatchID")
        events = []
        if match_id is not None:
            events = self.app.api.get_match_events(match_id)

        rows = []
        for event in events:
            if not isinstance(event, dict):
                continue
            rows.append((render_event_row(match, event), event))
        if not rows:
            rows = [(_("No events available"), None)]
        self.set_rows(rows)


class SubscriptionsScreen(BaseListScreen):
    def __init__(self, session, app):
        BaseListScreen.__init__(self, session, _("Subscriptions"), _("Delete") + " / " + _("Add"))
        self.app = app
        self["key_red"] = StaticText(_("Delete"))
        self["key_green"] = StaticText(_("Add"))
        self.onShow.append(self.reload)

    def reload(self):
        rows = []
        for idx, item in enumerate(self.app.store.get_subscriptions()):
            if not isinstance(item, dict):
                continue
            if item.get("type") == "team":
                text = "[TEAM] %s | %s | %s" % (
                    item.get("teamName", "?"),
                    item.get("leagueShortcut", "?"),
                    item.get("season", "?"),
                )
            elif item.get("type") == "matchday":
                text = "[MATCHDAY] %s | %s | %s" % (
                    item.get("leagueShortcut", "?"),
                    item.get("season", "?"),
                    item.get("matchday", "?"),
                )
            elif item.get("type") == "season":
                text = "[SEASON] %s | %s" % (
                    item.get("leagueShortcut", "?"),
                    item.get("season", "?"),
                )
            else:
                text = "[LEAGUE] %s | %s" % (
                    item.get("leagueShortcut", "?"),
                    item.get("season", "?"),
                )
            rows.append((text, idx))
        self.set_rows(rows)

    def key_red(self):
        index = self.current_data()
        if index is None:
            self.session.open(MessageBox, _("No subscription selected"), MessageBox.TYPE_INFO, timeout=3)
            return
        if self.app.store.remove_subscription(index):
            self.session.open(MessageBox, _("Subscription removed"), MessageBox.TYPE_INFO, timeout=3)
            self.reload()

    def key_green(self):
        tree = self.app.api.get_sports_tree()
        if not isinstance(tree, dict) or not tree:
            self.session.open(MessageBox, _("No sports available"), MessageBox.TYPE_INFO, timeout=4)
            return
        self.session.open(AddSubTypeScreen, self.app, tree)



class AddSubTypeScreen(BaseListScreen):
    def __init__(self, session, app, tree):
        BaseListScreen.__init__(self, session, _("Add subscription"), _("Select subscription type"))
        self.app = app
        self.tree = tree
        self.set_rows([
            (_("League"), "league"),
            (_("Team"), "team"),
        ])

    def key_ok(self):
        mode = self.current_data()
        if mode:
            self.session.open(AddSubSportScreen, self.app, self.tree, mode)


class AddSubSportScreen(BaseListScreen):
    def __init__(self, session, app, tree, mode):
        BaseListScreen.__init__(self, session, _("Select a sport"), _("Select a sport"))
        self.app = app
        self.tree = tree
        self.mode = mode
        rows = []
        for sport in sorted(tree.keys()):
            rows.append((sport, sport))
        self.set_rows(rows)

    def key_ok(self):
        sport = self.current_data()
        if sport and sport in self.tree:
            if self.mode == "team":
                self.session.open(AddSubTeamScreen, self.app, sport, self.tree[sport])
            else:
                self.session.open(AddSubLeagueScreen, self.app, sport, self.tree[sport], self.mode)


class AddSubLeagueScreen(BaseListScreen):
    def __init__(self, session, app, sport, leagues, mode):
        BaseListScreen.__init__(self, session, _("Select a league"), _("Select a league"))
        self.app = app
        self.sport = sport
        self.leagues = leagues if isinstance(leagues, dict) else {}
        self.mode = mode
        rows = []

        def _sort_key(sk):
            lg = self.leagues.get(sk) or {}
            return (-len(lg.get("seasons") or []), (lg.get("name") or sk).lower())

        for shortcut in sorted(self.leagues.keys(), key=_sort_key):
            league = self.leagues.get(shortcut) or {}
            if not isinstance(league, dict):
                continue
            rows.append(("%s (%s)" % (league.get("name", shortcut), shortcut), league))
        self.set_rows(rows)

    def key_ok(self):
        league = self.current_data()
        if not league:
            return
        season = league_latest_season(league)
        if season is None:
            self.session.open(MessageBox, _("No season available for this league"), MessageBox.TYPE_INFO, timeout=4)
            return
        created = self.app.store.add_subscription(
            make_league_subscription(self.sport, _league_for_season(league, season), season)
        )
        text = _("League subscription added") if created else _("Already subscribed")
        self.session.open(MessageBox, text, MessageBox.TYPE_INFO, timeout=4)


class AddSubTeamScreen(BaseListScreen):
    def __init__(self, session, app, sport, all_leagues):
        BaseListScreen.__init__(self, session, _("Select a team"), _("Subscribes the team in all leagues of this sport"))
        self.app = app
        self.sport = sport
        self.all_leagues = all_leagues if isinstance(all_leagues, dict) else {}
        rows = []
        # Use the league with the most seasons as canonical team list source
        primary = None
        for lg in self.all_leagues.values():
            if not isinstance(lg, dict):
                continue
            if primary is None or len(lg.get("seasons") or []) > len(primary.get("seasons") or []):
                primary = lg
        if primary:
            season = league_latest_season(primary)
            if season is not None:
                teams = self.app.api.get_available_teams(primary.get("shortcut", ""), season)
                for team in sorted(teams, key=lambda t: (t.get("teamName") or t.get("TeamName") or "").lower()):
                    if not isinstance(team, dict):
                        continue
                    name = team.get("teamName") or team.get("TeamName") or team_short(team)
                    rows.append((name, team))
        self.set_rows(rows)

    def key_ok(self):
        team = self.current_data()
        if not isinstance(team, dict):
            return
        team_id = team.get("teamId") or team.get("TeamId")
        team_name = team.get("teamName") or team.get("TeamName") or team_short(team)
        added = _subscribe_team_all_leagues(self.app, self.sport, self.all_leagues, team_id, team_name)
        if added > 0:
            text = _("%d leagues subscribed for %s") % (added, team_name)
        else:
            text = _("Already subscribed or no leagues found")
        self.session.open(MessageBox, text, MessageBox.TYPE_INFO, timeout=5)
        self.close()


class SettingsScreen(BaseListScreen):
    TARGET_OPTIONS = [
        ("ui", _("UI only")),
        ("lcd", _("LCD only")),
        ("both", _("UI + LCD")),
    ]
    POLL_OPTIONS = [60, 120, 300, 600, 900]
    MESSAGE_OPTIONS = [4, 6, 8, 10, 15]

    def __init__(self, session, app):
        BaseListScreen.__init__(self, session, _("Settings"), _("Left/Right changes value"))
        self.app = app
        self["key_green"] = StaticText(_("Save"))
        self.settings = self.app.store.get_settings()
        self.fields = ["output_target", "polling_interval_sec", "message_timeout_sec"]
        self.render_rows()

    def render_rows(self):
        target_value = self.settings.get("output_target", "both")
        target_label = target_value
        for key, label in self.TARGET_OPTIONS:
            if key == target_value:
                target_label = label
                break
        rows = [
            (_("Output target") + ": " + target_label, "output_target"),
            (_("Polling interval (s)") + ": " + str(self.settings.get("polling_interval_sec", 300)), "polling_interval_sec"),
            (_("Message timeout (s)") + ": " + str(self.settings.get("message_timeout_sec", 8)), "message_timeout_sec"),
        ]
        self.set_rows(rows)

    def _rotate(self, key, direction):
        current = self.settings.get(key)
        if key == "output_target":
            values = [x[0] for x in self.TARGET_OPTIONS]
        elif key == "polling_interval_sec":
            values = self.POLL_OPTIONS
        else:
            values = self.MESSAGE_OPTIONS

        if current not in values:
            current = values[0]
        index = values.index(current)
        index = (index + direction) % len(values)
        self.settings[key] = values[index]

    def key_left(self):
        key = self.current_data()
        if key:
            self._rotate(key, -1)
            self.render_rows()

    def key_right(self):
        key = self.current_data()
        if key:
            self._rotate(key, 1)
            self.render_rows()

    def key_green(self):
        self.app.store.save_settings(self.settings)
        self.app.poller.start()
        self.session.open(MessageBox, _("Settings saved"), MessageBox.TYPE_INFO, timeout=3)


class InfoScreen(Screen):
    skin = """
        <screen name="InfoScreen" position="center,90" size="1000,620" title="OpenLigaDB Info">
            <widget source="title" render="Label" position="20,10" size="960,35" font="Regular;30" />
            <widget name="body" position="20,55" size="690,520" scrollbarMode="showOnDemand" />
            <widget name="qr" position="740,100" size="240,240" alphatest="blend" />
            <widget source="support" render="Label" position="20,560" size="960,24" font="Regular;18" foregroundColor="#666666" />
            <ePixmap pixmap="skin_default/buttons/red.png" position="20,585" size="220,30" alphatest="on" />
            <widget source="key_red" render="Label" position="20,585" size="220,30" font="Regular;22" halign="center" valign="center" transparent="1" />
        </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self["title"] = StaticText(_("Information"))
        self["key_red"] = StaticText(_("Close"))
        self["support"] = StaticText("Support this plugin: https://buymeacoffee.com/madoe21")
        self["body"] = ScrollLabel(self._build_info_text())
        self["qr"] = Pixmap()
        self.onLayoutFinish.append(self._load_qr_png)

        self["actions"] = ActionMap(
            ["OkCancelActions", "DirectionActions", "ColorActions"],
            {
                "cancel": self.close,
                "ok": self.close,
                "red": self.close,
                "up": self["body"].pageUp,
                "down": self["body"].pageDown,
                "left": self["body"].pageUp,
                "right": self["body"].pageDown,
            },
            -1,
        )

    def _build_info_text(self):
        lines = [
            "OpenLigaDB Plugin",
            "",
            _("Data source") + ": OpenLigaDB (https://www.openligadb.de)",
            _("Data may be delayed by OpenLigaDB providers."),
            "",
            _("Controls") + ":",
            _("RED = Back/Exit, GREEN = direct action, BLUE = context action"),
            "",
            _("Thanks") + ":",
            _("Thank you OpenLigaDB for providing open sports data."),
            "",
            "GitHub: https://github.com/madoe21/enigma2-openliga-db",
            "Buy me a coffee: https://buymeacoffee.com/madoe21",
        ]
        return "\n".join(lines)

    def _load_qr_png(self):
        candidate_paths = [
            resolveFilename(SCOPE_PLUGINS, "Extensions/OpenLigaDB/res/qr_buymeacoffee.png"),
            resolveFilename(SCOPE_PLUGINS, "Extensions/OpenLigaDB/res/qr_code.png"),
            os.path.join(os.path.dirname(__file__), "res", "qr_buymeacoffee.png"),
            os.path.join(os.path.dirname(__file__), "res", "qr_code.png"),
        ]
        for path in candidate_paths:
            if os.path.exists(path):
                try:
                    self["qr"].instance.setPixmapFromFile(path)
                    return
                except Exception:
                    pass
