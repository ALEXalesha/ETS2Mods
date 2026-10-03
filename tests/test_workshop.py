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
MANIFEST_FIELDS = ["package_version", "author", "category", "icon", "description_file"]
# The SCS Workshop Uploader rejects these in Workshop packages (ERROR 00010 for compatible_versions,
# WARN 00002 for display_name): versions come from versions.sii and the name from the Steam page.
WORKSHOP_FORBIDDEN = ["compatible_versions", "display_name"]
# personal data that must never reach a public upload
def private_strings():
    """Personal strings that must never reach a public upload.

    None of them is written in this file (it is public itself): they come from the
    local git config (user.email, publish.privateName, publish.privateExtra), the
    Gitea remote, the folder this repository lives in and the Steam user/profile
    folders on this PC. On a machine without them only the generic checks remain.
    """
    import glob
    import subprocess

    def git(*args):
        try:
            return subprocess.run(["git", "-C", ROOT] + list(args), capture_output=True,
                                  text=True, encoding="utf-8").stdout.strip()
        except OSError:
            return ""

    out = {b"gmail.com", b"steam\\userdata", b"steam/userdata"}
    email = git("config", "user.email")
    if email:
        out.add(email.lower().encode())
    for word in (git("config", "publish.privateName") + " " +
                 git("config", "publish.privateExtra").replace("|", " ")).split():
        if len(word) >= 4:
            out.add(word.lower().encode("utf-8"))
    origin = git("remote", "get-url", "origin")
    m = re.match(r"^[a-z]+://([^/:]+)(?::\d+)?/([^/]+)/([^/.]+)", origin)
    if m:
        out.update(x.lower().encode() for x in m.groups())
    parent = os.path.dirname(ROOT)
    for variant in (parent, parent.replace("\\", "/")):
        out.add(variant.lower().encode())
    for d in glob.glob(r"C:\Program Files (x86)\Steam\userdata\*"):
        out.add(os.path.basename(d).lower().encode())
        for prof in glob.glob(os.path.join(d, "227300", "remote", "profiles", "*")):
            out.add(os.path.basename(prof).lower().encode())
    return sorted(x for x in out if len(x) >= 4)


FORBIDDEN = private_strings()
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
            for f in WORKSHOP_FORBIDDEN:
                self.assertNotRegex(man, r"(?m)^\s*%s(\[\])?\s*:" % f, "%s: %s must not be in a Workshop manifest" % (base, f))
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

    def test_release_assets(self):
        import zipfile
        import build_workshop
        out = tempfile.mkdtemp(prefix="ets2rel_test_")
        assets = build_workshop.release_assets(folders(), out)
        scs = [a for a in assets if a.endswith(".scs")]
        self.assertEqual(len(scs), len(folders()))
        for a in scs:
            self.assertTrue(os.path.basename(a).startswith("OpenRoad_"))
            with zipfile.ZipFile(a) as z:
                names = z.namelist()
                self.assertIn("manifest.sii", names)
                man = z.read("manifest.sii").decode("utf-8")
                # installed locally, so the Mod Manager fields are back
                self.assertRegex(man, r'display_name: "OpenRoad: [^"]+"')
                self.assertIn('compatible_versions[]: "1.61.*"', man)
                self.assertTrue(man.startswith("SiiNunit") and man.rstrip().endswith("}"))
                self.assertFalse([n for n in names if n.endswith("/") or "\\" in n])
                for n in names:
                    for bad in FORBIDDEN:
                        self.assertNotIn(bad, z.read(n).lower(), "%s:%s" % (a, n))
        self.assertTrue(any(a.endswith("OpenRoad_Workshop_Folders.zip") for a in assets))

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
