# -*- coding: utf-8 -*-
from __future__ import absolute_import

import gettext

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

PLUGIN_DOMAIN = "OpenLigaDB"
PLUGIN_PATH = "Extensions/OpenLigaDB/locale"

_DE_FALLBACK = {
    "OpenLigaDB": "OpenLigaDB",
    "Browse events": "Ereignisse durchsuchen",
    "Subscriptions": "Abonnements",
    "Settings": "Einstellungen",
    "Information": "Informationen",
    "Refresh now": "Jetzt aktualisieren",
    "OpenLigaDB Browser": "OpenLigaDB Browser",
    "Sports": "Sportarten",
    "Leagues": "Ligen",
    "Seasons": "Saisons",
    "Matchdays": "Spieltage",
    "Matches": "Spiele",
    "Events": "Ereignisse",
    "No entries available": "Keine Einträge verfügbar",
    "Already subscribed": "Bereits abonniert",
    "No events available": "Keine Ereignisse verfügbar",
    "Delete": "Löschen",
    "Add": "Hinzufügen",
    "Back": "Zurück",
    "Exit": "Beenden",
    "Save": "Speichern",
    "Polling interval (s)": "Polling-Intervall (s)",
    "Message timeout (s)": "Meldungsdauer (s)",
    "Output target": "Ausgabeziel",
    "UI only": "Nur UI",
    "LCD only": "Nur LCD",
    "UI + LCD": "UI + LCD",
    "League subscription added": "Liga-Abonnement hinzugefügt",
    "Team subscription added": "Vereins-Abonnement hinzugefügt",
    "Subscription removed": "Abonnement entfernt",
    "Data source": "Datenquelle",
    "Delayed data notice": "Hinweis zu zeitverzögerten Daten",
    "Data may be delayed by OpenLigaDB providers.": "Daten können durch OpenLigaDB-Quellen zeitverzögert sein.",
    "Thanks": "Dank",
    "Thank you OpenLigaDB for providing open sports data.": "Danke an OpenLigaDB für die Bereitstellung offener Sportdaten.",
    "Choose subscription type": "Abonnement-Typ wählen",
    "League": "Liga",
    "Team": "Verein",
    "Select a sport": "Sportart wählen",
    "Select a league": "Liga wählen",
    "Select a team": "Verein wählen",
    "Select a matchday": "Spieltag wählen",
    "Current season": "Aktuelle Saison",
    "OK": "OK",
    "Left/Right changes value": "Links/Rechts ändert den Wert",
    "No subscription selected": "Kein Abonnement ausgewählt",
    "Settings saved": "Einstellungen gespeichert",
    "Poll executed": "Polling ausgeführt",
    "Network/API error": "Netzwerk/API-Fehler",
}


def localeInit():
    gettext.bindtextdomain(PLUGIN_DOMAIN, resolveFilename(SCOPE_PLUGINS, PLUGIN_PATH))


def _(txt):
    translated = gettext.dgettext(PLUGIN_DOMAIN, txt)
    if translated != txt:
        return translated

    try:
        lang = language.getLanguage()[:2]
    except Exception:
        lang = "en"

    if lang == "de":
        return _DE_FALLBACK.get(txt, txt)
    return txt


localeInit()
try:
    language.addCallback(localeInit)
except Exception:
    pass
