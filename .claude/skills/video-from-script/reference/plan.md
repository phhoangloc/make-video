# Plan – The Same River Trap Worked Twice

Output: 1920×1080, **8 fps** stepped 2D animation (user request). Voice (re-voiced 2026-11-20 to match the Đại Việt video): `en-US-ChristopherNeural`, rate -10%, pitch -10Hz; emphasised phrases -14Hz / +25% volume. Pauses: exactly 0.25 s at commas, 1.0 s at full stops; first noun of every sentence (marked *like this* in `tts_scene.py`) +4 dB and ~15% longer. Word timings in `assets/audio/scene-NN.words.json` drive in-sentence beats (`wt()` in build_video.py). Music: original orchestral bed from `make_music.py`, baked to 20% (`music-orchestral-20pct.wav`, about -30 LUFS) on A2 at 0 dB. Old versions kept as `tts_scene_old_v1.py` / `build_video_old_v1.py`.
Status: **all 9 scenes rendered.** Each scene: voice from 0 s (no lead-in), 2 s after the last word. Total ≈ 9:07.

## Visual style
**Contemporary Vietnamese folk art** (switched 2026-11-24 at user request; all 19 images regenerated with Figma AI under the same names). Prompt paragraph: "Contemporary Vietnamese folk art illustration, a modern reinterpretation of Đông Hồ woodblock prints and Hàng Trống paintings: flat bold shapes, thick confident black outlines, hand-printed texture on cream dó paper with visible fibres, limited palette of vermilion red, turmeric yellow, indigo blue, leaf green and earth brown, decorative stylised patterns for water waves and clouds, slightly naive perspective, graphic and elegant, no gradient shading. No text, no letters, no signature." Props are generated on pure white and keyed to transparency (incl. enclosed white gaps). Library copies: `image-source/*/<id>-folk.png`. Previous realistic-flat images kept in `assets/images/_realistic/`.

## Characters
| id | Name | Role | Description | Poses | Image |
|---|---|---|---|---|---|
| admiral-southern-han | Invading admiral (generic) | Not used yet (removed from scene 1) | Middle-aged, thin mustache + short beard, black topknot under dark official hat, crimson lamellar armor robe with gold trim, dark navy cape, sword | pointing forward | generated (Figma AI) |
| ngo-quyen | Ngô Quyền | Victor of 938 | ~40, short black beard, topknot with dark-teal headband, dark-teal/ochre lamellar armor, spear; ochre backdrop | portrait | generated |
| tran-hung-dao | Trần Hưng Đạo | Victor of 1288 | ~60, long grey-streaked beard, Trần general's helmet, navy/gold armor, red cape, hand on sword; teal backdrop | portrait | generated |
| duong-dinh-nghe | Dương Đình Nghệ | Governor, murdered 937 | ~50, grey-streaked beard, dark official cap, deep-green/ochre robe with lamellar collar; green backdrop | portrait (+ greyed after death) | generated |
| kieu-cong-tien | Kiều Công Tiễn | Officer who killed him | ~45, narrow eyes, thin mustache + goatee, navy armor over purple robe, dagger, half-shadowed face; slate backdrop | portrait (+ crossed out) | generated |
| liu-hongcao | Lưu Hoằng Tháo (Liu Hongcao) | Southern Han prince, fleet commander | ~25, clean-shaven, gold crown pin, crimson/gold armored robe, navy cape; red backdrop | portrait | generated |
| toghan | Toghan | Yuan prince, son of Kublai Khan, 1287–88 commander | ~35, thin long mustache, braids, fur-trimmed spiked helmet, steel-grey lamellar over red robe; steel-blue backdrop | portrait (+ greyed: escaped) | generated |

## Props
| id | Description | Image |
|---|---|---|
| viet-boat | Small Vietnamese war boat, six rowers in conical hats, faces left (flipped when fleeing) | generated |
| war-junk | Medieval Chinese war junk, side view facing right, ochre battened sails, red-brown hull, red banners, oars | generated |

## Backgrounds
| id | Description | Time / mood | Image |
|---|---|---|---|
| bach-dang-estuary-high-tide-dawn | Wide calm estuary at high tide, karst hills, mangroves | Dawn, peaceful/ominous | generated |
| palace-hall-night-10th-century | Governor's hall at night, red beams, empty dais, oil lamps | Night, conspiratorial | generated |
| southern-han-port-pearl-river | Walled harbor city with gate towers, piers, open water to the right | Morning haze | generated |
| co-loa-citadel-aerial | Spiral ramparts and moats, palace at the center | Morning, triumphant | generated |
| yuan-grain-fleet-burning-night | Yuan grain junks on fire near karst islands | Night, chaotic | generated |
| yuan-army-camp-hungry | Tents, exhausted soldiers, empty rice baskets | Hot haze, desperate | generated |
| soldiers-driving-stakes-low-tide | Soldiers hammering stakes into the mud | Late afternoon | generated |
| bach-dang-1288-battle-fire | Yuan junks stuck on stakes, burning, archers in small boats | Sunset, decisive | generated |
| excavation-stake-field | Trench with rows of ancient stakes, archaeologists | Overcast | generated |
| museum-stake-display | Ancient stake in a glass case under a spotlight | Quiet | generated |
| bach-dang-estuary-low-tide-stakes | Same estuary drained, mudflats, rows of sharpened stakes | Late morning, tense | generated |

