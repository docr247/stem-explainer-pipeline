# Daily episode runbook

This is the procedure a scheduled run follows to make **one new episode** of the "Inside the Chip" series (a long-form video, a Short and a thumbnail) and publish it to **Ravi's Tech Lab** on YouTube. No computer of Ravi's is involved: everything happens in the cloud workspace, GitHub and Zapier.

Repo: `https://github.com/{{OWNER}}/stem-explainer-pipeline` (public). Raw files: `https://raw.githubusercontent.com/{{OWNER}}/stem-explainer-pipeline/main/<path>`.

## 0. Prepare
1. Clone the repo (attach it with push access first), `cd` into it, run `bash setup.sh`. It must print `setup ok`.
2. Read `queue.json`. The episode to make is the first one with `"status": "next"`, else the first `"queued"`. Call its number **N** (two-digit form **NN**, e.g. 07).
3. **Duplicate guard.** If that episode's status is `"uploading"`, a previous run stopped mid-way: search YouTube (Zapier `youtube_find_video`, channel = the connected channel, query = the planned title) before uploading anything. Never upload the same episode twice.
4. If fewer than 3 episodes remain `queued`, append 5 new topics in the same spirit (computer engineering, embedded systems, electronics, biosignals; "how does X actually work?" questions with a visual answer) before you start.

## 1. Write the episode (in `src/`)
Copy the shape of the latest finished episode exactly: `ep6.py`, `short6.py`, `thumb_ep6.py`.

- `src/epN.py`: **9 scenes**, 1920×1080, 30 fps: hook → 6 explanation steps → recap → end card that teases the next queued topic. Each scene is ~9–12 s before narration stretches it. Use `chrome(d, "STEP k · NAME", "Title", "caption", t, dur)` for every scene except hook (empty step/title) and the end card.
- `src/shortN.py`: **5 scenes**, 1080×1920: bold hook headline → 3 quick ideas → "Watch the full video" CTA. Keep content between x=70 and x=930 (Shorts buttons) and above y≈1500.
- Both modules define `NARRATION = {scene_name: text}` and `OUTPUT = "<slug>_epN_narrated.mp4"` / `"epN_short_<slug>_narrated.mp4"`, and a `render()` that writes into a folder named after the module (`epN/`, `shortN/`).
- **Style:** dark navy `BG`, colours from `render.py` (CYAN, AMBER, GREEN, RED, PURPLE). Inter for text, DejaVu Sans Mono for code, hex and numbers. No emoji, no photos, no logos or brand marks, no real people.
- **Narration:** conversational, one idea per sentence, about 35–60 words per long-form scene and 15–25 per Short scene. Write acronyms the way they are spoken: "S P I", "you-art", "I squared C", "P W M", "I D". Read hex as "hex, four eight, zero zero…". The on-screen caption is a shorter version of the narration.
- **Accuracy comes first.** This is a teaching channel run by an embedded-systems lecturer. Only state facts you are sure of. Prefer typical values ("typically 1–10 ms") over precise claims, label made-up example values as examples on screen, and use the same STM32 (72 MHz, PA5 LED) context as earlier episodes where code appears.

## 2. Check, then render
1. From inside `src/`, `python3 epN.py preview` and `python3 shortN.py preview` write contact sheets (`epN/sheet.jpg`, `shortN/sheet.jpg`). **Open them and look.** Fix any overlap, clipped text or text running into the captions, then preview again.
2. Render with narration from inside `src/`: `python3 narrate.py epN` and `python3 narrate.py shortN`.
3. `src/thumb_epN.py` (run from inside `src/`, writes `thumbs/epN_thumbnail.jpg`): 1280×720 JPEG under 2 MB, same visual system as the earlier thumbnails (big glowing subject on the left, 2–3 line heavy headline on the right with one amber word, one tilted amber tag). Nothing important in the bottom-right corner (YouTube covers it with the duration). Open the image and check nothing is clipped.
4. QA: `ffprobe` both videos (long-form 1920×1080, Short 1080×1920 and **under 60 s**), and check `ffmpeg -af volumedetect` gives a mean around −16 to −18 dB.

## 3. Put the files online
1. Copy the three files to `media/epNN/` (`long.mp4`, `short.mp4`, `thumb.jpg`), commit them together with the new `src/` files, and push to `main`.
2. Set the episode's status to `"uploading"` in `queue.json`, commit and push.
3. Confirm each raw URL returns HTTP 200 before uploading (retry for up to 2 minutes; raw files can take a moment to appear).

## 4. Upload to YouTube with Zapier
App: YouTube (`selected_api` `YouTubeV4CLIAPI`). Inspect the action first if the schema might have changed.

1. **Long-form:** `execute_zapier_write_action`, action `upload_video` (tool `youtube_upload_video`):
   - `video`: raw URL of `long.mp4`; `thumbnail`: raw URL of `thumb.jpg`
   - `title`: curiosity-driven, under 70 characters, with a short bracketed hint of what's inside (like "How Does PWM Dim an LED? (Duty Cycle, Timers & Code Explained)")
   - `description`: 2-sentence hook, then chapters (`0:00 …`, starting from the actual scene start times printed by `narrate.py`), a series line, the next-episode line, and 5–6 hashtags
   - `tags`: 10–13 relevant tags; `category_id` `"27"` (Education); `privacy_status` `"public"`; `made_for_kids` `"false"`; `notify_subscribers` `"true"`; `default_language` and `default_audio_language` `"en"`; `license` `"youtube"`; `embeddable` `"true"`
2. **Short:** the same action with `video` = raw URL of `short.mp4`, title ending in `#Shorts` (under 60 characters), a 2–3 sentence description that names the full video, and `#Shorts` first in the hashtags. No thumbnail.
3. If the long-form thumbnail did not take, set it with `upload_video_thumbnail` (tool `youtube_update_video_thumbnail`), `video_id` + the raw thumbnail URL.
4. **Playlist:** `add_video_to_playlist` (tool `youtube_add_video_to_playlist`), `playlist_id` `"PLT6z28qw0fmU"` ("Computer Engineering 101"), long-form first, then the Short.

## 5. Record and tidy
1. In `queue.json`: set status `"published"`, add `long_id`, `short_id`, `published` (ISO date), and the titles. Mark the next queued episode `"next"`.
2. Remove media older than the last 3 episodes from `media/` (`git rm`), commit and push.
3. Tell Ravi in one short message: the episode title and both YouTube links, plus anything that went wrong.

## If something fails
- Never publish half an episode on purpose: if the long-form upload fails, do not upload the Short.
- Set status `"failed"` with a one-line `"error"` in `queue.json`, push, and tell Ravi what failed and at which step.
- If Zapier or YouTube reports an expired connection, stop and tell Ravi to reconnect it in Zapier.
