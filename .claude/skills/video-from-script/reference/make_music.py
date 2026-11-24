"""Original orchestral background bed, synthesized in code (no licensing / attribution needed).

D minor, ~60 bpm: string ensemble chords, low strings, a sparse horn motif and timpani.
Intensity follows the story (tense hook, builds into the 938 trap, peaks at the 1288 battle, settles in the outro).
Length = exact timeline length (sum of the scene clips), with a fade-out at the end.
Output: assets/audio/music-orchestral.wav, loudness-normalised to -16 LUFS like the narration;
the Resolve script then sets it ~30 % (-10.5 dB) under that.

Usage: python make_music.py
"""
import re, subprocess, math
from pathlib import Path
import numpy as np, imageio_ffmpeg

ROOT = Path(__file__).parent
FF = imageio_ffmpeg.get_ffmpeg_exe()
SR = 44100
rng = np.random.default_rng(7)


def dur(p):
    e = subprocess.run([FF, "-i", str(p)], capture_output=True, text=True).stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", e).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


# scene boundaries on the timeline (clip length = narration + 0.3 s, rounded up to whole frames)
FPS = 8  # this video's clips are 8 fps
clips = [math.ceil((dur(ROOT / f"assets/audio/scene-{i:02d}.mp3") + 0.3) * FPS) / FPS for i in range(1, 10)]
starts = np.concatenate([[0], np.cumsum(clips)])
TOTAL = float(starts[-1])
N = int(TOTAL * SR)
t_all = np.arange(N) / SR

# intensity per scene (0..1): hook, intro, 937-938, trap 938, 1287-88, trap 1288, stakes, lesson, outro
LEVEL = [0.6, 0.5, 0.6, 0.85, 0.75, 1.0, 0.5, 0.6, 0.45]


def intensity(t):
    """Smoothly interpolated scene intensity at times t."""
    mids = (starts[:-1] + starts[1:]) / 2
    return np.interp(t, mids, LEVEL)


# --- band-limited saw wavetable (harmonics up to ~5 kHz at the notes we use)
TAB = 4096
ph = np.arange(TAB) / TAB


def table(nh, rolloff=1.0):
    w = np.zeros(TAB)
    for k in range(1, nh + 1):
        w += np.sin(2 * np.pi * k * ph) / k ** rolloff
    return w / np.abs(w).max()


SAW = table(24)            # strings
HORN = table(8, 1.6)       # mellow brass


def osc(freq, n, tab, vib=0.0, vib_rate=5.0, phase0=0.0):
    t = np.arange(n) / SR
    f = freq * (1 + vib * np.sin(2 * np.pi * vib_rate * t + rng.uniform(0, 6.28)))
    phase = (phase0 + np.cumsum(f) / SR) % 1.0
    return tab[(phase * TAB).astype(np.int32)]


def env(n, a, r):
    e = np.ones(n)
    na, nr = min(int(a * SR), n), min(int(r * SR), n)
    e[:na] = np.linspace(0, 1, na) ** 1.5
    e[n - nr:] *= np.linspace(1, 0, nr) ** 1.5
    return e


def note_hz(n):  # MIDI -> Hz
    return 440.0 * 2 ** ((n - 69) / 12)


# --- harmony: 4-bar loop of 4 s chords (D minor), with a second, darker variant
PROG_A = [[50, 57, 62, 65], [46, 53, 58, 62], [41, 53, 57, 60], [48, 55, 60, 64]]   # Dm  Bb  F   C
PROG_B = [[50, 57, 62, 65], [43, 55, 58, 62], [46, 53, 58, 65], [45, 52, 57, 61]]   # Dm  Gm  Bb  A
CH = 4.0

L = np.zeros(N); R = np.zeros(N)


def add(sig, start, pan=0.0, gain=1.0):
    s = int(start * SR)
    e = min(N, s + len(sig))
    if e <= s:
        return
    sig = sig[: e - s] * gain
    L[s:e] += sig * math.cos((pan + 1) * math.pi / 4)
    R[s:e] += sig * math.sin((pan + 1) * math.pi / 4)


