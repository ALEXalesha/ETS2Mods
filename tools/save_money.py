"""Show or change the money in an ETS2 save (game.sii) - the game must be closed.

  python tools/save_money.py                      list profiles, saves and money
  python tools/save_money.py --save autosave --set 5000000000          dry run
  python tools/save_money.py --save autosave --set 5000000000 --apply  write
  python tools/save_money.py --save autosave --set-eur 50000000 --apply
  python tools/save_money.py --save autosave --restore                 put the last backup back

Currency: the save keeps money in EUR; the game shows it in the currency chosen
in the profile (Options - Gameplay - Currency; the profile's config.cfg,
uset g_currency "N"). --set takes the amount AS THE GAME SHOWS IT, in that
currency, and converts it with the game's rate (def/economy_data.sii,
currency_ratio). With roubles (rate 93.991) --set 5000000000 writes
53,196,583 EUR to the file and the game shows 5,000,000,000 RUB.
--set-eur writes an EUR amount as is. --currency CODE (EUR, RUB, ...) overrides
the profile's currency. Every readout shows both: EUR in the file and the
amount on screen.

Before writing, the whole save folder is copied to
  Documents\\Euro Truck Simulator 2\\save_backups\\<profile>\\<save>_<time>\\

Formats (see sii_save.py):
  - text save (g_save_format "2"): money_account is replaced in the bank unit;
  - encrypted binary save (ScsC + BSII, the default): decrypted, the 8 bytes of
    bank.money_account are replaced and the file is written as plain BSII,
    the same binary format without the encryption layer.
Needs pycryptodome for encrypted saves (installed in the project venv).
"""

import argparse
import datetime
import glob
import os
import re
import shutil
import struct
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sii_save import Bsii, SiiError, load_plain  # noqa: E402

DOCS = os.path.join(os.path.expanduser("~"), "Documents", "Euro Truck Simulator 2")
STEAM_USERDATA = r"C:\Program Files (x86)\Steam\userdata"
BACKUP_ROOT = os.path.join(DOCS, "save_backups")
GAME_DIR = r"C:\Program Files (x86)\Steam\steamapps\common\Euro Truck Simulator 2"
INT64_MAX = 2 ** 63 - 1

# def/economy_data.sii of 1.61, used when the game files cannot be read.
# The order matters: g_currency is an index into this list.
BUILTIN_CURRENCIES = [
    {"code": c, "ratio": r, "sign2": "", "sign3": ""} for c, r in (
        ("EUR", 1.0), ("CHF", 0.9160), ("CZK", 24.4945), ("GBP", 0.8646), ("PLN", 4.2734),
        ("HUF", 387.68), ("DKK", 7.4721), ("SEK", 10.864), ("NOK", 11.161), ("RUB", 93.991),
        ("BGN*", 1.9558), ("RON", 5.0966), ("TRY", 51.195), ("ALL", 96.086), ("BAM", 1.9558),
        ("MKD", 61.616), ("RSD", 117.45))
]


def parse_currencies(text):
    """The currency list of economy_data.sii, in file order."""
    codes = re.findall(r'^\s*currency_code\[\]\s*:\s*"([^"]*)"', text, re.M)
    ratios = re.findall(r'^\s*currency_ratio\[\]\s*:\s*([-\d.]+)', text, re.M)
    sign2 = re.findall(r'^\s*currency_sign2\[\]\s*:\s*"([^"]*)"', text, re.M)
    sign3 = re.findall(r'^\s*currency_sign3\[\]\s*:\s*"([^"]*)"', text, re.M)
    if not codes or len(codes) != len(ratios):
        raise SiiError("currency list: %d codes, %d ratios" % (len(codes), len(ratios)))
    return [{"code": c, "ratio": float(r), "sign2": sign2[i] if i < len(sign2) else "",
             "sign3": sign3[i] if i < len(sign3) else ""} for i, (c, r) in enumerate(zip(codes, ratios))]


def game_currencies(game_dir=GAME_DIR):
    """The currency list from the installed game, or the built-in 1.61 list."""
    try:
        from hashfs import HashFs
        text = HashFs(os.path.join(game_dir, "def.scs")).read("def/economy_data.sii").decode("utf-8-sig")
        return parse_currencies(text)
    except Exception:  # no game here or another layout: the 1.61 list
        return BUILTIN_CURRENCIES


