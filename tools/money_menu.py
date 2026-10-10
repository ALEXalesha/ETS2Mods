"""Change the money in ETS2 by double click: money.bat / "Деньги ETS2.bat" run this.

Asks in Russian, step by step:
  1. shows the profiles with their newest save and the money as the game shows it;
  2. asks for the new amount in the game's currency (roubles for a profile with
     roubles), e.g. 10000000000, "10 000 000 000" or "10 млрд";
  3. checks that the game is closed (asks to close it if eurotrucks2.exe runs);
  4. backs up the save folder and writes (save_money.write_money), reads it back;
  5. prints a big "ЗАПИСАНО" with the amount, and what to do next.

The newest save is the one the game's "Continue" loads. For tests the profile
folders, the backup folder and the input can be given: --profile-dir, --backup-dir;
run() takes the input function and the "is the game running" check.
"""

import argparse
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import save_money as sm  # noqa: E402
from sii_save import SiiError  # noqa: E402

# A precaution, not a known game limit: the save holds a 64-bit number, but how the
# game's screens handle more than about two billion EUR is not tested.
MAX_EUR = 2_000_000_000

BAR = "=" * 70

_WORDS = [  # (pattern, multiplier) for "10 млрд", "1,5 миллиона", "500 тыс"
    (r"(млрд|миллиард\w*|billion|bn)", 10 ** 9),
    (r"(млн|миллион\w*|million|mln)", 10 ** 6),
    (r"(тыс\w*|thousand|k)", 10 ** 3),
]
_CURRENCY_WORDS = r"(руб\w*|р\.?|₽|rub|eur|евро|€)"


