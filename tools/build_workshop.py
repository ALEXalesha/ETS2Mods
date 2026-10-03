"""Prepare Steam Workshop folders for the SCS Workshop Uploader (nothing is uploaded).

  .venv\\Scripts\\python tools\\build_workshop.py [--out workshop]

Built from the same sources as the local .scs mods (tools/build_mods.py), with
neutral names (family prefix "OpenRoad"). Layout per mod, following the SCS
modding wiki (SCS Workshop Uploader: validation rules):

  workshop/NN_OpenRoad_<Name>/
      upload/                  <- pick THIS folder in the uploader
          versions.sii         one universal version
          universal/
              manifest.sii     mod_package with display_name, author, category, icon, ...
              mod_icon.jpg     276x162 JPG, < 1 MB
              mod_description.txt   UTF-8, EN + RU
              def/...          the changed def files
      preview.jpg              640x360 Workshop preview image, < 1 MB
      steam_page.txt           title, type tag, visibility, page text to paste

Rules applied from the wiki: the upload root holds only versions.sii and the
version package; every .sii starts with "SiiNunit" (the BOM of the stock
economy_data.sii is removed); only referenced .txt/.jpg files; no .scs inside.
NN is the recommended load order (01 = top of the Mod Manager list).
"""

import argparse
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_mods  # noqa: E402

ROOT = build_mods.ROOT
FAMILY = "OpenRoad"
AUTHOR = "OpenRoad"
BOM = b"\xef\xbb\xbf"


def ws(name):
    with open(os.path.join(ROOT, "mods", name, "workshop.json"), encoding="utf-8") as fh:
        return json.load(fh)


def package_name(name):
    return "openroad_" + name


def folder_name(i, name):
    return "%02d_%s" % (i + 1, ws(name)["title"].replace(": ", "_").replace(" & ", "_and_").replace(" ", "_"))


def neutral_text(data, order):
    for n in order:
        data = data.replace(("alexey_" + n).encode(), package_name(n).encode())
    return data


def order_lines(order, lang):
    replaces = build_mods.load_replaces()
    out = []
    for i, n in enumerate(order):
        line = "%d. %s" % (i + 1, ws(n)["title"])
        if any(n in v for v in replaces.values()):
            line += " (off when Hyper Power is on)" if lang == "en" else " (выключить, если включён Hyper Power)"
        out.append(line)
    return out


def description(name, order, version_glob):
    w = ws(name)
    ver = version_glob.rstrip(".*")
    en = ["[orange]%s[normal]" % w["title"], ""] + w["en"] + [
        "",
        "Load order in the Mod Manager (top = highest priority). Mods of this family that change the same file "
        "already carry the changes of the ones below them:",
    ] + order_lines(order, "en") + [
        "",
        "Compatibility: game version %s (built from the %s game files), single player only. "
        "Not for TruckersMP or Convoy. After a big game update the mod may need an update." % (ver, ver),
    ]
    ru = ["", "-----", "[orange]%s[normal]" % w["title"], ""] + w["ru"] + [
        "",
        "Порядок в Менеджере модов (верхний - главный). Моды этой серии, меняющие один и тот же файл, "
        "уже несут правки тех, что ниже:",
    ] + order_lines(order, "ru") + [
        "",
        "Совместимость: версия игры %s (собрано из файлов %s), только одиночная игра. "
        "Не для TruckersMP и Конвоя. После крупного обновления игры мод может потребовать обновления." % (ver, ver),
    ]
    return "\n".join(en + ru) + "\n"


def manifest(spec):
    # No display_name and no compatible_versions: the SCS Workshop Uploader rejects
    # compatible_versions in Workshop packages (ERROR 00010, versions come from versions.sii)
    # and warns on display_name (WARN 00002, the name comes from the Steam page).
    # The local .scs builds (build_mods.py) keep both, the game's mod manager needs them.
    return (
        "SiiNunit\n{\n"
        "mod_package : .package_name\n{\n"
        '\tpackage_version: "%s"\n'
        '\tauthor: "%s"\n'
        '\tcategory[]: "%s"\n'
        '\ticon: "mod_icon.jpg"\n'
        '\tdescription_file: "mod_description.txt"\n'
        "}\n}\n"
    ) % (spec["version"], AUTHOR, spec["category"])


