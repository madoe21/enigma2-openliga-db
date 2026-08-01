# -*- coding: utf-8 -*-
"""Regression test for the goal-events bug: the OpenLigaDB API returns a match's
goals under the "Goals" key (each item has MatchMinute/GoalGetterID/GoalGetterName/
IsPenalty/IsOwnGoal/ScoreTeam1/ScoreTeam2) - the plugin used to read the
non-existent "GoalGetter"/"GoalGetterMinute" keys instead, so it silently never
found any goal events at all.
"""
from __future__ import absolute_import

import os
import sys
import unittest

try:
    from unittest import mock
except ImportError:  # Python 2
    import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# OpenLigaDB/__init__.py imports real Enigma2 runtime modules (Components.Language,
# Tools.Directories) that only exist on the receiver - stub them so the package can be
# imported standalone for testing the plugin-independent logic (api.py, polling_core.py,
# event_formatter.py never touch enigma modules themselves).
if "Components.Language" not in sys.modules:
    components_pkg = mock.MagicMock()
    components_pkg.language = mock.MagicMock()
    components_pkg.language.getLanguage.return_value = "en_EN"
    components_pkg.language.addCallback = lambda cb: None
    sys.modules["Components"] = mock.MagicMock()
    sys.modules["Components.Language"] = components_pkg
if "Tools.Directories" not in sys.modules:
    tools_pkg = mock.MagicMock()
    tools_pkg.resolveFilename = lambda scope, path: path
    tools_pkg.SCOPE_PLUGINS = "plugins"
    sys.modules["Tools"] = mock.MagicMock()
    sys.modules["Tools.Directories"] = tools_pkg

from OpenLigaDB.core.api import OpenLigaDbClient  # noqa: E402
from OpenLigaDB.polling_core import PollingEngine  # noqa: E402


# Shape matches the real OpenLigaDB getmatchdata response.
SAMPLE_MATCH = {
    "MatchID": 72214,
    "Team1": {"TeamId": 40, "ShortName": "BVB", "TeamName": "Borussia Dortmund"},
    "Team2": {"TeamId": 7, "ShortName": "S04", "TeamName": "Schalke 04"},
    "MatchIsFinished": True,
    "Goals": [
        {
            "GoalID": 1,
            "ScoreTeam1": 1,
            "ScoreTeam2": 0,
            "MatchMinute": 23,
            "GoalGetterID": 11,
            "GoalGetterName": "Max Mustermann",
            "IsPenalty": False,
            "IsOwnGoal": False,
        },
        {
            "GoalID": 2,
            "ScoreTeam1": 1,
            "ScoreTeam2": 1,
            "MatchMinute": 67,
            "GoalGetterID": 22,
            "GoalGetterName": "Erika Musterfrau",
            "IsPenalty": True,
            "IsOwnGoal": False,
        },
    ],
}


class GetMatchEventsTest(unittest.TestCase):
    def test_reads_goals_array_from_real_api_shape(self):
        client = OpenLigaDbClient()
        with mock.patch.object(client, "get_match", return_value=SAMPLE_MATCH):
            events = client.get_match_events(72214)

        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["MatchMinute"], 23)
        self.assertEqual(events[0]["GoalGetterName"], "Max Mustermann")
        self.assertEqual(events[1]["IsPenalty"], True)


class PollingEngineTest(unittest.TestCase):
    def test_collect_new_events_finds_goals_and_reports_minute(self):
        api = mock.Mock()
        api.get_current_group.return_value = {"GroupOrderID": 1}
        api.get_matchday_matches.return_value = [SAMPLE_MATCH]

        engine = PollingEngine(api)
        result = engine.collect_new_events(
            subscriptions=[{"leagueShortcut": "bl1", "season": 2024, "type": "league"}],
            seen_ids=[],
        )

        self.assertEqual(len(result["new_seen"]), 2)
        self.assertEqual(len(result["messages"]), 2)
        # The rendered popup must show the real minute, not the "?" fallback.
        self.assertIn("23'", result["messages"][0])
        self.assertIn("Max Mustermann", result["messages"][0])


if __name__ == "__main__":
    unittest.main()
