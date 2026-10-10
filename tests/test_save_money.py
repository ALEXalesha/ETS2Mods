"""save_money.py and the game's display currency (report of 10.10.2026).

The save keeps money in EUR. The game shows it in the currency chosen in the
profile (config.cfg of the profile: uset g_currency "N", an index into the
currency list of def/economy_data.sii). With RUB (index 9, ratio 93.991) the
50,000,000 written by --set showed as 4,699,550,000 RUB, which looked like
"the tool always gives 4.7 billion".

Since 1.2.0 --set takes the amount as the game shows it and the tool prints
both: EUR in the file and the amount on screen. --set-eur writes EUR as is.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import save_money  # noqa: E402

TEXT = ("SiiNunit\n{\neconomy : _nameless.1 {\n bank: _nameless.2\n experience_points: 44339\n}\n\n"
        "bank : _nameless.2 {\n money_account: 50000000\n coinsurance_fixed: 0\n}\n}\n")

ECONOMY = """SiiNunit
{
economy_data : economy.data.storage
{
	currency_code[]: "EUR"
	currency_ratio[]: 1
	currency_sign1[]: ""
	currency_sign2[]: "€"
	currency_sign3[]: ""

	currency_code[]: "CHF"
	currency_ratio[]: 0.9160
	currency_sign1[]: ""
	currency_sign2[]: ""
	currency_sign3[]: " CHF"

	currency_code[]: "RUB"
	currency_ratio[]: 93.991
	currency_sign1[]: ""
	currency_sign2[]: "₽"
	currency_sign3[]: ""
}
}
"""


class CurrencyTest(unittest.TestCase):
    def test_parse_currency_list(self):
        cur = save_money.parse_currencies(ECONOMY)
        self.assertEqual([c["code"] for c in cur], ["EUR", "CHF", "RUB"])
        self.assertAlmostEqual(cur[2]["ratio"], 93.991)
        self.assertEqual(cur[2]["sign2"], "₽")

    def test_builtin_table_matches_1_61(self):
        cur = save_money.BUILTIN_CURRENCIES
        self.assertEqual(cur[0]["code"], "EUR")
        self.assertEqual(cur[9]["code"], "RUB")          # g_currency "9" in the report's profile
        self.assertAlmostEqual(cur[9]["ratio"], 93.991)

    def test_report_numbers(self):
        rub = save_money.BUILTIN_CURRENCIES[9]
        # 50,000,000 EUR in the file is the "fixed 4.7 billion" on screen
        self.assertEqual(save_money.to_screen(50000000, rub), 4699550000)
        self.assertEqual(save_money.from_screen(4699550000, rub), 50000000)
        self.assertEqual(save_money.from_screen(50000000, rub), 531966)
        eur = save_money.BUILTIN_CURRENCIES[0]
        self.assertEqual(save_money.from_screen(50000000, eur), 50000000)

    def test_profile_currency_index(self):
        d = tempfile.mkdtemp(prefix="ets2cur_")
        try:
            self.assertEqual(save_money.profile_currency_index(d), 0)      # no config.cfg: EUR
            with open(os.path.join(d, "config.cfg"), "w", encoding="utf-8") as fh:
                fh.write('uset g_lang "ru_ru"\nuset g_currency "9"\n')
            self.assertEqual(save_money.profile_currency_index(d), 9)
        finally:
            shutil.rmtree(d)


class CommandLineTest(unittest.TestCase):
    """End to end on a throw-away profile folder: --set in the screen currency, read back."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ets2money_")
        self.prof = os.path.join(self.tmp, "414C6578")
        os.makedirs(os.path.join(self.prof, "save", "autosave"))
        with open(os.path.join(self.prof, "save", "autosave", "game.sii"), "w", encoding="utf-8") as fh:
            fh.write(TEXT)
        with open(os.path.join(self.prof, "config.cfg"), "w", encoding="utf-8") as fh:
            fh.write('uset g_currency "9"\n')
        self.backups = os.path.join(self.tmp, "backups")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_tool(self, *args):
        cmd = [sys.executable, os.path.join(ROOT, "tools", "save_money.py"),
               "--profile-dir", self.prof, "--backup-dir", self.backups] + list(args)
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r.stdout

    def money_in_file(self):
        kind, _raw, money, _w = save_money.read_money(os.path.join(self.prof, "save", "autosave", "game.sii"))
        return money

    def test_show_both_currencies(self):
        out = self.run_tool("--save", "autosave")
        self.assertIn("50,000,000 EUR", out)
        self.assertIn("4,699,550,000 RUB", out)

    def test_set_in_screen_currency(self):
        out = self.run_tool("--save", "autosave", "--set", "1000000000", "--apply")
        self.assertEqual(self.money_in_file(), 10639317)          # 1e9 / 93.991 = 10,639,316.5
        self.assertIn("1,000,000,000 RUB", out)
        self.assertIn("10,639,317 EUR", out)
        self.assertTrue(os.listdir(os.path.join(self.backups, "414C6578")))

    def test_set_eur(self):
        self.run_tool("--save", "autosave", "--set-eur", "70000000", "--apply")
        self.assertEqual(self.money_in_file(), 70000000)

    def test_dry_run_writes_nothing(self):
        out = self.run_tool("--save", "autosave", "--set", "1000000000")
        self.assertEqual(self.money_in_file(), 50000000)
        self.assertIn("dry run", out)

    def test_currency_override(self):
        out = self.run_tool("--save", "autosave", "--currency", "EUR", "--set", "123456", "--apply")
        self.assertEqual(self.money_in_file(), 123456)
        self.assertIn("123,456 EUR", out)


if __name__ == "__main__":
    unittest.main()
