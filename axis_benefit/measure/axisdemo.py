"""Does an annotated umbilicus axis make villa's spiral geometry work better?

Conditions are identical apart from the axis.  Everything that defines the
spiral model is villa's own code, imported unmodified from
``_villa/volume-cartographer/scripts/spiral``:

  * ``umbilicus.json_umbilicus_z_to_yx``  -- the loader ``fit_spiral.py`` calls at
    line 137 on ``<dataset>/umbilicus.json``; our files are that file.
  * ``sample_spiral.get_theta_and_radii`` -- the parameterisation fit_spiral fits.
    A winding is a level set of ``shifted_radius = radius - theta/2pi * dr``.
  * ``sample_spiral.get_spiral_yxs``      -- the canonical Archimedean spiral
    fit_spiral starts from, used here for the overlay figure.

Measurements, per z-slice and per candidate axis:

  M1  winding-phase concentration Rbar in [0,1]: the mean resultant length of
      ``2*pi * shifted_radius / dr`` over papyrus pixels in a fixed annulus,
      maximised over dr independently for each axis.  Rbar = 1 means every
      papyrus pixel sits at the same phase of the canonical spiral, i.e. the
      windings are exactly the level sets villa's model says they are.
  M2  radial drift of the sheet pattern in the polar unwrap, peak-to-peak, in
      micrometres, after removing the best linear trend (which absorbs the true
      pitch).  This is the radial deformation fit_spiral's deformation field has
      to absorb before its canonical spiral matches the scroll.
  M3  distance from the axis point to the nearest papyrus voxel: if this is 0
      the "centre" is buried inside the wound sheets and the polar frame is not
      just imprecise but topologically wrong.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import torch
from scipy.ndimage import map_coordinates, distance_transform_edt, gaussian_filter

VILLA_SPIRAL = "/home/alexr/vesuvius/_villa/volume-cartographer/scripts/spiral"
sys.path.insert(0, VILLA_SPIRAL)
from umbilicus import json_umbilicus_z_to_yx  # noqa: E402  villa, unmodified
import sample_spiral  # noqa: E402  villa, unmodified

torch.manual_seed(0)
np.random.seed(0)


# ----------------------------------------------------------------- axes ----

def villa_axis(umb_json: str, level: int):
    """villa's own loader, at pyramid `level` -> callable z_level -> (y, x)."""
    return json_umbilicus_z_to_yx(umb_json, downsample_factor=2 ** level)


def stick_from_mean(umb_json: str, level: int):
    """The straight vertical stick that best matches the annotation: the
    per-stack mean of the control points, held constant in z."""
    pts = json.load(open(umb_json))["control_points"]
    yx = np.array([(p["y"], p["x"]) for p in pts], float).mean(0) / 2 ** level
    return lambda z: yx.copy()


def stick_volume_centre(shape_hw):
    """The straight vertical stick you get with no umbilicus at all."""
    c = np.array([shape_hw[0] / 2.0, shape_hw[1] / 2.0])
    return lambda z: c.copy()


def displaced(axis_fn, dy, dx):
    d = np.array([dy, dx], float)
    return lambda z: np.asarray(axis_fn(z), float) + d


# --------------------------------------------------------------- masks -----

def papyrus_mask(img: np.ndarray):
    """Papyrus = above the median of the in-scroll (non-air) intensities.

    The volumes are masked, so air outside the scroll is exactly 0.  Inside,
    sheets are brighter than the gaps between them.
    """
    inside = img > 0
    thr = np.median(img[inside])
    return (img > thr), inside, float(thr)


# ------------------------------------------------------- M1: phase --------

