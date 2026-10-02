"""Read and patch ETS2 save files (game.sii): ScsC (encrypted), BSII (binary) and text.

ScsC: "ScsC", 32-byte HMAC, 16-byte IV, u32 plain size, AES-256-CBC data that is
zlib-compressed. The key below is the one public tools (SII_Decrypt) use; it is
verified at run time: decryption must give valid zlib data of exactly the size
stored in the header.

BSII: "BSII", u32 version, then blocks. Block type 0 defines a structure
(field names and types), any other block type is a unit of that structure.
This reader walks every block and must end exactly at the end marker, so a
wrong guess about a value type stops with an error instead of silently
producing garbage.
"""

import struct
import zlib

SCSC_KEY = bytes([
    0x2A, 0x5F, 0xCB, 0x17, 0x91, 0xD2, 0x2F, 0xB6, 0x02, 0x45, 0xB3, 0xD8, 0x36, 0x9E, 0xD0, 0xB2,
    0xC2, 0x73, 0x71, 0x56, 0x3F, 0xBF, 0x1F, 0x3C, 0x9E, 0xDF, 0x6B, 0x11, 0x82, 0x5A, 0x5D, 0x0A,
])


class SiiError(Exception):
    pass


def decrypt_scsc(blob):
    try:
        from Crypto.Cipher import AES
    except ImportError as e:  # pragma: no cover
        raise SiiError("pycryptodome is needed for encrypted saves (pip install pycryptodome)") from e
    if blob[:4] != b"ScsC":
        raise SiiError("not a ScsC file")
    iv = blob[36:52]
    size = struct.unpack_from("<I", blob, 52)[0]
    dec = AES.new(SCSC_KEY, AES.MODE_CBC, iv).decrypt(blob[56:])
    raw = zlib.decompress(dec)
    if len(raw) != size:
        raise SiiError("ScsC size mismatch: %d != %d" % (len(raw), size))
    return raw


def load_plain(blob):
    """Return the decrypted file content (BSII bytes or text bytes)."""
    if blob[:4] == b"ScsC":
        return decrypt_scsc(blob)
    return blob


# ------------------------------------------------------------------ BSII

# value type -> fixed element size in bytes (scalars); arrays are 0x?? + 1 with u32 count
FIXED = {
    0x03: 8,    # token
    0x05: 4,    # float
    0x07: 8,    # float2
    0x09: 12,   # float3
    0x11: 12,   # int3
    0x17: 16,   # float4 (quaternion)
    0x25: 4,    # s32
    0x27: 4,    # u32
    0x29: 2,    # s16
    0x2B: 2,    # u16
    0x2F: 4,    # u32 (variant)
    0x31: 8,    # s64
    0x33: 8,    # u64
    0x35: 1,    # bool
    0x37: 4,    # ordinal string index
}
FIXED_ARRAY = {t + 1: s for t, s in FIXED.items() if t not in (0x2F, 0x37)}
ID_TYPES = (0x39, 0x3B, 0x3D)
ID_ARRAY_TYPES = (0x3A, 0x3C, 0x3E)


class Reader:
    def __init__(self, data, pos=0):
        self.d = data
        self.p = pos

    def u8(self):
        v = self.d[self.p]
        self.p += 1
        return v

    def u32(self):
        v = struct.unpack_from("<I", self.d, self.p)[0]
        self.p += 4
        return v

    def u64(self):
        v = struct.unpack_from("<Q", self.d, self.p)[0]
        self.p += 8
        return v

    def s64(self):
        v = struct.unpack_from("<q", self.d, self.p)[0]
        self.p += 8
        return v

    def string(self):
        n = self.u32()
        s = self.d[self.p:self.p + n]
        self.p += n
        return s.decode("utf-8", "replace")

    def skip(self, n):
        self.p += n


TOKEN_CHARS = "0123456789abcdefghijklmnopqrstuvwxyz_"


def decode_token(v):
    out = []
    while v:
        v, r = divmod(v, 38)
        out.append(TOKEN_CHARS[r - 1] if r else "?")
    return "".join(out)


def read_id(r):
    n = r.u8()
    if n == 0xFF:
        return "_nameless.%x" % r.u64()
    return ".".join(decode_token(r.u64()) for _ in range(n))


class Bsii:
    def __init__(self, data):
        if data[:4] != b"BSII":
            raise SiiError("not BSII")
        self.data = data
        self.version = struct.unpack_from("<I", data, 4)[0]
        self.structs = {}   # id -> (name, [(type, field_name)])
        self.units = []     # (struct_name, unit_id, {field: (type, offset)})
        self._parse()

    def _skip_value(self, r, t, offsets=None, name=None):
        start = r.p
        if t in FIXED:
            r.skip(FIXED[t])
        elif t in FIXED_ARRAY:
            r.skip(FIXED_ARRAY[t] * r.u32())
        elif t == 0x01:
            r.string()
        elif t == 0x02:
            for _ in range(r.u32()):
                r.string()
        elif t == 0x19:
            r.skip(self._vec8_size())
        elif t == 0x1A:
            r.skip(self._vec8_size() * r.u32())
        elif t in ID_TYPES:
            read_id(r)
        elif t in ID_ARRAY_TYPES:
            for _ in range(r.u32()):
                read_id(r)
        else:
            raise SiiError("unknown BSII value type 0x%02X (field %s) at %d" % (t, name, start))
        if offsets is not None:
            offsets[name] = (t, start)

    def _vec8_size(self):
        # version 1: 8 floats; versions 2+: 3 floats position + 4 floats rotation = 28? Detected below.
        return self._v8

    def _parse(self):
        # vec8 size differs between format versions; try the candidates and keep the one that parses.
        last = None
        for v8 in ((32,) if self.version == 1 else (32, 28, 36)):
            self._v8 = v8
            try:
                self._parse_once()
                return
            except (SiiError, struct.error, IndexError, KeyError) as e:
                last = e
        raise SiiError("BSII parse failed: %s" % last)

    def _parse_once(self):
        self.structs = {}
        self.units = []
        r = Reader(self.data, 8)
        while True:
            bt = r.u32()
            if bt == 0:
                valid = r.u8()
                if not valid:
                    if r.p != len(self.data):
                        raise SiiError("end marker at %d, file size %d" % (r.p, len(self.data)))
                    return
                sid = r.u32()
                sname = r.string()
                fields = []
                while True:
                    t = r.u32()
                    if t == 0:
                        break
                    fname = r.string()
                    if t == 0x37:
                        for _ in range(r.u32()):
                            r.u32()
                            r.string()
                    fields.append((t, fname))
                self.structs[sid] = (sname, fields)
            else:
                if bt not in self.structs:
                    raise SiiError("unit of undefined structure %d at %d" % (bt, r.p - 4))
                sname, fields = self.structs[bt]
                uid = read_id(r)
                offsets = {}
                for t, fname in fields:
                    self._skip_value(r, t, offsets, fname)
                self.units.append((sname, uid, offsets))

    def find(self, struct_name):
        return [u for u in self.units if u[0] == struct_name]
