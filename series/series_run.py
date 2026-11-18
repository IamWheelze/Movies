'''Series pipeline for the Pod (LTX-2.3). Run from /workspace/t.

python3 series_run.py stills EP [--n 2]      keyframe candidates for every shot of an episode (ep01 ...)
python3 series_run.py pick EP "e01s01:1 e01s02:0 ..."
python3 series_run.py clips EP               animate every shot with LTX, check each spoken line, re-roll misses
python3 series_run.py assemble EP            trim, upscale to 1080x1920, loudness, captions, music -> out/EP.mp4

Episode files live in /workspace/Movies/series/EP.txt: id|still tags|LTX prompt|seconds|line
'''
import difflib, glob, json, os, re, shutil, subprocess, sys, time

R = '/workspace/Movies/series/'
OUT = '/workspace/series_out/'
COMFY = '/workspace/runpod-slim/ComfyUI/'
os.makedirs(OUT, exist_ok=True)
W, H = 768, 1344
TAGS = {
    'BALY': 'male focus, teenage boy, dark brown skin, black curly hair, indigo tunic, sand sash',
    'BALG': 'male focus, young man, dark brown skin, black curly hair tied back, light stubble, indigo tunic, sand sash',
    'BALO': 'male focus, man, dark brown skin, black curly hair with gray at the temples, short beard, indigo cloak, sand sash',
    'BEOR': 'old man, male focus, gray curly hair, short gray beard, olive-brown tunic',
    'HAD': 'male focus, middle-aged man, broad shoulders, square black beard, cream tunic, rust-brown mantle',
    'BAKER': 'middle-aged woman, brown headscarf, flour-dusted apron, dark skin',
    'BOATWOMAN': 'adult woman, gray-green wrap, brown headscarf, dark skin',
    'GIRL': 'little girl, two short braids, ochre tunic',
}
ENV = dict(os.environ, SW='768', SH='1344', CW='768', CH='1344',
           PREFIX='anime screenshot, ancient Mesopotamia, hand-painted background, earth tones, ochre, indigo, ',
           NEGX=', split screen, multiple views, collage, comic, panels, manga, japanese architecture, pagoda, torii, kimono, castle, modern clothes, blonde hair, text')


def shots(ep):
    out = []
    for line in open(R + ep + '.txt'):
        if line.strip():
            p = line.rstrip('\n').split('|')
            out.append(dict(id=p[0], still=p[1], prompt=p[2], secs=int(p[3]), line=p[4] if len(p) > 4 else ''))
    return out


def expand(t):
    for k in sorted(TAGS, key=len, reverse=True):
        t = re.sub(r'\b%s\b' % k, TAGS[k], t)
    return t


def sh(*a, **k):
    return subprocess.run(a, check=True, **k)


def norm(s):
    return re.sub(r'[^a-z0-9 ]', '', s.lower().replace("'", ''))


def whisper_model():
    from faster_whisper import WhisperModel
    return WhisperModel('base.en', device='cpu', compute_type='int8')


mode, ep = sys.argv[1], sys.argv[2]
S = shots(ep)

if mode == 'stills':
    n = sys.argv[4] if len(sys.argv) > 4 else '2'
    tmp = '/workspace/t/stills_%s.txt' % ep
    open(tmp, 'w').write(''.join('%s|%s|x|81\n' % (s['id'], expand(s['still'])) for s in S))
    sh('python3', '/workspace/Movies/anime/make.py', 'stills', tmp, '--n', n, env=ENV, cwd='/workspace/t')
elif mode == 'pick':
    sh('python3', '/workspace/Movies/anime/make.py', 'pick', *sys.argv[3].split(), env=ENV, cwd='/workspace/t')
