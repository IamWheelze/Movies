#!/bin/sh
# Download the 29 GB LTX checkpoint over 10 parallel connections, then join the parts.
mkdir -p /workspace/t/parts; cd /workspace/t/parts
URL=https://huggingface.co/Lightricks/LTX-2.3-fp8/resolve/main/ltx-2.3-22b-dev-fp8.safetensors
SIZE=29145431166
N=10
CH=$(( (SIZE + N - 1) / N ))
part() {
  i=$1; s=$(( i * CH )); e=$(( s + CH - 1 )); [ $e -ge $SIZE ] && e=$(( SIZE - 1 )); want=$(( e - s + 1 ))
  for t in 1 2 3 4 5 6 7 8 9 10 11 12; do
    have=$(stat -c %s p$i 2>/dev/null || echo 0)
    [ $have -ge $want ] && return
    curl -sL -r $(( s + have ))-$e $URL >> p$i
  done
}
i=0; while [ $i -lt $N ]; do part $i & i=$(( i + 1 )); done
wait
total=0; for i in 0 1 2 3 4 5 6 7 8 9; do total=$(( total + $(stat -c %s p$i) )); done
if [ $total -eq $SIZE ]; then
  cat p0 p1 p2 p3 p4 p5 p6 p7 p8 p9 > /workspace/runpod-slim/ComfyUI/models/checkpoints/ltx-2.3-22b-dev-fp8.safetensors && rm -f p? && echo got ckpt >> /workspace/t/dl.log
else echo SIZEMISMATCH $total >> /workspace/t/dl.log; fi
