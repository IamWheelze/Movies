'''Chained-take pipeline for the Pod (LTX-2.3). Run from /workspace/t.

python3 chain_run.py keys CH          keyframe candidates for the scene openers in /workspace/Movies/series/CH_keys.txt
python3 chain_run.py clips CH         animate every unit; each unit starts from the last frame of the previous one,
                                      except scene openers, which start from their picked keyframe (still-<key>.png)
python3 chain_run.py assemble CH      narrator voice, join, captions, music -> /workspace/series_out/CH.mp4

Units file /workspace/Movies/series/CH.txt: id|keyframe or -|LTX prompt|seconds|spoken line|narrator line
'''
import difflib, glob, json, os, re, shutil, subprocess, sys, time

R = '/workspace/Movies/series/'
OUT = '/workspace/series_out/'
COMFY = '/workspace/runpod-slim/ComfyUI/'
W, H = 768, 1344
TAGS = {'BALY': 'male focus, teenage boy, dark brown skin, black curly hair, indigo tunic, sand sash'}
ENV = dict(os.environ, SW='768', SH='1344', CW='768', CH='1344',
           PREFIX='anime screenshot, ancient Mesopotamia, hand-painted background, earth tones, ochre, indigo, ',
           NEGX=', split screen, multiple views, collage, comic, panels, manga, japanese architecture, pagoda, torii, kimono, castle, modern clothes, blonde hair, text')
mode, ch = sys.argv[1], sys.argv[2]


def units():
    out = []
    for line in open(R + ch + '.txt'):
        if line.strip():
            p = line.rstrip('\n').split('|')
            out.append(dict(id=p[0], key=p[1], prompt=p[2], secs=int(p[3]), line=p[4], narr=p[5] if len(p) > 5 else ''))
    return out


def sh(*a, **k):
    return subprocess.run(a, check=True, **k)


def norm(s):
    return re.sub(r'[^a-z0-9 ]', '', s.lower().replace("'", ''))


def vdur(p):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=duration', '-of', 'csv=p=0', p]))


if mode == 'keys':
    tmp = '/workspace/t/%s_keys_tmp.txt' % ch
    txt = open(R + ch + '_keys.txt').read()
    for k, v in TAGS.items():
        txt = re.sub(r'\b%s\b' % k, v, txt)
    open(tmp, 'w').write(txt)
    sh('python3', '/workspace/Movies/anime/make.py', 'stills', tmp, '--n', '4', env=ENV, cwd='/workspace/t')
elif mode == 'clips':
    from faster_whisper import WhisperModel
    wm = WhisperModel('base.en', device='cpu', compute_type='int8')
    d = OUT + ch + '/'
    os.makedirs(d, exist_ok=True)
    prev, report = None, {}
    for u in units():
        dst = d + u['id'] + '.mp4'
        if os.path.exists(dst):
            prev = dst
            continue
        if u['key'] not in ('-',) and not u['key'].startswith('from:'):
            img = 'still-%s.png' % u['key']
        else:
            # '-' continues from the previous unit; 'from:uNN' continues from the last frame of an earlier unit
            img = 'chain-%s.png' % u['id']
            origin = d + u['key'][5:] + '.mp4' if u['key'].startswith('from:') else prev
            sh('ffmpeg', '-y', '-loglevel', 'error', '-sseof', '-0.1', '-i', origin, '-frames:v', '1', '-update', '1', '-q:v', '1', COMFY + 'input/' + img)
        best = None
        for tr in range(3):
            name = '%s_%s_t%d' % (ch, u['id'], tr)
            t0 = time.time()
            subprocess.run(['python3', '/workspace/t/ltx_run.py', img, u['prompt'], name, '--seconds', str(u['secs']), '--seed', str(1 + tr * 7),
                            '--w', str(W), '--h', str(H)], cwd='/workspace/t')
            f = sorted(glob.glob(COMFY + 'output/ltx/%s_*.mp4' % name))
            if not f:
                continue
            score = 1.0
            if u['line']:
                seg, _ = wm.transcribe(f[-1])
                score = difflib.SequenceMatcher(None, norm(' '.join(x.text for x in seg)), norm(u['line'])).ratio()
            print(u['id'], 'try', tr, 'match %.2f' % score, '%.0fs' % (time.time() - t0), flush=True)
            if best is None or score > best[0]:
                best = (score, f[-1])
            if score >= 0.8:
                break
        if best:
            shutil.copy(best[1], dst)
            report[u['id']] = round(best[0], 2)
            prev = dst
    json.dump(report, open(OUT + ch + '_report.json', 'w'))
    print('CLIPS DONE', ch, report, flush=True)
