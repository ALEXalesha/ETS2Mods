"""Pure Python CityHash64, version 1.0.x (the variant SCS HashFS uses).

The `cityhash` package on PyPI implements CityHash 1.1, which gives different
results for most inputs, so HashFS path lookups need this older variant.
"""

M = 0xFFFFFFFFFFFFFFFF
k0 = 0xC3A5C85C97CB3127
k1 = 0xB492B66FBE98F273
k2 = 0x9AE16A3B2F90404F
k3 = 0xC949D7C7509E6557
KMUL = 0x9DDFEA08EB382D69


def _f64(s, i):
    return int.from_bytes(s[i:i + 8], "little")


def _f32(s, i):
    return int.from_bytes(s[i:i + 4], "little")


def _rot(v, sh):
    return v if sh == 0 else ((v >> sh) | (v << (64 - sh))) & M


def _rot1(v, sh):
    return ((v >> sh) | (v << (64 - sh))) & M


def _smix(v):
    return v ^ (v >> 47)


def _h16(u, v):
    a = ((u ^ v) * KMUL) & M
    a ^= a >> 47
    b = ((v ^ a) * KMUL) & M
    b ^= b >> 47
    return (b * KMUL) & M


def _len0to16(s, n):
    if n > 8:
        a = _f64(s, 0)
        b = _f64(s, n - 8)
        return _h16(a, _rot1((b + n) & M, n)) ^ b
    if n >= 4:
        a = _f32(s, 0)
        return _h16((n + (a << 3)) & M, _f32(s, n - 4))
    if n > 0:
        a, b, c = s[0], s[n >> 1], s[n - 1]
        y = (a + (b << 8)) & 0xFFFFFFFF
        z = (n + (c << 2)) & 0xFFFFFFFF
        return (_smix(((y * k2) ^ (z * k3)) & M) * k2) & M
    return k2


def _len17to32(s, n):
    a = (_f64(s, 0) * k1) & M
    b = _f64(s, 8)
    c = (_f64(s, n - 8) * k2) & M
    d = (_f64(s, n - 16) * k0) & M
    return _h16((_rot((a - b) & M, 43) + _rot(c, 30) + d) & M,
                (a + _rot(b ^ k3, 20) - c + n) & M)


def _weak(w, x, y, z, a, b):
    a = (a + w) & M
    b = _rot((b + a + z) & M, 21)
    c = a
    a = (a + x + y) & M
    b = (b + _rot(a, 44)) & M
    return (a + z) & M, (b + c) & M


def _weak_s(s, i, a, b):
    return _weak(_f64(s, i), _f64(s, i + 8), _f64(s, i + 16), _f64(s, i + 24), a, b)


def _len33to64(s, n):
    z = _f64(s, 24)
    a = (_f64(s, 0) + (n + _f64(s, n - 16)) * k0) & M
    b = _rot((a + z) & M, 52)
    c = _rot(a, 37)
    a = (a + _f64(s, 8)) & M
    c = (c + _rot(a, 7)) & M
    a = (a + _f64(s, 16)) & M
    vf = (a + z) & M
    vs = (b + _rot(a, 31) + c) & M
    a = (_f64(s, 16) + _f64(s, n - 32)) & M
    z = _f64(s, n - 8)
    b = _rot((a + z) & M, 52)
    c = _rot(a, 37)
    a = (a + _f64(s, n - 24)) & M
    c = (c + _rot(a, 7)) & M
    a = (a + _f64(s, n - 16)) & M
    wf = (a + z) & M
    ws = (b + _rot(a, 31) + c) & M
    r = _smix(((vf + ws) * k2 + (wf + vs) * k0) & M)
    return (_smix((r * k0 + vs) & M) * k2) & M


def cityhash64(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    s = data
    n = len(s)
    if n <= 32:
        return _len0to16(s, n) if n <= 16 else _len17to32(s, n)
    if n <= 64:
        return _len33to64(s, n)
    x = _f64(s, 0)
    y = _f64(s, n - 16) ^ k1
    z = _f64(s, n - 56) ^ k0
    v = _weak_s(s, n - 64, n, y)
    w = _weak_s(s, n - 32, (n * k1) & M, k0)
    z = (z + _smix(v[1]) * k1) & M
    x = (_rot((z + x) & M, 39) * k1) & M
    y = (_rot(y, 33) * k1) & M
    rem = (n - 1) & ~63
    p = 0
    while True:
        x = (_rot((x + y + v[0] + _f64(s, p + 16)) & M, 37) * k1) & M
        y = (_rot((y + v[1] + _f64(s, p + 48)) & M, 42) * k1) & M
        x ^= w[1]
        y ^= v[0]
        z = _rot(z ^ w[0], 33)
        v = _weak_s(s, p, (v[1] * k1) & M, (x + w[0]) & M)
        w = _weak_s(s, p + 32, (z + w[1]) & M, y)
        z, x = x, z
        p += 64
        rem -= 64
        if rem == 0:
            break
    return _h16((_h16(v[0], w[0]) + _smix(y) * k1 + z) & M,
                (_h16(v[1], w[1]) + x) & M)
