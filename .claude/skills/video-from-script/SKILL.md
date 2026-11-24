---
name: "video-from-script"
description: "Turn a saved script in the scripts/ folder (by its title) into a video in the user's house style (contemporary Vietnamese folk-art images, hand-painted ink-wash maps with calligraphic lettering, 8 fps stepped animation, Edge TTS narration with exact pauses, original orchestral music bed, subtitles): reuse images from image-source/ or generate them with Figma AI, and package it as a DaVinci Resolve timeline script (review, edit and export in Resolve)."
---

# Video From Script

Usage: `/video-from-script <script-title> [extra requirements]`

- `<script-title>` is the folder name under `scripts/` (e.g. `the-mystery-of-co-loa-citadel`).
- Everything after the title is the user's **extra requirements** for the video (length, aspect ratio, voice, pacing, subtitles, music, mood…). They override every default below.

All paths are relative to the root of the current project.

## House style (user defaults)

The user approved this look and sound on `scripts/the-same-river-trap-worked-twice-350-years-apart/` (2026-11-24). Use it for every new video unless the extra requirements say otherwise. That folder is the **reference implementation**: copy from its `tts_scene.py`, `build_video.py` and `make_music.py` rather than starting from scratch. `scripts/` is not in git, so copies of those files (and its `plan.md`) are kept in `reference/` next to this SKILL.md. Use them when the folder is missing.

| Area | Default |
|---|---|
| Picture | 1920×1080, **8 fps** stepped 2D animation (Resolve timeline 24 fps, each frame held 3×) |
| Images | **Contemporary Vietnamese folk art** (modern Đông Hồ / Hàng Trống), generated with Figma AI; prompt paragraph in Step 2 |
| Maps | **Hand-painted ink-wash (thủy mặc)** maps drawn in code from Natural Earth data, `folk_style.map_frame()` (Step 5) |
| Map text | **Dancing Script Bold** (`image-source/fonts/DancingScript.ttf`, OFL, full Vietnamese), ink / vermilion / indigo with a paper halo |
| Other text | Lower thirds, captions and titles over pictures: Arial Bold, cream on dark; big years and numbers: Georgia Bold |
| Portraits | Chest-up 4:5 folk portrait on a plain flat backdrop colour per character, shown as tilted cream "cards" with name + year |
| Voice (English) | `en-US-ChristopherNeural`, rate `-10%`, pitch `-10Hz`; emphasised phrases `-14Hz` / `+25%` volume; exact pauses + first-noun stress (Step 4) |
| Music | Original orchestral bed synthesized in code (`make_music.py`), as long as the timeline, baked to about **-30 LUFS** and placed at `--music-db 0` (Step 6) |
| Subtitles | **On the timeline** (`--subtitles`), for YouTube too |
| Ending | Question for the comments + short sign-off. **No next-video teaser and no "subscribe"** unless the user asks |

## Folder layout

```
scripts/<script-title>/
├── script.md            # input (written by video-script-writer)
├── plan.md              # character + scene breakdown (this skill)
├── assets/
│   ├── images/          # images used in this video
│   ├── audio/           # one narration file per scene + subtitles.srt
│   └── clips/           # scene-NN.mp4: animated picture per scene (no audio)
│       └── handles/     # same clips + frozen-frame handles (made by the helper)
├── build_video.py       # renders the scene clips
├── resolve/
│   ├── build_timeline.lua # run inside DaVinci Resolve
│   └── build_log.txt      # written by that script on each run
└── output/              # Resolve's Deliver page is preset to export here
image-source/            # shared, reusable library
├── characters/          # <id>-folk.png = folk-art portraits
├── backgrounds/         # <id>-folk.png = folk-art backgrounds
├── props/               # transparent sprites (ships, boats…)
├── fonts/               # DancingScript.ttf (map lettering) + licence
└── data/                # Natural Earth geojson (land 50m/10m, rivers 10m, admin0 50m)
.claude/skills/video-from-script/folk_style.py   # ink-wash maps, map lettering, prop cut-out
```

