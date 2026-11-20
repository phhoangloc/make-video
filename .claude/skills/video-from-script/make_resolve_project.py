"""Package a video-from-script project for DaVinci Resolve.

Usage:
  python make_resolve_project.py scripts/<script-title> [--subtitles] [--music path.mp3 [--music-db -20]]
                                 [--transition 0.4] [--no-install]

Expects, per scene NN (01, 02, ...):
  assets/clips/scene-NN.mp4    animated picture, exact scene length, no audio
  assets/audio/scene-NN.mp3    narration
  assets/audio/scene-NN.json   phrase timings [{text,start,end}]  (or scene-NN.vtt)

Writes:
  assets/clips/handles/scene-NN.mp4   same clip + frozen-frame handles (for dissolves)
  assets/audio/subtitles.srt          merged subtitles on the timeline clock
  resolve/build_timeline.lua          script to run inside Resolve (Lua: always available,
                                      unlike Python which Resolve may not detect)
and installs a copy in Resolve's Workspace > Scripts > Utility menu.
"""
import argparse, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).parent
# Timeline rates Resolve offers. Clips at other rates (e.g. 8 fps) go on the smallest
# supported multiple, so every source frame is simply held 2-3x and timing stays exact.
RESOLVE_RATES = [24, 25, 30, 48, 50, 60, 16, 18, 72, 96, 100, 120]  # preferred first


def ffmpeg_exe():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit("ffmpeg not found: install it or `pip install imageio-ffmpeg`")


FF = ffmpeg_exe()


def probe(path):
    err = subprocess.run([FF, "-i", str(path)], capture_output=True, text=True).stderr
    h, mi, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err).groups()
    fps = re.search(r"([\d.]+) fps", err)
    wh = re.search(r"Video:.*?(\d{3,5})x(\d{3,5})", err)
    return (int(h) * 3600 + int(mi) * 60 + float(s), float(fps.group(1)) if fps else None,
            (int(wh.group(1)), int(wh.group(2))) if wh else None)


def section_names(script_md):
    """Section titles + narration from script.md, in order."""
    out = []
    if not script_md.exists():
        return out
    parts = re.split(r"^### +", script_md.read_text(encoding="utf-8"), flags=re.M)[1:]
    for p in parts:
        title = p.splitlines()[0].strip()
        nar = re.search(r"\*\*Narration:\*\*\s*(.+?)(?=\n\*\*|\Z)", p, flags=re.S)
        out.append((title, " ".join(nar.group(1).split()) if nar else ""))
    return out


def cues(audio_dir, nn):
    j = audio_dir / f"scene-{nn}.json"
    if j.exists():
        return [(c["start"], c["end"], c["text"]) for c in json.loads(j.read_text(encoding="utf-8"))]
    v = audio_dir / f"scene-{nn}.vtt"
    res = []
    if v.exists():
        ts = lambda x: sum(float(a) * b for a, b in zip(x.replace(",", ".").split(":"), (3600, 60, 1)))
        for blk in re.split(r"\n\s*\n", v.read_text(encoding="utf-8")):
            m = re.search(r"([\d:.,]+) --> ([\d:.,]+)\s*\n(.+)", blk, flags=re.S)
            if m:
                res.append((ts(m.group(1)), ts(m.group(2)), " ".join(m.group(3).split())))
    return res


def to_lua(v, ind=""):
    """Python value -> Lua literal."""
    if v is None:
        return "nil"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
    nxt = ind + "  "
    if isinstance(v, list):
        return "{\n" + "".join(f"{nxt}{to_lua(x, nxt)},\n" for x in v) + ind + "}"
    return "{\n" + "".join(f"{nxt}{k} = {to_lua(x, nxt)},\n" for k, x in v.items()) + ind + "}"