Maps (since 2026-11-24): hand-painted **ink-wash (thủy mặc)** style drawn in code by `map_frame()` – dó paper, uneven ochre land wash with ink bleeding at the coast, dry-brush coastline, indigo rivers, sparse ink-painting mountains on uplands; map text in calligraphic **Dancing Script Bold** (`image-source/fonts/`, OFL, full Vietnamese) in ink / vermilion / indigo with a paper halo. Labels switch style automatically on images tagged `info['map']`. Map: drawn from Natural Earth data (`image-source/data/`: 50m/10m land, 10m rivers – Hồng, Đà; 50m countries for the approximate Yuan extent = China + Mongolia). Diagrams (tide cross-section, tide chart, year bars, radiocarbon range, end screen) are drawn in code.

All generated images are also stored in `image-source/` (characters/, backgrounds/, props/).

## Scenes
| # | Section | Beats (s) | Background | Characters / props | Camera | On-screen text |
|---|---|---|---|---|---|---|
| 1 | 0:00 Hook | opening on the empty calm river (admiral removed at user request) · fleet sails in · 8.2–9.2 tide drains (crossfade) · 9.2–14.2 ships stuck on stakes, shaking · 14.2–end darken + text | high tide → low tide | admiral (pointing), 3× war-junk | slow zoom out (high tide), slow zoom in (low tide) | "938 … 1288" |
| 2 | 0:15 Intro | map dive Asia → Bạch Đằng (pin + lower third) · Hải Phòng / Quảng Ninh / Hà Nội / Gulf of Tonkin labels · Ngô Quyền card (938) · Trần Hưng Đạo card (1288) + "= same trap" · Yuan lower third · stake field, camera punches in 2×/s, "Two empires. One trap." / "Why didn't they see it coming?" · dawn river fades to "938" | map → low tide → high tide | 2 portrait cards | exponential zoom; stepped push-in | as listed |
| 3 | 0:50 Part 1: A country without a ruler | region map + "≈ 1,000 years of Chinese rule" · Dương Đình Nghệ card · palace: dagger sweep + red flash, card greys out, Kiều card, "937: … assassinated" · map arc Đại La → Panyu, "Help me." · port: Lưu Hoằng Tháo card, 3 junks sail out, "938: Southern Han fleet sets sail" · family tree (son-in-law), Kiều crossed out · fleet icons along real sea route (`assets/fleet_route_938.json`) to Bạch Đằng, "No navy to match it" · dawn river: "Fight the river." | map, palace, port, river | 4 portrait cards, war-junk | slow pushes | as listed |
| 4 | 2:15 Part 2: The trap (938) | dawn river "A tidal river" · cross-section: water rises/falls · stakes grow, then hidden at high tide ("High tide: stakes hidden") · bait: Vietnamese boats row out, turn, flee; junks follow over ghosted stakes · low tide: ships stuck, shaking, two collide ("Low tide: trap closes") · Ngô Quyền attacks: boats from both sides, flames, Lưu Hoằng Tháo crossed out · Cổ Loa (939) · "One battle. One river." | river, diagram, low tide, Cổ Loa | Ngô Quyền, Lưu Hoằng Tháo, boats, junks | pushes | High/Low tide labels, 938/939 lower thirds |
| 5 | 3:45 Part 3: 1287–1288 | year counter 938→1288 · Đại Việt / Trần dynasty map · Asia map, Yuan extent (approx.) · invasions bar 1258, 1285 (pushed back), 1287–88 + Toghan · Trần Hưng Đạo vs Toghan · Vân Đồn: grain ship on map → burning fleet, Trần Khánh Dư · hungry camp · retreat arrow Vạn Kiếp → Bạch Đằng, "Omar · Fan Yi" · "He knew this river." | dark, maps, fire, camp, river | Trần Hưng Đạo, Toghan | pushes | "3rd Mongol invasion: 1287–1288", "Vân Đồn: the supply fleet is destroyed" |
| 6 | 5:15 Part 4: The trap, again | Ngô Quyền = Trần Hưng Đạo · driving stakes · tide chart · "9 April 1288" fleet enters · 938 / 1288 cross-sections side by side, water drops · battle with fire ("Burned, sunk or captured") · Omar captured / Fan Yi killed · Toghan escapes north, "Đại Việt 3 – Mongols 0" · "Not surprise. The river." · tide chart with draft line · "almost to the hour" | various | cards, junks | pushes | "9 April 1288", "Same river. Same tide. Same trap." |
| 7 | 6:45 Part 5: The stakes are still there | excavation · Quảng Yên map ("Yên Giang stake field – discovered 1958") · radiocarbon bar 1270–1400 vs 1288 ("Dated: late 13th–14th century") · museum · caveat map: 2019–20 Hải Phòng piles far older (Đông Sơn) · "Evidence, not just legend." | excavation, map, museum | – | pushes | as listed |
| 8 | 8:00 Part 6: What it teaches | question · invaders' cards · commanders + "Home ground = weapon / river · tide · timing" · "Two empires. Two fleets. One river." | dawn river | 4 cards | push | as listed |
| 9 | 8:40 Outro | Trần Hưng Đạo card + "One question… → comments" · next-video card + pulsing SUBSCRIBE · "See you on the river." fade to black | river, end screen | Trần Hưng Đạo | push | "Next: 3 Mongol invasions, 3 defeats" |
