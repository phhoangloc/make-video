"""House-style helpers for video-from-script (contemporary Vietnamese folk art + ink-wash maps).

Import from a video's build_video.py:

    import sys; sys.path.insert(0, str(ROOT.parents[1] / ".claude" / "skills" / "video-from-script"))
    import folk_style as fs
    fs.configure(W, H, ROOT.parents[1])            # frame size + project root (for fonts / map data)

    land = fs.load_polys("ne_10m_land.geojson")     # 50m for wide views (> ~20 deg), 10m for close ones
    rivers = fs.load_rivers({"Hong", "Da"})
    img, pr = fs.map_frame(land, rivers, lon, lat, width_deg)   # RGBA, img.info["map"] = True
    fs.map_label(img, pr(105.85, 21.03), "Hà Nội", size=36, role="ink", anchor="ms")

    sprite = fs.key_out_white(Image.open("war-junk-raw.png"))   # props generated on pure white

Map look: cream dó paper with fibres, uneven ochre land wash with ink bleeding inside the coast,
pale indigo wash along the shore, dry-brush ink coastline, indigo rivers, sparse ink-painting
mountains on uplands (they fade in while zooming). Everything is drawn from Natural Earth data,
so zooms stay smooth and coastlines stay accurate. Text on maps: Dancing Script Bold (calligraphic,
full Vietnamese) in ink / vermilion / indigo with a thin paper halo.
"""
import json, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
PROJECT = Path(".")
PAPER = np.array([236, 224, 196], np.float32)
INK = (38, 32, 28)
VERMILION = (172, 44, 34)
INDIGO = (38, 66, 104)
_cache = {}


def configure(width, height, project_root):
    global W, H, PROJECT
    W, H, PROJECT = width, height, Path(project_root)
    _cache.clear()


def font_path():
    return str(PROJECT / "image-source" / "fonts" / "DancingScript.ttf")


def data_path(name):
    return PROJECT / "image-source" / "data" / name


# ------------------------------------------------------------------ data
def load_polys(name):
    """Natural Earth land/country polygons -> [(ring_xy, minx, maxx, miny, maxy)]."""
    if ("polys", name) in _cache:
        return _cache[("polys", name)]
    polys = []
    for f in json.loads(data_path(name).read_text(encoding="utf-8"))["features"]:
        g = f["geometry"]
        rings = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for poly in rings:
            r = np.array(poly[0])
            polys.append((r, r[:, 0].min(), r[:, 0].max(), r[:, 1].min(), r[:, 1].max()))
    _cache[("polys", name)] = polys
    return polys


def load_rivers(names, file="ne_10m_rivers.geojson"):
    out = []
    for f in json.loads(data_path(file).read_text(encoding="utf-8"))["features"]:
        g = f["geometry"]
        if not g or f["properties"].get("name") not in names:
            continue
        ls = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
        out += [np.array(l) for l in ls]
    return out


# ------------------------------------------------------------------ textures
def _blur(a, sigma):
    import cv2
    return cv2.GaussianBlur(a, (0, 0), sigma)


