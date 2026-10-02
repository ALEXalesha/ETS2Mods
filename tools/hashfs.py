"""Minimal reader for SCS HashFS archives (.scs), versions 1 and 2.

Only uses the Python standard library. Paths are hashed with CityHash64 1.0.x
(see cityhash103.py); directory entries list their children, so the whole
tree can be walked from the root ("").

Usage:
  python hashfs.py info    <archive>
  python hashfs.py ls      <archive> [dir]
  python hashfs.py tree    <archive> [dir]          (recursive listing)
  python hashfs.py extract <archive> <out_dir> <path_or_dir> [...]
  python hashfs.py cat     <archive> <path>

Textures in v2 archives (metadata type "image") are not decoded; this tool
is meant for text/def data.
"""

import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cityhash103 import cityhash64  # noqa: E402

MAGIC = b"SCS#"

# v2 metadata entry types (high byte of the metadata header word)
MD_IMAGE = 1
MD_SAMPLE = 2
MD_MIP_PROXY = 3
MD_INLINE_DIR = 4
MD_PLAIN = 128
MD_DIRECTORY = 129


class HashFsError(Exception):
    pass


class Entry:
    __slots__ = ("hash", "is_dir", "offset", "size", "csize", "compression", "kind")

    def __init__(self, h, is_dir, offset, size, csize, compression, kind="plain"):
        self.hash = h
        self.is_dir = is_dir
        self.offset = offset
        self.size = size
        self.csize = csize
        self.compression = compression  # 0 = stored, 1 = zlib
        self.kind = kind


class HashFs:
    def __init__(self, path):
        self.path = path
        self.f = open(path, "rb")
        hdr = self.f.read(0x40)
        if hdr[:4] != MAGIC:
            raise HashFsError("not a HashFS archive (magic %r)" % hdr[:4])
        self.version, self.salt = struct.unpack_from("<HH", hdr, 4)
        self.hash_method = hdr[8:12]
        if self.hash_method != b"CITY":
            raise HashFsError("unsupported hash method %r" % self.hash_method)
        self.entries = {}
        if self.version == 1:
            self._read_v1(hdr)
        elif self.version == 2:
            self._read_v2(hdr)
        else:
            raise HashFsError("unsupported HashFS version %d" % self.version)

    # ---------------------------------------------------------------- v1
    def _read_v1(self, hdr):
        count, start = struct.unpack_from("<II", hdr, 12)
        self.f.seek(start)
        raw = self.f.read(count * 32)
        for i in range(count):
            h, off, flags, crc, size, csize = struct.unpack_from("<QQIIII", raw, i * 32)
            self.entries[h] = Entry(h, bool(flags & 1), off, size, csize,
                                    1 if flags & 2 else 0)

    # ---------------------------------------------------------------- v2
    def _read_v2(self, hdr):
        (ecount, esize, mcount, msize, estart, mstart, _sec) = struct.unpack_from(
            "<IIIIQQQ", hdr, 12)
        self.f.seek(estart)
        et = zlib.decompress(self.f.read(esize))
        self.f.seek(mstart)
        mt = zlib.decompress(self.f.read(msize))
        if len(et) != ecount * 16:
            raise HashFsError("entry table size mismatch")
        words = struct.unpack("<%dI" % (len(mt) // 4), mt)
        for i in range(ecount):
            h, midx, mcnt, flags = struct.unpack_from("<QIHH", et, i * 16)
            is_dir = bool(flags & 1)
            ent = None
            for j in range(mcnt):
                w = words[midx + j]
                idx, typ = w & 0xFFFFFF, w >> 24
                if typ in (MD_PLAIN, MD_DIRECTORY):
                    a, size, _unk, block = words[idx:idx + 4]
                    csize = a & 0x0FFFFFFF
                    comp = (a >> 28) & 0xF
                    ent = Entry(h, typ == MD_DIRECTORY or is_dir, block * 16,
                                size & 0x0FFFFFFF, csize, comp)
                    break
                if typ == MD_IMAGE:
                    ent = Entry(h, False, 0, 0, 0, 0, kind="image")
            if ent is None:
                ent = Entry(h, is_dir, 0, 0, 0, 0, kind="unknown")
            self.entries[h] = ent

    # ---------------------------------------------------------------- api
    @staticmethod
    def norm(path):
        return path.strip("/").replace("\\", "/")

    def get(self, path):
        return self.entries.get(cityhash64(self.norm(path)))

    def exists(self, path):
        return self.get(path) is not None

    def read_entry(self, e):
        if e.kind != "plain":
            raise HashFsError("entry kind %s cannot be read as plain data" % e.kind)
        self.f.seek(e.offset)
        data = self.f.read(e.csize)
        if e.compression == 0:
            return data
        if e.compression == 1:
            return zlib.decompress(data)
        raise HashFsError("unsupported compression %d" % e.compression)

    def read(self, path):
        e = self.get(path)
        if e is None:
            raise KeyError(path)
        return self.read_entry(e)

    def listdir(self, path=""):
        """Return (dirs, files) names directly under `path`."""
        e = self.get(path)
        if e is None or not e.is_dir:
            raise KeyError("directory not found: %r" % path)
        data = self.read_entry(e)
        dirs, files = [], []
        if self.version == 1:
            for line in data.decode("utf-8", "replace").splitlines():
                if not line:
                    continue
                (dirs if line.startswith("*") else files).append(line.lstrip("*"))
        else:
            (n,) = struct.unpack_from("<I", data, 0)
            lens = data[4:4 + n]
            p = 4 + n
            for ln in lens:
                name = data[p:p + ln].decode("utf-8", "replace")
                p += ln
                (dirs if name.startswith("/") else files).append(name.lstrip("/"))
        return dirs, files

    def walk(self, path=""):
        """Yield every file path (no leading slash) under `path`."""
        base = self.norm(path)
        try:
            dirs, files = self.listdir(base)
        except KeyError:
            return
        for fn in files:
            yield (base + "/" + fn) if base else fn
        for d in dirs:
            yield from self.walk((base + "/" + d) if base else d)


def _out(path_out, data):
    os.makedirs(os.path.dirname(path_out) or ".", exist_ok=True)
    with open(path_out, "wb") as fh:
        fh.write(data)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd, arc = argv[0], argv[1]
    fs = HashFs(arc)
    if cmd == "info":
        kinds = {}
        for e in fs.entries.values():
            kinds[e.kind] = kinds.get(e.kind, 0) + 1
        print("version", fs.version, "salt", fs.salt, "entries", len(fs.entries), kinds)
    elif cmd == "ls":
        d, f = fs.listdir(argv[2] if len(argv) > 2 else "")
        for x in d:
            print(x + "/")
        for x in f:
            print(x)
    elif cmd == "tree":
        for p in fs.walk(argv[2] if len(argv) > 2 else ""):
            print(p)
    elif cmd == "cat":
        sys.stdout.buffer.write(fs.read(argv[2]))
    elif cmd == "extract":
        out = argv[2]
        for target in argv[3:]:
            e = fs.get(target)
            if e is None:
                print("missing:", target)
                continue
            paths = list(fs.walk(target)) if e.is_dir else [fs.norm(target)]
            for p in paths:
                ent = fs.get(p)
                if ent is None or ent.kind != "plain":
                    continue
                _out(os.path.join(out, p), fs.read_entry(ent))
                print(p)
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
