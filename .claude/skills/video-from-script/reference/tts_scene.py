"""Expressive narration with Edge TTS (re-voiced 2026-11-20 to match the Đại Việt video: 10% slower).

Pacing rules (user request, 2026-11-20):
  * pause 0.25 s at every comma (also ; and :), 1.0 s at every full stop (also ? and !).
    Each phrase is cut at its punctuation and every piece is voiced separately, so these
    pauses are exact instead of whatever the TTS engine would choose.
  * the first noun after a full stop (i.e. the first noun of each sentence) is stressed
    and drawn out a little: marked with *asterisks* below, found through Edge TTS word
    timings, then made louder (+4 dB) and ~15 % longer (atempo 0.87).
Writes assets/audio/scene-NN.mp3 + scene-NN.json (start/end of every phrase; the phrase
list per scene is unchanged, so build_video.py's animation beats still line up).
Vietnamese names are written without diacritics so the English voice can say them.

Usage: python tts_scene.py [scene ...]   (default: all)
"""
import asyncio, json, subprocess, sys, re
from pathlib import Path
import edge_tts, imageio_ffmpeg

ROOT = Path(__file__).parent
AUD = ROOT / "assets" / "audio"
TMP = AUD / "_parts"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

VOICE = "en-US-ChristopherNeural"
BASE = dict(rate="-10%", pitch="-10Hz", volume="+0%")
STRONG = dict(rate="-10%", pitch="-14Hz", volume="+25%")
LEAD, TAIL = 0.0, 2.0  # no lead-in: the voice starts at 0 s; 2 s after the last word
SCENE_PAD = 0.3            # build_video.py adds this after the audio
PAUSE_COMMA, PAUSE_STOP = 0.25, 1.0
STRESS_DB, STRESS_TEMPO = 4.0, 0.87

