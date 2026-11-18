#!/bin/sh
# Runs after the vertical clips are rendered: trim each clip to its performance, upscale to 1080x1920, assemble.
# Run on the Pod from /workspace/anime. It never stops the Pod; the fixed-clock watchdog does that.
cd /workspace/anime
until grep -q 'CLIPS DONE' clips.log 2>/dev/null; do sleep 5; done
. ./env.sh
O=/workspace/runpod-slim/ComfyUI/output
M=/workspace/runpod-slim/ComfyUI/models/upscale_models/RealESRGAN_x4plus_anime_6B.pth
mkdir -p up trim
for c in 01:6.0 02:5.0 03:5.5 04:5.0 05:5.5 06:5.0 07:4.0 08:4.0 09:5.8 10:6.0 11:5.8 12:5.6 13:5.2 14:4.0 15:7.0 16:6.5 17:5.0 18:6.5; do
  id=${c%%:*}; sec=${c##*:}
  src=$(ls $O/clips/${id}_s*.mp4 | head -1)
  ffmpeg -y -loglevel error -i $src -t $(echo "$sec + 0.2" | bc) -c:v libx264 -crf 10 -an trim/$id.mp4
  CW=720 CH=1280 OW=1080 OH=1920 python3 upscale.py $M trim/$id.mp4 up/$id.mp4 >> up.log 2>&1
  echo upscaled $id $(date -u +%H:%M:%S) >> up.log
done
python3 final_v.py $O/episode01_vertical.mp4 > final.log 2>&1
echo QUEUEDONE >> final.log
