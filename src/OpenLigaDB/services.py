# -*- coding: utf-8 -*-
from __future__ import absolute_import

from enigma import eTimer

try:
    from enigma import evfd
except Exception:
    evfd = None

try:
    from enigma import eDBoxLCD
except Exception:
    eDBoxLCD = None

from Screens.MessageBox import MessageBox
from Tools import Notifications

from .polling_core import PollingEngine



def timer_connect(timer, callback):
    try:
        timer.timeout.connect(callback)
    except Exception:
        timer.callback.append(callback)


class UiEventService(object):
    def __init__(self, session):
        self.session = session

    def show(self, text, timeout_sec):
        Notifications.AddPopup(text, MessageBox.TYPE_INFO, timeout=timeout_sec)


class LcdEventService(object):
    def __init__(self):
        self.restore_timer = eTimer()
        timer_connect(self.restore_timer, self.restore)

    def _write(self, text):
        if evfd is not None:
            try:
                evfd.getInstance().vfd_write_string(text)
                return
            except Exception:
                pass
        if eDBoxLCD is not None:
            try:
                eDBoxLCD.getInstance().setText(text)
            except Exception:
                pass

    def show(self, text, timeout_sec):
        short = text.replace("\n", " | ")
        self._write(short[:60])
        self.restore_timer.start(timeout_sec * 1000, True)

    def restore(self):
        self._write("")


class EventDispatcher(object):
    def __init__(self, ui_service, lcd_service, store):
        self.ui_service = ui_service
        self.lcd_service = lcd_service
        self.store = store

    def dispatch(self, text):
        settings = self.store.get_settings()
        target = settings.get("output_target", "both")
        timeout = int(settings.get("message_timeout_sec", 8))

        if target in ("ui", "both"):
            self.ui_service.show(text, timeout)
        if target in ("lcd", "both"):
            self.lcd_service.show(text, timeout)


class PollingService(object):
    MIN_INTERVAL_MS = 15000

    def __init__(self, api, store, dispatcher):
        self.api = api
        self.store = store
        self.dispatcher = dispatcher
        self.engine = PollingEngine(api)
        self.timer = eTimer()
        timer_connect(self.timer, self._on_timer)
        self._worker = None
        self._result = None

    def start(self):
        self._schedule_next(5000)

    def stop(self):
        try:
            self.timer.stop()
        except Exception:
            pass

    def trigger_now(self):
        self._start_worker()

    def _schedule_next(self, delay_ms=None):
        settings = self.store.get_settings()
        polling_interval = int(settings.get("polling_interval_sec", 300))
        if delay_ms is None:
            delay_ms = max(polling_interval * 1000, self.MIN_INTERVAL_MS)
        else:
            delay_ms = max(delay_ms, self.MIN_INTERVAL_MS)
        self.timer.start(delay_ms, True)

    def _on_timer(self):
        if self._worker is not None and self._worker.is_alive():
            self.timer.start(2000, True)
            return
        if self._result is not None:
            self._process_result(self._result)
            self._result = None
            self._schedule_next()
        else:
            self._start_worker()

    def _start_worker(self):
        import threading
        self._result = None
        self._worker = threading.Thread(target=self._tick_bg)
        self._worker.daemon = True
        self._worker.start()
        self.timer.start(2000, True)

    def _tick_bg(self):
        try:
            result = self.engine.collect_new_events(
                self.store.get_subscriptions(),
                self.store.get_seen_ids(),
            )
        except Exception:
            result = {"new_seen": [], "messages": []}
        self._result = result

    def _process_result(self, result):
        new_seen = result.get("new_seen", [])
        messages = result.get("messages", [])

        for text in messages:
            self.dispatcher.dispatch(text)

        if new_seen:
            self.store.add_seen_ids(new_seen)
