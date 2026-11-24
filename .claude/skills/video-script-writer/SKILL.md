---
name: "video-script-writer"
description: "Pick from 10 video categories, then 10 compelling topics in that category, then write a full video script and save it to a folder in the project. Use when brainstorming and scripting videos."
---
 
# Video Script Writer
 
A 3-step flow: **Category → Topic → Script**, pausing at each step for the user to choose.
 
## Configuration
 
- **Output folder:** `xxx/` (relative to the root of the current project). Change this line to rename the folder.
- **Script language:** the language the user is writing in, unless they ask for another.
If the user passes a category or topic when invoking the skill (e.g. `/video-script-writer history`), skip the matching step.
 
## Step 1 — Offer 10 categories
 
List **10 varied categories** with strong viewing potential, numbered 1–10. Give each a one-line description (why it's engaging, who the audience is).
 
Reference examples (not mandatory): Vietnamese history, Food & culture, Travel, Tech & AI, Programming / building products, Mysteries & surprising facts, Everyday psychology, Personal finance, Science made simple, Life abroad.
 
End with: *"Which category number do you pick? (or type a different one)"* and **stop and wait for the answer**.
 
## Step 2 — Offer 10 compelling topics
 
For the chosen category, offer **10 specific video topics**, numbered 1–10. Each includes:
- **Title** that sparks curiosity (written like a real video title, not generic)
- **Angle / hook** in one sentence: what makes viewers click
Topic criteria: an element of surprise, conflict, mystery, or clear benefit; specific enough for a single video; no overlap between topics.
 
If a topic depends on current events or recent figures, verify with web search before suggesting it.
 
End with: *"Which topic number do you pick? Roughly how long should the video be, and for which platform (YouTube, TikTok/Shorts…)?"* and **stop and wait for the answer**. If no length is given, default to a ~8–10 minute YouTube video.
 
## Step 3 — Write the script
 
If the content involves facts (history, statistics, events), research them first to make sure they are accurate. Never invent quotes or figures.
 
Write the script in this structure (Markdown):
 
```markdown
# <Video title>
 
- **Category:** ...
- **Platform / length:** ...
- **Target audience:** ...
- **Core message:** (one sentence)
 
## Alternative titles
1. ...
2. ...
3. ...
 
## Thumbnail idea
- Visual: ...
- Thumbnail text: ...
 
## Script
 
### 0:00 – Hook (≤ 15 seconds)
**Narration:** ...
**Visuals / B-roll:** ...
 
### 0:15 – Intro
**Narration:** ...
**Visuals / B-roll:** ...
 
### <timestamp> – Part 1: <section name>
Customize
video-script-writer
New
by you · v3 · updated just now


Video script writer v3 · current
0003

SKILL.md
/SKILL.md


---
name: "video-script-writer"
description: "Pick from 10 video categories, then 10 compelling topics in that category, then write a full video script and save it to a folder in the project. Use when brainstorming and scripting videos."
---
 
# Video Script Writer
 
A 3-step flow: **Category → Topic → Script**, pausing at each step for the user to choose.
 
## Configuration
 
- **Output folder:** `scripts/<script-title>/` (relative to the root of the current project): each script gets its own folder inside `scripts/`.
- **Script language:** the language the user is writing in, unless they ask for another.
If the user passes a category or topic when invoking the skill (e.g. `/video-script-writer history`), skip the matching step.
 
## Step 1 — Offer 10 categories
 
List **10 varied categories** with strong viewing potential, numbered 1–10. Give each a one-line description (why it's engaging, who the audience is).
 
Reference examples (not mandatory): Vietnamese history, Food & culture, Travel, Tech & AI, Programming / building products, Mysteries & surprising facts, Everyday psychology, Personal finance, Science made simple, Life abroad.
 
End with: *"Which category number do you pick? (or type a different one)"* and **stop and wait for the answer**.
 
## Step 2 — Offer 10 compelling topics
 
For the chosen category, offer **10 specific video topics**, numbered 1–10. Each includes:
- **Title** that sparks curiosity (written like a real video title, not generic)
- **Angle / hook** in one sentence: what makes viewers click
Topic criteria: an element of surprise, conflict, mystery, or clear benefit; specific enough for a single video; no overlap between topics.
 
If a topic depends on current events or recent figures, verify with web search before suggesting it.
 
End with: *"Which topic number do you pick? Roughly how long should the video be, and for which platform (YouTube, TikTok/Shorts…)?"* and **stop and wait for the answer**. If no length is given, default to a ~8–10 minute YouTube video.
 
## Step 3 — Write the script
 
If the content involves facts (history, statistics, events), research them first to make sure they are accurate. Never invent quotes or figures.
 
Write the script in this structure (Markdown):
 
```markdown
# <Video title>
 
- **Category:** ...
- **Platform / length:** ...
- **Target audience:** ...
- **Core message:** (one sentence)
 
## Alternative titles
1. ...
2. ...
3. ...
 
## Thumbnail idea
- Visual: ...
- Thumbnail text: ...
 
## Script
 
### 0:00 – Hook (≤ 15 seconds)
**Narration:** ...
**Visuals / B-roll:** ...
 
### 0:15 – Intro
**Narration:** ...
**Visuals / B-roll:** ...
 
### <timestamp> – Part 1: <section name>
**Narration:** ...
**Visuals / B-roll:** ...
**On-screen text:** (if any)
 
... (further sections)
 
### <timestamp> – Outro
**Narration:** ...
**Visuals / B-roll:** ...
 
## Sources
- (if research was done)
```
 
Writing rules:
- The opening hook must pose a question or situation that makes viewers keep watching; no long greetings.
- Write narration for speaking: short sentences, easy to read aloud.
- Add a retention beat every 30–60 seconds (a question, a surprising detail, a scene change).
- Estimate timestamps at ~150 words per minute; the total must match the chosen length.
- Outro (user preference, default): a question for the comments plus a short sign-off tied to the story (e.g. "See you on the river."). No next-video teaser and no "subscribe" line unless the user asks for one; they have no follow-up video planned.
- Short videos (TikTok/Shorts ≤ 60s): trim to Hook → 2–3 key points → short outro, and drop the thumbnail section.
## Step 4 — Save the file
 
1. Build `<script-title>` from the video title: lowercase, diacritics removed, spaces replaced with `-`, max ~60 characters.
2. Create `scripts/<script-title>/` at the project root (create `scripts/` too if it doesn't exist). If that folder already exists, add a suffix `-2`, `-3`, …
3. Save the script as `scripts/<script-title>/script.md`.
4. Tell the user the file path and give a 1–2 sentence summary (title, length, number of sections). Don't paste the whole script into the chat.
5. Briefly ask whether they want any changes (tone, shorter version, an extra Shorts cut…).
**Narration:** ...
**Visuals / B-roll:** ...
**On-screen text:** (if any)
 
... (further sections)
 
### <timestamp> – Outro
**Narration:** ...
**Visuals / B-roll:** ...
 
## Sources
- (if research was done)
```
 
Writing rules:
- The opening hook must pose a question or situation that makes viewers keep watching; no long greetings.
- Write narration for speaking: short sentences, easy to read aloud.
- Add a retention beat every 30–60 seconds (a question, a surprising detail, a scene change).
- Estimate timestamps at ~150 words per minute; the total must match the chosen length.
- Outro (user preference, default): a question for the comments plus a short sign-off tied to the story (e.g. "See you on the river."). No next-video teaser and no "subscribe" line unless the user asks for one; they have no follow-up video planned.
- Short videos (TikTok/Shorts ≤ 60s): trim to Hook → 2–3 key points → short outro, and drop the thumbnail section.
## Step 4 — Save the file
 
1. Create the `xxx/` folder at the project root if it doesn't exist.
2. Save the script as `xxx/YYYY-MM-DD-<title-slug>.md`
   - `slug`: lowercase title, diacritics removed, spaces replaced with `-`, max ~60 characters.
   - If the filename already exists, add a suffix `-2`, `-3`, …
3. Tell the user the file path and give a 1–2 sentence summary (title, length, number of sections). Don't paste the whole script into the chat.
4. Briefly ask whether they want any changes (tone, shorter version, an extra Shorts cut…).