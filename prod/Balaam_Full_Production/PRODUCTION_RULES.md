# Production rules

## Story and picture

The first 35 minutes belong to Pethor. Balak enters episode 8. Keep Balaam outside Israel's community in the backstory. His relationship with God is expressed through ordinary conversations, obedience, waiting, free service and encounters he cannot reproduce at will. The first adversarial prediction occurs only after the meadow bargain. The idea of buying relief now and asking forgiveness afterward becomes explicit in episode 7. His years of repair are real years. The temptation at Balak's court returns after those years.

A restrained hand-painted 2D anime treatment carries through the film. Approve the looks of the ridge, home, market and river before composing the individual first frames. Lens numbers in the shot descriptions specify a perspective target for the artwork. They are direction for composition, not measured lens metadata from an animation camera.

Balaam's youth, maturity and later years must preserve eyes, nose, chin and hairline. Use front, three-quarter, profile and full-body references. Match height against Beor and the rescued girl in shared frames. Approve neutral, listening, grief, alarm and gentle-smile expressions. A character sheet alone does not compose a two-person video input. Build and approve an actual first frame for every setup.

Keep silver as irregular weighed fragments, rings or ingot pieces, without stamped currency faces. The Pethor rescue stories use fictional geography grounded in river life. Avoid assigning an archaeological certainty to this invented settlement plan.

## Staging and geography

Pethor is on the river-left bank looking downstream. The old post is downstream of the main bend and above the inlet. Rescue boats and loose oars move downstream in the same river-facing view. The post, hook, stair and inlet retain their distances in every master plate.

The house bench remains on the right wall. The table is center-left and the river-facing doorway camera-left in the master. Set a floor-plan reference before reverse angles. The first wide shot establishes each conversation axis. Frame close-ups from the same side of that axis. Screen-left and screen-right in lighting refer to the chosen master camera. Recalculate physically for a reverse angle to keep the same world-space source.

At the Moab overlooks, approve three genuinely different locations. Maintain king, prophet and valley positions within each. Use ground-level Israelite scenes to make the people below visible as individuals.

Establish location and elapsed time with the first Midian shot. Editorial labels are added in post. The story does not infer how long Balaam was in Midian. The death staging is fictional.

Background-role identity decisions are explicit creative assumptions. BOY1 in the market and BOY1 in the distant city are distinct extras; BOY2 in Pethor and BOY2 in Israel are distinct extras. Generate scene-scoped assets for them. DRIVER, TRADER and WORKER also receive scene-scoped faces unless the script explicitly calls back a recurring character. The girl from the original boat is the same person through GIRL_CHILD, GIRL_ADULT and GIRL_OLDER. Her mother is MOTHER. The mother in the fire is CITY_MOTHER.

## Performance and mouth

Record dialogue first. The cue text is the sole source for the words. Keep a clean mono master for each approved take, using a consistent sample rate in the production library. Convert a copy if the selected encoder requires another rate. Lock the actor or approved synthetic voice preset across episodes.

GOD and ADVERSARY share the same performer, cadence family and acoustic perspective. Their cue IDs distinguish editorial identity. Caption their spoken words without revealing the source through labels. Use the script's first appearance and moral direction to convey the distinction. ANGEL has a separate voice. DONKEY_VOICE is a plain spoken voice, with muzzle articulation tested separately.

Balaam's listening scenes keep lips at rest or softly breathing. Do not animate a visible mouth to voiceover from GOD or ADVERSARY. For a wide shot or prop insert, the dialogue can remain offscreen. Mouth-visible close-ups and medium shots receive the exact selected waveform through the A2V workflow. One foreground speaker per source piece keeps attribution legible.

Record each cue with a short lead and tail. Keep the selected words and breaths. Run forced alignment against the exact cue text, then listen to proper names and any low-confidence interval. WhisperX word timestamps are useful for locating speech and subtitles. A separate phoneme aligner or reviewed phoneme timing is required for explicit viseme intervals. Word alignment alone does not specify lips for every phoneme.

For hand animation or repair, inspect M/B/P closure, F/V lip-to-teeth contact, rounded W and OO shapes, open vowels, and transitions around stops. Allow coarticulation. Render at 24 fps and inspect frames around salient closures. Target audible consonants and lip contacts within about one or two frames when perceptually appropriate; this is a review goal rather than a promise from the generator. Donkey speech has its own muzzle test.

