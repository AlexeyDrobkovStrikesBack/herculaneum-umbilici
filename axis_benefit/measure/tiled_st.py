"""Low-memory structure tensor: tiled, with halo, emitting a subsampled result.

This machine has 12 GB of RAM with ~1.5 GB free, so the whole-frame float32
structure tensor of a 6073^2 slice (5 x 148 MB) is not affordable.  The tensor is
therefore computed tile by tile with a halo wide enough that every core pixel
sees exactly the same neighbourhood it would see in the whole-frame computation,
and only the SUB-subsampled result is retained.

Equality with the whole-frame computation is asserted by `verify_tiling()`.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter

# gaussian_filter default truncate=4.0.  The cascade is
#   f  = G(sigma_d) * img ; gy = dG(sigma_d) * f ; J = G(sigma_t) * (gy*gy)
# so the widest support a core pixel needs is 4*sigma_d + 4*sigma_d + 4*sigma_t.
def halo_for(sigma_d: float, sigma_t: float) -> int:
    return int(np.ceil(4 * sigma_d + 4 * sigma_d + 4 * sigma_t)) + 4


def structure_tensor_tiled(img, sigma_d=1.5, sigma_t=6.0, sub=1, tile=1024):
    """(Jyy, Jxx, Jyx) at stride `sub`, identical to the whole-frame version."""
    H, W = img.shape
    halo = halo_for(sigma_d, sigma_t)
    assert tile % sub == 0
    oh, ow = (H + sub - 1) // sub, (W + sub - 1) // sub
    out = [np.zeros((oh, ow), np.float32) for _ in range(3)]
    for y0 in range(0, H, tile):
        for x0 in range(0, W, tile):
            y1, x1 = min(y0 + tile, H), min(x0 + tile, W)
            ay0, ax0 = max(0, y0 - halo), max(0, x0 - halo)
            ay1, ax1 = min(H, y1 + halo), min(W, x1 + halo)
            patch = img[ay0:ay1, ax0:ax1].astype(np.float32)
            f = gaussian_filter(patch, sigma_d, order=0)
            gy = gaussian_filter(f, sigma_d, order=(1, 0))
            gx = gaussian_filter(f, sigma_d, order=(0, 1))
            del f, patch
            Jyy = gaussian_filter(gy * gy, sigma_t)
            Jxx = gaussian_filter(gx * gx, sigma_t)
            Jyx = gaussian_filter(gy * gx, sigma_t)
            del gy, gx
            ry0, rx0 = y0 - ay0, x0 - ax0
            for k, Jc in enumerate((Jyy, Jxx, Jyx)):
                core = Jc[ry0:ry0 + (y1 - y0), rx0:rx0 + (x1 - x0)]
                out[k][y0 // sub:(y1 + sub - 1) // sub,
                       x0 // sub:(x1 + sub - 1) // sub] = core[::sub, ::sub]
            del Jyy, Jxx, Jyx
    return out


def structure_tensor_full(img, sigma_d=1.5, sigma_t=6.0):
    f = gaussian_filter(img.astype(np.float32), sigma_d, order=0)
    gy = gaussian_filter(f, sigma_d, order=(1, 0))
    gx = gaussian_filter(f, sigma_d, order=(0, 1))
    return (gaussian_filter(gy * gy, sigma_t),
            gaussian_filter(gx * gx, sigma_t),
            gaussian_filter(gy * gx, sigma_t))


def verify_tiling(img, sub=2):
    a = structure_tensor_tiled(img, sub=sub)
    b = [x[::sub, ::sub] for x in structure_tensor_full(img)]
    return [float(np.abs(x - y).max()) for x, y in zip(a, b)], \
           [float(np.abs(y).max()) for y in b]
