"""Build the ETS2 mods from the game's own def files.

The repository does not contain SCS's original files. This script reads them
from the installed game (def.scs plus the dlc_*.scs archives), applies the value
changes listed in mods/<name>/mod.json and packs each mod as a .scs (plain zip,
stored, no directory entries).

Every change must match the expected number of lines. If a game update renames
or removes a parameter, the build stops with an error instead of producing a
broken mod.

Load order and shared files
---------------------------
mods/order.json lists the mods from the top of the in-game Mod Manager list
(highest priority) to the bottom. The game uses only the top-most copy of a
file. When several of our mods change the same file (economy_data.sii, the
engine files, physics.sii), the copy in a mod also carries the changes of every
mod BELOW it in that list. With the recommended order nothing is lost.

Patch operations (mod.json, "patches": {path_pattern: [op, ...]}):
  {"key": K, "value": V}                    set an existing value (count: 1)
  {"key": K, "value": V, "count": N}        ... N lines (K may contain [*])
  {"key": K, "scale": F}                    multiply an existing number
  {"insert_after_key": K, "line": L, "absent_key": A}
                                            add line L after each K line;
                                            fails if A is already set
  {"insert_after": TEXT, "line": L, "absent_key": A}
                                            add line L after the anchor text
  "per_unit": CLASS   instead of count: one match per "CLASS :" unit header
  "optional": true    zero matches allowed (count or per_unit as maximum)
Path patterns may use * in any part, e.g. def/vehicle/truck/*/engine/*.sii;
"require": TEXT keeps only files that contain TEXT.

Usage:
  python tools/build_mods.py [--game DIR] [--install]
"""

import argparse
import fnmatch
import glob
import json
import os
import re
import shutil
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hashfs import HashFs  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_GAME = r"C:\Program Files (x86)\Steam\steamapps\common\Euro Truck Simulator 2"
DEFAULT_MOD_DIR = os.path.join(os.path.expanduser("~"), "Documents", "Euro Truck Simulator 2", "mod")


class PatchError(Exception):
    pass


class LayeredFs:
    """def.scs plus every dlc_*.scs, read-only. A later archive wins for the same path."""

    def __init__(self, game_dir):
        paths = [os.path.join(game_dir, "def.scs")] + sorted(glob.glob(os.path.join(game_dir, "dlc_*.scs")))
        self.archives = []
        for p in paths:
            fs = HashFs(p)
            if fs.exists("def"):
                self.archives.append((os.path.basename(p), fs))

    def source(self, path):
        for name, fs in reversed(self.archives):
            e = fs.get(path)
            if e is not None and not e.is_dir:
                return name
        return None

    def read(self, path):
        for _name, fs in reversed(self.archives):
            e = fs.get(path)
            if e is not None and not e.is_dir:
                return fs.read_entry(e)
        raise KeyError(path)

    def listdir(self, path):
        dirs, files = set(), set()
        found = False
        for _name, fs in self.archives:
            try:
                d, f = fs.listdir(path)
            except KeyError:
                continue
            found = True
            dirs.update(d)
            files.update(f)
        if not found:
            raise KeyError(path)
        return sorted(dirs), sorted(files)


def game_version(game_dir):
    fs = HashFs(os.path.join(game_dir, "version.scs"))
    text = fs.read("version.sii").decode("utf-8", "replace")
    m = re.search(r'version:\s*"([0-9.]+)"', text)
    if not m:
        raise PatchError("cannot read game version from version.scs")
    return m.group(1)


def key_regex(key):
    # "fine_amounts[*]" matches fine_amounts[0], fine_amounts[1], ...
    return re.escape(key).replace(r"\[\*\]", r"\[\d+\]")


LINE_RE = r"^(?P<indent>[ \t]*)(?P<key>{key})[ \t]*:[ \t]*(?P<val>[^#\n]*?)[ \t]*(?P<comment>#.*)?$"


def fmt_number(old, factor):
    v = float(old) * factor
    if re.fullmatch(r"-?\d+", old.strip()):
        return str(int(round(v)))
    return ("%.4f" % v).rstrip("0").rstrip(".")


def expected_count(text, patch):
    if "per_unit" in patch:
        return len(re.findall(r"^\s*%s\s*:" % re.escape(patch["per_unit"]), text, re.M))
    return patch.get("count", 1)


