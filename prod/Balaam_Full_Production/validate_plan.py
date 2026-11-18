#!/usr/bin/env python3
"""Validate the authored plan. This does not assess rendered performances."""
import csv
import json
from pathlib import Path

root = Path(__file__).resolve().parent
shots = json.loads((root / "manifests/shots.json").read_text())
jobs = json.loads((root / "manifests/render_jobs.json").read_text())
scenes = json.loads((root / "manifests/scenes.json").read_text())
cues = json.loads((root / "dialogue/cues.json").read_text())
cast = json.loads((root / "manifests/cast.json").read_text())
look = json.loads((root / "manifests/look.json").read_text())

assert len(shots) == 360
assert len(scenes) == 72
assert shots[0]["start_frame"] == 0
total_frames = shots[-1]["end_frame_exclusive"]
assert 86400 <= total_frames <= 172800
assert total_frames % 24 == 0
assert len({s["id"] for s in shots}) == len(shots)
assert all(a["end_frame_exclusive"] == b["start_frame"] for a, b in zip(shots, shots[1:]))

shot_lookup = {shot["id"]: shot for shot in shots}
cue_lookup = {cue["id"]: cue for cue in cues}
for shot in shots:
    assert shot["location"] in look["locations"]
    assert shot["light_id"] in look["lighting"]
    assert all(name in cast for name in shot["cast"])
    assert shot["phases"][0]["start"] == 0
    assert shot["phases"][-1]["end"] == shot["duration_seconds"]
    assert sum(j["duration_seconds"] for j in shot["source_segments"]) == shot["duration_seconds"]
    if shot["cue_id"]:
        assert shot["cue_id"] in cue_lookup
for episode in range(1, 13):
    episode_shots = [s for s in shots if s["episode"] == episode]
    assert len(episode_shots) == 30
    assert episode_shots[-1]["film_end"] - episode_shots[0]["film_start"] == sum(s["duration_seconds"] for s in episode_shots)
for cue in cues:
    shot = shot_lookup[cue["shot_id"]]
    assert shot["film_start"] <= cue["planned_film_start"] < cue["planned_film_end"] <= shot["film_end"]
    if cue["reuse_approved_cue"]:
        original = cue_lookup[cue["reuse_approved_cue"]]
        assert cue["text"] == original["text"]
    assert all(w["start"] < w["end"] for w in cue["estimated_words"])
assert len({job["id"] for job in jobs}) == len(jobs)
assert all(job["shot_id"] in shot_lookup and 0 < job["duration_seconds"] for job in jobs)
with (root / "timelines/seconds.csv").open(newline="") as handle:
    seconds = list(csv.DictReader(handle))
assert [int(s["film_second"]) for s in seconds] == list(range(total_frames // 24))
assert all(int(s["end_frame_exclusive"]) - int(s["start_frame"]) == 24 for s in seconds)
print(f"Passed: 12 episodes, {len(scenes)} scenes, {len(shots)} shots, {len(jobs)} proposed render pieces, {len(cues)} dialogue cues, {total_frames // 24} seconds, {total_frames:,} frames.")
print("Recordings, references, actual workflow execution, final pacing and lip sync remain production checks.")
