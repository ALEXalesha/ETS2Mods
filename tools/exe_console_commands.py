"""List the console commands compiled into eurotrucks2.exe and whether the game registers them.

Why: in 1.61 `cheat money ...` answers "unknown command". This script shows that
the `cheat` command exists in the exe but no code ever registers it, so no cvar
or launch option can turn it on.

How it works (static analysis, the game is not started):
  - a command descriptor in .data looks like
      node+0x00 next, node+0x08 prev, node+0x10 name ptr (.rdata),
      node+0x18 handler ptr (.text), node+0x20 0xFFFFFFFF
  - registration code loads the node address with `lea reg, [rip+disp32]`;
  - a descriptor with no such reference is never added to the command list.

Usage: python tools/exe_console_commands.py [name ...]
Needs pefile (pip install pefile).
"""

import os
import re
import struct
import sys

import pefile

EXE = r"C:\Program Files (x86)\Steam\steamapps\common\Euro Truck Simulator 2\bin\win_x64\eurotrucks2.exe"


def main(argv):
    exe = os.environ.get("ETS2_EXE", EXE)
    pe = pefile.PE(exe, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    secs = {s.Name.rstrip(b"\0").decode(): s for s in pe.sections}
    text, rdata, dsec = secs[".text"], secs[".rdata"], secs[".data"]
    tdata, tva = text.get_data(), text.VirtualAddress
    raw = open(exe, "rb").read()

    lea_targets = {}
    for m in re.finditer(rb"[\x48\x4c]\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]", tdata):
        i = m.start()
        tgt = tva + i + 7 + struct.unpack_from("<i", tdata, i + 3)[0]
        lea_targets[tgt] = lea_targets.get(tgt, 0) + 1

    t_lo, t_hi = base + tva, base + tva + text.Misc_VirtualSize
    r_lo, r_hi = base + rdata.VirtualAddress, base + rdata.VirtualAddress + rdata.Misc_VirtualSize

    def cstr(va):
        off = pe.get_offset_from_rva(va - base)
        s = raw[off:raw.find(b"\0", off, off + 64)]
        try:
            s = s.decode("ascii")
        except UnicodeDecodeError:
            return None
        return s if s and all(c.isalnum() or c in "_." for c in s) else None

    dd, dva = dsec.get_data(), dsec.VirtualAddress
    rows = []
    for i in range(0, len(dd) - 0x28, 8):
        name, func, flag = struct.unpack_from("<QQQ", dd, i)
        if r_lo <= name < r_hi and t_lo <= func < t_hi and flag == 0xFFFFFFFF:
            n = cstr(name)
            if n:
                node = dva + i - 0x10
                rows.append((n, node, lea_targets.get(node, 0)))
    want = set(argv)
    for n, node, k in sorted(rows):
        if not want or n in want:
            print("%-28s %s" % (n, "registered" if k else "NOT REGISTERED"))
    print("descriptors: %d, not registered: %d" % (len(rows), sum(1 for r in rows if not r[2])))


if __name__ == "__main__":
    main(sys.argv[1:])
