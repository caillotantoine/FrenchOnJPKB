#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('registry', REPO / 'scripts/xkb_registry.py')
registry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(registry)


class RegistryTests(unittest.TestCase):
    SAMPLE = '''<?xml version="1.0"?>
<!DOCTYPE xkbConfigRegistry SYSTEM "xkb.dtd">
<xkbConfigRegistry><layoutList><layout><configItem><name>us</name></configItem></layout>
</layoutList></xkbConfigRegistry>'''

    def test_patch_round_trip(self):
        changed = registry.patch_registry(self.SAMPLE, True)
        self.assertEqual(changed.count('<name>frk68</name>'), 1)
        self.assertEqual(registry.patch_registry(changed, True), changed)
        restored = registry.patch_registry(changed, False)
        self.assertNotIn('frk68', restored)
        ET.fromstring(restored)

    def test_reject_conflicts(self):
        with self.assertRaises(ValueError):
            registry.patch_registry(self.SAMPLE.replace('us', 'frk68'), True)
        with self.assertRaises(ValueError):
            registry.patch_registry(self.SAMPLE + registry.BEGIN, True)

    def test_install_twice_uninstall(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'symbols').mkdir()
            (root / 'rules').mkdir()
            xml = root / 'rules/evdev.xml'
            xml.write_text(self.SAMPLE)
            call = [sys.executable, str(REPO / 'scripts/xkb_registry.py')]
            for action in ['install', 'install', 'uninstall']:
                subprocess.run(call + [action, '--xkb-root', str(root)], check=True,
                               stdout=subprocess.DEVNULL)
            self.assertFalse((root / 'symbols/frk68').exists())
            self.assertNotIn('frk68', xml.read_text())
            self.assertTrue(list((root / '.frenchon-jpkb-backups').glob('*')))


if __name__ == '__main__':
    unittest.main()
