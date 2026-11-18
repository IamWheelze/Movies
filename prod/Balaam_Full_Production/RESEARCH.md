# Research and adaptation notes
Checked 18 November 2026.

This research supports the production mechanics, material choices and biblical sequence. Each Pethor scene is original dramatic invention. The per-second ledger is authored staging; no external source can establish the camera or mouth movement of a fictional encounter.

## R1 · LTX prompt construction
https://docs.ltx.io/open-source-model/usage-guides/prompting-guide

The official guide supports concrete camera language, ordered physical actions, consistent lighting, character detail and quoted dialogue. Those principles informed the shot-specific prompts. The package uses single camera setups as its basic unit. Temporal match transitions are edited from separate takes. The completed script is creative work, not a quotation or reproduction of the documentation.

## R2 · LTX audio-to-video
https://docs.ltx.io/open-source-model/usage-guides/audio-to-video/

The documented workflow takes a trimmed input audio clip, optionally a first frame, and generates video conditioned on that sound. Its model list specifies release-matched components. This supports the fixed-voice approach for visible speakers. The package leaves exact mouth alignment pending until the actor's waveform exists.

## R3 · Official ComfyUI LTX workflow family
https://github.com/Lightricks/ComfyUI-LTXVideo/tree/master/example_workflows/2.5

The example family includes single-stage and two-stage text/image-to-video, audio-to-video and control graphs. The pipeline should load and validate the actual matching graph from this family against the pod. Template files are linked here; they are not bundled as executable graphs because the user's installed version and node inventory are unknown.

## R4 · Word alignment
https://github.com/m-bain/whisperX

WhisperX provides word-level alignment. That makes it useful for measured speech windows and subtitle timing. The plan explicitly distinguishes word boundaries from phoneme-to-viseme animation. Every estimated word time in the package is provisional.

## R5 · RunPod storage
https://docs.runpod.io/pods/troubleshooting/zero-gpus

RunPod describes network volumes as storage decoupled from a particular GPU machine. The pipeline should inspect the real mounted path and preserve source assets, checkpoints and job state there rather than assume every scratch directory survives a pod replacement.

## R6 · Ancient Near Eastern materials
https://www.metmuseum.org/art/collection/search/325851
https://www.metmuseum.org/art/collection/search/327405
https://www.metmuseum.org/it/essays/uruk-the-first-city

The museum's caravan account illustrates long-distance donkey transport and trade in textiles and metals. Its ingot entry discusses weighed silver and the later arrival of coinage. Those references informed pack animals and irregular silver rather than stamped coins. Mudbrick is a broad regional material reference. These objects and cities do not establish an exact date, building plan or costume for Balaam's Pethor. The production uses an invented coherent regional look and documents it as such.

## R7 · Inspiration for transport and strange encounters
https://www.biblegateway.com/passage/?search=Acts+8%3A39-40&version=WEB
https://www.biblegateway.com/passage/?search=1+Kings+18%3A12&version=WEB

Philip's transport and Obadiah's fear that Elijah might be carried away provide inspiration for the imagined distant-city encounter. The film does not assert that Balaam performed that event in the biblical record. The recurring call, listening and dependable signs also draw creatively on the user's requested Samuel and Elijah characteristics.

## R8 · Balak, journey and angel
https://www.biblegateway.com/passage/?search=Numbers+22&version=WEB

The script retains the first prohibition, later conditional permission, divine opposition on the road, the donkey's actions and speech, the angel's explanation and the continuing limit on Balaam's words. Private adversarial persuasion, emotional history and conversations at home are dramatic interpretation.

## R9 · The oracles
https://www.biblegateway.com/passage/?search=Numbers+23-24&version=WEB

Three settings and blessing sequences culminate in the Spirit's coming upon Balaam and the later star-and-scepter oracle. Dialogue in the screenplay is an original adaptation of this material. It condenses rather than quotes every oracle.

## R10 · Peor and death
https://www.biblegateway.com/passage/?search=Numbers+25&version=WEB
https://www.biblegateway.com/passage/?search=Numbers+31%3A8%2C16&version=WEB

Peor includes sexual relations, participation in sacrifices, worship and the plague. Numbers 31 attributes counsel to Balaam and records his death by the sword. The private sale of that counsel, payment gesture, young brothers, exact death staging and epilogue are invented. The Midian sequence makes its later location explicit.

## R11 · Optional local speech research
https://github.com/resemble-ai/chatterbox

The surfaced repository documentation identifies the project as retired research as of August 2026. It can be inspected if already installed, but the package makes no dependency on it. The voice pipeline may instead use recorded actors or another installed documented local speech model. Its reference material and model terms must be checked for the particular implementation.

## Scene application map
SCENE_RESEARCH.csv maps every scene to the applicable references and its creative decisions. General prompt mechanics R1–R4 apply across the package. Each scene's historical or biblical basis is described separately, so invented signs are not mistaken for documented episodes in Balaam's life.

## R12 · ComfyUI server routes
https://docs.comfy.org/development/comfyui-server/comms_routes

The documented routes cover node metadata, queue submission and history. The implementation prompt uses those documented route names while leaving node mappings to validation against the actual installation.
