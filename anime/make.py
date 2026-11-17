'''Anime scene maker for ComfyUI: anime stills with Animagine XL, then 720p clips with Wan 2.2.

python3 make.py stills SHOTS.txt [--n 3] [--only 01,02]   make N candidate stills per shot
python3 make.py pick 01:0 02:2                            choose a candidate for each shot
python3 make.py clips SHOTS.txt [--only 01,02]            animate the chosen stills

SHOTS.txt lines: id|still prompt|motion prompt
'''
import glob, json, random, shutil, sys, time, urllib.request

host = 'http://127.0.0.1:8188'
comfy = '/workspace/runpod-slim/ComfyUI'
mode = sys.argv[1]
opt = dict(zip(sys.argv[2:], sys.argv[3:]))
only = opt['--only'].split(',') if '--only' in opt else None
QUALITY = 'masterpiece, high score, great score, absurdres, anime screenshot, cinematic lighting, detailed background, '
NEG = ('lowres, bad anatomy, bad hands, text, error, missing finger, extra digits, fewer digits, cropped, worst quality, low quality, '
       'low score, bad score, average score, signature, watermark, username, blurry, 3d, realistic, photo, multiple boys, crowd')
WAN_NEG = 'blurry, static, still image, deformed, extra limbs, bad hands, text, subtitles, watermark, jpeg artifacts, realistic, 3d render'


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def api(path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(host + path, data, {'Content-Type': 'application/json'})
    try:
        return json.load(urllib.request.urlopen(req))
    except urllib.error.HTTPError as e:
        raise RuntimeError(e.read().decode()[:600])


def run(wf):
    pid = api('/prompt', {'prompt': wf})['prompt_id']
    while True:
        time.sleep(3)
        h = api('/history/' + pid)
        if pid in h:
            if h[pid]['status']['status_str'] != 'success':
                raise RuntimeError(json.dumps(h[pid]['status'])[:600])
            return h[pid]['outputs']


def shots():
    out = []
    for line in open(sys.argv[2]):
        if line.strip():
            sid, still, motion = line.strip().split('|', 2)
            if only is None or sid in only:
                out.append((sid, still, motion))
    return out


def still_wf(text, seed, name):
    return {
        '1': {'class_type': 'CheckpointLoaderSimple', 'inputs': {'ckpt_name': 'animagine-xl-4.0.safetensors'}},
        '2': {'class_type': 'CLIPTextEncode', 'inputs': {'clip': ['1', 1], 'text': QUALITY + text}},
        '3': {'class_type': 'CLIPTextEncode', 'inputs': {'clip': ['1', 1], 'text': NEG}},
        '4': {'class_type': 'EmptyLatentImage', 'inputs': {'width': 1344, 'height': 768, 'batch_size': 1}},
        '5': {'class_type': 'KSampler', 'inputs': {'model': ['1', 0], 'positive': ['2', 0], 'negative': ['3', 0], 'latent_image': ['4', 0],
              'seed': seed, 'steps': 28, 'cfg': 5, 'sampler_name': 'euler_ancestral', 'scheduler': 'normal', 'denoise': 1}},
        '6': {'class_type': 'VAEDecode', 'inputs': {'samples': ['5', 0], 'vae': ['1', 2]}},
        '7': {'class_type': 'SaveImage', 'inputs': {'images': ['6', 0], 'filename_prefix': name}},
    }


def branch(n, noise):
    return {
        n + '0': {'class_type': 'UNETLoader', 'inputs': {'unet_name': 'wan2.2_i2v_%s_noise_14B_fp8_scaled.safetensors' % noise, 'weight_dtype': 'default'}},
        n + '1': {'class_type': 'LoraLoaderModelOnly', 'inputs': {'model': [n + '0', 0], 'lora_name': 'wan2.2_i2v_lightx2v_4steps_lora_v1_%s_noise.safetensors' % noise, 'strength_model': 1}},
        n + '2': {'class_type': 'ModelSamplingSD3', 'inputs': {'model': [n + '1', 0], 'shift': 5}},
    }


def clip_wf(image, text, seed, name, frames=81):
    def sampler(model, latent, add, start, end, leftover):
        return {'class_type': 'KSamplerAdvanced', 'inputs': {'model': [model, 0], 'positive': ['6', 0], 'negative': ['6', 1], 'latent_image': latent,
                'add_noise': add, 'noise_seed': seed, 'steps': 4, 'cfg': 1, 'sampler_name': 'euler', 'scheduler': 'simple',
                'start_at_step': start, 'end_at_step': end, 'return_with_leftover_noise': leftover}}
    wf = {}
    wf.update(branch('h', 'high'))
    wf.update(branch('l', 'low'))
    wf.update({
        '1': {'class_type': 'CLIPLoader', 'inputs': {'clip_name': 'umt5_xxl_fp8_e4m3fn_scaled.safetensors', 'type': 'wan', 'device': 'default'}},
        '2': {'class_type': 'VAELoader', 'inputs': {'vae_name': 'wan_2.1_vae.safetensors'}},
        '3': {'class_type': 'CLIPTextEncode', 'inputs': {'clip': ['1', 0], 'text': text}},
        '4': {'class_type': 'CLIPTextEncode', 'inputs': {'clip': ['1', 0], 'text': WAN_NEG}},
        '5': {'class_type': 'LoadImage', 'inputs': {'image': image}},
        '6': {'class_type': 'WanImageToVideo', 'inputs': {'positive': ['3', 0], 'negative': ['4', 0], 'vae': ['2', 0], 'start_image': ['5', 0],
              'width': 1280, 'height': 720, 'length': frames, 'batch_size': 1}},
        '7': sampler('h2', ['6', 2], 'enable', 0, 2, 'enable'),
        '8': sampler('l2', ['7', 0], 'disable', 2, 4, 'disable'),
        '9': {'class_type': 'VAEDecode', 'inputs': {'samples': ['8', 0], 'vae': ['2', 0]}},
        '10': {'class_type': 'CreateVideo', 'inputs': {'images': ['9', 0], 'fps': 16}},
        '11': {'class_type': 'SaveVideo', 'inputs': {'video': ['10', 0], 'filename_prefix': name, 'format': 'auto', 'codec': 'auto'}},
    })
    return wf


if mode == 'stills':
    n = int(opt.get('--n', 3))
    for sid, still, motion in shots():
        for k in range(n):
            out = run(still_wf(still, random.randrange(2**31), 'stills/%s_c%d' % (sid, k)))
            f = out['7']['images'][0]
            shutil.copy(comfy + '/output/' + f['subfolder'] + '/' + f['filename'], comfy + '/input/cand-%s-%d.png' % (sid, k))
            log('still', sid, 'candidate', k)
    log('STILLS DONE')
elif mode == 'pick':
    for p in sys.argv[2:]:
        sid, k = p.split(':')
        shutil.copy(comfy + '/input/cand-%s-%s.png' % (sid, k), comfy + '/input/still-%s.png' % sid)
        log('picked', sid, k)
elif mode == 'clips':
    for sid, still, motion in shots():
        text = motion + ' Anime style, smooth hand-drawn animation, expressive, cinematic.'
        run(clip_wf('still-%s.png' % sid, text, random.randrange(2**31), 'clips/%s_s%d' % (sid, random.randrange(10**6))))
        log('clip', sid, 'done')
    log('CLIPS DONE')
