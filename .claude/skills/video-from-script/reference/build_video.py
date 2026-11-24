"""Build the animated video for "The Same River Trap Worked Twice".

Usage:  python build_video.py [scene ...]      (default: scene 1 only)
Renders 1920x1080 at 8 fps by default; pass --fps 24 for smooth motion.
"""
import math, subprocess, sys, re
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

ROOT = Path(__file__).parent
IMG = ROOT / "assets" / "images"
AUD = ROOT / "assets" / "audio"
OUT = ROOT / "output"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS = 1920, 1080, 8
FONT = "C:/Windows/Fonts/georgiab.ttf"


def load(name):
    return Image.open(IMG / name).convert("RGBA")


def audio_duration(path):
    err = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True).stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def camera(img, zoom, cx=0.5, cy=0.5):
    """Crop around (cx, cy) with given zoom, resize back to W x H."""
    w, h = W / zoom, H / zoom
    x0 = min(max(cx * W - w / 2, 0), W - w)
    y0 = min(max(cy * H - h / 2, 0), H - h)
    out = img.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + w, y0 + h))
    out.info.update(img.info)   # keep the "map" tag (ink-style labels)
    return out


def water_shimmer(canvas, frame, y_top, y_bot, color, n=26, seed=1):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0)); draw = ImageDraw.Draw(layer)
    rng = np.random.default_rng(seed)
    xs = rng.uniform(0, W, n); ys = rng.uniform(y_top, y_bot, n); ls = rng.uniform(30, 120, n)
    for x, y, l in zip(xs, ys, ls):
        dx = (frame * 48 / FPS + x) % (W + 200) - 100  # time-based drift, no flicker
        if True:
            draw.line([(dx, y), (dx + l * (0.5 + (y - y_top) / (y_bot - y_top)), y)], fill=color, width=2)
    canvas.alpha_composite(layer)


def place_ship(canvas, ship, x, y_bottom, width, angle=0.0, submerge=0.07):
    s = ship.resize((int(width), int(width * ship.height / ship.width)), Image.LANCZOS)
    s = s.crop((0, 0, s.width, int(s.height * (1 - submerge))))
    # reflection / waterline shadow
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([x - width * 0.05, y_bottom - 12, x + width * 1.05, y_bottom + 18], fill=(10, 30, 40, 110))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    if angle:
        s = s.rotate(angle, resample=Image.BICUBIC, expand=True)
    canvas.alpha_composite(s, (int(x), int(y_bottom - s.height)))


def stake(draw, x, y_base, h, lean, color=(45, 32, 24, 255)):
    w = 14
    draw.polygon([(x - w, y_base), (x + w, y_base), (x + lean + 3, y_base - h), (x + lean - 3, y_base - h)], fill=color)


def text_card(canvas, lines, alpha):
    if alpha <= 0:
        return
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    font = ImageFont.truetype(FONT, 150)
    total = sum(d.textbbox((0, 0), t, font=font)[3] for t, _ in lines) + 40 * (len(lines) - 1)
    y = (H - total) / 2
    for t, show in lines:
        bw = d.textbbox((0, 0), t, font=font)
        if show:
            x = (W - (bw[2] - bw[0])) / 2
            d.text((x + 6, y + 6), t, font=font, fill=(0, 0, 0, int(160 * alpha)))
            d.text((x, y), t, font=font, fill=(245, 225, 180, int(255 * alpha)))
        y += bw[3] + 40
    canvas.alpha_composite(layer)


# ---------------------------------------------------------------- scene 1 (Hook)
def scene_01():
    bg_high = load("bg-river-high-tide-dawn.png").resize((W, H), Image.LANCZOS)
    bg_low = load("bg-river-low-tide-stakes.png").resize((W, H), Image.LANCZOS)
    ship = load("war-junk.png")
    audio = AUD / "scene-01.mp3"
    dur = audio_duration(audio) + 0.3
    n = math.ceil(dur * FPS)
    # beats from the phrase timings written by tts_scene.py
    import json
    ph = {p["text"]: p["start"] for p in json.loads((AUD / "scene-01.json").read_text())}
    T_FLEET = ph["You sail a huge war fleet into a quiet river."]
    T_LATER = ph["A few hours later,"]
    T_STUCK = ph["They're stuck"]
    T_TWICE = ph["And here's the crazy part:"]
    T_938 = ph["this exact trap worked here twice."]
    T_1288 = ph["Three hundred and fifty years apart."]

    # fleet: (start_x, y_bottom, width) — farther ships smaller and higher
    fleet = [(-560, 790, 520), (-420, 705, 360), (-280, 648, 250)]
    fleet_end_x = [250, 820, 1300]

    for f in range(n):
        t = f / FPS

        if t < T_LATER:
            c = bg_high.copy()
            d = ImageDraw.Draw(c)
            water_shimmer(c, f, 600, 1060, (255, 214, 160, 70))
            p = ease((t - T_FLEET) / (T_LATER - T_FLEET))
            for i, (sx, yb, wdt) in reversed(list(enumerate(fleet))):
                x = sx + p * (fleet_end_x[i] - sx)
                bob = 4 * math.sin(t * 2.5 + i)
                place_ship(c, ship, x, yb + bob, wdt)
            zoom = 1.12 - 0.08 * ease(t / T_LATER)
            frame = camera(c, zoom, 0.5, 0.55)
        else:
            c = bg_low.copy()
            d = ImageDraw.Draw(c)
            stuck = ease((t - T_STUCK) / 1.0)
            ships_low = [(560, 690, 420, 6), (1010, 640, 300, -9), (1290, 610, 210, 12)]
            for i, (x, yb, wdt, ang) in reversed(list(enumerate(ships_low))):
                shake = 4 * math.sin(t * 9) * stuck if t < T_TWICE else 0
                place_ship(c, ship, x + shake, yb + 18, wdt, angle=ang * (0.4 + 0.6 * stuck), submerge=0.0)
                sd = ImageDraw.Draw(c)
                for k in range(3):  # stakes piercing the hull
                    sxk = x + wdt * (0.25 + 0.25 * k)
                    stake(sd, sxk, yb + 30, 60 + 45 * stuck + 10 * k, lean=12 * (k - 1))
            zoom = 1.0 + 0.18 * ease((t - T_LATER) / (n / FPS - T_LATER))
            frame = camera(c, zoom, 0.5, 0.6)
            # tide-drain transition: crossfade from high tide over 1 s
            if t < T_LATER + 1.0:
                prev = camera(bg_high.copy(), 1.04, 0.5, 0.55)
                a = ease((t - T_LATER) / 1.0)
                frame = Image.blend(prev, frame, a)
            if t >= T_TWICE:  # darken + "938 … 1288"
                k = ease((t - T_TWICE) / 0.75)
                frame = Image.blend(frame, Image.new("RGBA", (W, H), (8, 12, 20, 255)), 0.55 * k)
                text_card(frame, [("938", t >= T_938), ("…", t >= (T_938 + T_1288) / 2), ("1288", t >= T_1288)], k)
        yield frame.convert("RGB")
    return


# ---------------------------------------------------------------- scene 2 (Intro)
DATA = ROOT.parent.parent / "image-source" / "data"
FONT_UI = "C:/Windows/Fonts/arialbd.ttf"   # has Vietnamese diacritics
SEA, LAND, LAND_EDGE, RIVER = (24, 62, 72), (214, 178, 120), (120, 92, 58), (40, 96, 104)
BACH_DANG = (106.78, 20.92)


def _load_polys(name):
    import json
    polys = []
    for f in json.loads((DATA / name).read_text(encoding="utf-8"))["features"]:
        g = f["geometry"]
        rings = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for poly in rings:
            r = np.array(poly[0])
            polys.append((r, r[:, 0].min(), r[:, 0].max(), r[:, 1].min(), r[:, 1].max()))
    return polys


def _load_rivers(names):
    import json
    out = []
    for f in json.loads((DATA / "ne_10m_rivers.geojson").read_text(encoding="utf-8"))["features"]:
        g = f["geometry"]
        if not g or f["properties"].get("name") not in names:
            continue
        ls = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
        out += [np.array(l) for l in ls]
    return out


# ---- hand-painted ink-wash (thuy mac) map style
MAP_PAPER = np.array([236, 224, 196], np.float32)
MAP_INK = (38, 32, 28)
MAP_VERMILION = (172, 44, 34)
MAP_INDIGO = (38, 66, 104)


def _blur(a, sigma):
    import cv2
    return cv2.GaussianBlur(a, (0, 0), sigma)


