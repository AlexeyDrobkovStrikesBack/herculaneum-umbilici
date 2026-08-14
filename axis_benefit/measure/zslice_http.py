"""Stream one z-plane of a raw-chunked OME-Zarr volume over anonymous HTTPS.

Identical in effect to `zslice.read_zslice` (which uses s3fs), but with no
dependency beyond `requests`, so that the whole experiment runs in one
interpreter -- the one that also has torch, i.e. the one that can import villa's
`sample_spiral`.  Byte-identity against the s3fs path is asserted by
`_verify.py`.

Chunks are raw (compressor null, C order, u1), so the z-plane inside a chunk is
one contiguous 128*128 byte run; each chunk costs a single 16 KiB range GET.
Nothing is written to disk.
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import requests
from requests.adapters import HTTPAdapter

BASE = "https://vesuvius-challenge-open-data.s3.amazonaws.com"
BUCKET = "vesuvius-challenge-open-data"

_SESS = None


def sess(workers: int = 24):
    global _SESS
    if _SESS is None:
        s = requests.Session()
        a = HTTPAdapter(pool_connections=workers, pool_maxsize=workers, max_retries=3)
        s.mount("https://", a)
        _SESS = s
    return _SESS


def _url(key: str) -> str:
    assert key.startswith(BUCKET + "/")
    return f"{BASE}/{key[len(BUCKET) + 1:]}"


def zarray(volume_root: str, level: int) -> dict:
    r = sess().get(_url(f"{volume_root}/{level}/.zarray"), timeout=60)
    r.raise_for_status()
    return json.loads(r.content.decode())


def read_zslice(volume_root: str, level: int, z: int, workers: int = 24) -> np.ndarray:
    za = zarray(volume_root, level)
    assert za["compressor"] is None and za["order"] == "C" and za["dtype"] == "|u1"
    cz, cy, cx = za["chunks"]
    Z, H, W = za["shape"]
    assert 0 <= z < Z, (z, Z)
    fill = np.uint8(za.get("fill_value") or 0)

    kz, zin = divmod(z, cz)
    ny, nx = (H + cy - 1) // cy, (W + cx - 1) // cx
    out = np.full((ny * cy, nx * cx), fill, np.uint8)
    off = zin * cy * cx
    end = off + cy * cx - 1
    s = sess(workers)

    def grab(ij):
        i, j = ij
        url = _url(f"{volume_root}/{level}/{kz}/{i}/{j}")
        for _ in range(3):
            try:
                r = s.get(url, headers={"Range": f"bytes={off}-{end}"}, timeout=60)
            except requests.RequestException:
                continue
            if r.status_code in (403, 404):
                return
            if r.status_code in (200, 206) and len(r.content) == cy * cx:
                out[i * cy:(i + 1) * cy, j * cx:(j + 1) * cx] = \
                    np.frombuffer(r.content, np.uint8).reshape(cy, cx)
                return
        return

    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(grab, [(i, j) for i in range(ny) for j in range(nx)]))
    return out[:H, :W]
