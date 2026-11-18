# Balaam — full film production package

This package is a complete **60-minute editorial draft**, divided into twelve five-minute episodes. It follows the agreed story from the first call in Pethor through Balaam's supernatural encounters, the crisis over Beor, corruption and forgiveness, years of repair, Balak, the donkey, the blessings, Peor, Balaam's death and the remembered lamp.

The chosen delivery is **16:9, 1920 × 1080, 24 fps** because the current goal is a feature film. Each episode can be exported separately. A vertical release needs its own reframed first-frame compositions. Planned runtime includes deliberate listening, physical work, travel, waiting and reactions. About twenty minutes of the plan contain spoken words; the remaining picture time carries action and sound. These are editorial choices, ready to assess in an animatic.

## Open these in order

1. **BALAAM_FULL_SCRIPT.md** contains every scene and editorial shot, with cast, light, camera, focus, exact dialogue, mouth direction, still-image prompt and video prompt. The twelve episode files provide the same content in smaller units.
2. **timelines/SECONDS.md** gives a row for each second. **seconds.csv** and **seconds.jsonl** include the camera, light, focus, audio and frame interval for the same seconds.
3. **dialogue/RECORDING_SCRIPT.md** supplies the recording script. **cues.json** links each utterance to a voice profile and its shot.
4. **manifests/shots.json** is the machine-readable shooting script. **render_jobs.json** breaks its 360 editorial shots into 692 proposed source pieces. **scenes.json**, **cast.json** and **look.json** contain the shared specifications.
5. **CLAUDE_CODE_PROMPT.md** supplies the implementation instruction. **PRODUCTION_RULES.md** explains audio, continuity, rendering and quality review.
6. **RESEARCH.md** identifies the sources, their application and the creative boundaries. **SCENE_RESEARCH.csv** maps all 72 scenes to those decisions.
7. Run **python validate_plan.py** inside this folder to validate the editorial coverage and references.

## What has been completed

The screenplay and shot plan cover every second from 00:00:00 through 00:59:59, with 86,400 planned frames. Dialogue is written in full. Opening, middle and ending poses are authored for every shot. The second ledger expands those poses across their intended holds or movements; it is an animation plan with interpolated action progression.

## Production state

There are no rendered scenes, cast recordings, generated reference images or tested ComfyUI graphs in this package. The researched official workflow links are implementation inputs. This package has been validated as a script and timeline, and the visual execution still needs the pod and approved assets.

Every word window currently marked **editorial_estimate** must be replaced by timestamps measured from the selected performance. The script gives lip performance instructions. Exact phoneme timing and final lip sync require the recorded waveform, alignment and visual inspection. A text prompt cannot guarantee frame-exact mouth shapes.

First produce an animatic with the composed stills and recorded dialogue. Use it to approve the deliberate silences and movement lengths before batch generation. If a line runs longer naturally, move time within its scene before changing its words. Let the animatic determine scene and episode lengths within the agreed 60–120 minute film range. Update every time-dependent file after retiming.


**Reviewed edition** · Read QUALITY_REVIEW.md first. Anime is approved. Source prompt continuation and visible-speaker routing have been corrected. The current times remain a 60-minute initial edit.
