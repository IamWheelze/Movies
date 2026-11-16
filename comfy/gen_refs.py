"""Generate reference images with Z-Image through a ComfyUI server.

Usage: python3 gen_refs.py EPISODE_DIR [ref_id ...] [--seeds N] [--host URL]
Images land in ComfyUI's output folder under ref/<id>_*.png.
"""
import json, random, sys, time, urllib.request

args = [a for a in sys.argv[1:] if not a.startswith("--")]
opt = dict(zip(sys.argv[1:], sys.argv[2:]))
host = opt.get("--host", "http://127.0.0.1:8188")
seeds = int(opt.get("--seeds", 2))
ep = args[0]
style = json.load(open(f"{ep}/style.json"))
refs = json.load(open(f"{ep}/references.json"))
wanted = [a for a in args[1:] if not a.isdigit() and not a.startswith("http")]
WIDE = ("river", "house", "sandal")


def workflow(ref, seed):
    wide = any(k in ref["id"] for k in WIDE)
    w, h = (1344, 768) if wide else (896, 1152)
    pos = f'{ref["prompt"]} {style["style"]}'
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_bf16.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "lumina2", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        "4": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["1", 0], "shift": 3}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": pos}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": style["negative"]}},
        "7": {"class_type": "EmptySD3LatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "8": {"class_type": "KSampler", "inputs": {"model": ["4", 0], "positive": ["5", 0], "negative": ["6", 0],
              "latent_image": ["7", 0], "seed": seed, "steps": 25, "cfg": 4, "sampler_name": "res_multistep",
              "scheduler": "simple", "denoise": 1}},
        "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
        "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": f'ref/{ref["id"]}_s{seed}'}},
    }


def post(path, body):
    req = urllib.request.Request(host + path, json.dumps(body).encode(), {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req))


ids = []
for ref in refs:
    if wanted and ref["id"] not in wanted:
        continue
    for _ in range(seeds):
        seed = random.randrange(2**31)
        ids.append(post("/prompt", {"prompt": workflow(ref, seed)})["prompt_id"])
        print("queued", ref["id"], seed, flush=True)

while ids:
    time.sleep(3)
    hist = {i: json.load(urllib.request.urlopen(f"{host}/history/{i}")) for i in ids}
    for i, h in hist.items():
        if i in h:
            st = h[i]["status"]["status_str"]
            print("finished", st, [im["filename"] for o in h[i]["outputs"].values() for im in o.get("images", [])], flush=True)
            ids.remove(i)