B, S = BASE, STRONG
SCENES = {
    1: [
        ("Imagine you're an *admiral*.", B),
        ('You sail a huge *war* fleet into a quiet river.', B),
        ('No *enemy* in sight.', B),
        ('A few *hours* later,', B),
        ("your ships can't move.", S),
        ("They're stuck", S),
        ('on something under the *water*.', B),
        ("And here's the crazy *part*:", B),
        ('this exact trap worked here twice.', S),
        ('Three hundred and fifty *years* apart.', S),
    ],
    2: [
        ('This is the *Bach Dang River*, in northern Vietnam.', B),
        ("It flows into the *sea* near today's Hai Phong and Quang Ninh.", B),
        ('In *938*, a Vietnamese commander used it to destroy a Southern Han invasion fleet from China.', B),
        ('In *1288*, another commander used the same river,', B),
        ('and the same trick,', S),
        ('against the Mongol-led Yuan dynasty.', B),
        ('The *Mongols* had built the largest land empire the world had ever seen.', S),
        ('How did a *trap* made of wooden stakes beat two empires?', S),
        ("And why didn't the second *empire* see it coming?", B),
        ("Let's go back to the *beginning*.", B),
    ],
    3: [
        ('In the early *900s*, the land of the Viet had been under Chinese rule, on and off, for about a thousand years.', B),
        ('But local *leaders* were slowly taking control.', B),
        ('One of them was *Duong Dinh Nghe*.', S),
        ('Then, in *937*, he was murdered', S),
        ('by one of his own officers, Kieu Cong Tien.', B),
        ("*Kieu* knew he wasn't popular.", B),
        ('So he did something that made him even less popular:', B),
        ('he asked the Southern Han kingdom in southern China for help.', S),
        ('The *Southern Han* saw an opportunity.', B),
        ('Their *ruler* sent his own son, Liu Hongcao, called Luu Hoang Thao in Vietnamese, with a war fleet to take the region.', B),
        ('But someone moved faster.', S),
        ("*Ngo Quyen*, Duong Dinh Nghe's son-in-law, marched on Kieu Cong Tien and killed him.", B),
        ('Now *Ngo Quyen* had a new problem.', B),
        ('An *enemy* fleet was coming by sea.', S),
        ('And he did not have a *navy* that could beat it in open battle.', B),
        ('So he decided not to fight the *fleet*.', B),
        ('He decided to fight the *river*.', S),
    ],
    4: [
        ("Here's what makes the *Bach Dang* special.", B),
        ("It's a tidal *river*.", S),
        ('When the *tide* comes in, the water rises by several meters.', B),
        ('When it goes out, the *riverbed* near the mouth becomes shallow.', B),
        ("*Ngo Quyen's* men cut long wooden stakes, sharpened them, and capped them with iron.", B),
        ('Then they drove them into the *riverbed* across the estuary.', B),
        ('At high *tide*, the stakes were completely hidden.', S),
        ('Now, the *bait*.', S),
        ('When the *Southern Han* fleet arrived, small Vietnamese boats rowed out to fight, then turned and fled upriver, as if they were losing.', B),
        ('The *invaders* chased them, right over the hidden stakes.', B),
        ('And then they waited for the *tide* to turn.', B),
        ('As the *water* dropped, the big warships started hitting the stakes.', B),
        ('*Hulls* cracked. *Ships* got stuck.', S),
        ('Others tried to turn around and crashed into each other.', B),
        ("That's when *Ngo Quyen* attacked.", S),
        ('The *Southern Han* fleet was destroyed.', B),
        ('*Liu Hongcao*, the prince who led it, was killed.', B),
        ('A *year* later, in 939, Ngo Quyen declared himself king, with his capital at Co Loa.', B),
        ('*Historians* often mark this as the end of the long period of northern rule.', B),
        ('One *battle*. One *river*.', S),
        ('And a *turning point* for a whole country.', S),
    ],
    5: [
        ('Fast forward 350 *years*.', S),
        ('*Dai Viet* is now ruled by the Tran dynasty.', B),
        ('And it faces the most feared military *power* on Earth:', B),
        ('the Mongols, now ruling China as the Yuan dynasty.', S),
        ('The *Mongols* had already invaded Dai Viet twice, in 1258 and in 1285.', B),
        ('Both *times*, they were pushed back.', S),
        ("*Kublai Khan* wasn't done.", B),
        ('At the *end* of 1287, he sent a third invasion, led by his son Toghan, with a large army and a navy.', B),
        ('On the Vietnamese *side*, the supreme commander was Prince Tran Quoc Tuan, better known as Tran Hung Dao.', B),
        ("And here's a *detail* many people skip:", B),
        ('the Bach Dang victory actually started somewhere else.', S),
        ('The Mongol *army* depended on a huge supply fleet bringing grain by sea.', B),
        ('Near *Van Don*, Vietnamese commander Tran Khanh Du ambushed it and destroyed it.', S),
        ("Now picture *Toghan's* army: deep in enemy territory, rice running out, the hot season coming.", B),
        ('By *spring* 1288, he decided to withdraw.', B),
        ('And his *fleet*, under commanders Omar and Fan Yi, would leave the same way it came in, down the Bach Dang River.', B),
        ('*Tran Hung Dao* knew exactly where they had to go.', B),
        ('And he knew what had happened there before.', S),
    ],
    6: [
        ('So *Tran Hung Dao* did the same thing Ngo Quyen had done.', B),
        ('His *men* drove forests of wooden stakes into the riverbed, in places the retreating fleet had to pass.', B),
        ('He studied the *tide*. He picked the *timing*.', S),
        ('On the *9th* of April, 1288, the Yuan fleet sailed into the trap.', S),
        ('The *pattern* was the same.', B),
        ('Draw the *fleet* in at high water. Wait. Let the *river* drop.', S),
        ('The *ships* got stuck on the stakes.', B),
        ('Vietnamese *boats* attacked, reportedly with fire as well.', B),
        ('Many *Yuan* ships were burned, sunk or captured.', B),
        ('*Omar*, the Yuan naval commander, was taken prisoner. *Fan Yi* was killed.', B),
        ('On *land*, Toghan escaped back to China.', B),
        ('*Dai Viet* had beaten the Mongols for the third time.', S),
        ('But wait.', S),
        ('If this *trick* had already been used here, how did the Yuan commanders fall for it?', B),
        ('The *answer* is probably simple:', B),
        ("the trap didn't depend on surprise. It depended on the *river*.", S),
        ('Big *ships* need deep water.', B),
        ('The *estuary* only offers that at certain hours.', B),
        ('And a retreating *fleet* has no time to wait or to look around.', B),
        ("The *Vietnamese* didn't just know their enemy.", B),
        ('They knew their *tide*, almost to the hour.', S),
    ],
    7: [
        ("Here's the *part* that gives me chills:", B),
        ('we can still see the evidence.', S),
        ("In *1958*, workers in the Yen Giang area, in today's Quang Yen, found old wooden stakes buried in the ground near the old riverbed.", B),
        ('Later *excavations* found many more, set in lines, sharpened at the tip.', B),
        ('*Researchers*, including an international team of archaeologists, radiocarbon-dated stakes from Yen Giang and the nearby Dong Ma Ngua site.', B),
        ('The *results* point to the late 13th to 14th century,', B),
        ('which fits the 1288 battle.', S),
        ('Some of these *stakes* are now displayed in museums, including the National Museum of Vietnamese History in Hanoi.', B),
        ('One honest *caveat*:', S),
        ('not every old post found in this area belongs to the battle.', B),
        ('A recent *study* of piles unearthed in Hai Phong in 2019 and 2020 argues they are far older, possibly foundations of stilt houses from the Dong Son period.', B),
        ('So *archaeologists* keep testing each new find, rather than calling every stake Bach Dang.', B),
        ("That's good *news*, actually.", B),
        ('It means the *story* we tell rests on evidence, not just legend.', S),
    ],
    8: [
        ('So why did the same *trap* work twice?', S),
        ('Not because the *enemy* was stupid.', B),
        ('Both *invaders* were powerful and experienced.', B),
        ('It worked because the *defenders* turned their home ground into a weapon.', S),
        ('They knew the *river*, the tide and the timing.', B),
        ('And *Tran Hung Dao* knew his own history well enough to use it again.', B),
        ('Two *empires*.', S),
        ('Two *fleets*.', S),
        ('One *river*.', S),
    ],
    9: [
        ('If you could ask *Tran Hung Dao* one question, what would it be?', B),
        ('Tell me in the *comments*.', B),
        ('See you on the *river*.', S),
    ],
}