def _map_textures():
    def build():
        import cv2
        rng = np.random.default_rng(11)
        low = cv2.resize(rng.normal(0, 1, (18, 32)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        mid = cv2.resize(rng.normal(0, 1, (68, 120)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        grain = _blur(rng.normal(0, 1, (H, W)).astype(np.float32), 1.0)
        fib = np.zeros((H, W), np.float32)
        for _ in range(1400):   # paper fibres
            x, y = rng.uniform(0, W), rng.uniform(0, H)
            a, ln = rng.uniform(0, np.pi), rng.uniform(8, 46)
            cv2.line(fib, (int(x), int(y)), (int(x + ln * np.cos(a)), int(y + ln * np.sin(a))), 1.0, 1)
        fib = _blur(fib, 0.7)
        shade = 1.0 + 0.025 * low + 0.02 * grain - 0.05 * fib
        paper = MAP_PAPER[None, None] * shade[..., None]
        wash = np.clip(0.55 + 0.3 * low + 0.06 * mid, 0, 1)          # uneven wash density (soft, no mottling)
        dry = np.clip(0.75 + 0.5 * _blur(rng.normal(0, 1, (H, W)).astype(np.float32), 1.4), 0.25, 1)  # dry brush
        return paper, wash, dry
    return cached("map-tex", build)


def _mountains(draw, pr, m, inner, width_deg, sx):
    """Traditional ink-painting peaks on inland, upland areas (north VN / south China)."""
    fade = max(0.0, min(1.0, (16 - width_deg) / 5))
    if fade <= 0:
        return
    rng = np.random.default_rng(5)
    size = max(24.0, min(78.0, 0.28 * sx))
    step = 0.36
    # sparse: about one range per (2.6 x size)^2 of screen; points come in gradually while zooming
    density = min(0.8, (step * sx / (2.6 * size)) ** 2)
    for i, lo in enumerate(np.arange(101.0, 113.0, step)):
        for j, la in enumerate(np.arange(20.4, 26.5, step)):
            jx, jy, v = rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), rng.random()
            glo, gla = lo + jx, la + jy
            if (gla < 21.25 and glo > 105.3) or v > density:   # keep the Red River delta and plains open
                continue
            x, y = (float(c) for c in pr(glo, gla))
            if not (-80 < x < W + 80 and -80 < y < H + 80):
                continue
            xi, yi = int(min(max(x, 0), W - 1)), int(min(max(y, 0), H - 1))
            if m[yi, xi] < 0.5 or inner[yi, xi] < 0.97:
                continue
            r = np.random.default_rng(1000 * i + j)
            s = size * r.uniform(0.75, 1.2)
            peaks = int(r.integers(2, 4))
            for k in range(peaks):
                px = x + (k - (peaks - 1) / 2) * s * 0.55 + r.uniform(-4, 4)
                ph = s * r.uniform(0.55, 1.0) * (1.0 if k == peaks // 2 else 0.75)
                pw = s * r.uniform(0.38, 0.5)
                top = (px + r.uniform(-pw * 0.2, pw * 0.2), y - ph)
                poly = [(px - pw, y), top, (px + pw, y)]
                draw.polygon(poly, fill=(120, 132, 118, int(60 * fade)))
                draw.line([(px - pw, y), top, (px + pw * 0.85, y - ph * 0.08)], fill=MAP_INK + (int(200 * fade),),
                          width=max(2, int(s / 22)), joint="curve")
                for q in range(2):   # texture strokes
                    u = r.uniform(0.3, 0.7)
                    a = (top[0] + (px - pw - top[0]) * u, top[1] + (y - top[1]) * u)
                    draw.line([a, (a[0] + pw * 0.35, a[1] + ph * 0.18)], fill=MAP_INK + (int(110 * fade),), width=1)


def map_frame(polys, rivers, lon, lat, width_deg, grain=None):
    """Hand-painted ink-wash map: do paper, washed land with ink bleeding at the coast,
    dry-brush coastline, indigo rivers, ink-painting mountains. Returns (RGBA image tagged "map", projector)."""
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
    paper, wash, dry = _map_textures()

    out = paper.copy()
    # sea: pale indigo wash hugging the shore, fading out
    near = _blur(m, 22) * (1 - m)
    out = out * (1 - 0.35 * near[..., None]) + np.array([150, 168, 176], np.float32) * (0.35 * near[..., None])
    # land: uneven ochre wash, darker ink bleeding inside the coastline
    land = np.array([206, 186, 146], np.float32)
    a_land = m * (0.55 + 0.45 * wash)
    out = out * (1 - a_land[..., None]) + land * a_land[..., None] * (paper / MAP_PAPER)
    inner = _blur(m, 9)
    bleed = np.clip(m * (1 - inner) * 1.6, 0, 1)
    out = out * (1 - 0.45 * bleed[..., None]) + np.array([120, 96, 70], np.float32) * (0.45 * bleed[..., None])
    # coastline: dry-brush ink stroke
    kpx = 2 if width_deg > 20 else 3
    edge = cv2.morphologyEx((m > 0.5).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((kpx, kpx), np.uint8)).astype(np.float32)
    edge = np.clip(_blur(edge, 0.8) * 1.4, 0, 1) * dry
    # rivers: indigo ink
    riv = Image.new("L", (W, H), 0)
    rd = ImageDraw.Draw(riv)
    lw = max(2, int(5 - width_deg / 10))
    for l in rivers:
        rd.line([tuple(p) for p in proj(l)], fill=255, width=lw, joint="curve")
    rv = _blur(np.asarray(riv, np.float32) / 255.0, 0.8) * (0.6 + 0.4 * dry)
    out = out * (1 - 0.8 * rv[..., None]) + np.array(MAP_INDIGO, np.float32) * (0.8 * rv[..., None])
    out = out * (1 - edge[..., None]) + np.array(MAP_INK, np.float32) * edge[..., None]

    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    _mountains(ImageDraw.Draw(lay), lambda lo, la: proj(np.array([[lo, la]]))[0], m, _blur(m, 14), width_deg, sx)
    img.alpha_composite(lay)
    img.info["map"] = True
    return img, lambda lo, la: proj(np.array([[lo, la]]))[0]


def _map_color(color):
    """Translate the old light-on-dark label colours to ink colours for a paper map."""
    rgb, a = tuple(color[:3]), (color[3] if len(color) > 3 else 255)
    lum = 0.3 * rgb[0] + 0.59 * rgb[1] + 0.11 * rgb[2]
    sat = max(rgb) - min(rgb)
    if (lum > 200 and sat < 60) or lum < 90:
        c = MAP_INK
    elif rgb[2] > rgb[0]:
        c = MAP_INDIGO
    else:
        c = MAP_VERMILION
    return c + (a,)


def label(canvas, xy, text, size=40, color=(250, 238, 210), anchor="ls", font=None):
    if canvas.info.get("map"):
        # on a paper map: same font as the rest of the video, in ink colours with a thin paper halo
        f = ImageFont.truetype(font or FONT_UI, int(max(size, 32)))   # never too small to read
        c = _map_color(color)
        halo = tuple(int(v) for v in MAP_PAPER) + (int(c[3] * 0.9),)
        ImageDraw.Draw(canvas).text(xy, text, font=f, fill=c, anchor=anchor,
                                    stroke_width=max(2, int(size / 12)), stroke_fill=halo)
        return
    d = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(font or FONT_UI, size)
    x, y = xy
    d.text((x + 3, y + 3), text, font=f, fill=(0, 0, 0, 170), anchor=anchor)
    d.text((x, y), text, font=f, fill=color, anchor=anchor)


def lower_third(canvas, title, alpha):
    if alpha <= 0:
        return
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = ImageFont.truetype(FONT_UI, 54)
    tw = d.textlength(title, font=f)
    x0 = 90 - (1 - alpha) * 300
    d.rectangle([x0, 900, x0 + tw + 80, 990], fill=(16, 28, 36, int(220 * alpha)))
    d.rectangle([x0, 900, x0 + 12, 990], fill=(222, 120, 60, int(255 * alpha)))
    d.text((x0 + 44, 945), title, font=f, fill=(250, 238, 210, int(255 * alpha)), anchor="lm")
    canvas.alpha_composite(layer)


def portrait_card(img, name, year, w=520):
    h = int(w * 1.15)
    p = img.resize((w, int(w * img.height / img.width)), Image.LANCZOS).crop((0, 0, w, h))
    card = Image.new("RGBA", (w + 24, h + 150), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rectangle([0, 0, w + 23, h + 149], fill=(244, 232, 205, 255))
    card.alpha_composite(p, (12, 12))
    d.text(((w + 24) / 2, h + 60), name, font=ImageFont.truetype(FONT_UI, 46), fill=(30, 40, 48), anchor="mm")
    d.text(((w + 24) / 2, h + 112), year, font=ImageFont.truetype(FONT, 40), fill=(170, 80, 40), anchor="mm")
    return card


def paste_card(canvas, card, x, y, angle):
    c = card.rotate(angle, resample=Image.BICUBIC, expand=True)
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([x + 14, y + 18, x + c.width - 6, y + c.height - 2], fill=(0, 0, 0, 120))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    canvas.alpha_composite(c, (int(x), int(y)))


def scene_02():
    import json
    ph = [p["start"] for p in json.loads((AUD / "scene-02.json").read_text())]
    T_RIVER, T_CITIES, T_938, T_1288, T_TRICK, T_YUAN, T_MONGOL, T_HOW, T_WHY, T_BACK = ph
    dur = audio_duration(AUD / "scene-02.mp3") + 0.3
    n = math.ceil(dur * FPS)
    land50, land10 = _load_polys("ne_50m_land.geojson"), _load_polys("ne_10m_land.geojson")
    rivers = _load_rivers({"Hong", "Da"})
    rng = np.random.default_rng(3)
    grain = Image.fromarray(rng.integers(0, 255, (H, W), dtype=np.uint8)).convert("RGB")
    card_nq = portrait_card(load("portrait-ngo-quyen.png"), "Ngô Quyền", "938")
    card_thd = portrait_card(load("portrait-tran-hung-dao.png"), "Trần Hưng Đạo", "1288")
    bg_low = load("bg-river-low-tide-stakes.png").resize((W, H), Image.LANCZOS)
    bg_high = load("bg-river-high-tide-dawn.png").resize((W, H), Image.LANCZOS)
    close = map_frame(land10, rivers, 106.6, 21.0, 3.4, grain)
    places = [("Hải Phòng", (106.68, 20.86), (-30, 60), "ms"), ("Quảng Ninh", (107.10, 21.02), (20, -30), "ls"),
              ("Hà Nội", (105.85, 21.03), (0, -24), "ms"), ("Gulf of Tonkin", (107.4, 20.25), (0, 0), "ms")]

    for f in range(n):
        t = f / FPS
        if t < T_938:
            # dive from Asia (70° wide) to northern Vietnam (3.4°), exponential zoom
            p = ease(t / (T_CITIES - 0.4))
            if p >= 1:
                frame, pr = close[0].copy(), close[1]
            else:
                wdeg = 70 * (3.4 / 70) ** p
                frame, pr = map_frame(land50 if wdeg > 8 else land10, rivers,
                                      105 + 1.6 * p, 24 - 3.0 * p, wdeg, grain)
            d = ImageDraw.Draw(frame)
            bx, by = pr(*BACH_DANG)
            if t >= T_CITIES:
                for i, (name, (lo, la), off, anc) in enumerate(places):
                    if t >= T_CITIES + 0.4 * i:
                        x, y = pr(lo, la)
                        sea = name == "Gulf of Tonkin"
                        if not sea:
                            d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(30, 40, 48))
                        label(frame, (x + off[0], y + off[1]), name, size=38 if sea else 34,
                              color=(170, 205, 210) if sea else (250, 238, 210), anchor=anc)
            if p > 0.75:  # pin, pulsing every half second
                r = 20 + 5 * math.sin(t * 2 * math.pi)
                d.ellipse([bx - r, by - r, bx + r, by + r], outline=(222, 120, 60), width=5)
                d.ellipse([bx - 9, by - 9, bx + 9, by + 9], fill=(222, 120, 60))
                label(frame, (bx - 40, by - 34), "Bạch Đằng", size=44, color=(255, 214, 160), anchor="rs")
            lower_third(frame, "Bạch Đằng River – northern Vietnam", ease((t - T_RIVER - 1.6) / 0.5))
        elif t < T_HOW:
            # two commanders: dimmed map behind, cards slide in
            frame = Image.blend(close[0], Image.new("RGBA", (W, H), (10, 16, 22, 255)), 0.6)
            a = ease((t - T_938) / 0.6)
            paste_card(frame, card_nq, 190 - (1 - a) * 900, 90 + 4 * math.sin(t * 2), -3)
            if t >= T_1288:
                b = ease((t - T_1288) / 0.6)
                paste_card(frame, card_thd, 1170 + (1 - b) * 900, 90 + 4 * math.sin(t * 2 + 1.5), 3)
            if t >= T_TRICK:
                k = min(1, (t - T_TRICK) / 0.4)
                label(frame, (W / 2, 470), "=", size=int(150 * k) + 1, color=(222, 120, 60), anchor="mm")
                label(frame, (W / 2, 590), "same trap", size=int(44 * k) + 1, color=(250, 238, 210), anchor="mm")
            if t >= T_MONGOL:
                lower_third(frame, "Yuan dynasty – ruled by the Mongols", ease((t - T_MONGOL) / 0.5))
        elif t < T_BACK:
            # the question: camera punches in on the stake field twice a second
            frame = camera(bg_low.copy(), 1.0 + 0.3 * ease((t - T_HOW) / (T_BACK - T_HOW)), 0.42, 0.72)
            if t >= T_WHY:
                frame = Image.blend(frame, Image.new("RGBA", (W, H), (8, 12, 20, 255)), 0.45)
            q = "Two empires. One trap." if t < T_WHY else "Why didn’t they see it coming?"
            label(frame, (W / 2, 160), q, size=72, anchor="mm")
        else:
            # back to the beginning: dawn river, fade towards black with "938"
            k = ease((t - T_BACK) / (dur - T_BACK))
            frame = camera(bg_high.copy(), 1.0 + 0.1 * k, 0.5, 0.55)
            frame = Image.blend(frame, Image.new("RGBA", (W, H), (0, 0, 0, 255)), 0.85 * k)
            label(frame, (W / 2, H / 2), "938", size=160, color=(245, 225, 180), anchor="mm", font=FONT)
        yield frame.convert("RGB")


# ---------------------------------------------------------------- scene 3 (Part 1: 937–938)
DAI_LA, PANYU = (105.85, 21.03), (113.26, 23.13)


def grey(card):
    g = card.convert("LA").convert("RGBA")
    g.putalpha(card.getchannel("A"))
    return Image.blend(g, Image.new("RGBA", card.size, (40, 40, 40, 0)), 0.25)


def dagger(canvas, p):
    """Dagger silhouette sweeping across the frame, p = 0..1."""
    if not 0 <= p <= 1:
        return
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = -300 + p * (W + 600), 700 - p * 400
    ang = math.radians(-25)
    def rot(x, y):
        return (cx + x * math.cos(ang) - y * math.sin(ang), cy + x * math.sin(ang) + y * math.cos(ang))
    d.polygon([rot(-60, -22), rot(330, 0), rot(-60, 22)], fill=(12, 10, 14, 235))      # blade
    d.rectangle([0, 0, 0, 0])
    d.polygon([rot(-75, -55), rot(-60, -55), rot(-60, 55), rot(-75, 55)], fill=(12, 10, 14, 235))  # guard
    d.polygon([rot(-190, -14), rot(-75, -14), rot(-75, 14), rot(-190, 14)], fill=(12, 10, 14, 235))  # grip
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(1)))


def red_flash(frame, k):
    if k > 0:
        return Image.blend(frame, Image.new("RGBA", (W, H), (150, 20, 20, 255)), 0.45 * k)
    return frame


def route_point(route, p):
    seg = [math.dist(a, b) for a, b in zip(route, route[1:])]
    tot, acc = sum(seg), 0.0
    target = max(0.0, min(1.0, p)) * tot
    for (a, b), L in zip(zip(route, route[1:]), seg):
        if acc + L >= target:
            u = (target - acc) / L if L else 0
            return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
        acc += L
    return route[-1]


def caption(canvas, text, alpha, y=150, size=64):
    if alpha <= 0:
        return
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    layer.info["map"] = canvas.info.get("map", False)
    label(layer, (W / 2, y), text, size=size, anchor="mm", color=(250, 238, 210, int(255 * alpha)))
    canvas.alpha_composite(layer)


def scene_03():
    import json
    ph = [p["start"] for p in json.loads((AUD / "scene-03.json").read_text())]
    (T_RULE, T_LOCAL, T_NGHE, T_MURDER, T_KIEU, T_UNPOP, T_LESS, T_ASK, T_OPP, T_SON,
     T_FASTER, T_NQ, T_PROBLEM, T_FLEET, T_NONAVY, T_NOTFLEET, T_RIVER) = ph
    T_KILL = wt(3, 11, "killed")
    dur = audio_duration(AUD / "scene-03.mp3") + 0.3
    n = math.ceil(dur * FPS)
    land10 = _load_polys("ne_10m_land.geojson")
    rivers = _load_rivers({"Hong", "Da"})
    grain = Image.fromarray(np.random.default_rng(3).integers(0, 255, (H, W), dtype=np.uint8)).convert("RGB")
    route = [tuple(p) for p in json.loads((ROOT / "assets" / "fleet_route_938.json").read_text())]

    c_nghe = portrait_card(load("portrait-duong-dinh-nghe.png"), "Dương Đình Nghệ", "† 937")
    c_kieu = portrait_card(load("portrait-kieu-cong-tien.png"), "Kiều Công Tiễn", "937")
    c_liu = portrait_card(load("portrait-liu-hongcao.png"), "Lưu Hoằng Tháo", "Southern Han prince")
    c_nq = portrait_card(load("portrait-ngo-quyen.png"), "Ngô Quyền", "938")
    small = lambda c, s: c.resize((int(c.width * s), int(c.height * s)), Image.LANCZOS)
    palace = load("bg-palace-hall-night.png").resize((W, H), Image.LANCZOS)
    port = load("bg-southern-han-port.png").resize((W, H), Image.LANCZOS)
    river = load("bg-river-high-tide-dawn.png").resize((W, H), Image.LANCZOS)
    ship = load("war-junk.png")
    icon = ship.resize((70, int(70 * ship.height / ship.width)), Image.LANCZOS)
    region = map_frame(land10, rivers, 109.6, 21.6, 10.5, grain)   # Đại La … Panyu
    dark = lambda img, a: Image.blend(img, Image.new("RGBA", (W, H), (8, 12, 18, 255)), a)

    def pin(frame, pr, lonlat, name, color=(222, 120, 60), side="r", t=0.0):
        x, y = pr(*lonlat)
        d = ImageDraw.Draw(frame)
        r = 14 + 4 * math.sin(t * 2 * math.pi)
        d.ellipse([x - r, y - r, x + r, y + r], outline=color, width=4)
        d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=color)
        label(frame, (x + 26, y + 12) if side == "r" else (x - 26, y + 12), name, size=38,
              anchor="ls" if side == "r" else "rs")

    for f in range(n):
        t = f / FPS
        if t < T_NGHE:
            # ~1,000 years of Chinese rule: slow drift over the region map
            k = ease(t / T_NGHE)
            frame = camera(region[0], 1.0 + 0.08 * k, 0.4, 0.5)
            pr = lambda lo, la: ((region[1](lo, la)[0] - W * 0.4) * (1 + 0.08 * k) + W / 2,
                                 (region[1](lo, la)[1] - H * 0.5) * (1 + 0.08 * k) + H / 2)
            pin(frame, pr, DAI_LA, "Đại La (Hà Nội)", t=t)
            caption(frame, "≈ 1,000 years of Chinese rule", ease((t - T_RULE - 0.5) / 0.6))
            if t >= T_LOCAL:
                caption(frame, "local leaders take control", ease((t - T_LOCAL) / 0.5), y=240, size=44)
        elif t < T_MURDER:
            frame = dark(region[0], 0.6)
            a = ease((t - T_NGHE) / 0.6)
            paste_card(frame, c_nghe, (W - c_nghe.width) / 2, 80 + (1 - a) * 700 + 4 * math.sin(t * 2), -2)
        elif t < T_ASK:
            # palace intrigue: dagger, red flash, then Kiều steps out of the shadow
            k = ease((t - T_MURDER) / (T_ASK - T_MURDER))
            frame = camera(palace.copy(), 1.0 + 0.12 * k, 0.5, 0.55)
            paste_card(frame, grey(c_nghe) if t >= T_MURDER + 0.9 else c_nghe, 160, 80, -3)
            dagger(frame, (t - T_MURDER - 0.2) / 0.7)
            frame = red_flash(frame, max(0.0, 1 - abs(t - T_MURDER - 0.6) / 0.5))
            if t >= T_KIEU:
                b = ease((t - T_KIEU) / 0.6)
                paste_card(frame, c_kieu, 1210 + (1 - b) * 800, 80 + 4 * math.sin(t * 2 + 1), 3)
            if t >= T_UNPOP:
                frame = dark(frame, 0.25 * ease((t - T_UNPOP) / 0.6))
            lower_third(frame, "937: Dương Đình Nghệ assassinated", ease((t - T_MURDER - 0.8) / 0.5))
        elif t < T_SON:
            # Kiều calls on the Southern Han: arrow Đại La -> Panyu
            frame = region[0].copy()
            pr = region[1]
            pin(frame, pr, DAI_LA, "Đại La", t=t)
            p = ease((t - T_ASK - 0.3) / 1.6)
            if p > 0:
                (ax, ay), (bx, by) = pr(*DAI_LA), pr(*PANYU)
                pts = []
                for i in range(int(40 * p) + 1):
                    u = i / 40
                    pts.append((ax + (bx - ax) * u, ay + (by - ay) * u - math.sin(u * math.pi) * 160))
                if len(pts) > 1:
                    ImageDraw.Draw(frame).line(pts, fill=(222, 120, 60), width=7)
            if p >= 1:
                pin(frame, pr, PANYU, "Southern Han (Panyu)", color=(200, 60, 50), side="l", t=t)
                caption(frame, "“Help me.”", ease((t - T_ASK - 1.9) / 0.4), y=140)
            if t >= T_OPP:
                caption(frame, "An opportunity.", ease((t - T_OPP) / 0.5), y=220, size=48)
            paste_card(frame, small(c_kieu, 0.5), 60, 560, -3)
        elif t < T_FASTER:
            # the prince and his fleet leave port
            k = (t - T_SON) / (T_FASTER - T_SON)
            frame = camera(port.copy(), 1.04, 0.5, 0.5)
            for i, (y, w, d0) in enumerate(((610, 300, 0.0), (680, 380, 0.12), (760, 470, 0.25))):
                u = ease((k - d0) / (1 - d0)) if k > d0 else 0
                place_ship(frame, ship, 300 + u * 1500, y + 4 * math.sin(t * 2.5 + i), w)
            a = ease((t - T_SON) / 0.6)
            paste_card(frame, small(c_liu, 0.72), 80 - (1 - a) * 700, 60 + 4 * math.sin(t * 2), -2)
            lower_third(frame, "938: Southern Han fleet sets sail", ease((t - T_SON - 1.0) / 0.5))
        elif t < T_PROBLEM:
            # family tree: Dương Đình Nghệ -> son-in-law Ngô Quyền; Kiều crossed out
            frame = dark(palace.filter(ImageFilter.GaussianBlur(8)), 0.55)
            top, bot = small(c_nghe, 0.5), small(c_nq, 0.62)
            paste_card(frame, top, 380, 40, 0)
            d = ImageDraw.Draw(frame)
            x_line = 380 + top.width / 2
            a = ease((t - T_FASTER) / 0.6)
            if a > 0:
                d.line([(x_line, 40 + top.height), (x_line, 40 + top.height + 110 * a)], fill=(222, 120, 60), width=6)
                label(frame, (x_line + 20, 40 + top.height + 70), "son-in-law", size=36, anchor="ls")
                paste_card(frame, bot, x_line - bot.width / 2, 40 + top.height + 110 + (1 - a) * 400, 0)
            if t >= T_NQ:
                kc = small(c_kieu, 0.62)
                kx, ky = 1150, 260
                paste_card(frame, grey(kc) if t >= T_KILL else kc, kx, ky, 3)
                if t >= T_KILL:  # "...and killed him."
                    q = ease((t - T_KILL) / 0.4)
                    d = ImageDraw.Draw(frame)
                    d.line([(kx + 20, ky + 20), (kx + 20 + (kc.width - 40) * q, ky + 20 + (kc.height - 40) * q)],
                           fill=(200, 40, 40), width=16)
                    d.line([(kx + kc.width - 20, ky + 20),
                            (kx + kc.width - 20 - (kc.width - 40) * q, ky + 20 + (kc.height - 40) * q)],
                           fill=(200, 40, 40), width=16)
                # arrow Ngô Quyền -> Kiều
                ImageDraw.Draw(frame).line([(x_line + bot.width / 2 + 10, 700), (kx - 20, ky + kc.height / 2)],
                                           fill=(222, 120, 60), width=6)
        elif t < T_NOTFLEET:
            # the enemy fleet comes by sea toward Bạch Đằng
            frame = region[0].copy()
            pr = region[1]
            pin(frame, pr, BACH_DANG, "Bạch Đằng", side="l", t=t)
            p = (t - T_FLEET + 0.5) / (T_NOTFLEET - T_FLEET + 0.5)
            trail = [tuple(float(v) for v in pr(*route_point(route, q / 60 * max(p, 0)))) for q in range(61)]
            if p > 0:
                ImageDraw.Draw(frame).line(trail, fill=(200, 60, 50), width=4)
            for i in range(3):
                q = p - 0.05 * i
                if q > 0:
                    x, y = pr(*route_point(route, q))
                    frame.alpha_composite(icon, (int(x - icon.width / 2), int(y - icon.height + 8)))
            paste_card(frame, small(c_nq, 0.45), 60, 40, -3)  # top-left: keeps the Bạch Đằng label clear
            if t >= T_NONAVY:
                caption(frame, "No navy to match it", ease((t - T_NONAVY) / 0.5), y=140)
        else:
            # "fight the river"
            k = ease((t - T_NOTFLEET) / (dur - T_NOTFLEET))
            frame = camera(river.copy(), 1.0 + 0.2 * k, 0.5, 0.6)
            caption(frame, "Don't fight the fleet.", ease((t - T_NOTFLEET) / 0.5), y=380, size=60)
            if t >= T_RIVER:
                caption(frame, "Fight the river.", ease((t - T_RIVER) / 0.4), y=500, size=110)
        yield frame.convert("RGB")


# ================================================================ scenes 4–9: shared helpers
VAN_KIEP, VAN_DON, YEN_GIANG, THUY_NGUYEN = (106.40, 21.10), (107.43, 21.07), (106.81, 20.93), (106.67, 20.95)
_cache = {}


def cached(key, fn):
    if key not in _cache:
        _cache[key] = fn()
    return _cache[key]


def bg(name):
    return cached(("bg", name), lambda: load(name).resize((W, H), Image.LANCZOS))


def card(name, title, sub):
    return cached(("card", name, title, sub), lambda: portrait_card(load(name), title, sub))


def scaled(c, s):
    return c.resize((int(c.width * s), int(c.height * s)), Image.LANCZOS)


def darken(img, a, color=(8, 12, 18)):
    return Image.blend(img, Image.new("RGBA", (W, H), color + (255,)), a) if a > 0 else img


def phrases(no):
    import json
    return [p["start"] for p in json.loads((AUD / f"scene-{no:02d}.json").read_text())]


def wt(no, idx, word, nth=0):
    """Time (s) at which `word` is spoken in phrase `idx` of scene `no` (nth occurrence)."""
    import json
    ws = cached(("words", no), lambda: json.loads((AUD / f"scene-{no:02d}.words.json").read_text()))
    hits = [w["t"] for w in ws if w["phrase"] == idx and w["word"] == word]
    if len(hits) <= nth:  # Edge sometimes merges words ("in1258")
        hits = [w["t"] for w in ws if w["phrase"] == idx and word in w["word"]]
    if len(hits) > nth:
        return hits[nth]
    print(f"   ! word not found: scene {no} phrase {idx} '{word}'")
    return phrases(no)[idx]


def run_shots(no, shots):
    """shots: [(phrase_index, fn(t, tl, f, T, d))]; each shot runs until the next one starts."""
    T = phrases(no)
    dur = audio_duration(AUD / f"scene-{no:02d}.mp3") + 0.3
    starts = [0.0 if i == 0 else T[p] for i, (p, _) in enumerate(shots)] + [dur]
    for f in range(math.ceil(dur * FPS)):
        t = f / FPS
        k = max(i for i in range(len(shots)) if starts[i] <= t)
        tl, d = t - starts[k], starts[k + 1] - starts[k]
        yield shots[k][1](t, tl, f, T, d).convert("RGB")


def push(img, tl, d, z0=1.0, z1=1.12, cx=0.5, cy=0.5):
    return camera(img.copy(), z0 + (z1 - z0) * ease(tl / max(d, 0.1)), cx, cy)


def big_text(frame, lines, t, T_list, y0=None, size=110, gap=30):
    """Lines appear at their own times; lines = [(text, start_time, size or None)]."""
    shown = [(tx, s, sz or size) for tx, s, sz in lines if t >= s]
    if not shown:
        return frame
    hts = [sz + gap for _, _, sz in shown]
    y = (y0 if y0 is not None else (H - sum(hts)) / 2) + hts[0] / 2
    for (tx, s, sz), h in zip(shown, hts):
        a = ease((t - s) / 0.35)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        label(layer, (W / 2, y), tx, size=sz, anchor="mm", color=(250, 238, 210, int(255 * a)))
        frame.alpha_composite(layer)
        y += h
    return frame


def flames(frame, spots, f, scale=1.0):
    """Flickering flat flames + smoke at (x, y) spots; changes every 2 frames."""
    rng = np.random.default_rng(f // 2)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for x, y in spots:
        for j in range(3):
            sy = y - 120 * scale - j * 70 * scale - (f % 16) * 4
            r = (30 + j * 18) * scale
            d.ellipse([x - r + j * 10, sy - r, x + r + j * 10, sy + r], fill=(60, 60, 64, 90))
        for j in range(5):
            h = (70 + rng.uniform(0, 70)) * scale
            w = (22 + rng.uniform(0, 16)) * scale
            ox = (j - 2) * 18 * scale + rng.uniform(-6, 6)
            d.polygon([(x + ox - w, y), (x + ox + w, y), (x + ox + rng.uniform(-10, 10), y - h)],
                      fill=(240, 120 + int(rng.uniform(0, 60)), 40, 230))
            d.polygon([(x + ox - w / 2, y), (x + ox + w / 2, y), (x + ox, y - h * 0.55)], fill=(255, 220, 120, 240))
    frame.alpha_composite(layer.filter(ImageFilter.GaussianBlur(1.5)))
    return frame


def cross_section(level, grown=1.0, ships=(), title=None, labels=True, width=W, x0=0, canvas=None):
    """Side view of the estuary. level: 0 = low tide, 1 = high tide. ships: [(x, size)]."""
    img = canvas if canvas is not None else Image.new("RGBA", (W, H), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    sx = lambda u: x0 + u * width
    d.rectangle([x0, 0, x0 + width, H], fill=(236, 214, 170))
    bed_y = lambda u: 900 + 25 * math.sin(u * 7)
    water_y = 800 - 260 * level
    # stakes
    stakes = []
    for i in range(9):
        u = 0.22 + i * 0.07
        hgt = 230 * grown
        bx, by = sx(u), bed_y(u)
        tx, ty = bx + 22 * width / W, by - hgt
        stakes.append((tx, ty))
        if hgt > 4:
            d.polygon([(bx - 12, by), (bx + 12, by), (tx + 4, ty + 26), (tx - 4, ty + 26)], fill=(70, 48, 30))
            d.polygon([(tx - 7, ty + 28), (tx + 7, ty + 28), (tx, ty)], fill=(120, 124, 130))
    # water (drawn over the stakes, so submerged stakes read as hidden)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rectangle([x0, water_y, x0 + width, H], fill=(36, 96, 110, 225))
    img.alpha_composite(layer)
    d = ImageDraw.Draw(img)
    d.line([(x0, water_y), (x0 + width, water_y)], fill=(170, 215, 220), width=4)
    pts = [(sx(u / 60), bed_y(u / 60)) for u in range(61)] + [(x0 + width, H), (x0, H)]
    d.polygon(pts, fill=(118, 86, 52))
    for xs, size in ships:
        u = (xs - 0.0)
        hx = sx(u)
        rest = water_y
        tilt = 0.0
        for tx, ty in stakes:
            if abs(tx - (hx + size * 0.5)) < size * 0.5 and ty < rest:
                rest, tilt = ty, 6.0
        place_ship(img, load_ship(), hx, rest + 10, size, angle=tilt * (1 if level < 0.6 else 0), submerge=0.0)
    if labels:
        lab = "HIGH TIDE" if level > 0.5 else "LOW TIDE"
        label(img, (x0 + 40, 90), lab, size=48, color=(30, 50, 60), anchor="ls")
        d = ImageDraw.Draw(img)
        d.line([(x0 + width - 80, 540), (x0 + width - 80, 800)], fill=(30, 50, 60), width=4)
        d.polygon([(x0 + width - 92, 556), (x0 + width - 68, 556), (x0 + width - 80, 536)], fill=(30, 50, 60))
        d.polygon([(x0 + width - 92, 784), (x0 + width - 68, 784), (x0 + width - 80, 804)], fill=(30, 50, 60))
        label(img, (x0 + width - 100, 680), "several m", size=30, color=(30, 50, 60), anchor="rm")
    if title:
        label(img, (x0 + width / 2, 170), title, size=56, color=(30, 50, 60), anchor="mm")
    return img


def load_ship():
    return cached("ship", lambda: load("war-junk.png"))


def tide_chart(t, tl, window=True, title="Tide at the Bạch Đằng estuary", ship_line=False):
    img = Image.new("RGBA", (W, H), (236, 214, 170, 255))
    d = ImageDraw.Draw(img)
    x0, x1, ym, amp = 160, 1760, 560, 220
    d.line([(x0, ym + amp + 60), (x1, ym + amp + 60)], fill=(60, 60, 60), width=3)
    for i in range(5):
        x = x0 + i * (x1 - x0) / 4
        label(img, (x, ym + amp + 110), f"{i * 6:02d}:00", size=30, color=(60, 60, 60), anchor="ms")
    p = ease(tl / 2.5)
    pts = [(x0 + u * (x1 - x0), ym - amp * math.sin(u * 2 * math.pi * 1.0 - 0.8)) for u in np.linspace(0, p, 200)]
    if window and p >= 1:
        a, b = 0.18, 0.42
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(lay).rectangle([x0 + a * (x1 - x0), ym - amp - 40, x0 + b * (x1 - x0), ym + amp + 60],
                                      fill=(222, 120, 60, 70))
        img.alpha_composite(lay)
        label(img, (x0 + (a + b) / 2 * (x1 - x0), ym - amp - 60), "deep enough", size=36, color=(170, 80, 40), anchor="ms")
    if ship_line:
        d.line([(x0, ym - amp * 0.45), (x1, ym - amp * 0.45)], fill=(170, 80, 40), width=3)
        label(img, (x1, ym - amp * 0.45 - 14), "big ship needs", size=28, color=(170, 80, 40), anchor="rs")
    if len(pts) > 1:
        d.line(pts, fill=(36, 96, 110), width=8)
    label(img, (W / 2, 140), title, size=54, color=(30, 50, 60), anchor="mm")
    return img


def years_bar(items, t, title=None, base=None):
    """items: [(label, x01, start_time, mark)] — markers popping onto a horizontal bar."""
    img = base.copy() if base is not None else Image.new("RGBA", (W, H), (20, 32, 40, 255))
    d = ImageDraw.Draw(img)
    y = 560
    d.line([(160, y), (1760, y)], fill=(250, 238, 210), width=6)
    for lab, u, s, mark in items:
        if t < s:
            continue
        a = ease((t - s) / 0.4)
        x = 160 + u * 1600
        r = 22 * a
        d.ellipse([x - r, y - r, x + r, y + r], fill=(222, 120, 60))
        label(img, (x, y - 50), lab, size=52, anchor="ms")
        if mark:
            label(img, (x, y + 90), mark, size=34, anchor="ms", color=(170, 205, 210))
    if title:
        label(img, (W / 2, 220), title, size=58, anchor="mm")
    return img


def boat_sprite(flip=False):
    b = cached("boat", lambda: load("viet-boat.png"))
    return b.transpose(Image.FLIP_LEFT_RIGHT) if flip else b


def place_boat(frame, x, yb, w, flip=False):
    b = boat_sprite(flip)
    b = b.resize((int(w), int(w * b.height / b.width)), Image.LANCZOS)
    frame.alpha_composite(b, (int(x), int(yb - b.height)))


def region_map(lon, lat, wdeg, key):
    return cached(("map", key), lambda: map_frame(_load_polys("ne_10m_land.geojson") if wdeg < 20 else
                                                   _load_polys("ne_50m_land.geojson"),
                                                   _load_rivers({"Hong", "Da"}), lon, lat, wdeg,
                                                   Image.fromarray(np.random.default_rng(3).integers(
                                                       0, 255, (H, W), dtype=np.uint8)).convert("RGB")))


def pin_at(frame, pr, lonlat, name, t, side="r", color=(222, 120, 60), size=38):
    x, y = (float(v) for v in pr(*lonlat))
    d = ImageDraw.Draw(frame)
    r = 14 + 4 * math.sin(t * 2 * math.pi)
    d.ellipse([x - r, y - r, x + r, y + r], outline=color, width=4)
    d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=color)
    if name:
        label(frame, (x + 26, y + 12) if side == "r" else (x - 26, y + 12), name, size=size,
              anchor="ls" if side == "r" else "rs")
    return x, y


def arrow_path(frame, pts, p, color=(222, 120, 60), width=7):
    n = max(2, int(len(pts) * max(0.0, min(1.0, p))))
    seg = [tuple(float(v) for v in q) for q in pts[:n]]
    d = ImageDraw.Draw(frame)
    if len(seg) > 1:
        d.line(seg, fill=color, width=width)
        (ax, ay), (bx, by) = seg[-2], seg[-1]
        ang = math.atan2(by - ay, bx - ax)
        d.polygon([(bx + 22 * math.cos(ang), by + 22 * math.sin(ang)),
                   (bx + 16 * math.cos(ang + 2.4), by + 16 * math.sin(ang + 2.4)),
                   (bx + 16 * math.cos(ang - 2.4), by + 16 * math.sin(ang - 2.4))], fill=color)


def slide_card(frame, c, x, y, tl, from_dx=-900, angle=-2, t=0.0):
    a = ease(tl / 0.6)
    paste_card(frame, c, x + (1 - a) * from_dx, y + 4 * math.sin(t * 2), angle)


def cross_out(frame, x, y, w, h, p):
    d = ImageDraw.Draw(frame)
    q = ease(p)
    d.line([(x + 20, y + 20), (x + 20 + (w - 40) * q, y + 20 + (h - 40) * q)], fill=(200, 40, 40), width=16)
    d.line([(x + w - 20, y + 20), (x + w - 20 - (w - 40) * q, y + 20 + (h - 40) * q)], fill=(200, 40, 40), width=16)


# ---------------------------------------------------------------- scene 4 (Part 2: the trap, 938)
def scene_04():
    river, low = bg("bg-river-high-tide-dawn.png"), bg("bg-river-low-tide-stakes.png")
    nq = card("portrait-ngo-quyen.png", "Ngô Quyền", "938")
    liu = card("portrait-liu-hongcao.png", "Lưu Hoằng Tháo", "Southern Han prince")
    ship = load_ship()

    def s_tidal(t, tl, f, T, d):
        fr = push(river, tl, d, 1.0, 1.1)
        if t >= T[1]:
            caption(fr, "A tidal river", ease((t - T[1]) / 0.4), y=160, size=90)
        return fr

    def s_tide(t, tl, f, T, d):
        # rises during phrase 2, falls during phrase 3
        lvl = ease((t - T[2]) / 2.5) if t < T[3] else 1 - ease((t - T[3]) / 2.5)
        return cross_section(lvl, grown=0.0, title="Twice a day, the estuary fills and drains")

    def s_stakes(t, tl, f, T, d):
        grown = ease((t - T[4]) / max(T[6] - T[4] - 0.5, 1))
        lvl = ease((t - T[6]) / 1.5)
        fr = cross_section(lvl, grown=grown, title="Iron-tipped stakes across the estuary")
        if t >= T[6]:
            lower_third(fr, "High tide: stakes hidden", ease((t - T[6]) / 0.5))
        return fr

    def s_bait(t, tl, f, T, d):
        fr = river.copy()
        water_shimmer(fr, f, 600, 1060, (255, 214, 160, 60))
        if t < T[8]:
            caption(fr, "The bait", ease(tl / 0.4), y=200, size=100)
            return fr
        k = (t - T[8]) / (T[11] - T[8])
        # small boats row out (left), then turn and flee upriver (right)
        for i in range(3):
            if k < 0.25:
                x = 1300 - 600 * ease(k / 0.25) + i * 90
                flip = False
            else:
                x = 700 + 900 * ease((k - 0.25) / 0.75) + i * 90
                flip = True
            place_boat(fr, x, 830 + 25 * i, 260, flip=flip)
        # the fleet follows, over the hidden stakes
        for i, (y, w) in enumerate(((800, 420), (720, 320), (660, 240))):
            x = -500 + 1500 * ease(k) - i * 120
            place_ship(fr, ship, x, y + 4 * math.sin(t * 2.5 + i), w)
        if t >= T[9]:  # ghost of the stakes under the water
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            dd = ImageDraw.Draw(lay)
            for j in range(10):
                bx = 500 + j * 110
                dd.polygon([(bx - 10, 1080), (bx + 10, 1080), (bx + 30, 900), (bx + 24, 900)], fill=(20, 30, 30, 90))
            fr.alpha_composite(lay)
        if t >= T[10]:
            caption(fr, "…and wait for the tide.", ease((t - T[10]) / 0.4), y=160)
        return fr

    def s_stuck(t, tl, f, T, d):
        fr = push(low, tl, d, 1.0, 1.1, 0.5, 0.6)
        crash = ease((t - T[13]) / 1.2) if t >= T[13] else 0
        for i, (x, yb, w, ang) in enumerate(((560 + 120 * crash, 690, 420, 6), (1010 - 80 * crash, 640, 300, -9),
                                             (1290, 610, 210, 12))):
            shake = 4 * math.sin(t * 9) if T[12] <= t < T[14] else 0
            place_ship(fr, ship, x + shake, yb + 18, w, angle=ang, submerge=0.0)
            dd = ImageDraw.Draw(fr)
            for k in range(3):
                stake(dd, x + w * (0.25 + 0.25 * k), yb + 30, 90 + 10 * k, lean=12 * (k - 1))
        lower_third(fr, "Low tide: trap closes", ease(tl / 0.5))
        return fr

    def s_attack(t, tl, f, T, d):
        fr = push(low, tl, d, 1.1, 1.2, 0.5, 0.6)
        for i, (x, yb, w, ang) in enumerate(((680, 690, 420, 6), (930, 640, 300, -9), (1290, 610, 210, 12))):
            place_ship(fr, ship, x, yb + 18, w, angle=ang, submerge=0.0)
        if t >= T[15]:
            flames(fr, [(800, 640), (1000, 600), (1330, 590)], f, 1.8)
        for i in range(4):
            u = ease(tl / 2.0)
            place_boat(fr, -300 + u * (500 + i * 120), 900 + 30 * (i % 2), 230, flip=True)
            place_boat(fr, W + 100 - u * (480 + i * 110), 880 + 30 * (i % 2), 230, flip=False)
        fr = red_flash(fr, max(0.0, 1 - tl / 0.6) if t < T[15] else 0)
        if t < T[15]:
            slide_card(fr, scaled(nq, 0.6), 60, 60, tl, t=t)
        else:
            lc = scaled(liu, 0.6)
            paste_card(fr, grey(lc) if t >= wt(4, 16, "killed") else lc, 60, 60, -2)
            if t >= wt(4, 16, "killed"):
                cross_out(fr, 60, 60, lc.width, lc.height, (t - wt(4, 16, "killed")) / 0.4)
            lower_third(fr, "938: Southern Han fleet destroyed", ease((t - T[15]) / 0.5))
        return fr

    def s_king(t, tl, f, T, d):
        fr = push(bg("bg-co-loa-citadel.png"), tl, d, 1.0, 1.15)
        lower_third(fr, "939: Ngô Quyền becomes king – capital Cổ Loa", ease(tl / 0.5))
        if t >= T[18]:
            caption(fr, "End of ~1,000 years of northern rule", ease((t - T[18]) / 0.5), y=150)
        return fr

    def s_end(t, tl, f, T, d):
        fr = darken(push(river, tl, d, 1.0, 1.08), 0.35)
        return big_text(fr, [("One battle.", T[19], None), ("One river.", wt(4, 19, "one", 1), None),
                             ("A turning point.", T[20], 70)], t, T)

    return run_shots(4, [(0, s_tidal), (2, s_tide), (4, s_stakes), (7, s_bait), (11, s_stuck),
                         (14, s_attack), (17, s_king), (19, s_end)])


# ---------------------------------------------------------------- scene 5 (Part 3: 1287–1288)
def scene_05():
    import json
    thd = card("portrait-tran-hung-dao.png", "Trần Hưng Đạo", "1288")
    tog = card("portrait-toghan.png", "Toghan", "son of Kublai Khan")
    nq_map = region_map(106.9, 21.0, 2.6, "vn-close")

    def yuan_map():
        def build():
            img, pr = map_frame(_load_polys("ne_50m_land.geojson"), [], 103, 33, 70,
                                Image.fromarray(np.random.default_rng(3).integers(0, 255, (H, W), dtype=np.uint8)).convert("RGB"))
            data = json.loads((DATA / "ne_50m_admin0.geojson").read_text(encoding="utf-8"))
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(lay)
            for ft in data["features"]:
                if ft["properties"].get("ADMIN") not in ("China", "Mongolia"):
                    continue
                g = ft["geometry"]
                for poly in ([g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]):
                    pts = [tuple(float(v) for v in pr(lo, la)) for lo, la in poly[0]]
                    if len(pts) > 2:
                        d.polygon(pts, fill=(172, 44, 34, 85), outline=(172, 44, 34, 200))
            return img, pr, lay
        return cached("yuan", build)

    def s_forward(t, tl, f, T, d):
        fr = Image.new("RGBA", (W, H), (20, 32, 40, 255))
        yr = int(938 + (1288 - 938) * ease(tl / 2.2))
        label(fr, (W / 2, H / 2), str(yr), size=220, anchor="mm", font=FONT, color=(245, 225, 180))
        label(fr, (W / 2, H / 2 + 170), "+350 years", size=48, anchor="mm", color=(170, 205, 210))
        return fr

    def s_tran(t, tl, f, T, d):
        img, pr = region_map(106.2, 21.2, 6.0, "vn-mid")
        fr = img.copy()
        x, y = (float(v) for v in pr(105.85, 21.03))
        label(fr, (x, y - 40), "ĐẠI VIỆT", size=70, anchor="ms", color=(30, 50, 60))
        label(fr, (x, y + 20), "Trần dynasty", size=44, anchor="ms", color=(170, 80, 40))
        return fr

    def s_mongols(t, tl, f, T, d):
        img, pr, lay = yuan_map()
        fr = img.copy()
        a = ease((t - T[3]) / 0.8) if t >= T[3] else 0.25
        l2 = lay.copy()
        l2.putalpha(l2.getchannel("A").point(lambda v: int(v * a)))
        fr.alpha_composite(l2)
        x, y = (float(v) for v in pr(104, 37))
        if t >= T[3]:
            label(fr, (x, y), "YUAN (Mongol-ruled)", size=60, anchor="mm")
            label(fr, (x, y + 60), "approximate extent", size=30, anchor="mm", color=(60, 60, 60))
        pin_at(fr, pr, BACH_DANG, "Đại Việt", t, side="l")
        caption(fr, "The most feared military power on Earth", ease(tl / 0.5), y=110, size=56)
        return fr

    inv = [("1258", 0.15), ("1285", 0.55), ("1287–88", 0.9)]

    def s_invasions(t, tl, f, T, d):
        items = [(inv[0][0], inv[0][1], wt(5, 4, "1258"), "pushed back" if t >= T[5] else None),
                 (inv[1][0], inv[1][1], wt(5, 4, "1285"), "pushed back" if t >= T[5] else None)]
        if t >= T[7]:
            items.append((inv[2][0], inv[2][1], T[7] + 0.5, None))
        fr = years_bar(items, t, title="Mongol invasions of Đại Việt")
        if t >= T[7]:
            slide_card(fr, scaled(tog, 0.5), 1400, 640, t - T[7] - 1.0, from_dx=900, angle=3, t=t)
            lower_third(fr, "3rd Mongol invasion: 1287–1288", ease((t - T[7]) / 0.5))
        return fr

    def s_versus(t, tl, f, T, d):
        fr = darken(bg("bg-river-high-tide-dawn.png"), 0.6)
        paste_card(fr, scaled(tog, 0.8), 1100, 100, 3)
        slide_card(fr, scaled(thd, 0.8), 330, 100, tl, t=t)
        label(fr, (W / 2 + 30, 560), "vs", size=110, anchor="mm", color=(222, 120, 60))
        return fr

    def s_skip(t, tl, f, T, d):
        img, pr = nq_map
        fr = img.copy()
        pin_at(fr, pr, BACH_DANG, "Bạch Đằng", t, side="l")
        if t >= T[10]:
            pin_at(fr, pr, VAN_DON, "Vân Đồn", t, color=(200, 60, 50))
            caption(fr, "It started somewhere else", ease((t - T[10]) / 0.5), y=130)
        return fr

    def s_supply(t, tl, f, T, d):
        if t < T[12]:
            img, pr = nq_map
            fr = img.copy()
            pin_at(fr, pr, VAN_DON, "Vân Đồn", t, color=(200, 60, 50))
            route = [(108.6, 21.45), (108.1, 21.3), (107.75, 21.15), (107.5, 21.08)]
            p = ease(tl / max(d - 0.3, 0.5))
            pts = [pr(*route_point(route, q / 50 * p)) for q in range(51)]
            arrow_path(fr, pts, 1.0, color=(200, 60, 50), width=5)
            icon = cached("icon", lambda: load_ship().resize((70, int(70 * load_ship().height / load_ship().width)), Image.LANCZOS))
            x, y = (float(v) for v in pr(*route_point(route, p)))
            fr.alpha_composite(icon, (int(x - 35), int(y - icon.height + 6)))
            caption(fr, "Grain for the Yuan army, by sea", ease(tl / 0.5), y=130, size=56)
            return fr
        fr = push(bg("bg-grain-fleet-burning.png"), t - T[12], d, 1.0, 1.12)
        lower_third(fr, "Vân Đồn: the supply fleet is destroyed", ease((t - T[12]) / 0.5))
        caption(fr, "Trần Khánh Dư", ease((t - T[12] - 1.2) / 0.5), y=120, size=64)
        return fr

    def s_camp(t, tl, f, T, d):
        fr = push(bg("bg-mongol-camp.png"), tl, d, 1.0, 1.12)
        for i, (txt, dt) in enumerate((("deep in enemy territory", wt(5, 13, "deep") - T[13]), ("rice running out", wt(5, 13, "rice") - T[13]),
                                        ("the hot season coming", wt(5, 13, "hot") - T[13]))):
            caption(fr, txt, ease((tl - dt) / 0.4), y=110 + i * 80, size=54)
        return fr

    def s_retreat(t, tl, f, T, d):
        img, pr = nq_map
        fr = img.copy()
        pin_at(fr, pr, VAN_KIEP, "Vạn Kiếp (Yuan base)", t, side="l", color=(200, 60, 50))
        route = [VAN_KIEP, (106.55, 21.0), (106.72, 20.95), BACH_DANG, (106.95, 20.75), (107.3, 20.6)]
        p = ease((t - T[15] - 0.5) / 3.0) if t >= T[15] else 0
        pts = [pr(*route_point(route, q / 60)) for q in range(61)]
        arrow_path(fr, pts, p, color=(200, 60, 50))
        pin_at(fr, pr, BACH_DANG, "Bạch Đằng", t)
        caption(fr, "Spring 1288: retreat", ease(tl / 0.5), y=130)
        if t >= T[15]:
            caption(fr, "Fleet: Omar · Fan Yi", ease((t - T[15]) / 0.5), y=210, size=48)
        return fr

    def s_knew(t, tl, f, T, d):
        fr = darken(push(bg("bg-river-high-tide-dawn.png"), tl, d, 1.0, 1.1), 0.3)
        slide_card(fr, scaled(thd, 0.75), 140, 100, tl, t=t)
        if t >= T[17]:
            label(fr, (1350, 540), "He knew this river.", size=72, anchor="mm")
        return fr

    return run_shots(5, [(0, s_forward), (1, s_tran), (2, s_mongols), (4, s_invasions), (8, s_versus),
                         (9, s_skip), (11, s_supply), (13, s_camp), (14, s_retreat), (16, s_knew)])


# ---------------------------------------------------------------- scene 6 (Part 4: the trap again, 1288)
def scene_06():
    nq = card("portrait-ngo-quyen.png", "Ngô Quyền", "938")
    thd = card("portrait-tran-hung-dao.png", "Trần Hưng Đạo", "1288")
    tog = card("portrait-toghan.png", "Toghan", "escaped")
    ship = load_ship()

    def s_same(t, tl, f, T, d):
        fr = darken(bg("bg-river-low-tide-stakes.png"), 0.6)
        paste_card(fr, scaled(nq, 0.8), 300, 100, -3)
        slide_card(fr, scaled(thd, 0.8), 1130, 100, tl, from_dx=900, angle=3, t=t)
        label(fr, (W / 2 + 10, 520), "=", size=150, anchor="mm", color=(222, 120, 60))
        return fr

    def s_drive(t, tl, f, T, d):
        return push(bg("bg-driving-stakes.png"), tl, d, 1.0, 1.15, 0.45, 0.6)

    def s_tide(t, tl, f, T, d):
        return tide_chart(t, tl, title="He studied the tide. He picked the timing.")

    def s_date(t, tl, f, T, d):
        fr = bg("bg-river-high-tide-dawn.png").copy()
        k = ease(tl / d)
        for i, (y, w) in enumerate(((800, 420), (720, 320), (660, 240))):
            place_ship(fr, ship, -500 + 1500 * k - i * 120, y + 4 * math.sin(t * 2.5 + i), w)
        caption(fr, "9 April 1288", ease(tl / 0.4), y=170, size=110)
        return fr

    def s_pattern(t, tl, f, T, d):
        # 938 and 1288 side by side, moving in sync
        lvl = 1.0 if t < wt(6, 5, "let") else 1 - ease((t - wt(6, 5, "let")) / 1.5)
        fr = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        cross_section(lvl, 1.0, ships=[(0.35, 300)], labels=False, width=W // 2 - 6, x0=0, canvas=fr)
        cross_section(lvl, 1.0, ships=[(0.35, 300)], labels=False, width=W // 2 - 6, x0=W // 2 + 6, canvas=fr)
        label(fr, (W / 4, 120), "938", size=90, anchor="mm", font=FONT, color=(30, 50, 60))
        label(fr, (3 * W / 4, 120), "1288", size=90, anchor="mm", font=FONT, color=(30, 50, 60))
        txt = "Same river. Same tide. Same trap."
        for cand, dt in (("Draw them in at high water.", 0.0), ("Wait.", wt(6, 5, "wait") - T[5]), ("Let the river drop.", wt(6, 5, "let") - T[5])):
            if t >= T[5] + dt:
                txt = cand
        band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(band).rectangle([0, 960, W, 1060], fill=(20, 32, 40, 230))
        fr.alpha_composite(band)
        label(fr, (W / 2, 1010), txt, size=54, anchor="mm")
        return fr

    def s_battle(t, tl, f, T, d):
        fr = push(bg("bg-battle-1288.png"), tl, d, 1.0, 1.15, 0.45, 0.5)
        if t >= T[7]:
            flames(fr, [(520, 420), (1180, 470)], f, 0.8)
        if t >= T[8]:
            lower_third(fr, "Burned, sunk or captured", ease((t - T[8]) / 0.5))
        return fr

    def s_omar(t, tl, f, T, d):
        fr = darken(bg("bg-battle-1288.png").filter(ImageFilter.GaussianBlur(6)), 0.55)
        return big_text(fr, [("Omar – captured", T[9] + 0.2, 80), ("Fan Yi – killed", wt(6, 9, "fan"), 80)], t, T)

    def s_toghan(t, tl, f, T, d):
        img, pr = region_map(107.5, 22.6, 7.0, "north")
        fr = img.copy()
        pts = [pr(*route_point([VAN_KIEP, (106.6, 21.8), (106.75, 22.5), (107.0, 23.3)], q / 40)) for q in range(41)]
        arrow_path(fr, pts, ease(tl / 2.0), color=(200, 60, 50))
        pin_at(fr, pr, VAN_KIEP, "Vạn Kiếp", t, side="l", color=(200, 60, 50))
        tc = scaled(tog, 0.5)
        paste_card(fr, grey(tc), 1350, 80, 3)
        if t >= T[11]:
            fr = darken(fr, 0.55)
            fr = years_bar([("1258", 0.15, T[11], "✓"), ("1285", 0.55, T[11] + 0.3, "✓"), ("1288", 0.9, T[11] + 0.6, "✓")],
                           t, title="Đại Việt 3 – Mongols 0", base=fr)
        return fr

    def s_wait(t, tl, f, T, d):
        fr = darken(bg("bg-river-low-tide-stakes.png"), 0.65)
        lines = [("But wait…", T[12], 110), ("Why did the Yuan fall for it?", T[13], 70)]
        if t >= T[14]:
            lines = [("Not surprise.", T[15], 100), ("The river.", wt(6, 15, "river"), 130)]
        return big_text(fr, lines, t, T)

    def s_deep(t, tl, f, T, d):
        fr = tide_chart(t, tl, title="Big ships need deep water", ship_line=True)
        if t >= T[18]:
            label(fr, (W / 2, 960), "A retreating fleet can't wait for the next window.", size=44, anchor="mm",
                  color=(170, 80, 40))
        return fr

    def s_hour(t, tl, f, T, d):
        fr = darken(push(bg("bg-river-high-tide-dawn.png"), tl, d, 1.0, 1.1), 0.3)
        return big_text(fr, [("They knew the enemy.", T[19], 70), ("They knew the tide –", T[20], 90),
                             ("almost to the hour.", wt(6, 20, "almost"), 90)], t, T)

    return run_shots(6, [(0, s_same), (1, s_drive), (2, s_tide), (3, s_date), (4, s_pattern), (6, s_battle),
                         (9, s_omar), (10, s_toghan), (12, s_wait), (16, s_deep), (19, s_hour)])


# ---------------------------------------------------------------- scene 7 (Part 5: the stakes are still there)
def scene_07():
    def s_chills(t, tl, f, T, d):
        fr = push(bg("bg-excavation.png"), tl, d, 1.0, 1.1)
        if t >= T[1]:
            caption(fr, "The evidence is still in the ground", ease((t - T[1]) / 0.5), y=130)
        return fr

    def s_found(t, tl, f, T, d):
        img, pr = region_map(106.75, 20.92, 1.2, "quangyen")
        fr = img.copy()
        pin_at(fr, pr, YEN_GIANG, "Yên Giang (Quảng Yên)", t)
        lower_third(fr, "Yên Giang stake field – discovered 1958", ease(tl / 0.5))
        return fr

    def s_more(t, tl, f, T, d):
        return push(bg("bg-excavation.png"), tl, d, 1.15, 1.3, 0.55, 0.65)

    def s_dating(t, tl, f, T, d):
        fr = Image.new("RGBA", (W, H), (20, 32, 40, 255))
        dd = ImageDraw.Draw(fr)
        x0, x1, y = 200, 1720, 600
        yr = lambda v: x0 + (v - 1150) / (1500 - 1150) * (x1 - x0)
        dd.line([(x0, y), (x1, y)], fill=(250, 238, 210), width=5)
        for v in range(1150, 1501, 50):
            dd.line([(yr(v), y - 12), (yr(v), y + 12)], fill=(250, 238, 210), width=3)
            label(fr, (yr(v), y + 60), str(v), size=34, anchor="ms")
        if t >= T[5]:
            a = ease((t - T[5]) / 0.8)
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(lay).rectangle([yr(1270), y - 60, yr(1270) + (yr(1400) - yr(1270)) * a, y + 14],
                                          fill=(222, 120, 60, 170))
            fr.alpha_composite(lay)
            label(fr, ((yr(1270) + yr(1400)) / 2, y - 80), "Radiocarbon: ~1270–1400", size=44, anchor="ms")
        if t >= T[6]:
            dd = ImageDraw.Draw(fr)
            dd.line([(yr(1288), y - 140), (yr(1288), y + 20)], fill=(170, 205, 210), width=5)
            label(fr, (yr(1288), y - 160), "1288", size=52, anchor="ms", color=(170, 205, 210), font=FONT)
        label(fr, (W / 2, 200), "Stakes from Yên Giang & Đồng Má Ngựa", size=56, anchor="mm")
        lower_third(fr, "Dated: late 13th–14th century", ease((t - T[5]) / 0.5) if t >= T[5] else 0)
        return fr

    def s_museum(t, tl, f, T, d):
        fr = push(bg("bg-museum-stake.png"), tl, d, 1.0, 1.15, 0.5, 0.55)
        lower_third(fr, "National Museum of Vietnamese History, Hà Nội", ease(tl / 0.5))
        return fr

    def s_caveat(t, tl, f, T, d):
        img, pr = region_map(106.75, 20.92, 1.2, "quangyen")
        fr = img.copy()
        pin_at(fr, pr, YEN_GIANG, "Yên Giang: 13th–14th c.", t)
        caption(fr, "One honest caveat", ease(tl / 0.4), y=130, size=70)
        if t >= T[10]:
            pin_at(fr, pr, THUY_NGUYEN, "2019–20 piles: far older", t, side="l", color=(170, 205, 210))
            caption(fr, "Likely Đông Sơn stilt houses, not the battle", ease((t - T[10] - 1.5) / 0.5), y=930, size=48)
        if t >= T[11]:
            caption(fr, "Every find gets tested", ease((t - T[11]) / 0.5), y=210, size=50)
        return fr

    def s_evidence(t, tl, f, T, d):
        fr = darken(push(bg("bg-museum-stake.png"), tl, d, 1.1, 1.2, 0.5, 0.5), 0.45)
        return big_text(fr, [("Evidence,", T[13], 100), ("not just legend.", wt(7, 13, "not"), 100)], t, T)

    return run_shots(7, [(0, s_chills), (2, s_found), (3, s_more), (4, s_dating), (7, s_museum),
                         (8, s_caveat), (12, s_evidence)])


# ---------------------------------------------------------------- scene 8 (Part 6: what it teaches)
def scene_08():
    river = bg("bg-river-high-tide-dawn.png")
    liu = card("portrait-liu-hongcao.png", "Southern Han", "938")
    tog = card("portrait-toghan.png", "Yuan", "1288")
    nq = card("portrait-ngo-quyen.png", "Ngô Quyền", "938")
    thd = card("portrait-tran-hung-dao.png", "Trần Hưng Đạo", "1288")

    def s_why(t, tl, f, T, d):
        fr = darken(push(river, tl, d), 0.35)
        return big_text(fr, [("Why did the same trap work twice?", T[0], 80)], t, T)

    def s_invaders(t, tl, f, T, d):
        fr = darken(river, 0.55)
        slide_card(fr, scaled(liu, 0.75), 300, 120, tl, t=t)
        slide_card(fr, scaled(tog, 0.75), 1160, 120, tl - 0.3, from_dx=900, angle=3, t=t)
        if t >= T[2]:
            caption(fr, "Powerful. Experienced.", ease((t - T[2]) / 0.4), y=1000, size=60)
        return fr

    def s_home(t, tl, f, T, d):
        fr = darken(push(river, tl, d, 1.05, 1.15), 0.5)
        paste_card(fr, scaled(nq, 0.65), 160, 140, -3)
        paste_card(fr, scaled(thd, 0.65), 1360, 140, 3)
        lines = [("Home ground = weapon", T[3], 58)]
        if t >= T[4]:
            lines.append(("river · tide · timing", T[4], 56))
        if t >= T[5]:
            lines.append(("+ knowing their own history", T[5] + 0.8, 48))
        return big_text(fr, lines, t, T)

    def s_one(t, tl, f, T, d):
        fr = darken(push(river, tl, d, 1.0, 1.15), 0.3)
        return big_text(fr, [("Two empires.", T[6], 100), ("Two fleets.", T[7], 100), ("One river.", T[8], 130)], t, T)

    return run_shots(8, [(0, s_why), (1, s_invaders), (3, s_home), (6, s_one)])


# ---------------------------------------------------------------- scene 9 (Outro)
def scene_09():
    thd = card("portrait-tran-hung-dao.png", "Trần Hưng Đạo", "1288")

    def s_ask(t, tl, f, T, d):
        fr = darken(push(bg("bg-river-high-tide-dawn.png"), tl, d), 0.45)
        slide_card(fr, scaled(thd, 0.8), 180, 100, tl, t=t)
        label(fr, (1280, 470), "One question for", size=60, anchor="mm")
        label(fr, (1280, 560), "Trần Hưng Đạo?", size=80, anchor="mm", color=(255, 214, 160))
        if t >= T[1]:
            label(fr, (1280, 680), "→ comments", size=50, anchor="mm", color=(170, 205, 210))
        return fr

    def s_bye(t, tl, f, T, d):
        k = ease(tl / d)
        fr = push(bg("bg-river-high-tide-dawn.png"), tl, d, 1.0, 1.12)
        fr = big_text(fr, [("See you on the river.", T[2], 90)], t, T)
        return darken(fr, 0.9 * max(0.0, (tl - 1.6) / max(d - 1.6, 0.1)), (0, 0, 0))

    return run_shots(9, [(0, s_ask), (2, s_bye)])


def render(scene_no, frames):
    """Picture-only clip; narration, joins and export happen in DaVinci Resolve."""
    clips = ROOT / "assets" / "clips"
    clips.mkdir(exist_ok=True)
    out = clips / f"scene-{scene_no:02d}.mp4"
    cmd = [FFMPEG, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    for fr in frames:
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
    print("wrote", out)


SCENES = {1: scene_01, 2: scene_02, 3: scene_03, 4: scene_04, 5: scene_05, 6: scene_06, 7: scene_07, 8: scene_08, 9: scene_09}

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--fps" in args:  # e.g. --fps 24 for smooth motion (default 8)
        i = args.index("--fps"); FPS = int(args[i + 1]); del args[i:i + 2]
    nums = [int(a) for a in args] or [1]
    for s in nums:
        render(s, SCENES[s]())
