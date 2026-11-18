'''Proof runner (Pod): python3 run.py W H  -> renders every unit in units.txt from the picked keyframe, logs time and whisper words.'''
import glob, shutil, subprocess, sys, time, json
W, H = sys.argv[1], sys.argv[2]
PICK = {'K21': 1, 'K22': 1, 'K23': 3, 'K24': 1, 'K25': 2}
ST = '/workspace/runpod-slim/ComfyUI/output/stills/'
IN = '/workspace/runpod-slim/ComfyUI/input/'
OUT = '/workspace/runpod-slim/ComfyUI/output/ltx/'
from faster_whisper import WhisperModel
wm = WhisperModel('base.en', device='cpu', compute_type='int8')
rep = {}
for line in open('/workspace/Movies/prod/proof/units.txt'):
    if not line.strip():
        continue
    uid, key, prompt, secs = line.rstrip('\n').split('|')
    src = sorted(glob.glob(ST + '%s_c%d_*.png' % (key, PICK[key])))[0]
    shutil.copy(src, IN + 'pf_%s.png' % key)
    name = 'proof%s_%s' % (W, uid)
    t0 = time.time()
    subprocess.run(['python3', '/workspace/t/ltx_run.py', 'pf_%s.png' % key, prompt, name, '--seconds', secs, '--seed', '5', '--w', W, '--h', H], cwd='/workspace/t')
    f = sorted(glob.glob(OUT + name + '_*.mp4'))
    if f:
        seg = list(wm.transcribe(f[-1], word_timestamps=True)[0])
        rep[uid] = dict(file=f[-1], secs=round(time.time() - t0), words=[(round(w.start, 2), round(w.end, 2), w.word) for x in seg for w in x.words])
    print(uid, rep.get(uid, 'FAILED'), flush=True)
json.dump(rep, open('/workspace/t/proof%s.json' % W, 'w'))
print('PROOFDONE', flush=True)