## Step 0 — Check prerequisites

- `scripts/<script-title>/script.md` exists. If not, list the folders in `scripts/` and ask the user which one they mean.
- `ffmpeg` is installed (`ffmpeg -version`). If it isn't and can't be installed system-wide, `pip install imageio-ffmpeg` and use `imageio_ffmpeg.get_ffmpeg_exe()`; without `ffprobe`, read durations from `ffmpeg -i <file>` stderr.
- DaVinci Resolve (free or Studio) is installed: it is where the video is reviewed, edited and exported. The helper files for this live next to this SKILL.md: `make_resolve_project.py` and `resolve_timeline_template.lua`.
- `edge-tts` is installed (`pip install edge-tts`, or `pip install --break-system-packages edge-tts` if needed).
- The Figma MCP tools are available (only needed if images must be generated). If they are deferred, load them with ToolSearch first.

If something is missing and can't be installed, tell the user exactly what to install and stop.

## Step 1 — Read the script

Read `script.md` fully. Extract, for every section (`### <timestamp> – ...`):
- the **narration** text
- the **visuals / B-roll** notes
- any **on-screen text**

Also note the platform/length from the header (YouTube 16:9 or Shorts/TikTok 9:16).

## Step 2 — Analyze characters and scenes → `plan.md`

Write `scripts/<script-title>/plan.md` with:

1. **Visual style** (one paragraph used, word for word, in every image prompt). Default (house style):
   > Contemporary Vietnamese folk art illustration, a modern reinterpretation of Đông Hồ woodblock prints and Hàng Trống paintings: flat bold shapes, thick confident black outlines, hand-printed texture on cream dó paper with visible fibres, limited palette of vermilion red, turmeric yellow, indigo blue, leaf green and earth brown, decorative stylised patterns for water waves and clouds, slightly naive perspective, graphic and elegant, no gradient shading. No text, no letters, no signature.

   Use a different style only if the user's extra requirements ask for one.
2. **Characters**: for each one — `id` (kebab-case), name, role in the story, age/build, face & hair, outfit, signature colors, personality, and the expressions/poses the script needs.
3. **Backgrounds**: for each location — `id`, description, time of day, mood.
4. **Scene list**: one row per script section — scene number, section title, background id, character ids + pose, narration text, on-screen text, and camera move (slow zoom in / pan left / static…).

Keep character descriptions identical every time they are reused in a prompt, so the art stays consistent.

## Step 3 — Images: reuse first, then generate

For each character and background in `plan.md`:

