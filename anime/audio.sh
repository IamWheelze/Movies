#!/bin/sh
# Voices, river sound and door knocks for the episode. CPU only; run on the Pod from /workspace/anime.
mkdir -p audio && cd audio
pip install -q piper-tts > pip.log 2>&1
hf download rhasspy/piper-voices en/en_US/ryan/high/en_US-ryan-high.onnx en/en_US/ryan/high/en_US-ryan-high.onnx.json en/en_US/joe/medium/en_US-joe-medium.onnx en/en_US/joe/medium/en_US-joe-medium.onnx.json --local-dir voices > hf.log 2>&1
R=voices/en/en_US/ryan/high/en_US-ryan-high.onnx
J=voices/en/en_US/joe/medium/en_US-joe-medium.onnx
say() { echo "$3" | python3 -m piper -m $1 --length-scale $4 -f $2 > /dev/null 2>> piper.err; }
say $R god1.wav 'Balaam, son of Beor.' 1.25
say $R god2.wav 'Before the moon clears the ridge, the water will reach those roofs. Take them to the high bank.' 1.2
say $J bal1.wav 'They will ask how I know.' 1.15
say $R god3.wav 'Go, and wake them.' 1.25
say $J bal2.wav 'I never heard Him speak. I lied.' 1.2
say $J str1.wav "My brother's caravan is missing. Is he alive?" 1.1
for f in god1 god2 bal1 god3 bal2 str1; do
  ffmpeg -y -loglevel error -i $f.wav -af 'highpass=f=90,lowpass=f=7000,loudnorm=I=-18' ${f}_n.wav
done
ffmpeg -y -loglevel error -f lavfi -i 'aevalsrc=0.9*sin(2*PI*85*t)*exp(-14*t)+0.4*sin(2*PI*170*t)*exp(-20*t):d=0.5:s=44100' knock_n.wav
ffmpeg -y -loglevel error -f lavfi -i 'anoisesrc=color=brown:amplitude=0.6:duration=200:seed=3' -f lavfi -i 'anoisesrc=color=pink:amplitude=0.3:duration=200:seed=9' -filter_complex '[0]lowpass=f=650,highpass=f=50,tremolo=f=0.13:d=0.35[a];[1]highpass=f=1200,lowpass=f=3500,tremolo=f=0.55:d=0.8,volume=0.10[b];[a][b]amix=inputs=2:normalize=0,volume=0.9,afade=t=in:d=2' river.wav
echo AUDIODONE > audio.done
