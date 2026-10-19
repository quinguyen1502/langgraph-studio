# Intro video

Renders the 90 s LangGraph Studio intro video shown on the handbook home page,
from the handbook screenshots. `video.html` is an HTML timeline; Chrome
renders it frame by frame and ffmpeg encodes the frames with a generated
music bed.

Output goes to `handbook/docs/assets/video/studio-intro-<lang>.mp4`, with a
poster `studio-intro-<lang>.jpg` taken at 31 s. Intermediate files go to
`scripts/promo/build/` (ignored by git).

## Requirements

- Node 20 or later and `npm install` in `frontend/` (the renderer uses its
  Playwright).
- Google Chrome, or Playwright's Chromium (`npx playwright install chromium`
  in `frontend/`). Set `CHROME_PATH` for a Chrome in another place.
- `ffmpeg` on `PATH`.
- Network access for the Inter and JetBrains Mono web fonts.

## Render

```bash
cd scripts/promo
node render.mjs --lang en    # 1920x1080, 30 fps
node render.mjs --lang vi
```

Each run takes a few minutes. To check a layout without encoding, render stills
at chosen seconds:

```bash
node render.mjs --lang en --stills 16,31,45
```

Open `video.html?lang=vi` in Chrome and call `renderAt(seconds)` in the
console to inspect one frame. To use a licensed track instead of the generated
bed: `node render.mjs --lang en --audio path/to/track.m4a`. The track is cut to
the video's length and faded out over the last 3 s.

## Files

| File | Role |
| --- | --- |
| `video.html` | The timeline: scenes, the `en` and `vi` copy, highlight boxes and the camera keyframes (`CAM`) for the product tour. |
| `render.mjs` | Renders the poster, the frames and the final MP4. |
| `music.mjs` | Synthesises the music bed. Section times match the scene timeline. |
| `paths.mjs` | Shared paths and Chrome lookup. |

## Sources

Screens come from `handbook/docs/images/<lang>/`, so the video follows the
handbook: refresh the screenshots (`HANDBOOK_SHOTS=1 npm run e2e -- handbook`
in `frontend/`) and render again. Highlight boxes and camera moves are in
percent of the screenshot; check both languages with `--stills` after a
screenshot refresh.

Claims in the copy follow the handbook pages. Check them there before
changing the copy.