n_chords = int(math.ceil(TOTAL / CH))
for c in range(n_chords):
    t0 = c * CH
    prog = PROG_B if (c // 8) % 3 == 2 else PROG_A
    chord = prog[c % 4]
    n = int((CH + 1.6) * SR)  # overlap into the next chord (legato)
    lvl = float(intensity(np.array([t0 + 2]))[0])
    # string ensemble: upper voices, 3 detuned players each, spread across the stereo field
    for i, m in enumerate(chord[1:]):
        for d, pan in ((-0.06, -0.5), (0.0, 0.0), (0.07, 0.5)):
            add(osc(note_hz(m + d), n, SAW, vib=0.0035) * env(n, 1.4, 1.8), t0, pan + 0.15 * (i - 1), 0.05)
    # celli / basses: root, an octave down, swell with the story
    for d in (-0.05, 0.05):
        add(osc(note_hz(chord[0] - 12 + d), n, SAW, vib=0.002) * env(n, 1.0, 1.8), t0, -0.2, 0.08 * (0.6 + 0.6 * lvl))
    # violins an octave up only in the bigger scenes
    if lvl > 0.7:
        for d, pan in ((-0.08, -0.6), (0.08, 0.6)):
            add(osc(note_hz(chord[3] + 12 + d), n, SAW, vib=0.005) * env(n, 1.8, 1.8), t0, pan, 0.03 * (lvl - 0.6) / 0.4)

# --- horn motif (D – F – A – G – F – E – D), played at a few story beats
MOTIF = [(62, 1.0), (65, 1.0), (69, 2.0), (67, 1.0), (65, 1.0), (64, 1.0), (62, 3.0)]
for sc in (1, 3, 5, 8):               # intro, trap 938, trap 1288, outro
    t = starts[sc] + 1.0
    t = math.ceil(t / CH) * CH        # start on a chord change
    for m, b in MOTIF:
        n = int((b + 0.4) * SR)
        sig = osc(note_hz(m - 12), n, HORN, vib=0.004) * env(n, 0.25, 0.5)
        add(sig, t, 0.25, 0.09)
        t += b

# --- timpani: soft hit on every 4th chord, rolls into the dramatic scenes
def timp(freq, length=2.5, g=1.0):
    n = int(length * SR)
    tt = np.arange(n) / SR
    f = freq * (1 + 0.08 * np.exp(-tt * 20))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 2.2)
    thump = rng.normal(0, 1, n) * np.exp(-tt * 35) * 0.3
    return (body + thump) * g


for c in range(0, n_chords, 4):
    lvl = float(intensity(np.array([c * CH]))[0])
    add(timp(note_hz(38), g=0.12 * lvl), c * CH, -0.1)
for sc in (3, 4, 5):                  # 938 trap, 1287-88, 1288 trap: short roll leading into the scene
    t_end = starts[sc] + 0.2
    for k in range(14):
        add(timp(note_hz(38), 1.2, 0.03 + 0.07 * k / 13), t_end - 1.6 + k * 0.11, -0.1)

# --- hall reverb (tone low-pass is applied by ffmpeg at the end) (FFT convolution with a synthetic IR)
ir_n = int(2.8 * SR)
it = np.arange(ir_n) / SR
irL = rng.normal(0, 1, ir_n) * np.exp(-it * 2.6); irL[0] = 0
irR = rng.normal(0, 1, ir_n) * np.exp(-it * 2.6); irR[0] = 0
irL /= np.sqrt((irL ** 2).sum()); irR /= np.sqrt((irR ** 2).sum())


def conv(x, ir, blk=1 << 20):
    nfft = 1 << int(math.ceil(math.log2(blk + len(ir))))
    H = np.fft.rfft(ir, nfft)
    out = np.zeros(len(x) + len(ir))
    for s in range(0, len(x), blk):
        seg = x[s:s + blk]
        y = np.fft.irfft(np.fft.rfft(seg, nfft) * H, nfft)[: len(seg) + len(ir)]
        out[s:s + len(y)] += y
    return out[: len(x)]


wetL, wetR = conv(L, irL), conv(R, irR)
L, R = 0.65 * L + 0.55 * wetL, 0.65 * R + 0.55 * wetR

# fades: 2 s in, 5 s out at the very end of the timeline
fade = np.ones(N)
fade[: 2 * SR] = np.linspace(0, 1, 2 * SR)
fade[-5 * SR:] = np.linspace(1, 0, 5 * SR) ** 2
mix = np.stack([L * fade, R * fade], 1)
mix /= np.abs(mix).max() * 1.12

raw = ROOT / "assets/audio/_music_raw.wav"
pcm = (mix * 32767).astype("<i2")
import wave
with wave.open(str(raw), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
out = ROOT / "assets/audio/music-orchestral.wav"
subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(raw), "-af", "lowpass=f=5000,lowpass=f=5000,loudnorm=I=-16:TP=-1.5", "-ar", str(SR), str(out)],
               check=True)
raw.unlink()
print(out, f"{TOTAL:.2f}s")
