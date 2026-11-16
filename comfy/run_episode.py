'''Run a whole episode: make a keyframe for every shot, then animate each into a clip.

Usage: python3 run_episode.py EPISODE_DIR [--order 00,03,04] [--cands N --kf-only] [--comfy DIR] [--host URL] [--redo]
With --cands N it writes N candidate keyframes kf-<id>-<k>.png; copy the best to kf-<id>.png before rendering clips.
kf_overrides.txt (id|prompt) in the episode folder replaces the automatic keyframe prompt for a shot.
Reads style.json and shots.txt (id|seconds|refs|direct|prompt) from EPISODE_DIR.
Reference images must be in ComfyUI input as ref-<id>.png.
'''
import glob, json, os, random, shutil, sys, time, urllib.request

ep = sys.argv[1]
opt = dict(zip(sys.argv[2:], sys.argv[3:]))
host = opt.get('--host', 'http://127.0.0.1:8188')
comfy = opt.get('--comfy', '/workspace/runpod-slim/ComfyUI')
redo = '--redo' in sys.argv
cands = int(opt.get('--cands', 0))
kf_only = '--kf-only' in sys.argv
overrides = {}
if os.path.exists(ep + '/kf_overrides.txt'):
    for line in open(ep + '/kf_overrides.txt'):
        if line.strip():
            k, v = line.strip().split('|', 1)
            overrides[k] = v
style = json.load(open(ep + '/style.json'))
shots = {}
for line in open(ep + '/shots.txt'):
    if line.strip():
        sid, secs, refs, direct, prompt = line.strip().split('|', 4)
        shots[sid] = {'id': sid, 'seconds': int(secs), 'refs': refs.split(','), 'direct': direct == '1', 'prompt': prompt}
order = opt['--order'].split(',') if '--order' in opt else list(shots)
LOCATIONS = ('river-and-ferry', 'beor-house', 'beor-house-reverse')
WHO = {'balaam': 'Balaam, a young man', 'balaam-after-flood': 'Balaam, a young man with a linen-wrapped right palm',
       'beor': 'Beor, an older man', 'hadan': 'Hadan, a grain merchant', 'girl-and-mother': 'a girl and her mother',
       'stranger': 'a dusty traveler', 'stranger-sandal': 'a sandal'}
W, H = 1344, 768


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


def kf_workflow(images, text, seed, sid):
    wf = {
        '1': {'class_type': 'UNETLoader', 'inputs': {'unet_name': 'flux-2-klein-4b-fp8.safetensors', 'weight_dtype': 'default'}},
        '2': {'class_type': 'CLIPLoader', 'inputs': {'clip_name': 'qwen_3_4b.safetensors', 'type': 'flux2', 'device': 'default'}},
        '3': {'class_type': 'VAELoader', 'inputs': {'vae_name': 'flux2-vae.safetensors'}},
        '4': {'class_type': 'CLIPTextEncode', 'inputs': {'clip': ['2', 0], 'text': text}},
    }
    cond = ['4', 0]
    for n, img in enumerate(images):
        k = 'r%d' % n
        wf[k + 'a'] = {'class_type': 'LoadImage', 'inputs': {'image': img}}
        wf[k + 'b'] = {'class_type': 'ImageScaleToTotalPixels', 'inputs': {'image': [k + 'a', 0], 'upscale_method': 'nearest-exact', 'megapixels': 1, 'resolution_steps': 1}}
        wf[k + 'c'] = {'class_type': 'VAEEncode', 'inputs': {'pixels': [k + 'b', 0], 'vae': ['3', 0]}}
        wf[k + 'd'] = {'class_type': 'ReferenceLatent', 'inputs': {'conditioning': cond, 'latent': [k + 'c', 0]}}
        cond = [k + 'd', 0]
    wf.update({
        '5': {'class_type': 'ConditioningZeroOut', 'inputs': {'conditioning': ['4', 0]}},
        '6': {'class_type': 'EmptyFlux2LatentImage', 'inputs': {'width': W, 'height': H, 'batch_size': 1}},
        '7': {'class_type': 'Flux2Scheduler', 'inputs': {'steps': 4, 'width': W, 'height': H}},
        '8': {'class_type': 'KSamplerSelect', 'inputs': {'sampler_name': 'euler'}},
        '9': {'class_type': 'RandomNoise', 'inputs': {'noise_seed': seed}},
        '10': {'class_type': 'CFGGuider', 'inputs': {'model': ['1', 0], 'positive': cond, 'negative': ['5', 0], 'cfg': 1}},
        '11': {'class_type': 'SamplerCustomAdvanced', 'inputs': {'noise': ['9', 0], 'guider': ['10', 0], 'sampler': ['8', 0], 'sigmas': ['7', 0], 'latent_image': ['6', 0]}},
        '12': {'class_type': 'VAEDecode', 'inputs': {'samples': ['11', 0], 'vae': ['3', 0]}},
        '13': {'class_type': 'SaveImage', 'inputs': {'images': ['12', 0], 'filename_prefix': 'keyframes/%s_s%d' % (sid, seed)}},
    })
    return wf