def srt_time(t):
    ms = int(round(t * 1000))
    return "%02d:%02d:%02d,%03d" % (ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, ms % 1000)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--subtitles", action="store_true", help="put subtitles on the timeline")
    ap.add_argument("--music", help="background music file")
    ap.add_argument("--music-db", type=float, default=-20.0, help="music level on A2 in dB (default -20)")
    ap.add_argument("--transition", type=float, default=0.4, help="cross-dissolve seconds (0 = cuts)")
    ap.add_argument("--no-install", action="store_true", help="don't copy into Resolve's Scripts menu")
    a = ap.parse_args()

    root = Path(a.project_dir).resolve()
    title = root.name
    clips_dir, audio_dir = root / "assets" / "clips", root / "assets" / "audio"
    clips = sorted(clips_dir.glob("scene-[0-9][0-9].mp4"))
    if not clips:
        sys.exit(f"no clips in {clips_dir} (expected scene-NN.mp4)")

    names = section_names(root / "script.md")
    _, fps, wh = probe(clips[0])
    fps = int(round(fps))
    tl_fps = next((r for r in RESOLVE_RATES if r >= fps and r % fps == 0), None)
    if tl_fps is None:
        sys.exit(f"{fps} fps has no matching DaVinci Resolve timeline rate; render at 24/25/30 fps")
    mult = tl_fps // fps
    handle = max(1, int(round(max(a.transition, 0.25) * fps)))  # frozen frames each side (clip fps)
    (clips_dir / "handles").mkdir(exist_ok=True)

    scenes, srt, t0 = [], [], 0.0
    for i, clip in enumerate(clips):
        nn = clip.stem.split("-")[1]
        dur, cfps, _ = probe(clip)
        if int(round(cfps)) != fps:
            sys.exit(f"{clip.name} is {cfps} fps, expected {fps}: render all scenes at one frame rate")
        frames = int(round(dur * fps))
        hclip = clips_dir / "handles" / clip.name
        pad = handle / fps
        subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(clip), "-vf",
                        f"tpad=start_mode=clone:start_duration={pad}:stop_mode=clone:stop_duration={pad}",
                        "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
                        str(hclip)], check=True)
        audio = audio_dir / f"scene-{nn}.mp3"
        name, note = names[i] if i < len(names) else (f"Scene {nn}", "")
        scenes.append({"name": f"{nn} · {name}", "note": note[:900], "clip": hclip.as_posix(),
                       "audio": audio.as_posix() if audio.exists() else None,
                       "frames": frames, "handle_frames": handle, "timeline_frames": frames * mult})
        for s, e, text in cues(audio_dir, nn):
            srt.append((t0 + s, t0 + e, text))
        t0 += frames / fps

    srt_path = audio_dir / "subtitles.srt"
    srt_path.write_text("".join(f"{k}\n{srt_time(s)} --> {srt_time(e)}\n{t}\n\n"
                                for k, (s, e, t) in enumerate(srt, 1)), encoding="utf-8")

    manifest = {
        "title": title, "project": title, "build_id": time.strftime("%Y%m%d-%H%M"),
        "fps": tl_fps, "clip_fps": fps, "width": wh[0], "height": wh[1],
        "scenes": scenes, "subtitles": srt_path.as_posix(), "burn_subtitles": a.subtitles,
        "music": Path(a.music).resolve().as_posix() if a.music else None,
        "music_db": a.music_db,
        "transition_frames": int(round(a.transition * tl_fps)),
        "render_dir": (root / "output").as_posix(),
        "log_path": (root / "resolve" / "build_log.txt").as_posix(),
    }
    code = (HERE / "resolve_timeline_template.lua").read_text(encoding="utf-8")
    code = code.replace("__MANIFEST__", to_lua(manifest))
    out = root / "resolve" / "build_timeline.lua"
    out.parent.mkdir(exist_ok=True)
    out.write_text(code, encoding="utf-8")
    (root / "resolve" / "build_timeline.py").unlink(missing_ok=True)  # old Python version
    print("wrote", out)

    if not a.no_install:
        base = Path(os.environ.get("APPDATA", "")) / "Blackmagic Design" / "DaVinci Resolve" / "Support" / "Fusion" / "Scripts"
        if base.exists():
            util = base / "Utility"
            util.mkdir(exist_ok=True)
            (util / f"Build timeline - {title}.py").unlink(missing_ok=True)
            dst = util / f"Build timeline - {title}.lua"
            shutil.copy(out, dst)
            print("installed", dst, "(restart Resolve if it was open)")
        else:
            print("Resolve Scripts folder not found; run resolve/build_timeline.lua from Workspace > Console (Lua)")
    print(f"{len(scenes)} scenes, {t0:.1f}s, clips {fps} fps on a {tl_fps} fps timeline, {wh[0]}x{wh[1]}")


if __name__ == "__main__":
    main()