def check_count(n, want, patch, mod_name, what, path):
    if patch.get("optional"):
        if n > want:
            raise PatchError("%s: %s matched %d lines in %s, at most %d allowed" % (mod_name, what, n, path, want))
    elif n != want:
        raise PatchError("%s: %s matched %d lines in %s, expected %d" % (mod_name, what, n, path, want))


def apply_patch(text, patch, mod_name, log, path):
    absent = patch.get("absent_key")
    if absent and re.search(LINE_RE.format(key=key_regex(absent)), text, re.M):
        raise PatchError("%s: %s already set in %s" % (mod_name, absent, path))

    if "insert_after" in patch:
        anchor = patch["insert_after"]
        if text.count(anchor) != 1:
            raise PatchError("%s: anchor %r found %d times in %s"
                             % (mod_name, anchor, text.count(anchor), path))
        line = patch["line"]
        log.append((path, line.strip().split(":")[0], "(not set)",
                    line.split(":", 1)[1].split("#")[0].strip(), mod_name))
        return text.replace(anchor, anchor + "\n" + line, 1)

    if "insert_after_key" in patch:
        rx = re.compile(LINE_RE.format(key=key_regex(patch["insert_after_key"])), re.M)
        hits = list(rx.finditer(text))
        check_count(len(hits), expected_count(text, patch), patch, mod_name,
                    "anchor key " + patch["insert_after_key"], path)
        line = patch["line"]
        for m in reversed(hits):
            text = text[:m.end()] + "\n" + m.group("indent") + line + text[m.end():]
        for _ in hits:
            log.append((path, line.strip().split(":")[0], "(not set)",
                        line.split(":", 1)[1].split("#")[0].strip(), mod_name))
        return text

    key = patch["key"]
    rx = re.compile(LINE_RE.format(key=key_regex(key)), re.M)
    found = []

    def repl(m):
        old = m.group("val")
        new = fmt_number(old, patch["scale"]) if "scale" in patch else patch["value"]
        comment = (m.group("comment") or "").lstrip("#").strip()
        found.append((m.group("key"), old, new))
        note = "# %s[mod %s: was %s]" % (comment + " " if comment else "", mod_name, old)
        return "%s%s: %s\t%s" % (m.group("indent"), m.group("key"), new, note)

    new_text = rx.sub(repl, text)
    check_count(len(found), expected_count(text, patch), patch, mod_name, "key " + key, path)
    for k, old, new in found:
        log.append((path, k, old, new, mod_name))
    return new_text


def load_spec(name):
    with open(os.path.join(ROOT, "mods", name, "mod.json"), encoding="utf-8") as fh:
        return json.load(fh)


def load_order():
    with open(os.path.join(ROOT, "mods", "order.json"), encoding="utf-8") as fh:
        order = json.load(fh)["top_to_bottom"]
    present = sorted(n for n in os.listdir(os.path.join(ROOT, "mods"))
                     if os.path.isfile(os.path.join(ROOT, "mods", n, "mod.json")))
    if sorted(order) != present:
        raise PatchError("mods/order.json %s does not match mod folders %s" % (order, present))
    return order


def expand_path(defs, pattern, require=None):
    """Expand a path pattern with * in any component against the layered file system."""
    parts = pattern.split("/")
    cur = [""]
    for i, part in enumerate(parts):
        last = i == len(parts) - 1
        nxt = []
        for base in cur:
            if "*" not in part:
                nxt.append(base + part if not base else base + "/" + part)
                continue
            try:
                dirs, files = defs.listdir(base)
            except KeyError:
                continue
            for name in (files if last else dirs):
                if fnmatch.fnmatchcase(name, part):
                    nxt.append(base + "/" + name if base else name)
        cur = nxt
    hits = sorted(set(cur))
    if require:
        hits = [h for h in hits if require.encode() in defs.read(h)]
    if not hits:
        raise PatchError("no files match %s" % pattern)
    return hits


def own_plan(spec, defs):
    """{real_path: [patch, ...]} for one mod's own patches."""
    plan = {}
    for pattern, patches in spec["patches"].items():
        require = None
        ops = []
        for p in patches:
            if "require" in p:
                require = p["require"]
            ops.append(p)
        for real in expand_path(defs, pattern, require):
            plan.setdefault(real, []).extend(ops)
    return plan


