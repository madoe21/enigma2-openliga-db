# -*- coding: utf-8 -*-
from __future__ import absolute_import

import json
import os

SETTINGS_FILE = "/etc/enigma2/openligadb_settings.json"
SUBSCRIPTIONS_FILE = "/etc/enigma2/openligadb_subscriptions.json"
STATE_FILE = "/etc/enigma2/openligadb_state.json"


DEFAULT_SETTINGS = {
    "output_target": "both",
    "polling_interval_sec": 300,
    "message_timeout_sec": 8,
}


class OpenLigaStore(object):
    def __init__(
        self,
        settings_file=SETTINGS_FILE,
        subscriptions_file=SUBSCRIPTIONS_FILE,
        state_file=STATE_FILE,
    ):
        self.settings_file = settings_file
        self.subscriptions_file = subscriptions_file
        self.state_file = state_file

    def _read_json(self, path, fallback):
        try:
            with open(path, "r") as handle:
                return json.load(handle)
        except Exception:
            return fallback

    def _write_json(self, path, data):
        folder = os.path.dirname(path)
        if folder and not os.path.isdir(folder):
            os.makedirs(folder)
        with open(path, "w") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)

    def get_settings(self):
        settings = self._read_json(self.settings_file, {})
        merged = DEFAULT_SETTINGS.copy()
        merged.update(settings)
        return merged

    def save_settings(self, settings):
        merged = DEFAULT_SETTINGS.copy()
        merged.update(settings or {})
        self._write_json(self.settings_file, merged)

    def get_subscriptions(self):
        data = self._read_json(self.subscriptions_file, [])
        if isinstance(data, list):
            return data
        return []

    def save_subscriptions(self, subscriptions):
        self._write_json(self.subscriptions_file, subscriptions or [])

    def add_subscription(self, item):
        subscriptions = self.get_subscriptions()
        signature = self._subscription_signature(item)
        for current in subscriptions:
            if self._subscription_signature(current) == signature:
                return False
        subscriptions.append(item)
        self.save_subscriptions(subscriptions)
        return True

    def remove_subscription(self, index):
        subscriptions = self.get_subscriptions()
        if index < 0 or index >= len(subscriptions):
            return False
        subscriptions.pop(index)
        self.save_subscriptions(subscriptions)
        return True

    def get_seen_ids(self):
        state = self._read_json(self.state_file, {"seen": []})
        seen = state.get("seen") if isinstance(state, dict) else []
        if not isinstance(seen, list):
            return []
        return seen

    def add_seen_ids(self, ids):
        seen = set(self.get_seen_ids())
        for item in ids:
            seen.add(item)
        self._write_json(self.state_file, {"seen": list(seen)[-3000:]})

    def _subscription_signature(self, item):
        return "%s|%s|%s|%s|%s|%s" % (
            item.get("type", ""),
            item.get("sport", ""),
            item.get("leagueShortcut", ""),
            item.get("season", ""),
            item.get("matchday", ""),
            item.get("teamId", ""),
        )
