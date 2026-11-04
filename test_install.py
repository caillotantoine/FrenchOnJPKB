#!/usr/bin/env python3
"""Non-privileged regression tests for the custom variant and installer logic."""
import importlib.util
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("layout_install", ROOT / "install.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class LayoutTests(unittest.TestCase):
    def test_short_spacebar_and_altgr(self):
        source = mod.source_variant()
        for key in ("MUHE", "HENK"):
            self.assertRegex(source, rf'key <{key}>\s*\{{\s*\[\s*Space\s*\]')
        self.assertRegex(source, r'key <KANA>\s*\{\s*\[\s*Alt_R')
        self.assertIn('include "level3(ralt_switch)"', source)

    def test_rules_insertion_is_idempotent(self):
        xml = """<xkbConfigRegistry><layoutList><layout><configItem><name>fr</name></configItem><variantList><variant><configItem><name>oss</name></configItem></variant></variantList></layout></layoutList></xkbConfigRegistry>"""
        added = mod.modify_rules(xml, True)
        self.assertEqual(added, mod.modify_rules(added, True))
        self.assertIn("<name>frjp</name>", added)
        self.assertNotIn("<name>frjp</name>", mod.modify_rules(added, False))

    def test_symbols_insertion_is_idempotent(self):
        base = 'xkb_symbols "basic" { };\n'
        added = mod.modify_symbols(base, True)
        self.assertEqual(added, mod.modify_symbols(added, True))
        self.assertIn('xkb_symbols "frjp"', added)
        self.assertNotIn('xkb_symbols "frjp"', mod.modify_symbols(added, False))

    def test_unmanaged_layout_not_overwritten(self):
        with self.assertRaises(RuntimeError):
            mod.modify_symbols('xkb_symbols "frjp" { };', True)

if __name__ == "__main__":
    unittest.main()