def phase_concentration(img, mask, centre_yx, r0, r1, dr_grid, band=100.0,
                        max_pixels=400_000, rng=None):
    """Banded mean resultant length of villa's winding phase.

    A winding in villa's model is a level set of ``shifted_radius``; if the model
    holds, papyrus pixels pile up at one phase of ``shifted_radius mod dr``.
    Scored inside radial bands of `band` px (so a locally constant pitch is
    enough, rather than one exact Archimedean spiral across the whole scroll),
    then averaged over bands.  ``dr`` is chosen to maximise the score
    *independently for each axis*, so no axis is handed a better pitch.
    """
    cy, cx = float(centre_yx[0]), float(centre_yx[1])
    ys, xs = np.nonzero(mask)
    rel = np.stack([ys - cy, xs - cx], -1)
    rad = np.hypot(rel[:, 0], rel[:, 1])
    keep = (rad >= r0) & (rad <= r1)
    rel, rad = rel[keep], rad[keep]
    if len(rel) < 1000:
        return np.nan, np.nan, 0
    if len(rel) > max_pixels:
        rng = rng or np.random.default_rng(0)
        sel = rng.choice(len(rel), max_pixels, replace=False)
        rel, rad = rel[sel], rad[sel]
    bands = ((rad - r0) // band).astype(np.int64)
    nb = int(bands.max()) + 1
    rel_t = torch.from_numpy(rel.astype(np.float32))
    best = (-1.0, np.nan)
    for dr in dr_grid:
        # villa's own parameterisation, unmodified
        _, _, shifted = sample_spiral.get_theta_and_radii(rel_t, torch.tensor(float(dr)))
        ph = np.exp(2j * np.pi * (shifted.numpy() / dr))
        num = np.bincount(bands, ph.real, nb) + 1j * np.bincount(bands, ph.imag, nb)
        den = np.bincount(bands, None, nb)
        ok = den > 500
        if not ok.any():
            continue
        rbar = float(np.abs(num[ok] / den[ok]).mean())
        if rbar > best[0]:
            best = (rbar, float(dr))
    return best[0], best[1], len(rel)


# ------------------------------- M1b: radial gradient anisotropy ----------

def ring_inside_fraction(inside, cyx, r, n=360):
    """Fraction of the circle of radius r about cyx that lies on the scroll."""
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    yy = np.round(cyx[0] + r * np.sin(th)).astype(int)
    xx = np.round(cyx[1] + r * np.cos(th)).astype(int)
    H, W = inside.shape
    ok = (yy >= 0) & (yy < H) & (xx >= 0) & (xx < W)
    out = np.zeros(n, bool)
    out[ok] = inside[yy[ok], xx[ok]]
    return float(out.mean())


def common_outer_radius(inside, centres, r_max=2000, r_min=400, step=25, frac=0.95):
    """Largest annulus outer radius on which EVERY candidate axis sees a full ring.

    Without this the comparison is unfair in a way that has nothing to do with
    the axis being right: an axis nearer the scroll's edge is scored on a
    truncated crescent while a more central one is scored on a whole ring.
    """
    for r in range(int(r_max), int(r_min) - 1, -int(step)):
        if all(ring_inside_fraction(inside, c, r) >= frac for c in centres):
            return float(r)
    return float(r_min)


def structure_tensor(img, sigma_d=1.5, sigma_t=6.0):
    """Centre-independent: computed once per slice, reused by every axis."""
    f = gaussian_filter(img.astype(np.float32), sigma_d, order=0)
    gy = gaussian_filter(f, sigma_d, order=(1, 0))
    gx = gaussian_filter(f, sigma_d, order=(0, 1))
    Jyy = gaussian_filter(gy * gy, sigma_t)
    Jxx = gaussian_filter(gx * gx, sigma_t)
    Jyx = gaussian_filter(gy * gx, sigma_t)
    return Jyy, Jxx, Jyx


def radial_anisotropy_sectored(J, inside, centre_yx, r0, r1, n_sectors=72,
                               min_sector_frac=0.25, min_valid_sectors=0.90):
    """`radial_anisotropy`, but each 5-degree sector contributes equally.

    Without this, the score has a degenerate maximum: push the candidate centre
    far outside the scroll and every ray becomes nearly parallel, so any locally
    laminated crescent of papyrus scores high.  Equal weight per sector plus a
    validity requirement (at least `min_valid_sectors` of the 360 degrees must
    carry papyrus over at least `min_sector_frac` of the annulus) removes it:
    a centre that does not have the scroll wrapped around it is simply invalid.
    Returns (q, n_pixels, valid_sector_fraction).
    """
    Jyy, Jxx, Jyx = J
    H, W = Jyy.shape
    cy, cx = float(centre_yx[0]), float(centre_yx[1])
    yy = np.arange(H, dtype=np.float32)[:, None] - cy
    xx = np.arange(W, dtype=np.float32)[None, :] - cx
    r = np.sqrt(yy * yy + xx * xx)
    sel = inside & (r >= r0) & (r <= r1)
    n = int(sel.sum())
    if n < 1000:
        return np.nan, n, 0.0
    rs = np.where(r == 0, 1.0, r)
    uy, ux = (yy / rs)[sel], (xx / rs)[sel]
    th = np.arctan2(uy, ux) % (2 * np.pi)
    sec = np.minimum((th / (2 * np.pi) * n_sectors).astype(np.int64), n_sectors - 1)
    a, c, b = Jyy[sel], Jxx[sel], Jyx[sel]
    uJu = a * uy * uy + 2 * b * uy * ux + c * ux * ux
    tJt = a * ux * ux - 2 * b * ux * uy + c * uy * uy
    tr = a + c
    num = np.bincount(sec, uJu - tJt, n_sectors)
    den = np.bincount(sec, tr, n_sectors)
    cnt = np.bincount(sec, None, n_sectors)
    # a fully covered sector holds about (r1-r0) * (r1+r0)/2 * 2pi/n_sectors px
    full = (r1 - r0) * (r1 + r0) / 2 * 2 * np.pi / n_sectors
    ok = (cnt >= min_sector_frac * full) & (den > 0)
    frac = float(ok.mean())
    if frac < min_valid_sectors:
        return np.nan, n, frac
    return float((num[ok] / den[ok]).mean()), n, frac


def radial_anisotropy(J, inside, centre_yx, r0, r1):
    """Energy-weighted (radial - tangential) gradient energy, normalised.

    q = sum_p (u^T J u - t^T J t) / sum_p trace(J), over papyrus pixels in the
    annulus, where u is the unit radial and t the unit tangential direction
    about the candidate axis.  q = +1 means every sheet crosses the ray at right
    angles, i.e. the sheets are exactly the circles villa's spiral model assumes;
    q = 0 is no preference; q < 0 means the sheets run radially instead.
    Depends on the axis only through u, so the image evidence is identical
    across conditions.
    """
    Jyy, Jxx, Jyx = J
    H, W = Jyy.shape
    cy, cx = float(centre_yx[0]), float(centre_yx[1])
    yy = np.arange(H, dtype=np.float32)[:, None] - cy
    xx = np.arange(W, dtype=np.float32)[None, :] - cx
    r = np.sqrt(yy * yy + xx * xx)
    sel = inside & (r >= r0) & (r <= r1)
    if sel.sum() < 1000:
        return np.nan, 0
    rs = np.where(r == 0, 1.0, r)
    uy, ux = yy / rs, xx / rs
    uy, ux = uy[sel], ux[sel]
    a, c, b = Jyy[sel], Jxx[sel], Jyx[sel]
    uJu = a * uy * uy + 2 * b * uy * ux + c * ux * ux
    tJt = a * ux * ux - 2 * b * ux * uy + c * uy * uy
    tr = a + c
    return float((uJu - tJt).sum() / max(tr.sum(), 1e-9)), int(sel.sum())


# ------------------------------------------------- M2: unwrap + drift -----

def polar_unwrap(img, centre_yx, r0, r1, n_r=600, n_theta=720):
    cy, cx = float(centre_yx[0]), float(centre_yx[1])
    r = np.linspace(r0, r1, n_r)
    th = np.linspace(0, 2 * np.pi, n_theta, endpoint=False)
    R, TH = np.meshgrid(r, th, indexing="ij")
    yy = cy + R * np.sin(TH)
    xx = cx + R * np.cos(TH)
    return map_coordinates(img.astype(np.float32), [yy, xx], order=1, mode="constant", cval=0.0)


def drift_curve(U, max_shift=40):
    """Track the sheet pattern column-to-column by normalised cross-correlation.

    Returns the cumulative radial drift, in pixels of radius, as a function of
    angle.  A perfect concentric pattern drifts by exactly one pitch per turn.
    """
    n_r, n_theta = U.shape
    cols = U - U.mean(0, keepdims=True)
    sd = cols.std(0, keepdims=True)
    cols = cols / np.where(sd < 1e-6, 1.0, sd)
    shifts = np.zeros(n_theta)
    for j in range(1, n_theta):
        a, b = cols[:, j - 1], cols[:, j]
        best, bs = -np.inf, 0
        vals = {}
        for s in range(-max_shift, max_shift + 1):
            if s >= 0:
                v = float(np.dot(a[s:], b[: n_r - s])) / (n_r - s)
            else:
                v = float(np.dot(a[: n_r + s], b[-s:])) / (n_r + s)
            vals[s] = v
            if v > best:
                best, bs = v, s
        # parabolic refinement
        if -max_shift < bs < max_shift:
            ym, y0, yp = vals[bs - 1], vals[bs], vals[bs + 1]
            den = ym - 2 * y0 + yp
            if abs(den) > 1e-9:
                bs = bs + 0.5 * (ym - yp) / den
        shifts[j] = bs
    return np.cumsum(shifts)


def drift_stats(drift):
    n = len(drift)
    t = np.arange(n, dtype=float)
    A = np.stack([t, np.ones(n)], 1)
    coef, *_ = np.linalg.lstsq(A, drift, rcond=None)
    resid = drift - A @ coef
    return dict(
        pitch_per_turn_px=float(coef[0] * n),
        p2p_px=float(resid.max() - resid.min()),
        rms_px=float(np.sqrt((resid ** 2).mean())),
        resid=resid,
    )


# ------------------------------------------------- M3: centre in hole -----

def centre_clearance(mask_inside, centre_yx):
    """Distance in px from the axis point to the nearest non-air voxel."""
    cy, cx = int(round(centre_yx[0])), int(round(centre_yx[1]))
    H, W = mask_inside.shape
    if not (0 <= cy < H and 0 <= cx < W):
        return -1.0, False
    dt = distance_transform_edt(~mask_inside)
    return float(dt[cy, cx]), bool(mask_inside[cy, cx])
