# The measurement of README section 6, as it ran

These files are shipped **verbatim, as they were run**, not rewritten for
publication. They are here so the method is inspectable. They will not run from
a bare clone, and the reason is stated in README §6.9: the measurement streams
about 5.7 GB of z-planes out of ten public masked OME-Zarr volumes, and it
imports two of villa's files from a `volume-cartographer` checkout, which are
not ours to redistribute.

If you only want to check the arithmetic that turns a q per axis per slice into
`p = 0.0020`, you do not need any of this — `scripts/axis_benefit.py` does that
from the shipped per-slice results with numpy and scipy.

| file | what it is |
|---|---|
| `prereg_run.py` | the run. One `prereg_<scroll>.json` per scroll, exactly the files in the directory above. Every threshold, rule and slice index comes from `../PREREGISTRATION.md`; nothing here decides anything that file left open |
| `axisdemo.py` | the scoring code, frozen at pre-registration time: `radial_anisotropy_sectored` (the q of §6), `common_outer_radius`, `ring_inside_fraction`, `papyrus_mask`, `phase_concentration`. It imports villa's `umbilicus.json_umbilicus_z_to_yx` and villa's `sample_spiral`, both unmodified |
| `tiled_st.py` | the structure tensor, computed tile-wise with a 64 px halo because a whole-frame float32 tensor of a 6073² slice does not fit in the free RAM on the machine this ran on. Verified bit-identical (max abs difference 0.0 in all three components) to `axisdemo.structure_tensor` before the specification was written |
| `zslice_http.py` | streams one z-plane over anonymous HTTPS range GETs instead of `s3fs`, so the run lives in the one interpreter that also has torch. Verified byte-identical to the `s3fs` path on PHerc0813 L1 z = 2000 before the specification was written. Read-only, anonymous, no credentials |
| `zlist.py`, `scroll_meta.json` | the 300 slice indices. `scripts/axis_benefit.py` re-derives them independently from the shipped umbilicus files and checks the run used exactly those |
| `posthoc_fix.py` | builds the three post-hoc PHerc0813 variants of §6.6 into *copies*. It reads `PHerc0813_umbilicus.json` and never writes to it |

## Rough edges, stated rather than left to be found

- **Absolute paths are hard-wired**, because this ran on one machine and was
  never packaged: `axisdemo.py` points `VILLA_SPIRAL` at a
  `volume-cartographer/scripts/spiral` checkout, `zlist.py` opens
  `scroll_meta.json` by absolute path, `prereg_run.py` defaults `--umb-dir` to
  the repository's own location and polls a `load_status.txt` that is this
  station's compute gate and does not exist elsewhere. Anyone re-running this
  will edit those five lines first.
- `prereg_run.py` pauses on that gate before every slice. With no
  `load_status.txt` present it proceeds; the gate is a courtesy to the machine,
  not part of the measurement.
- The two verifications quoted above (byte-identical streaming, bit-identical
  structure tensor) were run before the specification was written and are
  recorded in `../PREREGISTRATION.md` §2. They are not re-run by anything that
  ships here.
