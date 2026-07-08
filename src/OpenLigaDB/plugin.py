# -*- coding: utf-8 -*-
from __future__ import absolute_import

from Plugins.Plugin import PluginDescriptor

from . import _
from .core.api import OpenLigaDbClient
from .core.config_store import OpenLigaStore
from .screens import OpenLigaMainScreen
from .services import EventDispatcher, LcdEventService, PollingService, UiEventService

_APP = None


class AppContext(object):
    def __init__(self, session):
        self.session = session
        self.store = OpenLigaStore()
        self.api = OpenLigaDbClient()
        self.ui_service = UiEventService(session)
        self.lcd_service = LcdEventService()
        self.dispatcher = EventDispatcher(self.ui_service, self.lcd_service, self.store)
        self.poller = PollingService(self.api, self.store, self.dispatcher)

    def start(self):
        self.poller.start()

    def stop(self):
        self.poller.stop()



def get_app(session):
    global _APP
    if _APP is None:
        _APP = AppContext(session)
        _APP.start()
    else:
        _APP.session = session
        _APP.ui_service.session = session
    return _APP



def autostart(reason, **kwargs):
    global _APP
    if reason == 0:
        session = kwargs.get("session")
        if session:
            get_app(session)
    elif reason == 1 and _APP is not None:
        _APP.stop()
        _APP = None



def main(session, **kwargs):
    app = get_app(session)
    session.open(OpenLigaMainScreen, app)



def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name="OpenLigaDB",
            description=_("OpenLigaDB Browser"),
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon="plugin.png",
            fnc=main,
        ),
        PluginDescriptor(
            where=PluginDescriptor.WHERE_AUTOSTART,
            fnc=autostart,
        ),
    ]