def vid_branch(n, noise):
    return {
        n + '0': {'class_type': 'UNETLoader', 'inputs': {'unet_name': 'wan2.2_i2v_%s_noise_14B_fp8_scaled.safetensors' % noise, 'weight_dtype': 'default'}},
        n + '1': {'class_type': 'LoraLoaderModelOnly', 'inputs': {'model': [n + '0', 0], 'lora_name': 'wan2.2_i2v_lightx2v_4steps_lora_v1_%s_noise.safetensors' % noise, 'strength_model': 1}},
        n + '2': {'class_type': 'ModelSamplingSD3', 'inputs': {'model': [n + '1', 0], 'shift': 5}},
    }


def vid_workflow(image, text, frames, seed, sid):
    def sampler(model, latent, add, start, end, leftover):
        return {'class_type': 'KSamplerAdvanced', 'inputs': {'model': [model, 0], 'positive': ['6', 0], 'negative': ['6', 1],
                'latent_image': latent, 'add_noise': add, 'noise_seed': seed, 'steps': 4, 'cfg': 1, 'sampler_name': 'euler',
                'scheduler': 'simple', 'start_at_step': start, 'end_at_step': end, 'return_with_leftover_noise': leftover}}
    wf = {}
    wf.update(vid_branch('h', 'high'))
    wf.update(vid_branch('l', 'low'))
    wf.update({
        '1': {'class_type': 'CLIPLoader', 'inputs': {'clip_name': 'umt5_xxl_fp8_e4m3fn_scaled.safetensors', 'type': 'wan', 'device': 'default'}},
        '2': {'class_type': 'VAELoader', 'inputs': {'vae_name': 'wan_2.1_vae.safetensors'}},
        '3': {'class_type': 'CLIPTextEncode', 'inputs': {'clip': ['1', 0], 'text': text}},
        '4': {'class_type': 'CLIPTextEncode', 'inputs': {'clip': ['1', 0], 'text': style['negative']}},
        '5': {'class_type': 'LoadImage', 'inputs': {'image': image}},
        '6': {'class_type': 'WanImageToVideo', 'inputs': {'positive': ['3', 0], 'negative': ['4', 0], 'vae': ['2', 0],
              'start_image': ['5', 0], 'width': 832, 'height': 480, 'length': frames, 'batch_size': 1}},
        '7': sampler('h2', ['6', 2], 'enable', 0, 2, 'enable'),
        '8': sampler('l2', ['7', 0], 'disable', 2, 4, 'disable'),
        '9': {'class_type': 'VAEDecode', 'inputs': {'samples': ['8', 0], 'vae': ['2', 0]}},
        '10': {'class_type': 'CreateVideo', 'inputs': {'images': ['9', 0], 'fps': 16}},
        '11': {'class_type': 'SaveVideo', 'inputs': {'video': ['10', 0], 'filename_prefix': 'shots/%s_s%d' % (sid, seed), 'format': 'auto', 'codec': 'auto'}},
    })
    return wf


def make_keyframe(shot):
    sid = shot['id']
    dest = comfy + '/input/kf-' + sid + '.png'
    if os.path.exists(dest) and not redo and not cands:
        return
    if shot['direct']:
        shutil.copy(comfy + '/input/ref-' + shot['refs'][0] + '.png', dest)
        log('keyframe', sid, 'copied from reference')
        return
    loc = [r for r in shot['refs'] if r in LOCATIONS] or ['river-and-ferry']
    chars = [r for r in shot['refs'] if r not in LOCATIONS][:3]
    images = ['ref-%s.png' % r for r in loc[:1] + chars]
    who = ' '.join('Image %d shows %s.' % (i + 2, WHO[c]) for i, c in enumerate(chars))
    text = ('Edit image 1 into the opening frame of a new shot. Shot: ' + shot['prompt'] + ' ' + who +
            ' Keep the hand-painted style, geography and architecture of image 1. Keep each person exact face, hair and clothes'
            ' from their own image. Show only the people this shot describes and no other people.')
    if sid in overrides:
        text = overrides[sid]
    for k in range(cands or 1):
        f = run(kf_workflow(images, text, random.randrange(2**31), sid))['13']['images'][0]
        shutil.copy(comfy + '/output/' + f['subfolder'] + '/' + f['filename'], comfy + '/input/kf-' + sid + ('-%d' % k if cands else '') + '.png')
        log('keyframe', sid, 'candidate', k)


def make_clip(shot):
    sid = shot['id']
    if glob.glob(comfy + '/output/shots/' + sid + '_s*.mp4') and not redo:
        return
    frames = min(shot['seconds'], 5) * 16 + 1
    if all(r in LOCATIONS for r in shot['refs']):
        extra = ' The scene stays completely empty and deserted: no people, no animals, and nobody walks into the frame. Only water, reeds, light and flames move.'
    else:
        extra = ' Only the people already in the first frame appear. Nobody else walks into the frame. Everyone wears ancient plain wool tunics and robes, never modern clothing.'
    text = shot['prompt'] + extra + ' Hand-painted 2D animation, painted backgrounds with visible texture, restrained deliberate movement, steady camera.'
    run(vid_workflow('kf-' + sid + '.png', text, frames, random.randrange(2**31), sid))
    log('clip', sid, 'done')


log('keyframes')
for sid in order:
    try:
        make_keyframe(shots[sid])
    except Exception as e:
        log('FAILED keyframe', sid, e)
if kf_only:
    log('KEYFRAMES DONE')
    sys.exit()
log('clips')
for sid in order:
    if not os.path.exists(comfy + '/input/kf-' + sid + '.png'):
        continue
    try:
        make_clip(shots[sid])
    except Exception as e:
        log('FAILED clip', sid, e)
log('ALLDONE')
