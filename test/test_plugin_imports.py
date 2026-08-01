# -*- coding: utf-8 -*-
"""Smoke test: the whole plugin module chain must actually import.

Regression for the crash reported when opening the Extensions menu: this
package used to ship both src/OpenLigaDB/core.py (a module) *and*
src/OpenLigaDB/core/ (a package) as siblings with the same name "core".
Python resolves the package on `from .core import <name>`, silently
shadowing the module - so `screens.py`'s `from .core import (build_table_row,
...)` always raised ImportError, which cascades: plugin.py imports screens.py
at module load time, so the whole plugin failed to import and Enigma2 could
neither list nor open it. `ast.parse()`-based syntax checks never catch this
class of bug - only an actual import does.
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


def _stub_module(name, **attrs):
    if name in sys.modules:
        return sys.modules[name]
    mod = mock.MagicMock()
    for key, value in attrs.items():
        setattr(mod, key, value)
    sys.modules[name] = mod
    return mod


# Every Enigma2-runtime import touched anywhere in the plugin's module chain
# (plugin.py -> screens.py/services.py -> Components.*/Screens.*/Tools.*/enigma/
# Plugins.Plugin) - only exists on the real receiver, so it's stubbed here to
# make the import chain exercisable in plain CI.
_stub_module("Components")
_stub_module("Components.Language", language=mock.MagicMock(
    getLanguage=lambda: "en_EN", addCallback=lambda cb: None,
))
_stub_module("Components.ActionMap", ActionMap=mock.MagicMock())
_stub_module("Components.Label", Label=mock.MagicMock())
_stub_module("Components.MenuList", MenuList=mock.MagicMock())
_stub_module("Components.Pixmap", Pixmap=mock.MagicMock())
_stub_module("Components.ScrollLabel", ScrollLabel=mock.MagicMock())
_stub_module("Components.Sources")
_stub_module("Components.Sources.StaticText", StaticText=mock.MagicMock())
_stub_module("Screens")
_stub_module("Screens.ChoiceBox", ChoiceBox=mock.MagicMock())
_stub_module("Screens.MessageBox", MessageBox=mock.MagicMock(TYPE_INFO=1))
_stub_module("Screens.Screen", Screen=object)
_stub_module("Tools")
_stub_module("Tools.Directories", resolveFilename=lambda scope, path: path, SCOPE_PLUGINS="plugins")
_stub_module("enigma", eTimer=mock.MagicMock, evfd=None, eDBoxLCD=None)
_stub_module("Plugins")
_stub_module("Plugins.Plugin", PluginDescriptor=mock.MagicMock())


class PluginImportTest(unittest.TestCase):
    def test_plugin_module_imports_end_to_end(self):
        """This is exactly the import chain Enigma2 runs when it scans/opens
        the plugin - if it raises, the Extensions menu can't list or open it."""
        import OpenLigaDB.plugin as plugin_module

        self.assertTrue(hasattr(plugin_module, "Plugins"))
        self.assertTrue(hasattr(plugin_module, "main"))
        self.assertTrue(hasattr(plugin_module, "autostart"))

    def test_screens_module_gets_the_real_helpers(self):
        import OpenLigaDB.screens as screens_module

        self.assertTrue(callable(screens_module.build_table_row))
        self.assertEqual(
            screens_module.build_table_row({"Points": 3}, 1),
            "1. ? | P:3 | T:0:0 | W/D/L:0/0/0",
        )


if __name__ == "__main__":
    unittest.main()