def _textures():
    if "tex" in _cache:
        return _cache["tex"]
    import cv2
    rng = np.random.default_rng(11)
    low = cv2.resize(rng.normal(0, 1, (18, 32)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    mid = cv2.resize(rng.normal(0, 1, (68, 120)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    grain = _blur(rng.normal(0, 1, (H, W)).astype(np.float32), 1.0)
    fib = np.zeros((H, W), np.float32)
    for _ in range(int(1400 * W * H / (1920 * 1080))):   # paper fibres
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        a, ln = rng.uniform(0, np.pi), rng.uniform(8, 46)
        cv2.line(fib, (int(x), int(y)), (int(x + ln * np.cos(a)), int(y + ln * np.sin(a))), 1.0, 1)
    fib = _blur(fib, 0.7)
    paper = PAPER[None, None] * (1.0 + 0.025 * low + 0.02 * grain - 0.05 * fib)[..., None]
    wash = np.clip(0.55 + 0.3 * low + 0.06 * mid, 0, 1)                       # soft, uneven wash
    dry = np.clip(0.75 + 0.5 * _blur(rng.normal(0, 1, (H, W)).astype(np.float32), 1.4), 0.25, 1)  # dry brush
    _cache["tex"] = (paper, wash, dry)
    return _cache["tex"]


# ------------------------------------------------------------------ mountains
def _mountains(draw, pr, m, inner, width_deg, sx, box, skip):
    fade = max(0.0, min(1.0, (16 - width_deg) / 5))
    if fade <= 0:
        return
    rng = np.random.default_rng(5)
    size = max(24.0, min(78.0, 0.28 * sx))
    step = 0.36
    density = min(0.8, (step * sx / (2.6 * size)) ** 2)   # sparse; ranges come in gradually while zooming
    lo0, lo1, la0, la1 = box
    for i, lo in enumerate(np.arange(lo0, lo1, step)):
        for j, la in enumerate(np.arange(la0, la1, step)):
            jx, jy, v = rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), rng.random()
            glo, gla = lo + jx, la + jy
            if v > density or (skip and skip(glo, gla)):
                continue
            x, y = (float(c) for c in pr(glo, gla))
            if not (-80 < x < W + 80 and -80 < y < H + 80):
                continue
            xi, yi = int(min(max(x, 0), W - 1)), int(min(max(y, 0), H - 1))
            if m[yi, xi] < 0.5 or inner[yi, xi] < 0.97:      # inland only
                continue
            r = np.random.default_rng(1000 * i + j)
            s = size * r.uniform(0.75, 1.2)
            peaks = int(r.integers(2, 4))
            for k in range(peaks):
                px = x + (k - (peaks - 1) / 2) * s * 0.55 + r.uniform(-4, 4)
                ph = s * r.uniform(0.55, 1.0) * (1.0 if k == peaks // 2 else 0.75)
                pw = s * r.uniform(0.38, 0.5)
                top = (px + r.uniform(-pw * 0.2, pw * 0.2), y - ph)
                draw.polygon([(px - pw, y), top, (px + pw, y)], fill=(120, 132, 118, int(60 * fade)))
                draw.line([(px - pw, y), top, (px + pw * 0.85, y - ph * 0.08)], fill=INK + (int(200 * fade),),
                          width=max(2, int(s / 22)), joint="curve")
                for _ in range(2):   # texture strokes
                    u = r.uniform(0.3, 0.7)
                    a = (top[0] + (px - pw - top[0]) * u, top[1] + (y - top[1]) * u)
                    draw.line([a, (a[0] + pw * 0.35, a[1] + ph * 0.18)], fill=INK + (int(110 * fade),), width=1)


def _skip_red_river_delta(lo, la):
    return la < 21.25 and lo > 105.3


# ------------------------------------------------------------------ map
def map_frame(polys, rivers, lon, lat, width_deg, mountain_box=(101.0, 113.0, 20.4, 26.5),
              mountain_skip=_skip_red_river_delta):
    """Hand-painted ink-wash map centred on (lon, lat), width_deg degrees wide.
    Returns (RGBA image tagged info["map"]=True, projector(lon, lat) -> (x, y)).
    mountain_box = (lon0, lon1, lat0, lat1) where peaks may be drawn; mountain_skip(lon, lat) -> True keeps plains open.
    Pass mountain_box=None for no mountains."""
    import cv2
    k = math.cos(math.radians(lat))
    sx = W / width_deg

    def proj(a):
        return np.stack([(a[:, 0] - lon) * k * sx + W / 2, (lat - a[:, 1]) * sx + H / 2], 1)

    half_w, half_h = width_deg / k / 2 + 1, H / sx / 2 + 1
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    for r, x0, x1, y0, y1 in polys:
        if x1 < lon - half_w or x0 > lon + half_w or y1 < lat - half_h or y0 > lat + half_h:
            continue
        pts = [tuple(p) for p in proj(r)]
        if len(pts) > 2:
            d.polygon(pts, fill=255)
    m = np.asarray(mask, np.float32) / 255.0
    paper, wash, dry = _textures()

    out = paper.copy()
    near = _blur(m, 22) * (1 - m)                                   # sea: indigo wash hugging the shore
    out = out * (1 - 0.35 * near[..., None]) + np.array([150, 168, 176], np.float32) * (0.35 * near[..., None])
    a_land = m * (0.55 + 0.45 * wash)                               # land: ochre wash
    out = out * (1 - a_land[..., None]) + np.array([206, 186, 146], np.float32) * a_land[..., None] * (paper / PAPER)
    bleed = np.clip(m * (1 - _blur(m, 9)) * 1.6, 0, 1)              # ink bleeding inside the coast
    out = out * (1 - 0.45 * bleed[..., None]) + np.array([120, 96, 70], np.float32) * (0.45 * bleed[..., None])
    kpx = 2 if width_deg > 20 else 3                                # dry-brush coastline
    edge = cv2.morphologyEx((m > 0.5).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((kpx, kpx), np.uint8)).astype(np.float32)
    edge = np.clip(_blur(edge, 0.8) * 1.4, 0, 1) * dry
    riv = Image.new("L", (W, H), 0)                                 # rivers: indigo ink
    rd = ImageDraw.Draw(riv)
    lw = max(2, int(5 - width_deg / 10))
    for l in rivers:
        rd.line([tuple(p) for p in proj(l)], fill=255, width=lw, joint="curve")
    rv = _blur(np.asarray(riv, np.float32) / 255.0, 0.8) * (0.6 + 0.4 * dry)
    out = out * (1 - 0.8 * rv[..., None]) + np.array(INDIGO, np.float32) * (0.8 * rv[..., None])
    out = out * (1 - edge[..., None]) + np.array(INK, np.float32) * edge[..., None]

    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).convert("RGBA")
    if mountain_box:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        _mountains(ImageDraw.Draw(lay), lambda lo, la: proj(np.array([[lo, la]]))[0], m, _blur(m, 14),
                   width_deg, sx, mountain_box, mountain_skip)
        img.alpha_composite(lay)
    img.info["map"] = True
    return img, lambda lo, la: proj(np.array([[lo, la]]))[0]


def region_wash(img, pr, polys, color=VERMILION, alpha=85):
    """Translucent territory wash with a thin brush outline (e.g. an empire's extent)."""
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for ring in polys:
        pts = [tuple(float(v) for v in pr(lo, la)) for lo, la in ring]
        if len(pts) > 2:
            d.polygon(pts, fill=color + (alpha,), outline=color + (200,))
    img.alpha_composite(lay)


# ------------------------------------------------------------------ text on maps
def map_font(size):
    f = ImageFont.truetype(font_path(), int(max(size, 36) * 1.2))   # never too small to read
    try:
        f.set_variation_by_axes([700])                               # bold
    except Exception:
        pass
    return f


def map_label(canvas, xy, text, size=40, role="ink", anchor="ls", alpha=255):
    """Calligraphic map lettering. role: "ink" (places, captions), "accent" (vermilion: the key place,
    enemies), "sea" (indigo: seas, rivers)."""
    c = {"ink": INK, "accent": VERMILION, "sea": INDIGO}[role] + (alpha,)
    halo = tuple(int(v) for v in PAPER) + (int(alpha * 0.9),)
    ImageDraw.Draw(canvas).text(tuple(float(v) for v in xy), text, font=map_font(size), fill=c, anchor=anchor,
                                stroke_width=max(2, int(size / 12)), stroke_fill=halo)


def role_for(color):
    """Map an old light-on-dark label colour to a map role (for converting existing code)."""
    rgb = tuple(color[:3])
    lum = 0.3 * rgb[0] + 0.59 * rgb[1] + 0.11 * rgb[2]
    if (lum > 200 and max(rgb) - min(rgb) < 60) or lum < 90:
        return "ink"
    return "sea" if rgb[2] > rgb[0] else "accent"


# ------------------------------------------------------------------ props
def key_out_white(img, threshold=232, tol=18, min_hole=400):
    """Props are generated on pure white: flood-fill the white background from the border, then also clear
    enclosed white gaps (between sails and rigging, rowers' arms) of at least `min_hole` px; crop to content."""
    import cv2
    a = np.array(img.convert("RGB"))
    h, w = a.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)
    flags = 4 | cv2.FLOODFILL_MASK_ONLY | cv2.FLOODFILL_FIXED_RANGE | (255 << 8)
    for x, y in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]:
        if a[y, x].min() > threshold - 7:
            cv2.floodFill(a.copy(), mask, (x, y), 0, (tol,) * 3, (tol,) * 3, flags)
    alpha = np.where(mask[1:-1, 1:-1] > 0, 0, 255).astype(np.uint8)
    white = ((a.min(-1) > threshold) & (alpha > 0)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(white, 4)
    holes = np.zeros_like(white)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] >= min_hole:
            holes[lab == i] = 1
    alpha[cv2.dilate(holes, np.ones((3, 3), np.uint8)) > 0] = 0
    alpha = cv2.GaussianBlur(cv2.erode(alpha, np.ones((3, 3), np.uint8)), (3, 3), 0)
    rgba = np.dstack([a, alpha])
    ys, xs = np.where(alpha > 0)
    return Image.fromarray(rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1])
