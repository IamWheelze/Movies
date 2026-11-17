#!/bin/sh
# The queue for everything after the stills are picked. Run on the Pod from /workspace/anime.
# It waits for picks.txt (for example "01:1 02:2 ..."), then renders every clip, upscales them to 1080p,
# joins them with the sound, makes a small copy in pieces for sending, and finally stops the Pod by
# itself 25 minutes later unless someone has already stopped it.
cd /workspace/anime
until [ -f picks.txt ]; do sleep 2; done
python3 make.py pick $(cat picks.txt) > pick.log 2>&1
python3 make.py clips ep1.txt > clips.log 2>&1
mkdir -p up
M=/workspace/runpod-slim/ComfyUI/models/upscale_models/4x_fatal_Anime_500000_G.pth
O=/workspace/runpod-slim/ComfyUI/output
for id in $(cut -d'|' -f1 ep1.txt); do
  python3 upscale.py $M $(ls $O/clips/${id}_s*.mp4 | head -1) up/$id.mp4 >> up.log 2>&1
  echo upscaled $id >> up.log
done
until [ -f audio/audio.done ]; do sleep 2; done
python3 final.py ep1.txt cues.txt $O/episode01_anime.mp4 > final.log 2>&1
ffmpeg -y -loglevel error -i $O/episode01_anime.mp4 -c:v libx264 -preset medium -crf 29 -pix_fmt yuv420p -c:a aac -b:a 96k -movflags +faststart send.mp4 >> final.log 2>&1
rm -f sv_*
split -b 650000 -d -a 2 send.mp4 sv_
md5sum send.mp4 >> final.log
echo QUEUEDONE >> final.log
sleep 1500
runpodctl stop pod $RUNPOD_POD_ID
