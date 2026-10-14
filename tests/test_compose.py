#!/usr/bin/env python3
"""Check the K68 tilde key and actual libxkbcommon UTF-8 composition.

This tests dead_tilde semantics without requiring a display server or keyboard.
"""

import ctypes
import ctypes.util
from pathlib import Path
import re
import unittest

LAYOUT = Path(__file__).resolve().parent.parent / 'layouts' / 'frk68'


class TildeComposeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        library = ctypes.util.find_library('xkbcommon')
        if not library:
            raise unittest.SkipTest('libxkbcommon not installed')
        cls.lib = ctypes.CDLL(library)
        cls.lib.xkb_context_new.argtypes = [ctypes.c_int]
        cls.lib.xkb_context_new.restype = ctypes.c_void_p
        cls.lib.xkb_compose_table_new_from_locale.argtypes = [
            ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int
        ]
        cls.lib.xkb_compose_table_new_from_locale.restype = ctypes.c_void_p
        cls.lib.xkb_compose_state_new.argtypes = [ctypes.c_void_p, ctypes.c_int]
        cls.lib.xkb_compose_state_new.restype = ctypes.c_void_p
        cls.lib.xkb_keysym_from_name.argtypes = [ctypes.c_char_p, ctypes.c_int]
        cls.lib.xkb_keysym_from_name.restype = ctypes.c_uint32
        cls.lib.xkb_compose_state_feed.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        cls.lib.xkb_compose_state_feed.restype = ctypes.c_int
        cls.lib.xkb_compose_state_get_status.argtypes = [ctypes.c_void_p]
        cls.lib.xkb_compose_state_get_status.restype = ctypes.c_int
        cls.lib.xkb_compose_state_get_utf8.argtypes = [
            ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t
        ]
        cls.lib.xkb_compose_state_get_utf8.restype = ctypes.c_int
        cls.lib.xkb_compose_state_unref.argtypes = [ctypes.c_void_p]
        cls.lib.xkb_compose_table_unref.argtypes = [ctypes.c_void_p]
        cls.lib.xkb_context_unref.argtypes = [ctypes.c_void_p]

        cls.ctx = cls.lib.xkb_context_new(0)
        if not cls.ctx:
            raise unittest.SkipTest('Could not initialize libxkbcommon')
        cls.table = cls.lib.xkb_compose_table_new_from_locale(cls.ctx, b'en_US.UTF-8', 0)
        if not cls.table:
            cls.lib.xkb_context_unref(cls.ctx)
            raise unittest.SkipTest('UTF-8 compose table unavailable')

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'table') and cls.table:
            cls.lib.xkb_compose_table_unref(cls.table)
        if hasattr(cls, 'ctx') and cls.ctx and getattr(cls, 'table', None):
            cls.lib.xkb_context_unref(cls.ctx)

    def test_right_alt_n_is_a_dead_tilde(self):
        layout = LAYOUT.read_text(encoding='utf-8')
        self.assertIn('include "level3(ralt_switch)"', layout)
        self.assertRegex(layout, re.compile(
            r'key\s*<AB06>\s*\{\s*\[\s*n\s*,\s*N\s*,\s*dead_tilde\s*,\s*dead_tilde\s*\]'
        ))

    def test_tilde_compose_sequences(self):
        for next_key, expected in [('n', 'ñ'), ('N', 'Ñ'), ('space', '~'), ('a', 'ã'), ('o', 'õ')]:
            with self.subTest(next_key=next_key):
                state = self.lib.xkb_compose_state_new(self.table, 0)
                self.assertTrue(state)
                try:
                    for key in ('dead_tilde', next_key):
                        keysym = self.lib.xkb_keysym_from_name(key.encode(), 0)
                        self.assertNotEqual(keysym, 0)
                        self.assertEqual(self.lib.xkb_compose_state_feed(state, keysym), 1)
                    self.assertEqual(self.lib.xkb_compose_state_get_status(state), 2)
                    output = ctypes.create_string_buffer(32)
                    self.lib.xkb_compose_state_get_utf8(state, output, len(output))
                    self.assertEqual(output.value.decode('utf-8'), expected)
                finally:
                    self.lib.xkb_compose_state_unref(state)


if __name__ == '__main__':
    unittest.main()
