"""BugWar Display: derives a stylized display font from an OFL base font by editing glyph outlines.

Styles (combinable):
  chamfer=shell  - all outer corners of each glyph cut at 45 degrees (carapace silhouette)
  chamfer=blade  - big asymmetric cuts top-left / bottom-right (mandible / blade feel)
  drips          - honey drips hanging from some stroke feet on the baseline
  antenna        - breve of Й/й replaced by two little bug antennae with ball tips
  --fx hex,stinger,segments,claws,shine - experimental extras (not used in v1.0)

Rebuild the v1.0 font (base = Rubik variable font instanced at wght 900 = Rubik Black):
  pip install -r tools/requirements.txt
  python tools/bugfont.py fonts/Rubik-Black.ttf fonts/BugWarDisplay-Regular.ttf \
      --chamfer shell --antenna --k 0.11 --family "BugWar Display"
"""
import argparse
import hashlib
import math

import pathops
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

OP = pathops.PathOp
SHELL_K = 0.22
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz" \
          "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя"
DIGITS = "0123456789"


def h01(name, salt=""):
    return int(hashlib.md5((name + salt).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def glyph_path(gs, name):
    rec = DecomposingRecordingPen(gs)
    gs[name].draw(rec)
    p = pathops.Path()
    rec.replay(p.getPen())
    return p


def poly(points):
    p = pathops.Path()
    pen = p.getPen()
    pen.moveTo(points[0])
    for pt in points[1:]:
        pen.lineTo(pt)
    pen.closePath()
    return p


def circle(cx, cy, r):
    k = 0.5523 * r
    p = pathops.Path()
    pen = p.getPen()
    pen.moveTo((cx + r, cy))
    pen.curveTo((cx + r, cy + k), (cx + k, cy + r), (cx, cy + r))
    pen.curveTo((cx - k, cy + r), (cx - r, cy + k), (cx - r, cy))
    pen.curveTo((cx - r, cy - k), (cx - k, cy - r), (cx, cy - r))
    pen.curveTo((cx + k, cy - r), (cx + r, cy - k), (cx + r, cy))
    pen.closePath()
    return p


def union(*paths):
    out = paths[0]
    for q in paths[1:]:
        out = pathops.op(out, q, OP.UNION, fix_winding=True)
    return out


def chamfer(p, cap, mode, keep_tl=False):
    if p.bounds is None:
        return p
    x0, y0, x1, y1 = p.bounds
    w, h = x1 - x0, y1 - y0
    lim = 0.32 * min(w, h)
    if mode == "shell":
        # cut is relative to the glyph's own height, so lowercase gets proportionally smaller cuts
        tl = tr = bl = br = min(SHELL_K * min(h, cap), lim)
    else:  # blade
        big, small = min(0.36 * cap, lim * 1.35), min(0.07 * cap, lim)
        tl, br, tr, bl = big, big, small, small
    if keep_tl:  # e.g. Б: cutting its top-left makes it read as "6"
        tl = 0
    e = 2  # tiny margin so straight edges are not touched
    x0, y0, x1, y1 = x0 - e, y0 - e, x1 + e, y1 + e
    octo = poly([(x0 + bl, y0), (x1 - br, y0), (x1, y0 + br), (x1, y1 - tr),
                 (x1 - tr, y1), (x0 + tl, y1), (x0, y1 - tl), (x0, y0 + bl)])
    return pathops.op(p, octo, OP.INTERSECTION, fix_winding=True)


def feet(p, cap):
    """Contours where the glyph touches the baseline -> list of (xmin, xmax)."""
    if p.bounds is None:
        return []
    x0, _, x1, _ = p.bounds
    strip = poly([(x0 - 10, -1), (x1 + 10, -1), (x1 + 10, 0.06 * cap), (x0 - 10, 0.06 * cap)])
    cut = pathops.op(p, strip, OP.INTERSECTION, fix_winding=True)
    res = []
    for c in cut.contours:
        b = c.bounds
        if b and b[2] - b[0] > 0.10 * cap:
            res.append((b[0], b[2]))
    return res


def drip(p, cap, name):
    if p.bounds is None or p.bounds[1] < -0.02 * cap:  # skip glyphs with descenders
        return p
    if h01(name, "d") > 0.5:
        return p
    fs = feet(p, cap)
    if not fs:
        return p
    # only the LEFT-most foot: Cyrillic has no left-side descenders, so no letter confusion (Ш->Щ etc.)
    a, b = min(fs)
    fw = b - a
    cx = a + fw * 0.42
    w = min(fw * 0.62, 0.17 * cap)
    L = (0.10 + 0.06 * h01(name, "l")) * cap
    r = w * 0.62
    neck = poly([(cx - w * 0.75, 0.04 * cap), (cx + w * 0.75, 0.04 * cap), (cx + w * 0.5, -L * 0.35),
                 (cx + w * 0.42, -L + r), (cx - w * 0.42, -L + r), (cx - w * 0.5, -L * 0.35)])
    return union(p, neck, circle(cx, -L + r * 0.8, r))


def stroke_quad(p0, p1, p2, width, n=24):
    pts = [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
            (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in (i / n for i in range(n + 1))]
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        xa, ya = pts[max(i - 1, 0)]
        xb, yb = pts[min(i + 1, n)]
        dx, dy = xb - xa, yb - ya
        ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln * width / 2, dx / ln * width / 2
        left.append((x + nx, y + ny))
        right.append((x - nx, y - ny))
    return poly(left + right[::-1])


def antenna(p_base, cap):
    x0, _, x1, top = p_base.bounds
    cx, w = (x0 + x1) / 2, x1 - x0
    sw, r = 0.075 * cap, 0.072 * cap
    parts = [p_base]
    for s in (-1, 1):
        a = (cx + s * 0.10 * w, top + 0.05 * cap)
        c = (cx + s * 0.12 * w, top + 0.24 * cap)
        e = (cx + s * 0.30 * w, top + 0.30 * cap)
        parts += [stroke_quad(a, c, e, sw), circle(e[0], e[1], r), circle(a[0], a[1], sw / 2)]
    return union(*parts)


def signed_area(p):
    from fontTools.pens.areaPen import AreaPen
    ap = AreaPen()
    p.draw(ap)
    return ap.value


def hex_counters(p, cap):
    """Replace the inner holes (counters) of a glyph with honeycomb hexagons."""
    contours = list(p.contours)
    if len(contours) < 2:
        return p
    areas = [signed_area(c) for c in contours]
    outer_sign = 1 if areas[max(range(len(areas)), key=lambda i: abs(areas[i]))] > 0 else -1
    out = p
    for c, a in zip(contours, areas):
        if (a > 0) == (outer_sign > 0):
            continue  # not a hole
        b = c.bounds
        w, h = b[2] - b[0], b[3] - b[1]
        if w < 0.12 * cap or h < 0.12 * cap:
            continue
        hole = pathops.op(c, pathops.Path(), OP.UNION, fix_winding=True)
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        hw, hh = w * 0.40, h * 0.47
        if h >= w:  # pointy-top hexagon for tall holes
            hexa = poly([(cx, cy + hh), (cx + hw, cy + hh / 2), (cx + hw, cy - hh / 2),
                         (cx, cy - hh), (cx - hw, cy - hh / 2), (cx - hw, cy + hh / 2)])
        else:  # flat-top for wide holes
            hw, hh = w * 0.47, h * 0.40
            hexa = poly([(cx - hw, cy), (cx - hw / 2, cy + hh), (cx + hw / 2, cy + hh),
                         (cx + hw, cy), (cx + hw / 2, cy - hh), (cx - hw / 2, cy - hh)])
        hexa = pathops.op(hexa, hole, OP.INTERSECTION, fix_winding=True)
        out = pathops.op(union(out, hole), hexa, OP.DIFFERENCE, fix_winding=True)
    return out


def stinger(p, cap):
    """Descender tails (Ц Щ Д ...) become sharp stingers."""
    x0, y0, x1, y1 = p.bounds
    if y0 > -0.08 * cap:
        return p
    below = poly([(x0 - 5, 0.0), (x1 + 5, 0.0), (x1 + 5, y0 - 5), (x0 - 5, y0 - 5)])
    tails = pathops.op(p, below, OP.INTERSECTION, fix_winding=True)
    out = pathops.op(p, below, OP.DIFFERENCE, fix_winding=True)
    for t in tails.contours:
        b = t.bounds
        if not b or b[2] - b[0] < 0.05 * cap:
            continue
        cx = (b[0] + b[2]) / 2
        tip = b[1] - 0.10 * cap
        out = union(out, poly([(b[0], 0.03 * cap), (b[2], 0.03 * cap), (b[2] - (b[2] - b[0]) * 0.15, b[1] * 0.4),
                               (cx + 0.01 * cap, tip), (cx - 0.01 * cap, tip), (b[0] + (b[2] - b[0]) * 0.15, b[1] * 0.4)]))
    return out


def segments(p, cap):
    """Two thin horizontal cuts like abdomen segments / bee stripes."""
    x0, y0, x1, y1 = p.bounds
    h = min(y1 - max(y0, 0), cap)
    base = max(y0, 0)
    th = 0.045 * h
    out = p
    for f in (0.36, 0.64):
        y = base + f * h
        out = pathops.op(out, poly([(x0 - 5, y - th / 2), (x1 + 5, y - th / 2), (x1 + 5, y + th / 2), (x0 - 5, y + th / 2)]),
                         OP.DIFFERENCE, fix_winding=True)
    return out


def claws(p, cap):
    """Small sharp spikes at the outer side of the outermost feet."""
    fs = feet(p, cap)
    if not fs:
        return p
    (la, _), (_, rb) = min(fs), max(fs)
    s = 0.075 * cap
    left = poly([(la + 2, 0), (la + 2, 0.12 * cap), (la - s, -0.015 * cap)])
    right = poly([(rb - 2, 0), (rb + s, -0.015 * cap), (rb - 2, 0.12 * cap)])
    return union(p, left, right)


def shine(p, cap):
    """Thin diagonal slit near the top-left, like a highlight on a shell."""
    x0, y0, x1, y1 = p.bounds
    w, h = x1 - x0, y1 - max(y0, 0)
    a = (x0 + 0.14 * w, y1 - 0.40 * h)
    b = (x0 + 0.34 * w, y1 - 0.08 * h)
    sw = 0.035 * cap
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy) or 1
    nx, ny = -dy / ln * sw / 2, dx / ln * sw / 2
    slit = poly([(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)])
    return pathops.op(p, slit, OP.DIFFERENCE, fix_winding=True)


def write_glyph(font, name, path):
    tt = TTGlyphPen(None)
    path.draw(Cu2QuPen(tt, max_err=1.0, reverse_direction=False))
    g = tt.glyph()
    g.recalcBounds(font["glyf"])
    font["glyf"][name] = g
    adv, _ = font["hmtx"][name]
    font["hmtx"][name] = (adv, getattr(g, "xMin", 0))


def build(src, dst, family, chamfer_mode, do_drips, do_antenna, fx=()):
    font = TTFont(src)
    orig = TTFont(src).getGlyphSet()
    cmap = font.getBestCmap()
    cap = getattr(font["OS/2"], "sCapHeight", 0) or font["head"].unitsPerEm * 0.7
    new = {}
    for ch in LETTERS + DIGITS:
        name = cmap.get(ord(ch))
        if not name or name in new:
            continue
        src_name = name
        if do_antenna and ch in "Йй":
            src_name = cmap[ord("И" if ch == "Й" else "и")]
        p = glyph_path(orig, src_name)
        if p.bounds is None:
            continue
        p = pathops.op(p, pathops.Path(), OP.UNION, fix_winding=True)  # normalise overlaps
        if chamfer_mode:
            p = chamfer(p, cap, chamfer_mode, keep_tl=ch in 'Бб')
        if do_antenna and ch in "Йй":
            p = antenna(p, cap)
        if "hex" in fx:
            p = hex_counters(p, cap)
        if "stinger" in fx and ch in "ЦЩДцщдУуРрФф":
            p = stinger(p, cap)
        if "segments" in fx and ch in LETTERS:
            p = segments(p, cap)
        if "claws" in fx and ch in LETTERS:
            p = claws(p, cap)
        if "shine" in fx and ch in LETTERS:
            p = shine(p, cap)
        if do_drips and ch in LETTERS:
            p = drip(p, cap, name)
        new[name] = p
    for name, p in new.items():
        write_glyph(font, name, p)

    for t in ("fpgm", "prep", "cvt ", "STAT"):
        if t in font:
            del font[t]
    ymax = max(font["glyf"][n].yMax for n in font.getGlyphOrder() if hasattr(font["glyf"][n], "yMax"))
    ymin = min(font["glyf"][n].yMin for n in font.getGlyphOrder() if hasattr(font["glyf"][n], "yMin"))
    font["OS/2"].usWinAscent = max(font["OS/2"].usWinAscent, ymax)
    font["OS/2"].usWinDescent = max(font["OS/2"].usWinDescent, -ymin)
    ps = family.replace(" ", "")
    for rec in font["name"].names:
        if rec.nameID in (1, 16):
            rec.string = family
        elif rec.nameID == 4:
            rec.string = family + " Regular" if rec.nameID == 4 else family
        elif rec.nameID == 6:
            rec.string = ps + "-Regular"
        elif rec.nameID == 3:
            rec.string = ps + "-Regular;derived"
    font.save(dst)
    print("saved", dst, "glyphs changed:", len(new))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--family", default="BugWar Display")
    ap.add_argument("--chamfer", choices=["shell", "blade"], default=None)
    ap.add_argument("--drips", action="store_true")
    ap.add_argument("--antenna", action="store_true")
    ap.add_argument("--fx", default="", help="comma list: hex,stinger,segments,claws,shine")
    ap.add_argument("--k", type=float, default=0.22, help="shell cut size relative to glyph height")
    a = ap.parse_args()
    SHELL_K = a.k
    build(a.src, a.dst, a.family, a.chamfer, a.drips, a.antenna, tuple(x for x in a.fx.split(',') if x))