1. **Look in `image-source/`** (`characters/`, `backgrounds/`, and any other subfolders). Match by file name first, then open likely candidates to check visually that they fit the description and style. If one fits, copy it into `assets/images/` and mark it `reused` in `plan.md`.
2. **If nothing fits, generate with Figma AI** through the Figma MCP tools (read each tool's description for exact parameters; typically `create_new_file` for a working file, `generate_image` or `generate_vector_illustration` for the art, and `download_assets` / `get_screenshot` to export it).
   - Prompt = visual style paragraph + the character/background description + pose/expression. The default model (`gpt-image-2.5-flare`) returns 1536×864 for 16:9; scale it to the frame when loading. Each call uses Figma AI credits, so generate each image once and independent images in parallel.
   - Portraits (house style): chest-up, facing 3/4 toward the viewer, centred, **plain flat backdrop** in the character's signature colour, 1024×1280.
   - Characters that are animated full-body, and props (ships, boats…): one isolated object seen exactly from the side, "on a completely plain flat pure white background (#FFFFFF), no water, no shadow, no paper texture in the background". Then cut it out with `folk_style.key_out_white(img)`. It flood-fills the white from the border and also clears enclosed white gaps (between sails and rigging, rowers' arms). Check the cut-out on a magenta background before using it.
   - Backgrounds: say where the empty space is, because animation is composited on top. For example, "EMPTY river, no boats, horizon at the middle of the image, the whole lower half open water" for a river that ships will sail on, or "city only in the LEFT third, the right two-thirds open water". 16:9 or 9:16 to match the video.
3. Save each new image to **both** `assets/images/` and the shared library (`image-source/characters/<id>-folk.png`, `image-source/backgrounds/<id>-folk.png`, `image-source/props/<id>-folk.png`) so future videos can reuse it.
4. If Figma generation fails, retry once; if it still fails, tell the user which images are missing and ask whether to continue with placeholders.

Show the user the character images (and a couple of backgrounds) before building the video when they are present, so they can request changes early.

## Step 4 — Narration with Edge TTS

Pick a voice that matches the script language unless the user specified one:
- English (house style): `en-US-ChristopherNeural`, `rate="-10%"`, `pitch="-10Hz"`. Phrases that carry the drama (a reveal, a punchline) use the stronger setting `pitch="-14Hz"`, `volume="+25%"`. Write Vietnamese names **without diacritics** in the TTS text ("Tran Hung Dao", "Bach Dang") so the English voice can say them; on screen they keep their diacritics.
- Vietnamese: `vi-VN-HoaiMyNeural` (female) / `vi-VN-NamMinhNeural` (male)
- Japanese: `ja-JP-NanamiNeural` / `ja-JP-KeitaNeural`

(`edge-tts --list-voices` shows all.) Generate one file per scene, `assets/audio/scene-NN.mp3`, plus phrase timings `scene-NN.json` (`[{text, start, end}]`), from a small script `scripts/<title>/tts_scene.py` so single scenes can be re-voiced.

Apply the user's requested speed with the `rate` option (e.g. `+10%`, `-10%`).

**Punctuation pauses (user preference, default):** pause exactly **0.25 s at every comma** (also `;` and `:`) and **1 s at every full stop** (also `?` and `!`). Edge TTS takes no SSML and picks its own pause lengths, so don't voice a whole scene in one call:
1. Split the narration after each punctuation mark followed by a space (`re.split(r"(?<=[,.;:!?])\s+", text)`). Don't split decimal numbers like `1,000`.
2. Voice each piece separately with `edge_tts.Communicate(piece, voice, rate=..., pitch=...)`.
3. Trim the TTS's own leading and trailing silence (ffmpeg `silenceremove` at the start, then `areverse`, `silenceremove`, `areverse` again), then add the pause with `apad=pad_dur=0.25` or `apad=pad_dur=1.0`, depending on the piece's last character.
4. Concatenate the pieces (ffmpeg concat demuxer) and record each phrase's start and end time in `scene-NN.json`. `build_video.py` reads these times to sync animations and the Resolve helper uses them for subtitles.
5. The last piece of a scene gets no punctuation pause; the scene tail below applies instead.

**Stress the first noun of each sentence (user preference, default):** the first noun after a full stop (so the first noun of every sentence, including the scene's first sentence) is read louder and drawn out a little.
1. Mark it by hand in the narration text with asterisks, e.g. `"The *Mongols* captured…"` or `"In the *1250s*, …"`. Pick it by reading the sentence; no tagger is needed.
   - Proper names used as modifiers count as the noun ("The *Tran* court", "the *Yuan* army").
   - Mark multi-word names in full (`*Dai Viet*`, `*Tran Hung Dao*`).
   - A sentence with no noun ("Small. Outnumbered.", "Fight!") gets no mark.
2. Remove the asterisks before sending the text to the TTS. Request word timings with `edge_tts.Communicate(..., boundary="WordBoundary")` and read the `WordBoundary` events from `.stream()`. Each event gives `text`, plus `offset` and `duration` in units of 100 ns.
3. Find the marked word in those timings. Compare words in lowercase with punctuation removed. Edge sometimes merges words into one timing ("thetrancourt", "in1285"). In that case, locate the noun inside the merged token by its letter position.
4. With ffmpeg, cut that piece into three parts: before the noun, the noun itself, and after it. The noun segment runs from its start to the start of the next word. Give the noun segment `volume=4dB` and `atempo=0.87`, which makes it about 15 % longer. Join the parts back with `acrossfade=d=0.012` to avoid clicks. Then trim the piece's silence and add its pause as above.
5. When a scene is generated, print any marked word that could not be found, and fix those before rendering.

Check the result: `ffmpeg -i scene-01.mp3 -af silencedetect=n=-40dB:d=0.06 -f null -` should list gaps of 0.25 s and 1.0 s. The reference example is `scripts/the-same-river-trap-worked-twice-350-years-apart/tts_scene.py`: voice, emphasis settings, pauses, stress and `LEAD = 0` are already set. Copy it and replace its `SCENES` table. Each entry is `(phrase, B or S)`, where `S` uses the stronger setting.

**Scene start and end (user preference, default):** the narration starts **right away**, with no silent lead-in at the start of a scene, and each scene ends **2 s** after the last word (`apad` at the end). Keep the silence after the last word at about 2 s in total, counting the ~0.3 s padding added when rendering. Since the voice starts at 0 s, the first shot of each scene must already show something meaningful at frame 0, not a blank or fade-in that delays the picture.

Measure each file's duration with `ffprobe` (or `ffmpeg -i`): that duration (plus ~0.3 s padding) becomes the scene length.

## Step 5 — Render the scene clips (picture only)

The skill does **not** export a finished video. It renders one animated clip per scene; joining, audio, transitions and the final export happen in DaVinci Resolve (Step 6).

Defaults (override with the user's extra requirements): 1920×1080 for YouTube, 1080×1920 for Shorts/TikTok; **8 fps** (house style: stepped, hand-made motion). All scenes must use the **same** frame rate.

**Maps (house style): hand-painted ink-wash, drawn in code.** Don't generate maps as images: draw them from the Natural Earth data in `image-source/data/` with `folk_style.py` (next to this SKILL.md, see its docstring). That keeps zooms smooth and coastlines accurate:
- `fs.configure(W, H, project_root)`, then `img, pr = fs.map_frame(fs.load_polys("ne_10m_land.geojson"), fs.load_rivers({"Hong", "Da"}), lon, lat, width_deg)`. Use `ne_50m_land` for wide views (more than ~20° across). Redraw every frame for zooms; cache static maps.
- Ink-painting mountains are drawn by default in north Vietnam / south China (`mountain_box`), with the Red River delta kept open (`mountain_skip`). Set `mountain_box` for other regions, or `None` for no mountains.
- Territories (an empire's extent): `fs.region_wash(img, pr, rings)`, a light vermilion wash with a thin outline, never solid fill.
- All text on a map goes through `fs.map_label(...)`: role `"ink"` for places and captions, `"accent"` (vermilion) for the key place and enemy places, `"sea"` (indigo) for seas and rivers. The minimum size is 36 px so small notes stay readable. Routes and arrows: vermilion lines; location pins: small vermilion circles.
- In the reference `build_video.py`, `label()` switches to this style by itself when the canvas has `info["map"]`. `camera()` and `caption()` pass that tag on.

**Text over pictures**: lower thirds (dark bar, orange accent, Arial Bold cream), captions and `big_text` in Arial Bold cream with a soft shadow, big years in Georgia Bold. Darken the picture (about 0.45–0.6) behind full-screen text.

For each scene:
1. Composite the background with the character image(s) on top (bottom-aligned, positioned per `plan.md`).
2. Animate it for the scene's duration (narration length + ~0.3 s): camera moves, characters/props entering, on-screen text. Drive motion from time (`t = frame / fps`), not from frame parity, so it stays smooth at any frame rate.
3. Write `assets/clips/scene-NN.mp4`: H.264 `-crf 16`, `yuv420p`, **no audio track**, length exactly = scene length.

Don't join scenes, add crossfades, mux narration, add music or burn subtitles here. The Resolve script does all of that.

Put the render code in `scripts/<title>/build_video.py` (e.g. `python build_video.py 1 2` renders scenes 1–2) so single scenes can be re-rendered after small edits.

## Step 6 — Package for DaVinci Resolve

Run the helper from the project root:

```bash
python .claude/skills/video-from-script/make_resolve_project.py scripts/<script-title> [--subtitles] [--music path/to/music.mp3] [--transition 0.4]
```

- `--subtitles`: put captions on the timeline (house style: **always on**, YouTube included). `subtitles.srt` is always imported into the Media Pool.
- `--music`: house style is an original orchestral bed:
  1. Copy `make_music.py` from the reference video. It synthesizes strings, low strings, a horn motif and timpani in D minor, with intensity following the story. Adapt its `intensity()` curve and scene count to the new script.
  2. Run it **after all narration is final**. Its length is the sum of the scene clips, so re-run it whenever a scene's narration changes length. Otherwise the music is cut before its fade-out.
  3. It writes `music-orchestral.wav` at -16 LUFS. Bake the level into a copy (`ffmpeg -af volume=0.2` → `music-orchestral-20pct.wav`, about -30 LUFS), check it with `ebur128`, and pass `--music <that file> --music-db 0`. Resolve's volume property can be ignored, so bake the level into the file.
  4. If the user gives a level, use it instead (percent → `volume=<p>`).
- `--transition 0`: hard cuts instead of cross-dissolves.

Resolve timelines only run at standard rates (16, 24, 25, 30, …). Clips at a rate Resolve doesn't offer, such as 8 fps, are placed on the first standard multiple (8 fps → 24 fps timeline): each frame is held 3×, so the 8 fps look and the timing are unchanged.

It reads `assets/clips/scene-NN.mp4`, `assets/audio/scene-NN.mp3` and the phrase timings in `scene-NN.json` (or `scene-NN.vtt`), then:
1. adds frozen-frame handles to each clip (`assets/clips/handles/`) so Resolve has room for cross-dissolves;
2. merges the subtitles into `assets/audio/subtitles.srt` on the timeline clock;
3. writes `resolve/build_timeline.lua` with every path, frame count and setting embedded. It is Lua on purpose: Resolve always has Lua, but on some installs it does not list Python scripts in the menu;
4. installs a copy as **Workspace › Scripts › Build timeline - <script-title>** (in `%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Utility\`).

When run inside Resolve, that script:
- creates (or opens) the project `<script-title>` and sets its frame rate and resolution;
- imports everything into a bin;
- builds a timeline: V1 scenes, A1 narration, plus an A2 music track and a subtitle track when requested;
- adds cross-dissolves, and a blue marker per scene with its narration as the note;
- presets the Deliver page to MP4/H.264 into `output/`, then opens the Edit page.

Each run adds a new version and never overwrites earlier edits:
- the timeline `v<N> · <build timestamp>` goes into the **Timelines** bin, next to all earlier versions;
- that version's media goes into **Media › v<N>**.

It never starts a render.

Resolve can't change a project's frame rate once the project has a timeline. If the project already exists at a different rate, the script logs it. Tell the user to rename or delete that project in Resolve, or to re-render the clips at the project's rate.

## Step 7 — Check and report

1. Check every scene clip: same frame rate and resolution, length = narration + padding (`ffmpeg -i`).
2. Extract 3–4 frames per scene (start, middle, end) and look at them: characters visible, nothing cut off, text readable. Include every map shot: no label hidden under mountains or other labels.
   - Check that the music file is as long as the timeline (the sum of the clip lengths) and is at about -30 LUFS.
3. Confirm the helper printed both paths (written + installed). If `lupa` is available (`pip install lupa`), load the Lua file once to catch syntax errors.
4. Tell the user:
   - how to run it: in Resolve, **Workspace › Scripts › Build timeline - <script-title>**. Resolve only scans scripts at startup, so restart it if it was open. Each run writes `resolve/build_log.txt` when Resolve allows file access (Resolve 21.2+ menu scripts have no `io`; then progress shows in Workspace › Console and errors land in `%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\logs\ResolveDebug.txt`). Read those to diagnose problems;
   - what lands on the timeline and the total duration;
   - how many images were reused vs. newly generated, and the voice used;
   - that they export from the Deliver page.

   Offer one natural next step (e.g. tweak a scene, change the voice, make a Shorts cut).