def duration(path):
    err = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True).stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def pause_for(chunk):
    return PAUSE_STOP if chunk.rstrip()[-1:] in ".!?" else PAUSE_COMMA


async def voice(text, cfg, mp3):
    """Voice one chunk; return word timings [(word, start_s, end_s)]."""
    for attempt in range(3):
        try:
            words = []
            with open(mp3, "wb") as fh:
                async for ch in edge_tts.Communicate(text, VOICE, boundary="WordBoundary", **cfg).stream():
                    if ch["type"] == "audio":
                        fh.write(ch["data"])
                    elif ch["type"] == "WordBoundary":
                        words.append((ch["text"], ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7))
            return words
        except Exception:
            if attempt == 2:
                raise
            await asyncio.sleep(2)


def stress_span(chunk, words):
    """(start, end) seconds of the *marked* word(s) in this chunk, or None."""
    m = re.search(r"\*([^*]+)\*", chunk)
    if not m:
        return None
    target = [norm(w) for w in m.group(1).split()]
    toks = [norm(w) for w, _, _ in words]
    for i in range(len(toks) - len(target) + 1):
        if toks[i:i + len(target)] == target:
            j = i + len(target) - 1
            start = max(0.0, words[i][1] - 0.02)
            end = words[j + 1][1] if j + 1 < len(words) else words[j][2] + 0.05
            return start, end
    # Edge sometimes merges words into one boundary ("thetrancourt", "in1285"):
    # locate the target inside the merged token by letter position.
    tgt = "".join(target)
    for (w, ws, we), tok in zip(words, toks):
        k = tok.find(tgt)
        if k >= 0 and tok:
            a, b = k / len(tok), (k + len(tgt)) / len(tok)
            return max(0.0, ws + (we - ws) * a - 0.03), ws + (we - ws) * b + 0.03
    print("   ! stress word not found:", m.group(1), toks)
    return None