E12_S028_D01 reuses the approved E01_S030_D01 recording for the remembered invitation. Preserve its waveform and performance.

## Timing and camera

In the initial edit, each scene has a 50-second allocation and each episode 300 seconds. Retiming may change these allocations within the agreed 60–120 minute film range. Shot duration is variable according to dialogue and action. Its three authored phases indicate the opening state, principal movement and settling or reaction state. The second ledger expands those phases into one-second direction. Continued action across rows is intentional.

Use start-inclusive and end-exclusive frame intervals. Master time runs from frame 0 through frame 86399. Each episode is 7200 frames. Seconds are 24-frame intervals. A word that straddles a second boundary may appear in both estimated rows. Those rows are a planning aid.

The source piece plan proposes clips of at most seven seconds. Resolve dimensions, temporal divisibility, duration limits and output frame count against the actual installed graph. If the graph needs extra frames, render enough and trim after decode. Record the real first and last frames used.

Long speaking shots should be split at a pause in the approved waveform, not blindly at the current proposed boundary. Rebalance the adjacent source pieces and keep the editorial shot length. Compose continuation images from a clean approved frame. For MATCH_LOCK and VISION_LOCK, generate the component plates separately and make the transition in the edit.

For each source piece, use the action phase that overlaps its interval. Do not ask a five-second piece to execute the entire fifteen-second shot. Add short handles where the workflow and budget permit, keeping trim points explicit.

## LTX and ComfyUI

Use the LTX version actually installed. The linked LTX-2.5 official examples provide a current candidate. If the pod has another LTX version, compare compatible official graphs and checkpoints before changing it. Match transformer, encoder, VAE, connectors and upscaler by release. Never mix components by similar filename alone.

The local image-to-video route animates the composed first frame. For visible speech, use the official audio-to-video graph, with the exact trimmed audio window and corresponding first frame. Keep speech fixed in the audio input. Evaluate the resulting mouth movement and body performance. Store visual outputs and original WAV separately for the final mix.

A prompt should state subject, scene, concrete action order, light and camera in present tense. The script supplies these directly. Preserve the quote for any spoken cue. Review any automatic prompt-enhancer rewrite against names, wardrobe, action order and words. Save the effective prompt that was actually encoded.

Prefer one local LTX checkpoint through a sequence. Start with the official single-stage or a supported lighter graph for previews, then test two-stage output where it improves the image. The guide does not prescribe a universal sampler, CFG or VRAM figure. Begin from the exact template defaults and measure the installed configuration.

## Sound and music

Carry continuous location ambience across cuts: river, house, market, field, road, heights, feast and camp. Avoid a synthetic silence every time a clip ends. Speech stems stay separate from water, fire, cloth, pottery and music.

Spot Foley against the resulting contact frames: foot on stone, lamp set down, rope drawn, boat against step, silver landing, gate bar seated and bowl rolling. The script's action phases identify the contact events. Their final audio times come from the selected visual take. Lower music under speech and leave prayer silences enough air to feel inhabited.

The lamp motif may be a small flute phrase used after safety, at the clay puppy and at the epilogue. Keep the competing voices acoustically alike. The death remains unheroic, with sparse sound and no triumphant musical resolution.

## Review and recovery

Save the pod environment report, ComfyUI commit, custom-node versions, workflow hash, checkpoint hashes, effective prompt, seed, reference hashes and audio hash for each source piece. Resume completed jobs by ID after timeouts before resubmitting. Requeue only failed or explicitly replaced pieces.

Review the first frame at contact scale before expensive video generation. Check faces, hands, heights, prop side, horizon and eyeline. Review the video for temporal drift, changing costume, bad contact, sliding feet, water direction and wrong mouth assignment. Regenerate or repair a failed source piece without discarding its neighbors.

First approve E01_S013 for a listening close-up, E03_S018 for the child under the stair, E09_S020 for donkey speech, and E11_S008 for a consequential speaking face. Each tests a different constraint. Then assemble the first five minutes to test pacing before scheduling the whole film.

Final deliverables are twelve episode files, the 60-minute compilation, clean and captioned versions, separate dialogue/effects/music stems, aligned subtitles and an asset provenance manifest. Verify all files with ffprobe and watch the whole assembled film. The automated checks validate technical structure; performance and storytelling still require viewing.
