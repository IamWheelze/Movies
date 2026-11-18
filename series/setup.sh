#!/bin/sh
# One-time setup on a fresh Pod: models, tools, scripts, safety timer. Usage: setup.sh SECONDS_UNTIL_SELF_STOP
export HF_XET_HIGH_PERFORMANCE=1
M=/workspace/runpod-slim/ComfyUI/models
mkdir -p /workspace/t /workspace/series_out $M/checkpoints $M/loras $M/text_encoders $M/latent_upscale_models /workspace/t/dl
cd /workspace/t
cp /workspace/Movies/anime/ltx_run.py /workspace/t/
END=$(( $(date +%s) + ${1:-9000} ))
cat > wd.sh <<'EOW'
#!/bin/sh
END=$1
while [ $(date +%s) -lt $END ]; do sleep 20; done
runpodctl stop pod $RUNPOD_POD_ID
EOW
chmod +x wd.sh; nohup ./wd.sh $END > wd.log 2>&1 &
pip install -q faster-whisper > pipw.log 2>&1 &
cd /workspace/t/dl
g() { for i in 1 2 3 4 5; do timeout 400 hf download $1 $2 --local-dir . >> ../dl.log 2>&1 && mv -f $2 $M/$3/ && echo got $2 >> ../dl.log && return; done; echo FAILED $2 >> ../dl.log; }
g Comfy-Org/ltx-2 split_files/text_encoders/gemma_3_12B_it_fp4_mixed.safetensors text_encoders
g Comfy-Org/ltx-2 split_files/loras/gemma-3-12b-it-abliterated_lora_rank64_bf16.safetensors loras
g Comfy-Org/ltx-2.3 split_files/loras/ltx_2.3_22b_distilled_1.1_lora_dynamic_fro09_avg_rank_111_bf16.safetensors loras
g Lightricks/LTX-2.3 ltx-2.3-spatial-upscaler-x2-1.1.safetensors latent_upscale_models
g cagliostrolab/animagine-xl-4.0 animagine-xl-4.0.safetensors checkpoints
g Lightricks/LTX-2.3-fp8 ltx-2.3-22b-dev-fp8.safetensors checkpoints
wait
echo ALLDONE >> ../dl.log
