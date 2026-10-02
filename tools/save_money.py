"""Show or change the money in an ETS2 save (game.sii) - the game must be closed.

  python tools/save_money.py                      list profiles, saves and money
  python tools/save_money.py --save autosave --set 50000000           dry run
  python tools/save_money.py --save autosave --set 50000000 --apply   write
  python tools/save_money.py --save autosave --restore                put the last backup back

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


def backup(save_dir, prof):
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    dst = os.path.join(BACKUP_ROOT, os.path.basename(prof), "%s_%s" % (os.path.basename(save_dir), stamp))
    shutil.copytree(save_dir, dst)
    return dst


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", help="profile folder name (hex) or display name; default: the only/first one")
    ap.add_argument("--save", help="save folder name, e.g. autosave, 1, quicksave")
    ap.add_argument("--set", type=int, help="new money_account value")
    ap.add_argument("--apply", action="store_true", help="really write (otherwise dry run)")
    ap.add_argument("--restore", action="store_true", help="copy the newest backup of --save back")
    a = ap.parse_args()

    profs = profile_dirs()
    if a.profile:
        profs = [p for p in profs if a.profile in (os.path.basename(p), profile_name(p))]
    if not profs:
        raise SystemExit("no profile with saves found")

    if not a.save:
        for p in profs:
            print("profile %s  (%s)" % (profile_name(p), p))
            saves = sorted(glob.glob(os.path.join(p, "save", "*", "game.sii")),
                           key=os.path.getmtime, reverse=True)
            for g in saves[:12]:
                when = datetime.datetime.fromtimestamp(os.path.getmtime(g)).strftime("%Y-%m-%d %H:%M")
                try:
                    kind, _, money, _ = read_money(g)
                    info = "%s, money %s" % (kind, format(money, ","))
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
        pat = os.path.join(BACKUP_ROOT, os.path.basename(prof), a.save + "_*")
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
    print("profile %s, save %s: %s save, money %s" % (profile_name(prof), a.save, kind, format(money, ",")))
    if a.set is None:
        return 0
    if kind == "binary":
        new = bytearray(raw)
        struct.pack_into("<q", new, where, a.set)
        new = bytes(new)
    else:
        text = raw.decode("utf-8")
        new = (text[:where.start(2)] + str(a.set) + text[where.end(2):]).encode("utf-8")
    # check the result reads back with the new value
    tmp_kind = "binary" if new[:4] == b"BSII" else "text"
    if tmp_kind == "binary":
        b = Bsii(new)
        t, off = b.find("bank")[0][2]["money_account"]
        assert struct.unpack_from("<q", new, off)[0] == a.set
    else:
        assert int(TEXT_BANK.search(new.decode("utf-8")).group(2)) == a.set
    if not a.apply:
        print("dry run: would set money to %s (add --apply to write)" % format(a.set, ","))
        return 0
    if game_running():
        raise SystemExit("ETS2 is running - close the game first, otherwise it overwrites the save")
    dst = backup(save_dir, prof)
    print("backup:", dst)
    with open(game, "wb") as fh:
        fh.write(new)
    print("written: money %s -> %s (%s)" % (format(money, ","), format(a.set, ","), game))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SiiError as e:
        print("ERROR:", e)
        sys.exit(2)