VERSIONS_SII = (
    "SiiNunit\n{\n"
    "package_version_info : .universal\n{\n"
    '\tpackage_name: "universal"\n'
    "}\n}\n"
)


def steam_page(name, desc_text):
    w = ws(name)
    bb = desc_text.replace("[orange]", "[b]").replace("[normal]", "[/b]")
    return (
        "TITLE (Mod name):\n%s\n\n"
        "VISIBILITY: Private for the first test, then Friends only or Public\n"
        "TYPE TAG: %s\n"
        "PREVIEW IMAGE: preview.jpg (640x360)\n"
        "MOD DATA FOLDER: upload\n\n"
        "DESCRIPTION (paste, at least 50 characters):\n%s"
    ) % (w["title"], w["type_tag"], bb)


def draw_images(name, spec, out_icon, out_preview):
    from PIL import Image, ImageDraw, ImageFont
    bold = r"C:\Windows\Fonts\segoeuib.ttf"
    reg = r"C:\Windows\Fonts\segoeui.ttf"
    w = ws(name)
    bg = tuple(spec["icon"]["bg"])
    accent = tuple(spec["icon"]["accent"])

    def fit(d, text, path, max_w, start):
        size = start
        while size > 10:
            f = ImageFont.truetype(path, size)
            if d.textlength(text, font=f) <= max_w:
                return f
            size -= 1
        return ImageFont.truetype(path, 10)

    def canvas(W, H):
        img = Image.new("RGB", (W, H), bg)
        d = ImageDraw.Draw(img)
        for y in range(H):
            k = 1.0 - 0.45 * y / H
            d.line([(0, y), (W, y)], fill=tuple(int(c * k) for c in bg))
        # simple road in perspective along the bottom
        road_top = int(H * 0.74)
        d.polygon([(W * 0.42, road_top), (W * 0.58, road_top), (W * 0.95, H), (W * 0.05, H)], fill=(30, 30, 34))
        for i in range(6):
            t0 = i / 6.0
            t1 = t0 + 0.08
            y0 = road_top + (H - road_top) * t0
            y1 = road_top + (H - road_top) * t1
            w0 = 2 + 6 * t0
            w1 = 2 + 6 * t1
            d.polygon([(W / 2 - w0, y0), (W / 2 + w0, y0), (W / 2 + w1, y1), (W / 2 - w1, y1)], fill=accent)
        return img, d

    # icon 276x162
    img, d = canvas(276, 162)
    d.rectangle([0, 0, 275, 161], outline=accent, width=3)
    d.text((10, 6), FAMILY.upper(), font=ImageFont.truetype(bold, 12), fill=(255, 255, 255))
    ft = fit(d, w["short"], bold, 250, 40)
    d.text(((276 - d.textlength(w["short"], font=ft)) / 2, 28), w["short"], font=ft, fill=accent)
    fs = fit(d, w["tag_en"], reg, 240, 18)
    d.text(((276 - d.textlength(w["tag_en"], font=fs)) / 2, 76), w["tag_en"], font=fs, fill=(255, 255, 255))
    img.save(out_icon, "JPEG", quality=90)

    # preview 640x360
    img, d = canvas(640, 360)
    d.rectangle([0, 0, 639, 359], outline=accent, width=6)
    d.text((24, 16), FAMILY.upper(), font=ImageFont.truetype(bold, 26), fill=(255, 255, 255))
    ft = fit(d, w["short"], bold, 590, 92)
    d.text(((640 - d.textlength(w["short"], font=ft)) / 2, 52), w["short"], font=ft, fill=accent)
    for j, line in enumerate((w["tag_en"], w["tag_ru"])):
        fs = fit(d, line, reg, 560, 34)
        d.text(((640 - d.textlength(line, font=fs)) / 2, 150 + j * 40), line, font=fs, fill=(255, 255, 255))
    img.save(out_preview, "JPEG", quality=88)


