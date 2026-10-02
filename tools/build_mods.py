"""Build the ETS2 mods from the game's own def files.

The repository does not contain SCS's original files. This script reads them
from the installed game (def.scs), applies the small value changes listed in
mods/<name>/mod.json and packs each mod as a .scs (plain zip, stored).

Every change must match exactly the expected number of lines. If a game
update renames or removes a parameter, the build stops with an error instead
of producing a broken mod.

Usage:
  python tools/build_mods.py [--game DIR] [--install]

  --install   also copy the built .scs files to
              %USERPROFILE%\\Documents\\Euro Truck Simulator 2\\mod
"""

import argparse
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


def apply_patch(text, patch, mod_name, log, path):
    if "insert_after" in patch:
        absent = patch.get("absent_key")
        if absent and re.search(LINE_RE.format(key=key_regex(absent)), text, re.M):
            raise PatchError("%s: %s already set in %s" % (mod_name, absent, path))
        anchor = patch["insert_after"]
        if text.count(anchor) != 1:
            raise PatchError("%s: anchor %r found %d times in %s"
                             % (mod_name, anchor, text.count(anchor), path))
        line = patch["line"]
        log.append((path, line.strip().split(":")[0], "(not set)", line.split(":", 1)[1].split("#")[0].strip()))
        return text.replace(anchor, anchor + "\n" + line, 1)

    key, value = patch["key"], patch["value"]
    want = patch.get("count", 1)
    rx = re.compile(LINE_RE.format(key=key_regex(key)), re.M)
    found = []

    def repl(m):
        old = m.group("val")
        comment = (m.group("comment") or "").lstrip("#").strip()
        found.append((m.group("key"), old))
        note = "# %s[mod %s: was %s]" % (comment + " " if comment else "", mod_name, old)
        return "%s%s: %s\t%s" % (m.group("indent"), m.group("key"), value, note)

    new_text = rx.sub(repl, text)
    if len(found) != want:
        raise PatchError("%s: key %s matched %d lines in %s, expected %d"
                         % (mod_name, key, len(found), path, want))
    for k, old in found:
        log.append((path, k, old, value))
    return new_text


def load_spec(name):
    with open(os.path.join(ROOT, "mods", name, "mod.json"), encoding="utf-8") as fh:
        return json.load(fh)


def build_files(name, spec, defs, log):
    """Return {archive_path: text} for one mod."""
    plan = {}
    for src_mod, path in spec.get("inherit", []):
        for p in load_spec(src_mod)["patches"][path]:
            plan.setdefault(path, []).append((src_mod, p))
    for path, patches in spec["patches"].items():
        for p in patches:
            plan.setdefault(path, []).append((spec["package"], p))
    out = {}
    for path, patches in plan.items():
        text = defs.read(path).decode("utf-8")
        for owner, p in patches:
            text = apply_patch(text, p, owner if owner == spec["package"] else load_spec(owner)["package"],
                               log, path)
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
    """files: {archive_path: bytes}. Plain zip, stored (no compression)."""
    dirs = set()
    for p in files:
        parts = p.split("/")[:-1]
        for i in range(1, len(parts) + 1):
            dirs.add("/".join(parts[:i]) + "/")
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_STORED) as z:
        for d in sorted(dirs):
            z.writestr(zipfile.ZipInfo(d, date_time=(2026, 1, 1, 0, 0, 0)), b"")
        for p in sorted(files):
            zi = zipfile.ZipInfo(p, date_time=(2026, 1, 1, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_STORED
            z.writestr(zi, files[p])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default=DEFAULT_GAME)
    ap.add_argument("--install", action="store_true")
    ap.add_argument("--mod-dir", default=DEFAULT_MOD_DIR)
    args = ap.parse_args()

    version = game_version(args.game)
    major_minor = ".".join(version.split(".")[:2])
    version_glob = major_minor + ".*"
    print("game version:", version, "-> compatible_versions", version_glob)

    defs = HashFs(os.path.join(args.game, "def.scs"))
    build_dir = os.path.join(ROOT, "build")
    os.makedirs(build_dir, exist_ok=True)
    built = []
    for name in sorted(os.listdir(os.path.join(ROOT, "mods"))):
        if not os.path.isfile(os.path.join(ROOT, "mods", name, "mod.json")):
            continue
        spec = load_spec(name)
        log = []
        texts = build_files(name, spec, defs, log)
        mod_src = os.path.join(ROOT, "mods", name)
        files = {p: t.encode("utf-8") for p, t in texts.items()}
        files["manifest.sii"] = manifest(spec, version_glob).encode("utf-8")
        with open(os.path.join(mod_src, "description.txt"), "rb") as fh:
            files["mod_description.txt"] = fh.read()
        with open(os.path.join(mod_src, "mod_icon.jpg"), "rb") as fh:
            files["mod_icon.jpg"] = fh.read()
        out = os.path.join(build_dir, spec["file"])
        write_scs(out, files)
        built.append(out)
        print("\n== %s -> %s" % (spec["display_name"], out))
        for path, key, old, new in log:
            print("   %-36s %-32s %10s -> %s" % (path, key, old, new))

    if args.install:
        if not os.path.isdir(args.mod_dir):
            raise SystemExit("mod folder not found: " + args.mod_dir)
        for out in built:
            dst = os.path.join(args.mod_dir, os.path.basename(out))
            shutil.copyfile(out, dst)
            print("installed:", dst)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except PatchError as e:
        print("BUILD FAILED:", e)
        sys.exit(2)