def profile_currency_index(profile_dir):
    """g_currency from the profile's config.cfg (0 = EUR when it is not there)."""
    try:
        with open(os.path.join(profile_dir, "config.cfg"), encoding="utf-8", errors="replace") as fh:
            m = re.search(r'^\s*uset\s+g_currency\s+"?(\d+)"?', fh.read(), re.M)
    except OSError:
        return 0
    return int(m.group(1)) if m else 0


def pick_currency(profile_dir, code=None):
    table = game_currencies()
    if code:
        for c in table:
            if c["code"].rstrip("*").upper() == code.rstrip("*").upper():
                return c
        raise SystemExit("unknown currency %s; known: %s" % (code, ", ".join(c["code"] for c in table)))
    i = profile_currency_index(profile_dir)
    return table[i] if 0 <= i < len(table) else table[0]


def to_screen(eur, cur):
    return int(round(eur * cur["ratio"]))


def from_screen(amount, cur):
    return int(round(amount / cur["ratio"]))


def fmt(amount, code):
    return "%s %s" % (format(amount, ","), code.rstrip("*"))


def both(eur, cur):
    """'50,000,000 EUR in the file = 4,699,550,000 RUB on screen (rate 93.991)'"""
    if cur["code"] == "EUR":
        return "%s in the file = on screen" % fmt(eur, "EUR")
    return "%s in the file = %s on screen (rate %s)" % (
        fmt(eur, "EUR"), fmt(to_screen(eur, cur), cur["code"]), format(cur["ratio"], "g"))


def profile_dirs():
    out = []
    for pat in (os.path.join(DOCS, "profiles", "*"),
                os.path.join(DOCS, "steam_profiles", "*"),
                os.path.join(STEAM_USERDATA, "*", "227300", "remote", "profiles", "*")):
        for d in glob.glob(pat):
            if os.path.isdir(os.path.join(d, "save")):
                out.append(d)
    return out


def profile_name(d):
    h = os.path.basename(d)
    try:
        return bytes.fromhex(h).decode("utf-8")
    except ValueError:
        return h


def game_running():
    try:
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq eurotrucks2.exe", "/NH"],
                           capture_output=True, text=True, errors="replace")
        return "eurotrucks2.exe" in r.stdout.lower()
    except OSError:
        return False


TEXT_BANK = re.compile(r"(^bank\s*:\s*[^\s{]+\s*\{.*?^\s*money_account\s*:\s*)(-?\d+)", re.M | re.S)


def read_money(path):
    with open(path, "rb") as fh:
        raw = load_plain(fh.read())
    if raw[:4] == b"BSII":
        b = Bsii(raw)
        banks = b.find("bank")
        if len(banks) != 1:
            raise SiiError("expected one bank unit, found %d" % len(banks))
        t, off = banks[0][2]["money_account"]
        if t != 0x31:
            raise SiiError("money_account has unexpected type 0x%02X" % t)
        return "binary", raw, struct.unpack_from("<q", raw, off)[0], off
    text = raw.decode("utf-8")
    ms = list(TEXT_BANK.finditer(text))
    if len(ms) != 1:
        raise SiiError("expected one bank unit with money_account in text save, found %d" % len(ms))
    return "text", raw, int(ms[0].group(2)), ms[0]


