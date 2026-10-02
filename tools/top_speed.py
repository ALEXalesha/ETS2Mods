"""Estimate the gear-limited top speed from the real transmission and engine defs.

  python tools/top_speed.py            stock values vs. build/alexey_hyper_power.scs

v = rpm / 60 * 2*pi*r / (lowest forward ratio * differential_ratio)
r = 0.506 m: 315/70 R22.5 tyre (rim 22.5" = 0.5715 m, sidewall 0.315*0.70 m), the
size named by the stock tyre defs (e.g. "@@rtire_315_70_trailmaster@@").
rpm = where the engine's torque curve ends (its last torque_curve point).
Air drag check uses physics.sii: force = air_resistance * v^2, so power = a * v^3.
"""

import math
import os
import re
import statistics
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_mods  # noqa: E402

R = 0.506


def num(text, key):
    return [float(v) for v in re.findall(r"^\s*%s\s*:\s*([\d.]+)" % re.escape(key), text, re.M)]


def overall_ratios(read, paths):
    out = []
    for p in paths:
        t = read(p)
        fw = [float(v) for v in re.findall(r"^\s*ratios_forward\[\d+\]\s*:\s*([\d.]+)", t, re.M)]
        dr = num(t, "differential_ratio")
        if fw and dr:
            out.append(min(fw) * dr[0])
    return out


def kmh(rpm, ratio):
    return rpm / 60.0 * 2 * math.pi * R / ratio * 3.6


def main():
    defs = build_mods.LayeredFs(build_mods.DEFAULT_GAME)
    trans = build_mods.expand_path(defs, "def/vehicle/truck/*/transmission/*.sii", "accessory_transmission_data")
    engines = build_mods.expand_path(defs, "def/vehicle/truck/*/engine/*.sii", "accessory_engine_data")
    stock_read = lambda p: defs.read(p).decode("utf-8")  # noqa: E731
    curve_end = []
    for p in engines:
        pts = re.findall(r"^\s*torque_curve\[\]\s*:\s*\(\s*([\d.]+)", stock_read(p), re.M)
        if pts:
            curve_end.append(max(float(x) for x in pts))
    rpm = statistics.median(curve_end)
    print("engines: %d, torque curve ends at %d..%d rpm (median %d)" % (len(engines), min(curve_end), max(curve_end), rpm))

    rows = [("stock", stock_read)]
    hp = os.path.join(build_mods.ROOT, "build", "alexey_hyper_power.scs")
    if os.path.isfile(hp):
        z = zipfile.ZipFile(hp)
        rows.append(("Hyper Power", lambda p: z.read(p).decode("utf-8")))
    for label, read in rows:
        ov = overall_ratios(read, trans)
        best, med, worst = min(ov), statistics.median(ov), max(ov)
        print("%-12s %d gearboxes, top-gear overall ratio %.3f / %.3f / %.3f (best / median / worst)"
              % (label, len(ov), best, med, worst))
        print("             gear-limited top speed at %d rpm: %.0f / %.0f / %.0f km/h"
              % (rpm, kmh(rpm, best), kmh(rpm, med), kmh(rpm, worst)))
        phys = read("def/vehicle/physics.sii") if label != "stock" else stock_read("def/vehicle/physics.sii")
        a = num(phys, "air_resistance")[0]
        v = kmh(rpm, med) / 3.6
        print("             air drag at the median top speed: a=%.2f -> %.0f kW" % (a, a * v ** 3 / 1000))


if __name__ == "__main__":
    main()
