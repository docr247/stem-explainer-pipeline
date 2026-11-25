# stem-explainer-pipeline

Code and episode queue for the **Tech 101** explainer series on Ravi's Tech Lab (YouTube): short animated, narrated explainers on how computers, microcontrollers and electronics actually work.

Every episode is drawn entirely in code (Python + Pillow + ffmpeg) and narrated with a free local voice model (Kokoro). Scheduled runs plan three episodes a day and publish them at about 06:00, 10:00 and 14:00 Dubai time, following `RUNBOOK.md`.

| Path | What it is |
| --- | --- |
| `RUNBOOK.md` | The step-by-step procedure each daily run follows |
| `queue.json` | Episode list: topics, status and YouTube video IDs |
| `setup.sh` | Installs the voice model, fonts and Python packages |
| `src/render.py` | Shared drawing helpers and episode 1 |
| `src/short.py` | Shared helpers for vertical Shorts and the episode 1 Short |
| `src/epN.py`, `src/shortN.py` | Each episode's long-form and Short |
| `src/thumb_epN.py` | Each episode's thumbnail |
| `src/narrate.py` | Adds narration and assembles the final video |
| `media/epNN/` | The latest finished videos and thumbnails, kept online so Zapier can upload them |

Make an episode by hand: `bash setup.sh && cd src && python3 narrate.py ep6 && python3 narrate.py short6`.