elif mode == 'assemble':
    from faster_whisper import WhisperModel
    import numpy as np, soundfile as sf
    from kokoro import KPipeline
    wm = WhisperModel('base.en', device='cpu', compute_type='int8')
    kp = KPipeline(lang_code='b')
    d = OUT + ch + '/'
    parts, srt, t = [], [], 0.0
    for u in units():
        src = d + u['id'] + '.mp4'
        if not os.path.exists(src):
            continue
        dur = vdur(src)
        dst = '/tmp/c_%s.mkv' % u['id']
        if u['narr']:
            audio = np.concatenate([np.asarray(a) for _, _, a in kp(u['narr'], voice='bm_lewis', speed=0.9)])
            sf.write('/tmp/n_%s_raw.wav' % u['id'], audio, 24000)
            sh('ffmpeg', '-y', '-loglevel', 'error', '-i', '/tmp/n_%s_raw.wav' % u['id'], '-ar', '48000', '-ac', '2', '-af', 'highpass=f=70,loudnorm=I=-17:TP=-2', '/tmp/n_%s.wav' % u['id'])
            nl = len(audio) / 24000.0
            if nl > dur - 0.5:
                print('WARNING narrator longer than unit', u['id'], round(nl, 1), round(dur, 1))
            fc = '[0:a]loudnorm=I=-18:TP=-2,aresample=48000,volume=0.45[c];[1:a]adelay=450|450[n];[c][n]amix=inputs=2:duration=first:normalize=0,apad[a]'
            ins = ['-i', src, '-i', '/tmp/n_%s.wav' % u['id']]
            srt.append((t + 0.45, min(t + 0.45 + nl + 0.2, t + dur), '<i>%s</i>' % u['narr']))
        else:
            fc = '[0:a]loudnorm=I=-18:TP=-2,aresample=48000,apad[a]'
            ins = ['-i', src]
        if u['line']:
            seg = list(wm.transcribe(src)[0])
            if seg:
                srt.append((t + seg[0].start, min(t + seg[-1].end + 0.2, t + dur), u['line']))
        sh('ffmpeg', '-y', '-loglevel', 'error', *ins, '-filter_complex', fc + ';[0:v]scale=1080:1920:flags=lanczos,unsharp=5:5:0.5:5:5:0.0,fps=25,format=yuv420p[v]',
           '-map', '[v]', '-map', '[a]', '-ac', '2', '-t', '%.3f' % dur, '-c:v', 'libx264', '-crf', '15', '-c:a', 'pcm_s16le', dst)
        parts.append(dst)
        t += dur
    open('/tmp/c_list.txt', 'w').write(''.join('file %s\n' % p for p in parts))
    sh('ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', '/tmp/c_list.txt', '-c', 'copy', '/tmp/c_all.mkv')

    def tc(x):
        return '%02d:%02d:%02d,%03d' % (x // 3600, x % 3600 // 60, int(x) % 60, int(round((x - int(x)) * 1000)) % 1000)
    srt.sort()
    with open(OUT + ch + '.srt', 'w') as f:
        for n, (a, b, tx) in enumerate(srt):
            f.write('%d\n%s --> %s\n%s\n\n' % (n + 1, tc(a), tc(b), tx))
    sh('ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i',
       'aevalsrc=0.30*sin(2*PI*110*t)+0.20*sin(2*PI*164.81*t)+0.15*sin(2*PI*220*t):d=%d:s=48000' % (t + 2), '-af',
       'lowpass=f=900,tremolo=f=0.1:d=0.25,afade=t=in:d=4,afade=t=out:st=%d:d=4' % (t - 4), '/tmp/c_pad.wav')
    vf = ("subtitles=%s.srt:original_size=1080x1920:force_style='FontName=DejaVu Sans,FontSize=9,Bold=1,PrimaryColour=&H00FFFFFF,"
          "OutlineColour=&H00000000,Outline=1.3,Shadow=0,Alignment=2,MarginV=62,MarginL=14,MarginR=14'" % (OUT + ch))
    sh('ffmpeg', '-y', '-loglevel', 'error', '-i', '/tmp/c_all.mkv', '-i', '/tmp/c_pad.wav', '-filter_complex',
       '[1:a]volume=0.08[p];[0:a][p]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5[a]', '-map', '0:v', '-map', '[a]', '-vf', vf,
       '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', OUT + ch + '.mp4')
    print('ASSEMBLED', ch, '%.1f s' % t)