elif mode == 'clips':
    wm = whisper_model()
    os.makedirs(OUT + ep, exist_ok=True)
    report = {}
    for s in S:
        dst = OUT + ep + '/' + s['id'] + '.mp4'
        if os.path.exists(dst):
            continue
        best = None
        for tr in range(3):
            name = '%s_t%d' % (s['id'], tr)
            t0 = time.time()
            subprocess.run(['python3', '/workspace/t/ltx_run.py', 'still-%s.png' % s['id'], s['prompt'], name, '--seconds', str(s['secs']),
                            '--seed', str(1 + tr * 7), '--w', str(W), '--h', str(H)], cwd='/workspace/t')
            f = sorted(glob.glob(COMFY + 'output/ltx/%s_*.mp4' % name))
            if not f:
                continue
            score = 1.0
            if s['line']:
                seg, _ = wm.transcribe(f[-1])
                said = ' '.join(x.text for x in seg)
                score = difflib.SequenceMatcher(None, norm(said), norm(s['line'])).ratio()
            print(s['id'], 'try', tr, 'match %.2f' % score, '%.0fs' % (time.time() - t0), flush=True)
            if best is None or score > best[0]:
                best = (score, f[-1])
            if score >= 0.8:
                break
        if best:
            shutil.copy(best[1], dst)
            report[s['id']] = round(best[0], 2)
    json.dump(report, open(OUT + ep + '_report.json', 'w'))
    print('CLIPS DONE', ep, report, flush=True)
elif mode == 'assemble':
    wm = whisper_model()
    d = OUT + ep + '/'
    parts, srt, t = [], [], 0.0
    for i, s in enumerate(S):
        src = d + s['id'] + '.mp4'
        if not os.path.exists(src):
            continue
        dst = '/tmp/a_%s.mkv' % s['id']
        # sound is cut to exactly the picture length and kept as PCM so clips join without drift
        dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=duration', '-of', 'csv=p=0', src]))
        sh('ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-vf', 'scale=1080:1920:flags=lanczos,unsharp=5:5:0.5:5:5:0.0,fps=25,format=yuv420p',
           '-af', 'loudnorm=I=-18:TP=-2,aresample=48000,apad', '-ac', '2', '-t', '%.3f' % dur, '-c:v', 'libx264', '-crf', '15', '-c:a', 'pcm_s16le', dst)
        if s['line']:
            seg, _ = wm.transcribe(src)
            seg = list(seg)
            if seg:
                a, b = seg[0].start, seg[-1].end
                srt.append((t + a, t + min(b + 0.2, dur), s['line']))
        parts.append(dst)
        t += dur
    open('/tmp/a_list.txt', 'w').write(''.join('file %s\n' % p for p in parts))
    sh('ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', '/tmp/a_list.txt', '-c', 'copy', '/tmp/a_all.mkv')

    def tc(x):
        return '%02d:%02d:%02d,%03d' % (x // 3600, x % 3600 // 60, int(x) % 60, int(round((x - int(x)) * 1000)) % 1000)
    with open(OUT + ep + '.srt', 'w') as f:
        for n, (a, b, tx) in enumerate(srt):
            f.write('%d\n%s --> %s\n%s\n\n' % (n + 1, tc(a), tc(b), tx))
    sh('ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i',
       'aevalsrc=0.30*sin(2*PI*110*t)+0.20*sin(2*PI*164.81*t)+0.15*sin(2*PI*220*t):d=%d:s=48000' % (t + 2), '-af',
       'lowpass=f=900,tremolo=f=0.1:d=0.25,afade=t=in:d=4,afade=t=out:st=%d:d=4' % (t - 4), '/tmp/a_pad.wav')
    vf = ("subtitles=%s.srt:original_size=1080x1920:force_style='FontName=DejaVu Sans,FontSize=9,Bold=1,PrimaryColour=&H00FFFFFF,"
          "OutlineColour=&H00000000,Outline=1.3,Shadow=0,Alignment=2,MarginV=62,MarginL=14,MarginR=14'" % (OUT + ep))
    sh('ffmpeg', '-y', '-loglevel', 'error', '-i', '/tmp/a_all.mkv', '-i', '/tmp/a_pad.wav', '-filter_complex',
       '[1:a]volume=0.10[p];[0:a][p]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5[a]', '-map', '0:v', '-map', '[a]', '-vf', vf,
       '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', OUT + ep + '.mp4')
    print('ASSEMBLED', ep, '%.1f s' % t)
