#!/bin/sh
# Fresh-Pod setup (v2): models, speech tools, scripts, self-stop timer. Usage: setup2.sh SECONDS_UNTIL_SELF_STOP
export HF_XET_HIGH_PERFORMANCE=1
M=/workspace/runpod-slim/ComfyUI/models
mkdir -p /workspace/t /workspace/series_out $M/checkpoints $M/loras $M/text_encoders $M/latent_upscale_models /workspace/t/dl
cd /workspace/t
cp /workspace/Movies/anime/ltx_run.py /workspace/t/
END=$(( $(date +%s) + ${1:-7200} ))
cat > wd.sh <<'EOW'
#!/bin/sh
END=$1
while [ $(date +%s) -lt $END ]; do sleep 20; done
runpodctl stop pod $RUNPOD_POD_ID
EOW
chmod +x wd.sh; nohup ./wd.sh $END > wd.log 2>&1 &
(apt-get install -y -q espeak-ng > apt.log 2>&1; pip install -q kokoro soundfile faster-whisper > pipw.log 2>&1; echo PIPDONE >> pipw.log) &
chmod +x /workspace/Movies/series/par_dl.sh; nohup /workspace/Movies/series/par_dl.sh > par.out 2>&1 &
cd /workspace/t/dl
g() { for i in 1 2 3 4 5; do timeout 300 hf download $1 $2 --local-dir . >> ../dl.log 2>&1 && mv -f $2 $M/$3/ && echo got $2 >> ../dl.log && return; done; echo FAILED $2 >> ../dl.log; }
g Comfy-Org/ltx-2 split_files/text_encoders/gemma_3_12B_it_fp4_mixed.safetensors text_encoders
g Comfy-Org/ltx-2 split_files/loras/gemma-3-12b-it-abliterated_lora_rank64_bf16.safetensors loras
g Comfy-Org/ltx-2.3 split_files/loras/ltx_2.3_22b_distilled_1.1_lora_dynamic_fro09_avg_rank_111_bf16.safetensors loras
g Lightricks/LTX-2.3 ltx-2.3-spatial-upscaler-x2-1.1.safetensors latent_upscale_models
g cagliostrolab/animagine-xl-4.0 animagine-xl-4.0.safetensors checkpoints
wait
echo ALLDONE >> ../dl.log
