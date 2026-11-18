'''Pod: generate LoRA training candidates. python3 gen_dataset.py  -> /workspace/t/ds/<char>/*.png (+ captions)'''
import json, os, random, sys, time, urllib.request
H = 'http://127.0.0.1:8188'
CH = {
 'balaam_c': '1boy, solo, male focus, young man, warm brown skin, narrow face, black curly hair tied at nape, light beard, indigo tunic, sand sash',
 'mother_c': '1girl, solo, adult woman, dark-skinned female, dark brown skin, dark hair in a low bun with side bangs, gray-green wrapped cloth dress, simple ancient robe, facing viewer, face visible, looking at viewer',
 'girl_c': '1girl, solo, little girl, warm brown skin, two short braids, ochre tunic',
}
POSES = ['front view, upper body, looking at viewer', 'three-quarter view, upper body', 'side profile, upper body', 'looking up, upper body',
         'looking down, upper body', 'smiling, upper body', 'worried expression, upper body', 'speaking, open mouth, upper body',
         'close-up face, portrait', 'full body, standing', 'cowboy shot, hand raised', 'looking back at viewer, face visible',
         'night, warm lamp light on face, upper body', 'river bank background, upper body']
BG = ['plain light background', 'ancient mesopotamian mudbrick wall background']
QUAL = 'masterpiece, high score, great score, absurdres, anime screenshot, hand-painted background, earth tones, '
NEG = 'lowres, bad anatomy, bad hands, text, error, worst quality, low quality, signature, watermark, blurry, 3d, realistic, photo, from behind, back view, light skin, pale skin, kimono, japanese clothes, obi, multiple people, collage, panels, blonde hair, modern clothes'

def api(p, b=None):
    r = urllib.request.Request(H + p, json.dumps(b).encode() if b is not None else None, {'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(r))

def wf(text, seed, name):
    return {'1': {'class_type': 'CheckpointLoaderSimple', 'inputs': {'ckpt_name': 'animagine-xl-4.0.safetensors'}},
            '2': {'class_type': 'CLIPTextEncode', 'inputs': {'clip': ['1', 1], 'text': QUAL + text}},
            '3': {'class_type': 'CLIPTextEncode', 'inputs': {'clip': ['1', 1], 'text': NEG}},
            '4': {'class_type': 'EmptyLatentImage', 'inputs': {'width': 1024, 'height': 1024, 'batch_size': 1}},
            '5': {'class_type': 'KSampler', 'inputs': {'model': ['1', 0], 'positive': ['2', 0], 'negative': ['3', 0], 'latent_image': ['4', 0], 'seed': seed, 'steps': 28, 'cfg': 5, 'sampler_name': 'euler_ancestral', 'scheduler': 'normal', 'denoise': 1}},
            '6': {'class_type': 'VAEDecode', 'inputs': {'samples': ['5', 0], 'vae': ['1', 2]}},
            '7': {'class_type': 'SaveImage', 'inputs': {'images': ['6', 0], 'filename_prefix': 'ds/' + name}}}
n = 0
import os
ONLY = os.environ.get('ONLY')
for c, tags in CH.items():
    if ONLY and c != ONLY:
        continue
    for i, p in enumerate(POSES):
        for j in range(2):
            seed = 1000 + i * 7 + j  # same seed family across characters keeps framing comparable
            txt = '%s, %s, %s, %s' % (c, tags, p, BG[j])
            pid = api('/prompt', {'prompt': wf(txt, seed, '%s_%02d_%d' % (c, i, j))})['prompt_id']
            while pid not in api('/history/' + pid):
                time.sleep(1)
            json.dump(txt, open('/workspace/t/ds_%s_%02d_%d.txt' % (c, i, j), 'w'))
            n += 1
            print(n, flush=True)
print('GENDONE', flush=True)
