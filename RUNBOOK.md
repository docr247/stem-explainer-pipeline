# Tech 101 runbook

Procedure for the scheduled runs that make and publish the **Tech 101** series on **Ravi's Tech Lab** (YouTube). Each episode is one long-form video (6–10 minutes), one Short and one thumbnail. Everything happens online (cloud workspace, GitHub, Zapier); Ravi's computer is never involved.

Repo: `https://github.com/docr247/stem-explainer-pipeline` (public). Raw files: `https://raw.githubusercontent.com/docr247/stem-explainer-pipeline/main/<path>`.

## Schedule (Asia/Dubai time)
- **05:07 planner run:** follow *A. Plan the day*.
- **05:41, 09:41, 13:41 production runs:** follow *B. Make and publish one episode*. Each publishes around 06:00, 10:00 and 14:00.
- Three episodes a day. Ravi chose this pace deliberately after weighing YouTube's daily upload cap and its policy on mass-produced content. Do not raise it on your own.

## Setup (every run)
Attach `docr247/stem-explainer-pipeline` with push access, clone it, `cd` in, and run `bash setup.sh` (must print `setup ok`). Always `git pull --rebase` right before every commit and push; other runs may have pushed.

## A. Plan the day
1. Today's date in Asia/Dubai is **D**. If three episodes already have `"planned_for": "D"`, stop: the day is planned.
2. Take episodes in queue order: first any `"queued"` episodes from Ravi's original list (numbers 8–15), then new topics. Give the three chosen episodes `"planned_for": "D"`, `"slot": 1|2|3` and `"status": "planned"`.
3. **New topics** (once the original list runs out, or to top up): "all things tech" for a curious general audience. Rotate across areas so no two consecutive episodes share one: computing and chips; the internet and networking; phones and gadgets; AI and software; energy, batteries and EVs; space and satellites; sensors, robotics and the human body (Ravi's PhD is in rehabilitative robotics and neurophysiological signal decoding); everyday tech (GPS, QR codes, noise cancelling, microwaves, cameras). Phrase each as a "how does X actually work?" question with a visual answer. Never repeat or near-repeat a topic already in `queue.json`.
4. Also pick each episode's **format**, rotating so consecutive episodes differ: `deep-dive` (step-by-step), `versus` (X vs Y), `myth-buster` (3 common beliefs, true or false), `what-happens-if` (follow one event through a system), `history` (how we got from A to B), `build-up` (start from one transistor or one wire and add layers).
5. Append new topics as episodes with the next numbers, `status`, `planned_for`, `slot` and `format`. Keep at least 6 `"queued"` topics beyond today. Commit and push.

## B. Make and publish one episode
### B0. Pick and claim
1. If `schedule.upload_blocked_until` is in the future, stop and do nothing.
2. If nothing has `"planned_for"` today, do *A. Plan the day* first.
3. Pick today's lowest-slot episode with status `planned` (or `failed` with fewer than 2 `attempts`). If an episode is `uploading`, search YouTube for its title (`youtube_find_video`) before anything else; never upload an episode twice.
4. **Claim it:** set `"status": "producing"`, `"claimed_at"` (ISO time), increment `attempts`, commit and push. If the push is rejected, pull and re-check that nobody else claimed it. Ignore episodes another run claimed less than 3 hours ago.
5. Call its number **N** (two-digit **NN**).

### B1. Write the episode (in `src/`)
Use the latest finished episode as the code template (`ep7.py`, `short7.py`, `thumb_ep7.py`): same helpers, colours, fonts, `chrome()` layout, fades and caption style. That look is the channel's brand, so keep it. But **every diagram must be drawn for this topic**: no recoloured copies of earlier scenes.

- **`src/epN.py`: long-form, 6–10 minutes.** About 900–1,400 narrated words over **22–32 scenes** of 1920×1080 at 30 fps, grouped into 5–7 chapters. Structure: a hook (a surprising fact or question in the first 10 seconds), a "here's what we'll cover" scene, the chapters (each opening with a `STEP k · NAME` scene), a recap, then an end card teasing the next planned or queued topic. Follow the episode's `format`. Aim for 35–60 words of narration per scene; `narrate.py` stretches each scene to fit its narration.
- **`src/shortN.py`: Short, 30–55 seconds**, 5 scenes of 1080×1920. A bold one-line hook, 3 quick visual ideas, then a "Watch the full video" call to action. Keep content between x=70 and x=930, and above y≈1500. The Short must stay **under 60 seconds**.
- Both modules define `NARRATION = {scene_name: text}`, `OUTPUT` (`<slug>_epN_narrated.mp4` and `epN_short_<slug>_narrated.mp4`), and a `render()` that writes into a folder named after the module.
- **Narration:** conversational, one idea per sentence. Write acronyms as spoken ("S P I", "you-art", "I squared C", "P W M", "I D", "A D C") and read hex as "hex, four eight, zero zero…". Each on-screen caption is a shorter version of its narration.
- **Accuracy comes first.** This is a teaching channel run by an engineering lecturer. State only facts you are confident of; prefer typical ranges to precise claims; label example values as examples on screen. For anything that changes over time (record numbers, current products), leave it out rather than guess.
- **Nothing that isn't Ravi's:** no logos, brand marks, product photos, real people or copyrighted characters. Generic shapes and diagrams only.

### B2. Check, then render
1. From inside `src/`, run `python3 epN.py preview` and `python3 shortN.py preview` (preview code samples scenes at 85% through). **Open the contact sheets and look.** For a long-form with more than 9 scenes, make the preview write several 3×3 sheets. Fix any overlap, clipped text or text running into captions, then preview again.
2. Render from inside `src/`: `python3 narrate.py epN` and `python3 narrate.py shortN`. Note the scene durations it prints; you need them for chapter times.
3. `src/thumb_epN.py` writes `thumbs/epN_thumbnail.jpg`: 1280×720 JPEG under 2 MB, same system as earlier thumbnails (a big glowing subject on the left; a 2–3 line heavy headline on the right with one amber word; one tilted amber tag; nothing important in the bottom-right corner). Open it and check nothing is clipped.
4. QA: `ffprobe` both videos (long-form 1920×1080 and 6–10 minutes; Short 1080×1920 and under 60 s), and check `ffmpeg -af volumedetect` gives a mean around −16 to −18 dB.

### B3. Put the files online
1. Make the upload copy of the long-form smaller: `ffmpeg -i <long> -c:v libx264 -preset medium -crf 23 -tune animation -c:a aac -b:a 128k media/epNN/long.mp4`. Copy the Short to `media/epNN/short.mp4` and the thumbnail to `media/epNN/thumb.jpg`.
2. Set the episode's status to `"uploading"`, then commit the media together with the new `src/` files, and push.
3. Confirm each raw URL returns HTTP 200 before uploading (retry for up to 2 minutes).

### B4. Upload to YouTube with Zapier
App: YouTube (`selected_api` `YouTubeV4CLIAPI`). Inspect the action first if its schema might have changed.
1. **Long-form:** `execute_zapier_write_action`, action `upload_video` (tool `youtube_upload_video`):
   - `video`: raw URL of `long.mp4`; `thumbnail`: raw URL of `thumb.jpg`
   - `title`: curiosity-driven, under 70 characters, with a short bracketed hint (for example "Your CPU Never Checks the Button (How Interrupts Really Work)")
   - `description`: a 2-sentence hook; chapters (`0:00 …`, built from the real scene start times, at least 3 chapters, each at least 10 s); "Part of the Tech 101 series on Ravi's Tech Lab."; the next-episode line; 5–6 hashtags
   - `tags`: 10–13 relevant tags; `category_id` `"27"` (Education); `privacy_status` `"public"`; `made_for_kids` `"false"`; `notify_subscribers` `"true"`; `default_language` and `default_audio_language` `"en"`; `license` `"youtube"`; `embeddable` `"true"`
2. **Short:** the same action, with `video` = raw URL of `short.mp4`, a title ending in `#Shorts` (under 60 characters), a 2–3 sentence description naming the full video, and `#Shorts` first in the hashtags. No thumbnail.
3. If the long-form thumbnail did not take, set it with `upload_video_thumbnail` (tool `youtube_update_video_thumbnail`).
4. **Playlist:** `add_video_to_playlist` (tool `youtube_add_video_to_playlist`), `playlist_id` `"PLT6z28qw0fmU"` ("Tech101"), long-form first, then the Short.

### B5. Record and tidy
1. In `queue.json`, set the episode to `"published"` with `long_id`, `short_id`, `published` (ISO time), `long_title` and `short_title`.
2. Delete `media/` folders for episodes published more than 2 days ago (`git rm -r`), then commit and push.
3. Send Ravi one short message with the episode title and both YouTube links.

## If something fails
- Never publish half an episode on purpose: if the long-form upload fails, do not upload the Short.
- **Upload cap:** if YouTube answers "Daily upload limit reached" or `uploadLimitExceeded`, don't retry. Set `schedule.upload_blocked_until` to 24 hours from now, set the episode back to `"planned"`, push, and tell Ravi once.
- Otherwise set `"status": "failed"` with a one-line `"error"`, push, and tell Ravi what failed and at which step. The next run retries it once.
- If Zapier or YouTube reports an expired connection, stop and tell Ravi to reconnect it in Zapier.
