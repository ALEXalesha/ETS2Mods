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
import re
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
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env)
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
        # impossible to miss (report 10.10: a dry run was taken for a write)
        self.assertIn("WRITTEN: 10,639,317 EUR in the file = 1,000,000,044 RUB on screen", out)
        self.assertIn("Now start the game and load the latest save", out)
        self.assertNotIn("NOTHING WRITTEN", out)

    def test_set_eur(self):
        self.run_tool("--save", "autosave", "--set-eur", "70000000", "--apply")
        self.assertEqual(self.money_in_file(), 70000000)

    def test_dry_run_writes_nothing(self):
        out = self.run_tool("--save", "autosave", "--set", "1000000000")
        self.assertEqual(self.money_in_file(), 50000000)
        self.assertIn("NOTHING WRITTEN", out)
        self.assertIn("add --apply", out)
        self.assertNotIn("WRITTEN:", out)
        self.assertFalse(os.path.exists(self.backups))

    def test_save_latest(self):
        older = os.path.join(self.prof, "save", "1")
        os.makedirs(older)
        with open(os.path.join(older, "game.sii"), "w", encoding="utf-8") as fh:
            fh.write(TEXT)
        os.utime(os.path.join(older, "game.sii"), (1600000000, 1600000000))
        out = self.run_tool("--save", "latest", "--set-eur", "777", "--apply")
        self.assertIn("latest save: autosave", out)
        self.assertEqual(self.money_in_file(), 777)
        kind, _raw, money, _w = save_money.read_money(os.path.join(older, "game.sii"))
        self.assertEqual(money, 50000000)

    def test_currency_override(self):
        out = self.run_tool("--save", "autosave", "--currency", "EUR", "--set", "123456", "--apply")
        self.assertEqual(self.money_in_file(), 123456)
        self.assertIn("123,456 EUR", out)


INFO = ("SiiNunit\n{\nsave_container : _nameless.1 {\n name: \"\"\n file_time: 1700000000\n"
        " info_players_experience: 1\n info_money_account: %d\n info_explored_ratio: 0.1\n}\n}\n")


class SaveFolderTest(unittest.TestCase):
    """Independent review of 16.10.2026, checked on a copy of a real 1.61 profile.

    1. The game names its saves autosave, autosave_job, autosave_job_1..9, autosave_drive,
       autosave_drive_1..9. --restore --save autosave looked for backups "autosave_*" and took
       the last one by name - "autosave_job_3_<time>" sorts after "autosave_<time>", so the
       backup of ANOTHER save was copied into autosave.
    2. The money is also in info.sii of the save (info_money_account, what the Load screen
       shows). In every real save it equals the bank's money_account. The tool wrote only
       game.sii, so the Load screen kept showing the old amount - it looked as if nothing had
       been written.
    3. Two writes of the same save within one second: the backup folder name (to the second)
       already existed and the second write failed.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ets2fold_")
        self.prof = os.path.join(self.tmp, "414C6578")
        self.backups = os.path.join(self.tmp, "backups")
        for name, money in (("autosave", 50000000), ("autosave_job_3", 3333), ("autosave_drive", 4444)):
            d = os.path.join(self.prof, "save", name)
            os.makedirs(d)
            with open(os.path.join(d, "game.sii"), "w", encoding="utf-8") as fh:
                fh.write(TEXT.replace("50000000", str(money)))
            with open(os.path.join(d, "info.sii"), "w", encoding="utf-8") as fh:
                fh.write(INFO % money)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def money(self, save):
        return save_money.read_money(os.path.join(self.prof, "save", save, "game.sii"))[2]

    def info_money(self, save):
        with open(os.path.join(self.prof, "save", save, "info.sii"), encoding="utf-8") as fh:
            return int(re.search(r"info_money_account:\s*(-?\d+)", fh.read()).group(1))

    def cli(self, *args):
        cmd = [sys.executable, os.path.join(ROOT, "tools", "save_money.py"),
               "--profile-dir", self.prof, "--backup-dir", self.backups] + list(args)
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r.stdout

    def test_restore_takes_the_backup_of_the_same_save(self):
        self.cli("--save", "autosave", "--set-eur", "111", "--apply")
        # later backups of saves whose names start with "autosave_"
        for other in ("autosave_job_3", "autosave_drive"):
            src = os.path.join(self.prof, "save", other)
            shutil.copytree(src, os.path.join(self.backups, "414C6578", other + "_20991231-235959"))
        out = self.cli("--save", "autosave", "--restore")
        self.assertEqual(self.money("autosave"), 50000000, out)      # its own money, not 3333/4444
        self.assertIn(os.sep + "autosave_2", out)

    def test_info_sii_follows_the_money(self):
        save_money.write_money(self.prof, "autosave", 106393165, self.backups)
        self.assertEqual(self.money("autosave"), 106393165)
        self.assertEqual(self.info_money("autosave"), 106393165)
        self.assertEqual(self.info_money("autosave_job_3"), 3333)    # other saves untouched

    def test_save_without_info_sii(self):
        os.remove(os.path.join(self.prof, "save", "autosave", "info.sii"))
        save_money.write_money(self.prof, "autosave", 777, self.backups)
        self.assertEqual(self.money("autosave"), 777)

    def test_two_writes_in_one_second(self):
        a = save_money.write_money(self.prof, "autosave", 1, self.backups)[2]
        b = save_money.write_money(self.prof, "autosave", 2, self.backups)[2]
        self.assertNotEqual(a, b)
        self.assertEqual(self.money("autosave"), 2)
        # both backups are real copies of what was there before each write
        self.assertEqual(save_money.read_money(os.path.join(a, "game.sii"))[2], 50000000)
        self.assertEqual(save_money.read_money(os.path.join(b, "game.sii"))[2], 1)


if __name__ == "__main__":
    unittest.main()
