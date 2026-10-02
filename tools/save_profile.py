"""Max out the driver level and all six skills in an ETS2 save - the game must be closed.

  python tools/save_profile.py --save autosave              show XP, level and skills
  python tools/save_profile.py --save autosave --max        dry run
  python tools/save_profile.py --save autosave --max --apply
  python tools/save_profile.py --save autosave --restore    put the last backup back

What --max writes into the "economy" unit of game.sii:
  experience_points  enough XP for level --level (default 100, see below)
  adr                63 (bit mask: all six ADR classes 1, 2, 3, 4, 6, 8)
  long_dist, heavy, fragile, urgent, mechanical   6 (max_rank in def/skill_data.sii)
heavy = High Value Cargo, urgent = Just-In-Time, mechanical = Ecodriving.

Level thresholds come from def/economy_data_xp.sii (level_xp[0..29]). The game
gives one skill point per level (checked on the real save: level 20 = 20 points
spent). Above level 30 the file has no thresholds; this tool assumes each
further level costs the last listed value (6800 XP). If the game uses a higher
cost there, the level ends up lower, but still far above the 36 points that
all skills need.

Backups and format handling are the same as tools/save_money.py.
"""

import argparse
import os
import re
import shutil
import struct
import sys
import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hashfs import HashFs  # noqa: E402
from sii_save import Bsii, SiiError, load_plain  # noqa: E402
from save_money import BACKUP_ROOT, backup, game_running, profile_dirs, profile_name  # noqa: E402

GAME = r"C:\Program Files (x86)\Steam\steamapps\common\Euro Truck Simulator 2"
SKILLS = ["adr", "long_dist", "heavy", "fragile", "urgent", "mechanical"]
FIELDS = ["experience_points"] + SKILLS


def level_table(game_dir=GAME):
    fs = HashFs(os.path.join(game_dir, "def.scs"))
    xp = fs.read("def/economy_data_xp.sii").decode("utf-8-sig")
    steps = [int(v) for _, v in sorted(
        ((int(i), v) for i, v in re.findall(r"^\s*level_xp\[(\d+)\]\s*:\s*(\d+)", xp, re.M)))]
    skills = fs.read("def/skill_data.sii").decode("utf-8-sig")
    ranks = sorted(set(int(r) for r in re.findall(r"^\s*max_rank\s*:\s*(\d+)", skills, re.M)))
    if not steps or ranks != [6]:
        raise SiiError("unexpected level/skill data: %d level steps, max ranks %s" % (len(steps), ranks))
    return steps


def level_for_xp(xp, steps):
    lvl, need = 0, 0
    while True:
        step = steps[lvl] if lvl < len(steps) else steps[-1]
        if need + step > xp:
            return lvl
        need += step
        lvl += 1


def xp_for_level(level, steps):
    return sum(steps[i] if i < len(steps) else steps[-1] for i in range(level))


def text_unit_span(text, unit_class):
    m = re.search(r"^%s\s*:\s*[^\s{]+\s*\{" % re.escape(unit_class), text, re.M)
    if not m:
        raise SiiError("no %s unit in text save" % unit_class)
    end = text.find("\n}", m.end())
    return m.end(), end


def read_fields(path):
    with open(path, "rb") as fh:
        raw = load_plain(fh.read())
    if raw[:4] == b"BSII":
        b = Bsii(raw)
        units = b.find("economy")
        if len(units) != 1:
            raise SiiError("expected one economy unit, found %d" % len(units))
        offs = units[0][2]
        vals, where = {}, {}
        for k in FIELDS:
            t, off = offs[k]
            if t != 0x27:
                raise SiiError("%s has type 0x%02X, expected u32" % (k, t))
            vals[k] = struct.unpack_from("<I", raw, off)[0]
            where[k] = off
        return "binary", raw, vals, where
    text = raw.decode("utf-8")
    s, e = text_unit_span(text, "economy")
    vals, where = {}, {}
    for k in FIELDS:
        rx = re.compile(r"^(\s*%s\s*:\s*)(\d+)\s*$" % re.escape(k), re.M)
        ms = list(rx.finditer(text, s, e))
        if len(ms) != 1:
            raise SiiError("field %s found %d times in economy unit" % (k, len(ms)))
        vals[k] = int(ms[0].group(2))
        where[k] = ms[0].span(2)
    return "text", raw, vals, where


def patch(kind, raw, where, new_vals):
    if kind == "binary":
        out = bytearray(raw)
        for k, v in new_vals.items():
            struct.pack_into("<I", out, where[k], v)
        return bytes(out)
    text = raw.decode("utf-8")
    for k, (a, b) in sorted(where.items(), key=lambda kv: kv[1][0], reverse=True):
        if k in new_vals:
            text = text[:a] + str(new_vals[k]) + text[b:]
    return text.encode("utf-8")


def describe(vals, steps):
    lvl = level_for_xp(vals["experience_points"], steps)
    sk = ", ".join("%s=%d" % (k, vals[k]) for k in SKILLS)
    return "XP %s (level %d), %s" % (format(vals["experience_points"], ","), lvl, sk)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile")
    ap.add_argument("--save", required=True)
    ap.add_argument("--max", action="store_true", help="max level and all skills")
    ap.add_argument("--level", type=int, default=100)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--restore", action="store_true")
    a = ap.parse_args()

    profs = profile_dirs()
    if a.profile:
        profs = [p for p in profs if a.profile in (os.path.basename(p), profile_name(p))]
    if not profs:
        raise SystemExit("no profile with saves found")
    prof = profs[0]
    save_dir = os.path.join(prof, "save", a.save)
    game = os.path.join(save_dir, "game.sii")

    if a.restore:
        cands = sorted(glob.glob(os.path.join(BACKUP_ROOT, os.path.basename(prof), a.save + "_*")))
        if not cands:
            raise SystemExit("no backup found")
        if game_running():
            raise SystemExit("ETS2 is running - close the game first")
        for f in os.listdir(cands[-1]):
            shutil.copy2(os.path.join(cands[-1], f), os.path.join(save_dir, f))
        print("restored", save_dir, "from", cands[-1])
        return 0

    steps = level_table()
    kind, raw, vals, where = read_fields(game)
    print("profile %s, save %s (%s): %s" % (profile_name(prof), a.save, kind, describe(vals, steps)))
    if not a.max:
        return 0
    new = {"experience_points": max(vals["experience_points"], xp_for_level(a.level, steps)),
           "adr": 63, "long_dist": 6, "heavy": 6, "fragile": 6, "urgent": 6, "mechanical": 6}
    out = patch(kind, raw, where, new)
    _k, _r, check, _w = read_fields_bytes(out)
    assert all(check[k] == v for k, v in new.items()), check
    print("new: %s" % describe(check, steps))
    if not a.apply:
        print("dry run: nothing written (add --apply)")
        return 0
    if game_running():
        raise SystemExit("ETS2 is running - close the game first, otherwise it overwrites the save")
    dst = backup(save_dir, prof)
    print("backup:", dst)
    with open(game, "wb") as fh:
        fh.write(out)
    print("written:", game)
    return 0


def read_fields_bytes(data):
    """read_fields for in-memory content (plain BSII or text)."""
    import tempfile
    fd, tmp = tempfile.mkstemp(suffix=".sii")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        return read_fields(tmp)
    finally:
        os.remove(tmp)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SiiError as e:
        print("ERROR:", e)
        sys.exit(2)
