'''Pod: keyframes with the character LoRA. python3 kf_lora.py KEYS.txt LORA.safetensors N [W H]  (lines id|prompt)'''
import json, sys, time, urllib.request
H = 'http://127.0.0.1:8188'
keys, lora, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
W, HH = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (1152, 640)
QUAL = 'masterpiece, high score, great score, absurdres, anime screenshot, hand-painted background, earth tones, ochre, indigo, '
NEG = 'lowres, bad anatomy, bad hands, text, error, worst quality, low quality, signature, watermark, blurry, 3d, realistic, photo, collage, panels, blonde hair, modern clothes, daylight'
def api(p, b=None):
    r = urllib.request.Request(H + p, json.dumps(b).encode() if b is not None else None, {'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(r))
for line in open(keys):
    if not line.strip():
        continue
    kid, txt = line.rstrip('\n').split('|')[:2]
    for c in range(n):
        g = {'1': {'class_type': 'CheckpointLoaderSimple', 'inputs': {'ckpt_name': 'animagine-xl-4.0.safetensors'}},
             'L': {'class_type': 'LoraLoader', 'inputs': {'model': ['1', 0], 'clip': ['1', 1], 'lora_name': lora, 'strength_model': 0.9, 'strength_clip': 0.9}},
             '2': {'class_type': 'CLIPTextEncode', 'inputs': {'clip': ['L', 1], 'text': QUAL + txt}},
             '3': {'class_type': 'CLIPTextEncode', 'inputs': {'clip': ['L', 1], 'text': NEG}},
             '4': {'class_type': 'EmptyLatentImage', 'inputs': {'width': W, 'height': HH, 'batch_size': 1}},
             '5': {'class_type': 'KSampler', 'inputs': {'model': ['L', 0], 'positive': ['2', 0], 'negative': ['3', 0], 'latent_image': ['4', 0], 'seed': 300 + c * 11, 'steps': 28, 'cfg': 5, 'sampler_name': 'euler_ancestral', 'scheduler': 'normal', 'denoise': 1}},
             '6': {'class_type': 'VAEDecode', 'inputs': {'samples': ['5', 0], 'vae': ['1', 2]}},
             '7': {'class_type': 'SaveImage', 'inputs': {'images': ['6', 0], 'filename_prefix': 'kfl/%s_c%d' % (kid, c)}}}
        pid = api('/prompt', {'prompt': g})['prompt_id']
        while pid not in api('/history/' + pid):
            time.sleep(1)
        print(kid, c, flush=True)
print('KFDONE', flush=True)
