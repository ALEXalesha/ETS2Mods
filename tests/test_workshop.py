"""Checks for the Steam Workshop folders (tools/build_workshop.py). Needs the game and Pillow.

Rules from the SCS modding wiki (SCS Workshop Uploader validation):
upload root = versions.sii + version package only; manifest/icon/description
next to each other; icon JPG exactly 276x162, < 1 MB; description UTF-8 .txt,
< 1 MB; every .sii starts with "SiiNunit"; no unreferenced .txt/.jpg; no .scs.
Preview image 640x360 (SCS forum), Steam limit 1 MB.
"""

import os
import re
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "tests"))

import build_mods  # noqa: E402
from test_mods import HAVE_GAME, jpeg_size, values  # noqa: E402

CATEGORIES = {"truck", "trailer", "interior", "tuning_parts", "ai_traffic", "sound", "paint_job", "cargo_pack",
              "map", "ui", "weather_setup", "physics", "graphics", "models", "movers", "walkers", "prefabs", "other"}
MANIFEST_FIELDS = ["package_version", "display_name", "author", "category", "icon", "description_file",
                   "compatible_versions"]
# personal data that must never reach a public upload
FORBIDDEN = [b"c:\\drive", b"c:/drive", b"Projects", b"Projects", b"gmail", b"192.168.",
             b"alexey", "алексей".encode(), b"ALEXalesha", "ALEXalesha".encode(), b"aloysha", b"alesha",
             b"steam\\userdata", b"etcmods", b"gitea"]
ZERO_KEYS = ["fuel_price", "consumption_coef", "air_resistance", "differential_ratio", "grip_factor",
             "brake_torque_factor", "torque", "steering_sensitivity_multiplier_minimum"]

_DIRS = []


def rb(path):
    with open(path, "rb") as fh:
        return fh.read()


def rt(path):
    return rb(path).decode("utf-8")


def folders():
    if not _DIRS:
        import build_workshop
        out = tempfile.mkdtemp(prefix="ets2ws_test_")
        _DIRS.extend(build_workshop.build(out, verbose=False))
    return _DIRS


@unittest.skipUnless(HAVE_GAME, "game not installed")
class WorkshopTest(unittest.TestCase):
    def test_one_folder_per_mod(self):
        self.assertEqual(len(folders()), len(build_mods.load_order()))

    def test_layout(self):
        for base in folders():
            self.assertEqual(sorted(os.listdir(base)), ["preview.jpg", "steam_page.txt", "upload"])
            self.assertEqual(sorted(os.listdir(os.path.join(base, "upload"))), ["universal", "versions.sii"])
            v = rb(os.path.join(base, "upload", "versions.sii"))
            self.assertTrue(v.startswith(b"SiiNunit"))
            self.assertEqual(len(re.findall(rb"package_version_info\s*:\s*\.universal", v)), 1)
            self.assertIn(b'package_name: "universal"', v)

    def test_manifest_icon_description(self):
        for base in folders():
            uni = os.path.join(base, "upload", "universal")
            man = rt(os.path.join(uni, "manifest.sii"))
            self.assertTrue(man.startswith("SiiNunit"))
            for f in MANIFEST_FIELDS:
                self.assertRegex(man, r"(?m)^\s*%s(\[\])?\s*:" % f, "%s: %s missing" % (base, f))
            for c in re.findall(r'category\[\]\s*:\s*"([^"]+)"', man):
                self.assertIn(c, CATEGORIES)
            self.assertIn('compatible_versions[]: "1.61.*"', man)
            icon = rb(os.path.join(uni, "mod_icon.jpg"))
            self.assertEqual(jpeg_size(icon), (276, 162))
            self.assertLess(len(icon), 1024 * 1024)
            desc = rb(os.path.join(uni, "mod_description.txt"))
            self.assertLess(len(desc), 1024 * 1024)
            text = desc.decode("utf-8")
            self.assertIn("1.61", text)
            self.assertIn("-----", text)            # EN part, then RU part
            self.assertRegex(text, "[а-яА-Я]")
            prev = rb(os.path.join(base, "preview.jpg"))
            self.assertEqual(jpeg_size(prev), (640, 360))
            self.assertLess(len(prev), 1024 * 1024)
            page = rt(os.path.join(base, "steam_page.txt"))
            self.assertGreater(len(page.split("DESCRIPTION", 1)[1]), 50)

    def test_files_valid_for_uploader(self):
        for base in folders():
            uni = os.path.join(base, "upload", "universal")
            for dp, _dn, fn in os.walk(uni):
                for f in fn:
                    p = os.path.join(dp, f)
                    rel = os.path.relpath(p, uni).replace("\\", "/")
                    self.assertFalse(f.endswith(".scs"), rel)
                    if f.endswith((".txt", ".jpg")):
                        self.assertIn(rel, ("mod_icon.jpg", "mod_description.txt"), "unreferenced " + rel)
                    if f.endswith(".sii"):
                        self.assertTrue(rb(p).startswith(b"SiiNunit"), rel)
                    self.assertTrue(f.endswith((".sii", ".sui", ".txt", ".jpg")), rel)

    def test_no_zero_divisors(self):
        for base in folders():
            for dp, _dn, fn in os.walk(os.path.join(base, "upload")):
                for f in fn:
                    if f.endswith((".sii", ".sui")):
                        text = rt(os.path.join(dp, f))
                        for k in ZERO_KEYS:
                            for v in values(text, k):
                                self.assertGreater(float(v), 0.0, "%s %s %s" % (base, f, k))

    def test_no_personal_data(self):
        for base in folders():
            for dp, _dn, fn in os.walk(base):
                for f in fn:
                    p = os.path.join(dp, f)
                    blob = (os.path.relpath(p, base) + "\n").encode("utf-8").lower() + rb(p).lower()
                    for bad in FORBIDDEN:
                        self.assertNotIn(bad, blob, "%s contains %r" % (p, bad))


if __name__ == "__main__":
    unittest.main()