def backup(save_dir, prof, root=BACKUP_ROOT):
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    dst = os.path.join(root, os.path.basename(prof), "%s_%s" % (os.path.basename(save_dir), stamp))
    shutil.copytree(save_dir, dst)
    return dst


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", help="profile folder name (hex) or display name; default: the only/first one")
    ap.add_argument("--profile-dir", help="path of one profile folder (the one with save inside)")
    ap.add_argument("--save", help="save folder name, e.g. autosave, 1, quicksave")
    ap.add_argument("--set", type=int, help="new money AS THE GAME SHOWS IT, in the profile's currency")
    ap.add_argument("--set-eur", type=int, help="new money in EUR, as stored in the save")
    ap.add_argument("--currency", help="currency code (EUR, RUB, ...) instead of the profile's")
    ap.add_argument("--apply", action="store_true", help="really write (otherwise dry run)")
    ap.add_argument("--restore", action="store_true", help="copy the newest backup of --save back")
    ap.add_argument("--backup-dir", default=BACKUP_ROOT, help="where backups go (default: %(default)s)")
    a = ap.parse_args()
    if a.set is not None and a.set_eur is not None:
        raise SystemExit("use --set or --set-eur, not both")

    profs = [a.profile_dir] if a.profile_dir else profile_dirs()
    if a.profile:
        profs = [p for p in profs if a.profile in (os.path.basename(p), profile_name(p))]
    if not profs:
        raise SystemExit("no profile with saves found")

    if not a.save:
        for p in profs:
            cur = pick_currency(p, a.currency)
            print("profile %s  (%s), currency on screen: %s" % (profile_name(p), p, cur["code"].rstrip("*")))
            saves = sorted(glob.glob(os.path.join(p, "save", "*", "game.sii")),
                           key=os.path.getmtime, reverse=True)
            for g in saves[:12]:
                when = datetime.datetime.fromtimestamp(os.path.getmtime(g)).strftime("%Y-%m-%d %H:%M")
                try:
                    kind, _, money, _ = read_money(g)
                    info = "%s, money %s" % (kind, both(money, cur))
                except Exception as e:  # report and keep listing
                    info = "unreadable: %s" % e
                print("  %-18s %s  %s" % (os.path.basename(os.path.dirname(g)), when, info))
        return 0

    prof = profs[0]
    save_dir = os.path.join(prof, "save", a.save)
    game = os.path.join(save_dir, "game.sii")
    if not os.path.isfile(game) and not a.restore:
        raise SystemExit("not found: " + game)

    if a.restore:
        pat = os.path.join(a.backup_dir, os.path.basename(prof), a.save + "_*")
        cands = sorted(glob.glob(pat))
        if not cands:
            raise SystemExit("no backup found: " + pat)
        if game_running():
            raise SystemExit("ETS2 is running - close the game first")
        src = cands[-1]
        for f in os.listdir(src):
            shutil.copy2(os.path.join(src, f), os.path.join(save_dir, f))
        print("restored", save_dir, "from", src)
        return 0

    kind, raw, money, where = read_money(game)
    cur = pick_currency(prof, a.currency)
    print("profile %s, save %s: %s save, money %s" % (profile_name(prof), a.save, kind, both(money, cur)))
    if a.set is None and a.set_eur is None:
        return 0
    if a.set_eur is not None:
        eur = a.set_eur
    else:
        eur = from_screen(a.set, cur)
        print("--set %s (the game shows %s): the file gets %s" % (
            fmt(a.set, cur["code"]), cur["code"].rstrip("*"), fmt(eur, "EUR")))
        if to_screen(eur, cur) != a.set:
            print("  the save holds whole euros, so the game will show %s" % fmt(to_screen(eur, cur), cur["code"]))
    if not 0 <= eur <= INT64_MAX:
        raise SystemExit("money must be between 0 and %s EUR" % format(INT64_MAX, ","))
    if kind == "binary":
        new = bytearray(raw)
        struct.pack_into("<q", new, where, eur)
        new = bytes(new)
    else:
        text = raw.decode("utf-8")
        new = (text[:where.start(2)] + str(eur) + text[where.end(2):]).encode("utf-8")
    # check the result reads back with the new value
    if new[:4] == b"BSII":
        b = Bsii(new)
        t, off = b.find("bank")[0][2]["money_account"]
        assert struct.unpack_from("<q", new, off)[0] == eur
    else:
        assert int(TEXT_BANK.search(new.decode("utf-8")).group(2)) == eur
    if not a.apply:
        print("dry run: would write %s (add --apply to write)" % both(eur, cur))
        return 0
    if game_running():
        raise SystemExit("ETS2 is running - close the game first, otherwise it overwrites the save")
    dst = backup(save_dir, prof, a.backup_dir)
    print("backup:", dst)
    with open(game, "wb") as fh:
        fh.write(new)
    _k, _r, check, _w = read_money(game)
    if check != eur:
        raise SystemExit("read back %s, expected %s - put the backup back with --restore" % (check, eur))
    print("written and read back: %s" % both(check, cur))
    print("was:                   %s" % both(money, cur))
    print("file:", game)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SiiError as e:
        print("ERROR:", e)
        sys.exit(2)
