"""Checks for the built mods and the tools. Needs the installed game (reads def.scs).

Run:  .venv\\Scripts\\python -m unittest discover -s tests -v
"""

import glob
import os
import re
import struct
import sys
import tempfile
import unittest
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import build_mods  # noqa: E402
from cityhash103 import cityhash64  # noqa: E402

GAME = build_mods.DEFAULT_GAME
HAVE_GAME = os.path.isfile(os.path.join(GAME, "def.scs"))
STEAM_SAVES = glob.glob(r"C:\Program Files (x86)\Steam\userdata\*\227300\remote\profiles\*\save\*\game.sii")

_BUILT = {}


def built():
    if not _BUILT:
        tmp = tempfile.mkdtemp(prefix="ets2mods_test_")
        _BUILT.update(build_mods.build_all(GAME, tmp, verbose=False))
    return _BUILT


def jpeg_size(data):
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            raise ValueError("bad JPEG marker")
        marker = data[i + 1]
        length = struct.unpack(">H", data[i + 2:i + 4])[0]
        if marker in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        i += 2 + length
    raise ValueError("no SOF marker")


def values(text, key):
    return [m.group(1) for m in re.finditer(r"^\s*%s\s*:\s*([^#\s]+)" % re.escape(key), text, re.M)]


class CityHashTest(unittest.TestCase):
    def test_known_paths(self):
        # values taken from version.scs / def.scs entry tables
        self.assertEqual(cityhash64(""), 11160318154034397263)
        self.assertEqual(cityhash64("version.sii"), 203568326075060621)


@unittest.skipUnless(HAVE_GAME, "game not installed")
class BuiltModsTest(unittest.TestCase):
    def test_no_fuel_price_is_zero(self):
        """Regression: fuel_price 0 made the gas station panel show 'Litres: -nan(ind)' (0/0)."""
        seen = 0
        for name, r in built().items():
            for path, data in r["files"].items():
                if not path.endswith((".sii", ".sui")):
                    continue
                for v in values(data.decode("utf-8"), "fuel_price"):
                    seen += 1
                    self.assertGreater(float(v), 0.0, "%s %s fuel_price=%s" % (name, path, v))
        self.assertGreaterEqual(seen, 36)

    def test_no_consumption_coef_is_zero(self):
        """Same divide-by-zero risk for the dashboard fuel range/average."""
        n = 0
        for name, r in built().items():
            for path, data in r["files"].items():
                if path.endswith(".sii"):
                    for v in values(data.decode("utf-8"), "consumption_coef"):
                        n += 1
                        self.assertGreater(float(v), 0.0, "%s %s" % (name, path))
        self.assertGreater(n, 0)

    def test_packages(self):
        for name, r in built().items():
            with zipfile.ZipFile(r["file"]) as z:
                names = z.namelist()
                self.assertFalse([n for n in names if n.endswith("/")], "%s has directory entries" % name)
                man = z.read("manifest.sii").decode("utf-8")
                self.assertIn('compatible_versions[]: "%s"' % r["version_glob"], man)
                self.assertIn('display_name: "%s"' % r["spec"]["display_name"], man)
                self.assertEqual(jpeg_size(z.read("mod_icon.jpg")), (276, 162))
                z.read("mod_description.txt").decode("utf-8")
                self.assertTrue(any(n.startswith("def/") for n in names))

    def test_every_patch_lands(self):
        """Every own log entry's new value is present in the built file."""
        for name, r in built().items():
            pkg = r["spec"]["package"]
            for path, key, old, new, owner in r["log"]:
                if owner != pkg:
                    continue
                text = r["files"][path].decode("utf-8")
                self.assertIn(new, values(text, key), "%s %s %s" % (name, path, key))

    def test_cascade_shared_files(self):
        """A shared file in a higher mod carries the changes of every lower mod that touches it."""
        order = build_mods.load_order()
        replaces = build_mods.load_replaces()
        res = built()
        for i, upper in enumerate(order):
            for lower in order[i + 1:]:
                if lower in replaces.get(upper, []):
                    continue
                shared = set(res[upper]["files"]) & set(res[lower]["files"])
                shared = {p for p in shared if p.startswith("def/")}
                lpkg = res[lower]["spec"]["package"]
                for p in shared:
                    self.assertIn("[mod %s" % lpkg, res[upper]["files"][p].decode("utf-8"),
                                  "%s:%s misses changes of %s" % (upper, p, lower))

    def test_all_engines_covered(self):
        defs = build_mods.LayeredFs(GAME)
        engines = build_mods.expand_path(defs, "def/vehicle/truck/*/engine/*.sii", "accessory_engine_data")
        units = sum(len(re.findall(r"^\s*accessory_engine_data\s*:", defs.read(p).decode("utf-8"), re.M))
                    for p in engines)
        sp = built()["super_power"]["files"]
        got = 0
        for p in engines:
            text = sp[p].decode("utf-8")
            got += len(values(text, "consumption_coef"))
            orig = values(defs.read(p).decode("utf-8"), "torque")
            new = values(text, "torque")
            self.assertEqual(len(orig), len(new))
            for o, n in zip(orig, new):
                self.assertAlmostEqual(float(n), float(o) * 3, delta=1.0)
        self.assertEqual(got, units)
        self.assertGreaterEqual(units, 200)

    def test_no_zero_divisors(self):
        """Values the game divides by (or multiplies into a divisor) must never be 0 or negative."""
        keys = ["fuel_price", "consumption_coef", "air_resistance", "differential_ratio", "grip_factor",
                "brake_torque_factor", "torque", "steering_sensitivity_multiplier_minimum"]
        for name, r in built().items():
            for path, data in r["files"].items():
                if not path.endswith((".sii", ".sui")):
                    continue
                text = data.decode("utf-8")
                for k in keys:
                    for v in values(text, k):
                        self.assertGreater(float(v), 0.0, "%s %s %s=%s" % (name, path, k, v))

    def test_hyper_power(self):
        """Hyper Power replaces Super Power: torque x12 of stock (not x36), final drive x0.35."""
        defs = build_mods.LayeredFs(GAME)
        hp = built()["hyper_power"]["files"]
        engines = build_mods.expand_path(defs, "def/vehicle/truck/*/engine/*.sii", "accessory_engine_data")
        trans = build_mods.expand_path(defs, "def/vehicle/truck/*/transmission/*.sii", "accessory_transmission_data")
        self.assertEqual(len(trans), len([p for p in hp if "/transmission/" in p]))
        for p in engines:
            for o, n in zip(values(defs.read(p).decode("utf-8"), "torque"), values(hp[p].decode("utf-8"), "torque")):
                self.assertAlmostEqual(float(n), float(o) * 12, delta=1.0, msg=p)
            self.assertNotIn("alexey_super_power", hp[p].decode("utf-8"))
            self.assertIn("consumption_coef", hp[p].decode("utf-8"))
        for p in trans:
            o = values(defs.read(p).decode("utf-8"), "differential_ratio")
            n = values(hp[p].decode("utf-8"), "differential_ratio")
            self.assertEqual(len(o), len(n))
            for a, b in zip(o, n):
                self.assertAlmostEqual(float(b), float(a) * 0.35, delta=0.001, msg=p)
        phys = hp["def/vehicle/physics.sii"].decode("utf-8")
        self.assertEqual(values(phys, "air_resistance"), ["0.1"])
        self.assertEqual(values(phys, "sway_bar_stiffness_factor"), ["3.0"])   # from No Rollover
        tires = [p for p in hp if "/f_tire/" in p or "/r_tire/" in p]
        self.assertEqual(len(tires), 31)

    def test_values_that_matter(self):
        res = built()
        econ = res["money"]["files"]["def/economy_data.sii"].decode("utf-8")
        self.assertEqual(values(econ, "revenue_per_km_base"), ["150"])
        self.assertEqual(values(econ, "maximum_driving_time"), ["10000000"])
        self.assertEqual(values(econ, "tow_price_base"), ["0"])
        dmg = res["no_damage"]["files"]["def/damage_data.sii"].decode("utf-8")
        self.assertEqual(values(dmg, "truck_damage_coef"), ["0.0"])
        phys = res["super_power"]["files"]["def/vehicle/physics.sii"].decode("utf-8")
        self.assertEqual(values(phys, "sway_bar_stiffness_factor"), ["3.0"])
        self.assertEqual(values(phys, "air_resistance"), ["1.5"])


