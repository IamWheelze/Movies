#!/bin/sh
cd /workspace/t
accelerate launch --mixed_precision=bf16 train_sdxl_lora.py \
 --pretrained_model_name_or_path=/workspace/t/animagine_diff --train_data_dir=/workspace/t/trainset --caption_column=text \
 --resolution=768 --center_crop --train_batch_size=2 --max_train_steps=${1:-1400} --learning_rate=1e-4 --lr_scheduler=constant --lr_warmup_steps=0 \
 --rank=32 --mixed_precision=bf16 --seed=7 --checkpointing_steps=700 --output_dir=/workspace/t/lora_out --gradient_checkpointing