def build_files(name, defs, order, plans, log):
    """Return {archive_path: text}: own patches plus those of mods below in the order."""
    idx = order.index(name)
    out = {}
    for path in sorted(plans[name]):
        text = defs.read(path).decode("utf-8")
        for lower in reversed(order[idx + 1:]):          # bottom-most first
            if path in plans[lower]:
                pkg = load_spec(lower)["package"]
                for p in plans[lower][path]:
                    text = apply_patch(text, p, pkg, log, path)
        pkg = load_spec(name)["package"]
        for p in plans[name][path]:
            text = apply_patch(text, p, pkg, log, path)
        out[path] = text
    return out


def manifest(spec, version_glob):
    return (
        "SiiNunit\n{\n"
        "mod_package : .package_name\n{\n"
        '\tpackage_version: "%s"\n'
        '\tdisplay_name: "%s"\n'
        '\tauthor: "Alexey"\n'
        '\tcategory[]: "%s"\n'
        '\ticon: "mod_icon.jpg"\n'
        '\tdescription_file: "mod_description.txt"\n'
        '\tcompatible_versions[]: "%s"\n'
        "}\n}\n"
    ) % (spec["version"], spec["display_name"], spec["category"], version_glob)


def write_scs(out_path, files):
    """files: {archive_path: bytes}. Plain zip, stored (no compression).
    No directory entries: with a "def/" entry the game logs
    "[zipfs] error reading a non-directory entry (/def)"."""
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_STORED) as z:
        for p in sorted(files):
            zi = zipfile.ZipInfo(p, date_time=(2026, 1, 1, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_STORED
            z.writestr(zi, files[p])


def build_all(game_dir, out_dir, verbose=True):
    """Build every mod into out_dir. Returns {mod_name: {"file", "spec", "files", "log"}}."""
    version = game_version(game_dir)
    version_glob = ".".join(version.split(".")[:2]) + ".*"
    if verbose:
        print("game version:", version, "-> compatible_versions", version_glob)
    defs = LayeredFs(game_dir)
    order = load_order()
    plans = {n: own_plan(load_spec(n), defs) for n in order}
    os.makedirs(out_dir, exist_ok=True)
    result = {}
    for name in order:
        spec = load_spec(name)
        log = []
        texts = build_files(name, defs, order, plans, log)
        mod_src = os.path.join(ROOT, "mods", name)
        files = {p: t.encode("utf-8") for p, t in texts.items()}
        files["manifest.sii"] = manifest(spec, version_glob).encode("utf-8")
        with open(os.path.join(mod_src, "description.txt"), "rb") as fh:
            files["mod_description.txt"] = fh.read()
        with open(os.path.join(mod_src, "mod_icon.jpg"), "rb") as fh:
            files["mod_icon.jpg"] = fh.read()
        out = os.path.join(out_dir, spec["file"])
        write_scs(out, files)
        result[name] = {"file": out, "spec": spec, "files": files, "log": log,
                        "version_glob": version_glob}
        if verbose:
            print("\n== %s -> %s (%d def files)" % (spec["display_name"], out, len(texts)))
            shown = {}
            for path, key, old, new, owner in log:
                # collapse long lists (engines, countries) to one line per (folder, key, owner)
                folder = path.rsplit("/", 1)[0]
                shown.setdefault((folder, key, owner), []).append((old, new))
            for (folder, key, owner), vals in shown.items():
                olds = sorted({o for o, _ in vals})
                news = sorted({n for _, n in vals})
                rng = olds[0] if len(olds) == 1 else "%d values" % len(olds)
                nrng = news[0] if len(news) == 1 else "%d values" % len(news)
                print("   %-44s %-30s %14s -> %-12s x%-4d %s" % (folder, key, rng, nrng, len(vals), owner))
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default=DEFAULT_GAME)
    ap.add_argument("--install", action="store_true")
    ap.add_argument("--mod-dir", default=DEFAULT_MOD_DIR)
    args = ap.parse_args()
    result = build_all(args.game, os.path.join(ROOT, "build"))
    if args.install:
        if not os.path.isdir(args.mod_dir):
            raise SystemExit("mod folder not found: " + args.mod_dir)
        for r in result.values():
            dst = os.path.join(args.mod_dir, os.path.basename(r["file"]))
            shutil.copyfile(r["file"], dst)
            print("installed:", dst)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except PatchError as e:
        print("BUILD FAILED:", e)
        sys.exit(2)