class SaveToolsTest(unittest.TestCase):
    TEXT = ("SiiNunit\n{\neconomy : _nameless.1 {\n bank: _nameless.2\n experience_points: 44339\n adr: 63\n"
            " long_dist: 6\n heavy: 2\n fragile: 0\n urgent: 0\n mechanical: 6\n}\n\n"
            "bank : _nameless.2 {\n money_account: 73117\n coinsurance_fixed: 0\n}\n}\n")

    def test_profile_patch_text(self):
        import save_profile
        steps = [200, 500, 700, 900, 1000, 1100, 1300, 1600, 1700, 2100, 2300, 2600, 2700, 2900, 3000,
                 3100, 3400, 3700, 4000, 4300, 4600, 4700, 4900, 5200, 5700, 5900, 6000, 6200, 6600, 6800]
        self.assertEqual(save_profile.level_for_xp(44339, steps), 20)   # matches 20 spent skill points
        kind, raw, vals, where = save_profile.read_fields_bytes(self.TEXT.encode())
        self.assertEqual(kind, "text")
        out = save_profile.patch(kind, raw, where, {"experience_points": 575700, "fragile": 6})
        _k, _r, v2, _w = save_profile.read_fields_bytes(out)
        self.assertEqual(v2["experience_points"], 575700)
        self.assertEqual(v2["fragile"], 6)
        self.assertEqual(v2["adr"], 63)
        self.assertIn(b"money_account: 73117", out)

    def test_money_regex_text(self):
        import save_money
        m = save_money.TEXT_BANK.search(self.TEXT)
        self.assertEqual(m.group(2), "73117")

    @unittest.skipUnless(STEAM_SAVES, "no saves on this PC")
    def test_real_saves_parse(self):
        import save_money
        for g in STEAM_SAVES[:5]:
            kind, _raw, money, _w = save_money.read_money(g)
            self.assertIn(kind, ("binary", "text"))
            self.assertIsInstance(money, int)


if __name__ == "__main__":
    unittest.main()
