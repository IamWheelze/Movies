"""Animate one keyframe into a clip with Wan 2.2 image-to-video through ComfyUI.

Usage: python3 gen_shot.py EPISODE_DIR SHOT_ID KEYFRAME [--prompt TEXT] [--seconds N] [--host URL]
KEYFRAME is a file name inside ComfyUI's input folder.
Clips land in ComfyUI's output folder under shots/<id>_*.mp4.
"""
import json, random, sys, time, urllib.request

args = [a for a in sys.argv[1:4]]
opt = dict(zip(sys.argv[4:], sys.argv[5:]))
host = opt.get("--host", "http://127.0.0.1:8188")
ep, shot_id, keyframe = args
style = json.load(open(f"{ep}/style.json"))
shots = {s["id"]: s for s in json.load(open(f"{ep}/shots.json"))} if "--prompt" not in opt else {}
text = opt.get("--prompt") or shots[shot_id]["prompt"]
seconds = int(opt.get("--seconds") or shots.get(shot_id, {}).get("seconds", 5))
frames = min(seconds, 5) * 16 + 1  # Wan 2.2 holds together up to about 5 s at 16 fps
seed = random.randrange(2**31)
pos = f"{text} Hand-painted 2D animation, painted backgrounds with visible texture, restrained deliberate movement, steady camera."
D = "diffusion_models"


def branch(n, noise):
    return {
        f"{n}0": {"class_type": "UNETLoader", "inputs": {"unet_name": f"wan2.2_i2v_{noise}_noise_14B_fp8_scaled.safetensors", "weight_dtype": "default"}},
        f"{n}1": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": [f"{n}0", 0], "lora_name": f"wan2.2_i2v_lightx2v_4steps_lora_v1_{noise}_noise.safetensors", "strength_model": 1}},
        f"{n}2": {"class_type": "ModelSamplingSD3", "inputs": {"model": [f"{n}1", 0], "shift": 5}},
    }


def sampler(model, latent, add, start, end, leftover):
    return {"class_type": "KSamplerAdvanced", "inputs": {"model": [model, 0], "positive": ["6", 0], "negative": ["6", 1],
            "latent_image": latent, "add_noise": add, "noise_seed": seed, "steps": 4, "cfg": 1, "sampler_name": "euler",
            "scheduler": "simple", "start_at_step": start, "end_at_step": end, "return_with_leftover_noise": leftover}}


wf = {
    **branch("h", "high"), **branch("l", "low"),
    "1": {"class_type": "CLIPLoader", "inputs": {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan", "device": "default"}},
    "2": {"class_type": "VAELoader", "inputs": {"vae_name": "wan_2.1_vae.safetensors"}},
    "3": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 0], "text": pos}},
    "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 0], "text": style["negative"]}},
    "5": {"class_type": "LoadImage", "inputs": {"image": keyframe}},
    "6": {"class_type": "WanImageToVideo", "inputs": {"positive": ["3", 0], "negative": ["4", 0], "vae": ["2", 0],
          "start_image": ["5", 0], "width": 832, "height": 480, "length": frames, "batch_size": 1}},
    "7": sampler("h2", ["6", 2], "enable", 0, 2, "enable"),
    "8": sampler("l2", ["7", 0], "disable", 2, 4, "disable"),
    "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["2", 0]}},
    "10": {"class_type": "CreateVideo", "inputs": {"images": ["9", 0], "fps": 16}},
    "11": {"class_type": "SaveVideo", "inputs": {"video": ["10", 0], "filename_prefix": f"shots/{shot_id}_s{seed}", "format": "auto", "codec": "auto"}},
}
req = urllib.request.Request(host + "/prompt", json.dumps({"prompt": wf}).encode(), {"Content-Type": "application/json"})
try:
    pid = json.load(urllib.request.urlopen(req))["prompt_id"]
except urllib.error.HTTPError as e:
    sys.exit(e.read().decode()[:2000])
print("queued", shot_id, seed, frames, "frames", flush=True)
while True:
    time.sleep(5)
    h = json.load(urllib.request.urlopen(f"{host}/history/{pid}"))
    if pid in h:
        print("finished", h[pid]["status"]["status_str"], json.dumps(h[pid]["outputs"])[:400], flush=True)
        break