def parse_amount(text):
    """The amount typed by the player, as a whole number, or None if it is not one.

    "10000000000", "10 000 000 000", "10.000.000.000", "10,000,000,000", "10 млрд",
    "1,5 млрд", "500 тыс руб" -> numbers; "", "abc", "-5", "1.5" (no word) -> None.
    """
    s = text.strip().lower().replace(" ", " ").replace(" ", " ")
    s = re.sub(r"\s*" + _CURRENCY_WORDS + r"\.?\s*$", "", s)
    mult = 1
    for pat, m in _WORDS:
        mm = re.search(r"\s*" + pat + r"\.?\s*$", s)
        if mm:
            mult, s = m, s[:mm.start()]
            break
    s = s.strip()
    if not s:
        return None
    if mult > 1:
        # with a word, a decimal point or comma is allowed: "1,5 млрд"
        mm = re.fullmatch(r"(\d+)(?:[.,](\d+))?", s.replace(" ", ""))
        if not mm:
            return None
        whole, frac = mm.group(1), mm.group(2) or ""
        return int(whole) * mult + (int(frac) * mult // 10 ** len(frac) if frac else 0)
    s = s.replace(" ", "").replace("_", "").replace("'", "")
    if re.fullmatch(r"\d+", s):
        return int(s)
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", s) or re.fullmatch(r"\d{1,3}(,\d{3})+", s):
        return int(s.replace(".", "").replace(",", ""))
    return None


def ru_num(n):
    """10000000000 -> '10 000 000 000'"""
    return format(n, ",").replace(",", " ")


def money_label(code):
    code = code.rstrip("*")
    return {"RUB": "руб.", "EUR": "€"}.get(code, code)


def on_screen(eur, cur):
    return "%s %s" % (ru_num(sm.to_screen(eur, cur)), money_label(cur["code"]))


def in_file(eur):
    return "%s € в файле сохранения" % ru_num(eur)


def find_profiles(dirs):
    """[(profile_dir, save_name, money_eur or the read error, currency, mtime)], newest first."""
    out = []
    for p in dirs:
        saves = sm.saves_newest_first(p)
        if not saves:
            continue
        game = os.path.join(saves[0], "game.sii")
        try:
            money = sm.read_money(game)[2]
        except Exception as e:  # an unreadable save is listed, not fatal
            money = str(e) or type(e).__name__
        out.append((p, os.path.basename(saves[0]), money, sm.pick_currency(p), os.path.getmtime(game)))
    out.sort(key=lambda e: e[4], reverse=True)
    return out


YES = {"", "д", "да", "y", "yes", "l", "lf"}   # "l"/"lf" = "д"/"да" typed on the English layout
CANCEL = {"н", "нет", "n", "no", "ytn", "0", "выход", "exit"}   # "ytn" = "нет" on the English layout


def run(argv=None, inp=input, out=print, is_running=sm.game_running):
    ap = argparse.ArgumentParser(description="ETS2: change money (interactive)")
    ap.add_argument("--profile-dir", action="append", help="profile folder (for tests); default: all found")
    ap.add_argument("--backup-dir", default=sm.BACKUP_ROOT)
    a = ap.parse_args(argv)

    out(BAR)
    out("  Деньги в Euro Truck Simulator 2")
    out(BAR)
    try:
        profs = find_profiles(a.profile_dir or sm.profile_dirs())
    except SiiError as e:
        out("Ошибка чтения сохранения: %s" % e)
        return 2
    if not profs:
        out("Не найдено ни одного профиля с сохранениями.")
        out("Профили ищутся в Документы\\Euro Truck Simulator 2\\profiles и в облаке Steam")
        out("(Steam\\userdata\\<номер>\\227300\\remote\\profiles).")
        return 1

    out("Профили (сверху - где играли последним):")
    for i, (p, save, money, cur, mtime) in enumerate(profs, 1):
        when = datetime.datetime.fromtimestamp(mtime).strftime("%d.%m.%Y %H:%M")
        where = "облако Steam" if sm.in_steam_cloud(p) else "Документы"
        now = on_screen(money, cur) if isinstance(money, int) else "не читается"
        out("  %d) %s - сохранение %s от %s - сейчас %s  [%s]" % (i, sm.profile_name(p), save, when, now, where))

    k = 0
    if len(profs) > 1:
        while True:
            ans = inp("Номер профиля (Enter - 1): ").strip()
            if ans == "":
                break
            if ans.isdigit() and 1 <= int(ans) <= len(profs):
                k = int(ans) - 1
                break
            out("Нужен номер от 1 до %d." % len(profs))
    prof, save, money, cur, _m = profs[k]
    if not isinstance(money, int):
        out("Сохранение %s не читается, деньги в нём поменять нельзя: %s" % (save, money))
        return 3 if "pycryptodome" in money else 2
    label = money_label(cur["code"])
    out("")
    out("Профиль %s, сохранение %s." % (sm.profile_name(prof), save))
    out("Сейчас в игре: %s (%s)" % (on_screen(money, cur), in_file(money)))
    out("")

    while True:
        ans = inp("Сколько денег поставить, в %s как в игре (например 10000000000 или 10 млрд).\n"
                  "Пусто и Enter - выйти без изменений: " % label)
        if ans.strip() == "":
            out("Ничего не записано.")
            return 0
        amount = parse_amount(ans)
        if amount is None:
            out("Не понял число «%s». Пишите цифрами, можно с пробелами, или «10 млрд»." % ans.strip())
            continue
        eur = sm.from_screen(amount, cur)
        if eur > MAX_EUR:
            out("Слишком много: %s - это %s. На всякий случай не больше %s." % (
                ru_num(amount) + " " + label, in_file(eur), on_screen(MAX_EUR, cur)))
            continue
        break

    out("")
    out("Будет записано: %s (%s, курс игры %s)." % (on_screen(eur, cur), in_file(eur), format(cur["ratio"], "g")))
    if sm.to_screen(eur, cur) != amount:
        out("(в сохранении целые евро, поэтому в игре будет %s вместо %s)" % (on_screen(eur, cur), ru_num(amount)))
    ans = inp("Записать? Д/н (Enter - да): ").strip().lower()
    if ans not in YES:
        out("Ничего не записано.")
        return 0

    while is_running():
        out("")
        out("Игра запущена (eurotrucks2.exe). Если писать сейчас, игра затрёт деньги своим сохранением.")
        ans = inp("Закройте игру полностью и нажмите Enter (или «нет» - выйти): ").strip().lower()
        if ans in CANCEL:
            out("Ничего не записано.")
            return 0

    try:
        before, after, dst = sm.write_money(prof, save, eur, a.backup_dir)
    except (SiiError, OSError) as e:
        out("ОШИБКА, деньги не записаны: %s" % e)
        return 2

    out("")
    out(BAR)
    out("  ЗАПИСАНО: %s" % on_screen(after, cur))
    out("            (%s)" % in_file(after))
    out("  Было:     %s" % on_screen(before, cur))
    out("")
    out("  Теперь запустите игру и загрузите последнее сохранение")
    out("  (кнопка «Продолжить» или «Загрузить» - %s)." % save)
    out(BAR)
    out("Копия сохранения до правки: %s" % dst)
    if sm.in_steam_cloud(prof):
        out("")
        out("Профиль в облаке Steam. При запуске игры Steam сам заметит, что файл изменился на этом")
        out("компьютере, и отправит его в облако - ничего делать не нужно. Если Steam всё же покажет")
        out("окно конфликта облачной синхронизации, выберите файлы ЭТОГО компьютера (локальные),")
        out("а не облачные - иначе вернётся старая сумма.")
    return 0


def main():
    for stream in (sys.stdout, sys.stderr, sys.stdin):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    fake = os.environ.get("ETS2_FAKE_GAME_RUNNING")    # tests on a PC where the game may be open
    running = (lambda: fake == "1") if fake in ("0", "1") else sm.game_running
    try:
        return run(is_running=running)
    except (EOFError, KeyboardInterrupt):
        print("\nНичего не записано.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
