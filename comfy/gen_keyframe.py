"""Build a shot's starting frame by placing a character into a scene with Flux.2 Klein (image edit).

Usage: python3 gen_keyframe.py SHOT_ID SCENE CHARACTER --prompt TEXT [--host URL]
SCENE and CHARACTER are file names in ComfyUI's input folder (image 1 and image 2 in the prompt).
Results land in ComfyUI's output folder under keyframes/<shot>_*.png.
"""
import json, random, sys, time, urllib.request

shot_id, scene, character = sys.argv[1:4]
opt = dict(zip(sys.argv[4:], sys.argv[5:]))
host = opt.get("--host", "http://127.0.0.1:8188")
text = opt["--prompt"]
seed = random.randrange(2**31)
W, H = 1344, 768


def ref(n, image, cond):
    return {
        f"{n}0": {"class_type": "LoadImage", "inputs": {"image": image}},
        f"{n}1": {"class_type": "ImageScaleToTotalPixels", "inputs": {"image": [f"{n}0", 0], "upscale_method": "nearest-exact", "megapixels": 1, "resolution_steps": 1}},
        f"{n}2": {"class_type": "VAEEncode", "inputs": {"pixels": [f"{n}1", 0], "vae": ["3", 0]}},
        f"{n}3": {"class_type": "ReferenceLatent", "inputs": {"conditioning": cond, "latent": [f"{n}2", 0]}},
    }


wf = {
    "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "flux-2-klein-4b-fp8.safetensors", "weight_dtype": "default"}},
    "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "flux2", "device": "default"}},
    "3": {"class_type": "VAELoader", "inputs": {"vae_name": "flux2-vae.safetensors"}},
    "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": text}},
    **ref("a", scene, ["4", 0]),
    **ref("b", character, ["a3", 0]),
    "5": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
    "6": {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": W, "height": H, "batch_size": 1}},
    "7": {"class_type": "Flux2Scheduler", "inputs": {"steps": 4, "width": W, "height": H}},
    "8": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
    "9": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
    "10": {"class_type": "CFGGuider", "inputs": {"model": ["1", 0], "positive": ["b3", 0], "negative": ["5", 0], "cfg": 1}},
    "11": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["9", 0], "guider": ["10", 0], "sampler": ["8", 0], "sigmas": ["7", 0], "latent_image": ["6", 0]}},
    "12": {"class_type": "VAEDecode", "inputs": {"samples": ["11", 0], "vae": ["3", 0]}},
    "13": {"class_type": "SaveImage", "inputs": {"images": ["12", 0], "filename_prefix": f"keyframes/{shot_id}_s{seed}"}},
}
req = urllib.request.Request(host + "/prompt", json.dumps({"prompt": wf}).encode(), {"Content-Type": "application/json"})
try:
    pid = json.load(urllib.request.urlopen(req))["prompt_id"]
except urllib.error.HTTPError as e:
    sys.exit(e.read().decode()[:2000])
print("queued", shot_id, seed, flush=True)
while True:
    time.sleep(3)
    h = json.load(urllib.request.urlopen(f"{host}/history/{pid}"))
    if pid in h:
        print("finished", h[pid]["status"]["status_str"], json.dumps(h[pid]["outputs"])[:300], flush=True)
        break
