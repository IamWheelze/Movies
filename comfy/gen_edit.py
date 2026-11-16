"""Edit a single image with Flux.2 Klein, for example to remove an unwanted person.

Usage: python3 gen_edit.py NAME IMAGE --prompt TEXT [--seeds N] [--host URL]
IMAGE is a file name in ComfyUI's input folder. Results land in output/edits/<name>_*.png.
"""
import json, random, sys, time, urllib.request

name, image = sys.argv[1:3]
opt = dict(zip(sys.argv[3:], sys.argv[4:]))
host = opt.get("--host", "http://127.0.0.1:8188")
text = opt["--prompt"]
seeds = int(opt.get("--seeds", 1))
W, H = 1344, 768


def workflow(seed):
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "flux-2-klein-4b-fp8.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "flux2", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "flux2-vae.safetensors"}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": text}},
        "a0": {"class_type": "LoadImage", "inputs": {"image": image}},
        "a1": {"class_type": "ImageScaleToTotalPixels", "inputs": {"image": ["a0", 0], "upscale_method": "nearest-exact", "megapixels": 1, "resolution_steps": 1}},
        "a2": {"class_type": "VAEEncode", "inputs": {"pixels": ["a1", 0], "vae": ["3", 0]}},
        "a3": {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["4", 0], "latent": ["a2", 0]}},
        "5": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
        "6": {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": W, "height": H, "batch_size": 1}},
        "7": {"class_type": "Flux2Scheduler", "inputs": {"steps": 4, "width": W, "height": H}},
        "8": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "9": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "10": {"class_type": "CFGGuider", "inputs": {"model": ["1", 0], "positive": ["a3", 0], "negative": ["5", 0], "cfg": 1}},
        "11": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["9", 0], "guider": ["10", 0], "sampler": ["8", 0], "sigmas": ["7", 0], "latent_image": ["6", 0]}},
        "12": {"class_type": "VAEDecode", "inputs": {"samples": ["11", 0], "vae": ["3", 0]}},
        "13": {"class_type": "SaveImage", "inputs": {"images": ["12", 0], "filename_prefix": f"edits/{name}_s{seed}"}},
    }


def post(body):
    req = urllib.request.Request(host + "/prompt", json.dumps({"prompt": body}).encode(), {"Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(req))["prompt_id"]
    except urllib.error.HTTPError as e:
        sys.exit(e.read().decode()[:2000])


ids = []
for _ in range(seeds):
    seed = random.randrange(2**31)
    ids.append(post(workflow(seed)))
    print("queued", name, seed, flush=True)
while ids:
    time.sleep(3)
    for i in list(ids):
        h = json.load(urllib.request.urlopen(f"{host}/history/{i}"))
        if i in h:
            print("finished", h[i]["status"]["status_str"], [im["filename"] for o in h[i]["outputs"].values() for im in o.get("images", [])], flush=True)
            ids.remove(i)
