'''Pod: python3 run2.py W H "R21:0 R22:1 R23:2 R25:0"  (picked LoRA keyframe candidates) -> renders units2.txt'''
import glob, json, shutil, subprocess, sys, time
W, H, picks = sys.argv[1], sys.argv[2], dict(p.split(':') for p in sys.argv[3].split())
OUT = '/workspace/runpod-slim/ComfyUI/output/ltx/'
from faster_whisper import WhisperModel
wm = WhisperModel('base.en', device='cpu', compute_type='int8')
rep = {}
for line in open('/workspace/Movies/prod/proof/units2.txt'):
    if not line.strip():
        continue
    uid, key, prompt, secs = line.rstrip('\n').split('|')
    src = sorted(glob.glob('/workspace/runpod-slim/ComfyUI/output/kfl/%s_c%s_*.png' % (key, picks[key])))[0]
    shutil.copy(src, '/workspace/runpod-slim/ComfyUI/input/pg_%s.png' % key)
    name = 'proof2_%s_%s' % (W, uid)
    t0 = time.time()
    subprocess.run(['python3', '/workspace/t/ltx_run.py', 'pg_%s.png' % key, prompt, name, '--seconds', secs, '--seed', '5', '--w', W, '--h', H], cwd='/workspace/t')
    f = sorted(glob.glob(OUT + name + '_*.mp4'))
    if f:
        seg = list(wm.transcribe(f[-1], word_timestamps=True)[0])
        rep[uid] = dict(file=f[-1], secs=round(time.time() - t0), words=[(round(w.start, 2), round(w.end, 2), w.word) for x in seg for w in x.words])
    print(uid, rep.get(uid, 'FAILED'), flush=True)
json.dump(rep, open('/workspace/t/proof2_%s.json' % W, 'w'))
print('PROOF2DONE', flush=True)
