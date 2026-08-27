# Draft section for README.md — the single-centre assumption, and where it fails

*Not committed. Paste into README.md when the wording is agreed; the files it
refers to are listed at the end and are not in the repo yet either.*

---

## Two scrolls where one centre per height is not enough — and they fail differently

Everything above treats an umbilicus as a function of height: one control point
per z, and the file is read as z → (x, y). Two of the ten scrolls break that, and
they break it in two different ways — which matters, because a single extension
has to cover both.

### PHerc0268 — two axes that never join

Over z 5560–6312, about 6.5 mm of height, the scroll carries **two separate
winding centres at the same time**, roughly 22 mm apart on every slice of the
band. They are not two readings of one axis: each has its own laminae converging
on it, they run in parallel through thirteen annotated heights, and neither
continues into the other. Annotated as branches, `PHerc0268_branch_lower` (26
points, z 2680–6312) and `PHerc0268_branch_upper` (54 points, z 5560–12584). This
is the case the additive `branches` key was proposed for.

### PHerc0800 — one axis that doubles back

The other kind is not a split at all.

Between z 18260 and z 18556 — 2.6 mm of height, near the top of the scroll —
three separate convergences of laminae are visible on every slice, about 8 mm
apart and spanning 16 mm across. They were annotated by hand on six consecutive
heights: eighteen points in all, each placed on the slice image. Traced as one
path, the axis returns in height: it runs up, comes back down, and goes up again,
so over that band it is not single-valued in z at all.

The consequence is not cosmetic. Forced into one point per slice, the same
annotation makes the polyline cross about 16 mm sideways between neighbouring
slices and back, and every reader we know of joins those points with a straight
segment — through papyrus, without a warning. The three tracks are individually
smooth: sorted by x they move by 2.2, 4.2 and 2.3 voxels per voxel of height at
worst, so the jump is an artefact of the representation, not of the annotation.

The difference is the point. On PHerc0268 the two centres are strangers: no path
connects them and each owns its own band. On PHerc0800 there is **one continuous
path**, traceable point by point through every annotated height — it simply is
not a function of z over 2.6 mm of its length. Branches describe the first and
say nothing useful about the second; explicit succession describes the second and
is redundant for the first. Any extension worth agreeing on has to hold both.

**What is in this repo, and what is not.** `PHerc0800_umbilicus.json` is
unchanged and remains valid outside that band; inside it, it necessarily follows
one of the three and is wrong about the other two. The three-centre annotation is
published beside it as per-slice point lists (`PHerc0800/axis_z*.json`), and the
cracks marked in the same plane on two of those heights as
`PHerc0800/crack_z*.json`. Nothing in the established format can express either,
which is the point of this section.

**Three directions, in order of how additive they are.**

1. **Explicit succession** — store the axis as an ordered path, this point
   continues into that one, instead of recovering the order by sorting on z.
   Sorting is what turns a returning path into interleaved zig-zag, and the loss
   is silent.
2. **The `branches` key** already proposed for multi-axis scrolls, with an
   explicit z range per branch, so more than one centre can live in one file
   without breaking any existing reader.
3. **A file being able to declare the range where the single-valued form does not
   hold**, so a consumer can refuse rather than interpolate through papyrus.

**Two questions we would like answered before proposing a shape.** Has anyone
seen more than one winding centre on a single slice in another scroll? And would
an additive extension along these lines be acceptable, or is there a preferred
form for it?

### Files this section refers to

    PHerc0800/axis_z18260.json … axis_z18556.json    three points per height, six heights
    PHerc0800/crack_z18480.json, crack_z18520.json   cracks marked in the same plane
