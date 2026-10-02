"""Draw mod_icon.jpg (276x162, the size the ETS2 mod manager shows) for every mod.

Needs Pillow (installed in the project venv):
  .venv\\Scripts\\python tools\\make_icons.py
"""

import json
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 276, 162
FONT_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
FONT_REG = r"C:\Windows\Fonts\segoeui.ttf"


def fit_font(draw, text, path, max_w, start):
    size = start
    while size > 10:
        f = ImageFont.truetype(path, size)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 1
    return ImageFont.truetype(path, size)


def stripes(draw, color):
    # diagonal road-marking stripes along the bottom edge
    for x in range(-40, W + 40, 28):
        draw.polygon([(x, H - 14), (x + 14, H - 14), (x + 24, H), (x + 10, H)], fill=color)


def draw_icon(spec, out_path):
    bg = tuple(spec["bg"])
    accent = tuple(spec["accent"])
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    # soft vertical gradient
    for y in range(H):
        k = 1.0 - 0.35 * y / H
        d.line([(0, y), (W, y)], fill=tuple(int(c * k) for c in bg))
    d.rectangle([0, 0, W - 1, H - 1], outline=accent, width=3)
    stripes(d, accent)
    title = spec["title"]
    sub = spec["subtitle"]
    ft = fit_font(d, title, FONT_BOLD, W - 30, 44)
    fs = fit_font(d, sub, FONT_REG, W - 40, 22)
    tw = d.textlength(title, font=ft)
    sw = d.textlength(sub, font=fs)
    d.text(((W - tw) / 2, 34), title, font=ft, fill=accent)
    d.text(((W - sw) / 2, 92), sub, font=fs, fill=(255, 255, 255))
    d.text((10, 6), "ETS2", font=ImageFont.truetype(FONT_BOLD, 13), fill=(255, 255, 255))
    img.save(out_path, "JPEG", quality=92)


def main():
    mods_dir = os.path.join(ROOT, "mods")
    for name in sorted(os.listdir(mods_dir)):
        spec_path = os.path.join(mods_dir, name, "mod.json")
        if not os.path.isfile(spec_path):
            continue
        with open(spec_path, encoding="utf-8") as fh:
            spec = json.load(fh)
        out = os.path.join(mods_dir, name, "mod_icon.jpg")
        draw_icon(spec["icon"], out)
        print("icon:", out)


if __name__ == "__main__":
    main()
