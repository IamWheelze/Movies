# Movies

AI-generated animated episodes, produced with ComfyUI on a rented Runpod GPU.

## Layout

- `episodes/<nn-title>/style.json` — the look of the whole episode, plus the negative prompt.
- `episodes/<nn-title>/references.json` — characters and locations to generate once and reuse.
- `episodes/<nn-title>/shots.json` — one entry per clip: prompt, length, and which references it needs.
- `comfy/gen_refs.py` — generates reference images with Z-Image.
- `comfy/gen_shot.py` — animates a keyframe into a clip with Wan 2.2 image-to-video.

## Running

Both scripts talk to a ComfyUI server (default `http://127.0.0.1:8188`, so run them on the Pod).

```bash
python3 comfy/gen_refs.py episodes/01-the-river-will-rise --seeds 2
```

```bash
python3 comfy/gen_shot.py episodes/01-the-river-will-rise 03 keyframe_03.png
```

Reference images land in ComfyUI's `output/ref/`, clips in `output/shots/`.
A keyframe for `gen_shot.py` must be in ComfyUI's `input/` folder.

## Models

From the `Comfy-Org` repositories on Hugging Face, placed under `ComfyUI/models/`:

- Z-Image: `diffusion_models/z_image_bf16.safetensors`, `text_encoders/qwen_3_4b.safetensors`, `vae/ae.safetensors`
- Wan 2.2 I2V 14B: both `wan2.2_i2v_*_noise_14B_fp8_scaled.safetensors`, both 4-step `lightx2v` LoRAs,
  `text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors`, `vae/wan_2.1_vae.safetensors`