def render_chunk(mp3, wav, span, pause):
    """Decode, stress the span (louder + drawn out), trim silences, add the pause."""
    trim = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
            "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
            f"apad=pad_dur={pause}")
    if span is None:
        fc = f"[0:a]{trim}[out]"
    else:
        s, e = span
        total = duration(mp3)
        s = max(s, 0.03)
        stressed = f"atrim={s}:{e},asetpts=PTS-STARTPTS,atempo={STRESS_TEMPO},volume={STRESS_DB}dB"
        if e < total - 0.03:
            fc = (f"[0:a]asplit=3[x][y][z];[x]atrim=0:{s},asetpts=PTS-STARTPTS[p];[y]{stressed}[w];"
                  f"[z]atrim={e},asetpts=PTS-STARTPTS[q];[p][w]acrossfade=d=0.012[pw];"
                  f"[pw][q]acrossfade=d=0.012,{trim}[out]")
        else:
            fc = (f"[0:a]asplit=2[x][y];[x]atrim=0:{s},asetpts=PTS-STARTPTS[p];[y]{stressed}[w];"
                  f"[p][w]acrossfade=d=0.012,{trim}[out]")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(mp3), "-filter_complex", fc, "-map", "[out]",
                    "-ar", "24000", "-ac", "1", str(wav)], check=True)


async def build(scene):
    TMP.mkdir(parents=True, exist_ok=True)
    parts, timings, t = [], [], 0.0
    word_times = []
    phrases = SCENES[scene]
    for i, (text, cfg) in enumerate(phrases):
        chunks = re.split(r"(?<=[,.;:!?])\s+", text.strip())
        p_start, p_end = None, None
        for k, chunk in enumerate(chunks):
            last = i == len(phrases) - 1 and k == len(chunks) - 1
            pause = 0.0 if last else pause_for(chunk)
            mp3 = TMP / f"s{scene:02d}_{i:02d}_{k}.mp3"
            words = await voice(chunk.replace("*", ""), cfg, mp3)
            wav = mp3.with_suffix(".wav")
            sp = stress_span(chunk, words)
            render_chunk(mp3, wav, sp, pause)
            d = duration(wav)
            w0 = words[0][1] if words else 0.0
            for w, ws, we in words:
                shift = (sp[1] - sp[0]) * (1 / STRESS_TEMPO - 1) if sp is not None and ws >= sp[1] - 1e-3 else 0.0
                word_times.append({"phrase": i, "word": norm(w), "t": round(LEAD + t + max(0.0, ws - w0) + shift, 3)})
            if p_start is None:
                p_start = LEAD + t
            p_end = LEAD + t + d - pause
            parts.append(wav); t += d
        timings.append({"text": text.replace("*", ""), "start": round(p_start, 3), "end": round(p_end, 3)})
    lst = TMP / f"list{scene:02d}.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts))
    out = AUD / f"scene-{scene:02d}.mp3"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-af", f"adelay={int(LEAD * 1000)},apad=pad_dur={TAIL - SCENE_PAD},bass=g=4:f=120,"
                    "acompressor=threshold=-18dB:ratio=3:attack=5:release=120,loudnorm=I=-16",
                    "-ar", "44100", "-b:a", "160k", str(out)], check=True)
    (AUD / f"scene-{scene:02d}.json").write_text(json.dumps(timings, indent=2))
    (AUD / f"scene-{scene:02d}.words.json").write_text(json.dumps(word_times))
    print(out.name, f"{duration(out):.2f}s", flush=True)


if __name__ == "__main__":
    for s in [int(a) for a in sys.argv[1:]] or list(SCENES):
        asyncio.run(build(s))