def to_recycle_bin(path):
    """Move a folder to the Windows Recycle Bin (not a permanent delete)."""
    import subprocess
    ps = ("Add-Type -AssemblyName Microsoft.VisualBasic; "
          "[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory('%s', "
          "'OnlyErrorDialogs', 'SendToRecycleBin')" % os.path.abspath(path).replace("'", "''"))
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
    if os.path.exists(path):
        raise RuntimeError("could not move %s to the Recycle Bin" % path)


def build(out_dir, verbose=True):
    tmp = tempfile.mkdtemp(prefix="ets2ws_")
    res = build_mods.build_all(build_mods.DEFAULT_GAME, tmp, verbose=False)
    order = build_mods.load_order()
    if os.path.isdir(out_dir) and os.listdir(out_dir):
        to_recycle_bin(out_dir)         # never a permanent delete
    os.makedirs(out_dir, exist_ok=True)
    folders = []
    for i, name in enumerate(order):
        r = res[name]
        spec = r["spec"]
        base = os.path.join(out_dir, folder_name(i, name))
        uni = os.path.join(base, "upload", "universal")
        os.makedirs(uni)
        with open(os.path.join(base, "upload", "versions.sii"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(VERSIONS_SII)
        for path, data in r["files"].items():
            if not path.startswith("def/"):
                continue
            if data.startswith(BOM):
                data = data[len(BOM):]
            data = neutral_text(data, order)
            dst = os.path.join(uni, *path.split("/"))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "wb") as fh:
                fh.write(data)
        with open(os.path.join(uni, "manifest.sii"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(manifest(spec))
        desc = description(name, order, r["version_glob"])
        with open(os.path.join(uni, "mod_description.txt"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(desc)
        draw_images(name, spec, os.path.join(uni, "mod_icon.jpg"), os.path.join(base, "preview.jpg"))
        with open(os.path.join(base, "steam_page.txt"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(steam_page(name, desc))
        folders.append(base)
        if verbose:
            print(base)
    return folders


def release_assets(folders, out_dir):
    """Neutral .scs per mod (the universal folder zipped, stored) and one zip of all
    Workshop folders - the files attached to a release."""
    import zipfile
    os.makedirs(out_dir, exist_ok=True)
    assets = []
    for base in folders:
        uni = os.path.join(base, "upload", "universal")
        name = os.path.basename(base).split("_", 1)[1]          # drop the NN_ order prefix
        scs = os.path.join(out_dir, name + ".scs")
        with zipfile.ZipFile(scs, "w", zipfile.ZIP_STORED) as z:
            for dp, _dn, fn in os.walk(uni):
                for f in sorted(fn):
                    full = os.path.join(dp, f)
                    z.write(full, os.path.relpath(full, uni).replace("\\", "/"))
        assets.append(scs)
    allzip = os.path.join(out_dir, "OpenRoad_Workshop_Folders.zip")
    with zipfile.ZipFile(allzip, "w", zipfile.ZIP_DEFLATED) as z:
        for base in folders:
            for dp, _dn, fn in os.walk(base):
                for f in sorted(fn):
                    full = os.path.join(dp, f)
                    z.write(full, os.path.relpath(full, os.path.dirname(base)).replace("\\", "/"))
    assets.append(allzip)
    return assets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "workshop"))
    ap.add_argument("--release", default=os.path.join(ROOT, "release"),
                    help="where to put the release .scs files and the Workshop zip")
    a = ap.parse_args()
    folders = build(a.out)
    if os.path.isdir(a.release) and os.listdir(a.release):
        to_recycle_bin(a.release)
    for f in release_assets(folders, a.release):
        print("asset:", f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
