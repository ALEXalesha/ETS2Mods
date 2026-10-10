"""money.bat / "Деньги ETS2.bat" and tools/money_menu.py (report of 10.10.2026).

The report: "the utility doesn't work at all". The tool itself worked; it was run
without --apply (a dry run writes nothing) or with an old amount. Since then a
double-click file asks for the amount in the game's currency, checks that the game
is closed, writes, and prints a big "ЗАПИСАНО". These tests drive the same steps
on a throw-away profile folder: the Python part in-process with scripted answers,
and the .bat files end to end through cmd.exe.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import money_menu  # noqa: E402
import save_money  # noqa: E402

TEXT = ("SiiNunit\n{\neconomy : _nameless.1 {\n bank: _nameless.2\n experience_points: 44339\n}\n\n"
        "bank : _nameless.2 {\n money_account: %d\n coinsurance_fixed: 0\n}\n}\n")
RUB = save_money.BUILTIN_CURRENCIES[9]


def make_profile(root, hexname="414C6578", money=50000000, currency=9, saves=("autosave",)):
    prof = os.path.join(root, hexname)
    for i, s in enumerate(saves):
        d = os.path.join(prof, "save", s)
        os.makedirs(d)
        with open(os.path.join(d, "game.sii"), "w", encoding="utf-8") as fh:
            fh.write(TEXT % money)
        t = 1700000000 + 1000 * (len(saves) - i)       # the first one is the newest
        os.utime(os.path.join(d, "game.sii"), (t, t))
    with open(os.path.join(prof, "config.cfg"), "w", encoding="utf-8") as fh:
        fh.write('uset g_currency "%d"\n' % currency)
    return prof


def money_in(prof, save="autosave"):
    return save_money.read_money(os.path.join(prof, "save", save, "game.sii"))[2]


class ParseAmountTest(unittest.TestCase):
    def test_accepted(self):
        cases = {
            "10000000000": 10 ** 10, "10 000 000 000": 10 ** 10, " 10 000 000 000 ": 10 ** 10,
            "10.000.000.000": 10 ** 10, "10,000,000,000": 10 ** 10, "10_000_000_000": 10 ** 10,
            "10 млрд": 10 ** 10, "10млрд": 10 ** 10, "10 миллиардов": 10 ** 10, "1,5 млрд": 1500000000,
            "2.25 млн": 2250000, "500 тыс": 500000, "500 тыс. руб.": 500000, "10 млрд ₽": 10 ** 10,
            "10000 руб": 10000, "0": 0,
        }
        for text, want in cases.items():
            self.assertEqual(money_menu.parse_amount(text), want, text)

    def test_rejected(self):
        for text in ("", "   ", "abc", "-5", "1.5", "10 000,5", "млрд", "1e9", "50000000..."):
            self.assertIsNone(money_menu.parse_amount(text), text)

    def test_russian_number_format(self):
        self.assertEqual(money_menu.ru_num(9999999972), "9 999 999 972")


class MenuTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ets2menu_")
        self.backups = os.path.join(self.tmp, "backups")
        self.lines = []

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_menu(self, answers, profs, running=None):
        it = iter(answers)

        def inp(prompt=""):
            self.lines.append(prompt)
            return next(it)
        args = []
        for p in profs:
            args += ["--profile-dir", p]
        args += ["--backup-dir", self.backups]
        rc = money_menu.run(args, inp=inp, out=lambda *a: self.lines.append(" ".join(map(str, a))),
                            is_running=running or (lambda: False))
        return rc, "\n".join(self.lines)

    def test_writes_amount_in_roubles(self):
        prof = make_profile(self.tmp)
        rc, out = self.run_menu(["10 млрд", ""], [prof])
        self.assertEqual(rc, 0)
        self.assertEqual(money_in(prof), 106393165)                 # 1e10 / 93.991
        self.assertIn("Сейчас в игре: 4 699 550 000 руб.", out)       # the report's 50,000,000 EUR
        self.assertIn("ЗАПИСАНО: 9 999 999 972 руб.", out)
        self.assertIn("106 393 165 € в файле", out)
        self.assertIn("загрузите последнее сохранение", out)
        self.assertTrue(os.listdir(os.path.join(self.backups, "414C6578")))

    def test_empty_amount_writes_nothing(self):
        prof = make_profile(self.tmp)
        rc, out = self.run_menu([""], [prof])
        self.assertEqual(rc, 0)
        self.assertEqual(money_in(prof), 50000000)
        self.assertIn("Ничего не записано", out)
        self.assertFalse(os.path.exists(self.backups))

    def test_no_at_confirmation_writes_nothing(self):
        prof = make_profile(self.tmp)
        rc, out = self.run_menu(["1000000", "нет"], [prof])
        self.assertEqual(money_in(prof), 50000000)
        self.assertIn("Ничего не записано", out)

    def test_bad_number_is_asked_again(self):
        prof = make_profile(self.tmp)
        rc, out = self.run_menu(["50000000...", "1 000 000 000", "д"], [prof])
        self.assertIn("Не понял число", out)
        self.assertEqual(money_in(prof), save_money.from_screen(10 ** 9, RUB))

    def test_too_much_is_refused(self):
        prof = make_profile(self.tmp)
        rc, out = self.run_menu(["1000 млрд", "100 млрд", ""], [prof])
        self.assertIn("Слишком много", out)
        self.assertEqual(money_in(prof), save_money.from_screen(10 ** 11, RUB))
        self.assertLessEqual(money_in(prof), money_menu.MAX_EUR)

    def test_waits_until_the_game_is_closed(self):
        prof = make_profile(self.tmp)
        state = iter([True, True, False])
        rc, out = self.run_menu(["10 млрд", "", "", ""], [prof], running=lambda: next(state))
        self.assertIn("Игра запущена", out)
        self.assertEqual(money_in(prof), 106393165)

    def test_game_running_cancel(self):
        prof = make_profile(self.tmp)
        rc, out = self.run_menu(["10 млрд", "", "нет"], [prof], running=lambda: True)
        self.assertEqual(money_in(prof), 50000000)
        self.assertIn("Ничего не записано", out)

    def test_newest_save_and_profile_choice(self):
        a = make_profile(self.tmp, "41", saves=("autosave", "autosave_job"))
        b = make_profile(self.tmp, "42", currency=0)
        os.utime(os.path.join(b, "save", "autosave", "game.sii"), (1600000000, 1600000000))   # older
        rc, out = self.run_menu(["2", "123456", ""], [b, a])
        self.assertEqual(money_in(b), 123456)                       # EUR profile: 1:1
        self.assertEqual(money_in(a), 50000000)
        self.assertIn("1) A - сохранение autosave", out)           # newest profile first
        self.lines.clear()
        # the profile just written is now the newest one, so A moved to number 2
        rc, out = self.run_menu(["2", "1 млрд", ""], [b, a])
        self.assertIn("1) B - сохранение autosave", out)
        self.assertEqual(money_in(a, "autosave"), save_money.from_screen(10 ** 9, RUB))
        self.assertEqual(money_in(a, "autosave_job"), 50000000)     # only the newest save

    def test_steam_cloud_note(self):
        cloud = os.path.join(self.tmp, "Steam", "userdata", "123", "227300", "remote", "profiles")
        os.makedirs(cloud)
        prof = make_profile(cloud)
        self.assertTrue(save_money.in_steam_cloud(prof))
        self.assertFalse(save_money.in_steam_cloud(make_profile(self.tmp, "99")))
        rc, out = self.run_menu(["10 млрд", ""], [prof])
        self.assertIn("облаке Steam", out)
        self.assertIn("ЭТОГО компьютера", out)

    def test_no_profiles(self):
        rc, out = self.run_menu([], [os.path.join(self.tmp, "nothing")])
        self.assertEqual(rc, 1)
        self.assertIn("Не найдено", out)


@unittest.skipUnless(os.name == "nt", "cmd.exe only")
class BatchFileTest(unittest.TestCase):
    """The double-click files themselves, through cmd.exe, with typed answers."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ets2bat_")
        self.prof = make_profile(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_bat(self, name, answers, game_running="0"):
        env = dict(os.environ, ETS2_PYTHON='"%s"' % sys.executable, ETS2_NO_PAUSE="1",
                   ETS2_FAKE_GAME_RUNNING=game_running)
        bat = os.path.join(ROOT, name)
        cmdline = 'cmd.exe /s /c ""%s" --profile-dir "%s" --backup-dir "%s""' % (
            bat, self.prof, os.path.join(self.tmp, "bk"))
        r = subprocess.run(cmdline, input=answers.encode("utf-8"), capture_output=True, env=env,
                           cwd=self.tmp, timeout=120)
        return r.returncode, r.stdout.decode("utf-8", errors="replace")

    def test_money_bat(self):
        rc, out = self.run_bat("money.bat", "10 млрд\n\n")
        self.assertEqual(rc, 0, out)
        self.assertIn("ЗАПИСАНО: 9 999 999 972 руб.", out)            # UTF-8 console: Russian intact
        self.assertEqual(money_in(self.prof), 106393165)

    def test_bat_asks_to_close_the_game(self):
        rc, out = self.run_bat("money.bat", "10 млрд\n\nнет\n", game_running="1")
        self.assertEqual(rc, 0, out)
        self.assertIn("Игра запущена", out)
        self.assertIn("Ничего не записано", out)
        self.assertEqual(money_in(self.prof), 50000000)

    def test_russian_named_bat(self):
        rc, out = self.run_bat("Деньги ETS2.bat", "\n")
        self.assertEqual(rc, 0, out)
        self.assertIn("Ничего не записано", out)
        self.assertEqual(money_in(self.prof), 50000000)

    def test_bat_files_are_crlf_and_start_with_utf8_console(self):
        for name in ("money.bat", "Деньги ETS2.bat"):
            with open(os.path.join(ROOT, name), "rb") as fh:
                data = fh.read()
            self.assertNotIn(b"\n", data.replace(b"\r\n", b""), name)   # cmd misreads bare LF
            self.assertFalse(data.startswith(b"\xef\xbb\xbf"), name)    # a BOM breaks "@echo off"
        with open(os.path.join(ROOT, "money.bat"), "rb") as fh:
            text = fh.read().decode("utf-8")
        before = text[:text.index("chcp 65001")]
        self.assertTrue(all(ord(c) < 128 for c in before), "Russian text before chcp 65001")


if __name__ == "__main__":
    unittest.main()
