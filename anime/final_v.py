'''Assemble the vertical Episode 1: trim each upscaled clip to its performance, smooth to 24 fps, mix voices,
river, a low music pad and sound effects, burn captions, and write the 1080x1920 master plus SRT and stems.

python3 final_v.py OUT.mp4
Needs /workspace/anime/up/<id>.mp4 (1080x1920) and /workspace/anime/audio/<name>_n.wav + lengths.json.
'''
import json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

A = '/workspace/anime/audio/'
OUT = sys.argv[1]
L = json.load(open(A + 'lengths.json'))
# shot -> seconds kept (room for a breath before each line and a reaction after it)
CUT = {'01': 6.0, '02': 5.0, '03': 5.5, '04': 5.0, '05': 5.5, '06': 5.0, '07': 4.0, '08': 4.0, '09': 5.8, '10': 6.0,
       '11': 5.8, '12': 5.6, '13': 5.2, '14': 4.0, '15': 7.0, '16': 6.5, '17': 5.0, '18': 6.5}
# voice and sound cues: (file, shot, seconds into the shot); captions come from CAP
CUES = [('god01', '01', 0.6), ('god02', '02', 0.3), ('bal03', '03', 0.9), ('god04', '04', 0.4), ('bal05', '05', 1.4),
        ('had06', '06', 1.4), ('old09', '09', 0.8), ('had10', '10', 3.4), ('had11', '11', 0.8), ('mom12', '12', 0.6),
        ('bal12', '12', 3.3), ('bal13', '13', 0.8), ('bal15', '15', 0.8), ('god15', '15', 4.3), ('god16', '16', 0.8),
        ('str17', '17', 3.0), ('str18', '18', 0.8)]
SFX = [('snap', '07', 0.2), ('tap', '10', 1.0), ('knock', '17', 0.3), ('knock', '17', 1.2), ('knock', '17', 2.1),
       ('pouch', '14', 1.6)]
CAP = {'god01': 'Balaam, son of Beor. Before the moon clears the ridge...', 'god02': '...the water will reach those roofs. Wake them.',
       'bal03': "They'll ask how I know.", 'god04': 'Go.', 'bal05': 'To the high bank. Leave the sacks.', 'had06': 'I have him!',
       'old09': 'Balaam. Son of Beor. He came back for me.', 'had10': 'Enough to pay your debt...',
       'had11': "...and build a boat. Tell them God says it's safe.", 'mom12': 'Did God tell you?', 'bal12': 'Yes.',
       'bal13': 'Wait. I never heard God say that.', 'bal15': 'I used your name. Forgive me.', 'god15': 'I forgive you.',
       'god16': "Three knocks at dawn. Blue thread. He'll bring silver.", 'str17': "My brother's missing.", 'str18': 'Is he alive?'}
order = sorted(CUT)


def sh(*a):
    subprocess.run(a, check=True)


def smooth(i):
    dst = '/tmp/v_%s.mp4' % i
    sh('ffmpeg', '-y', '-loglevel', 'error', '-i', '/workspace/anime/up/%s.mp4' % i, '-t', str(CUT[i]), '-vf',
       'minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:vsbmc=1,format=yuv420p', '-c:v', 'libx264', '-crf', '15', '-an', dst)
    return dst


with ThreadPoolExecutor(6) as ex:
    parts = list(ex.map(smooth, order))
start, t = {}, 0.0
for i in order:
    start[i] = t
    t += CUT[i]
total = t
open('/tmp/v_list.txt', 'w').write(''.join('file /tmp/v_%s.mp4\n' % i for i in order))
sh('ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', '/tmp/v_list.txt', '-c', 'copy', '/tmp/v_all.mp4')


def tc(s):
    return '%02d:%02d:%02d,%03d' % (s // 3600, s % 3600 // 60, int(s) % 60, int(round((s - int(s)) * 1000)) % 1000)


with open('/workspace/anime/ep1.srt', 'w') as f:
    for n, (name, shot, off) in enumerate(CUES):
        s = start[shot] + off
        f.write('%d\n%s --> %s\n%s\n\n' % (n + 1, tc(s), tc(s + L[name] + 0.2), CAP[name]))

# sound effects, river bed and a low drone made from scratch
S = '/tmp/'
sh('ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'aevalsrc=0.9*sin(2*PI*85*t)*exp(-14*t)+0.4*sin(2*PI*170*t)*exp(-20*t):d=0.5:s=48000', S + 'knock.wav')
sh('ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'anoisesrc=color=white:amplitude=0.8:duration=0.18', '-af', 'highpass=f=900,lowpass=f=6000,afade=t=out:st=0.02:d=0.16', S + 'snap.wav')
sh('ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'aevalsrc=0.8*sin(2*PI*520*t)*exp(-18*t):d=0.4:s=48000', S + 'tap.wav')
sh('ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'anoisesrc=color=brown:amplitude=0.7:duration=0.5', '-af', 'lowpass=f=700,afade=t=out:st=0.05:d=0.45', S + 'pouch.wav')
sh('ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'anoisesrc=color=brown:amplitude=0.6:duration=%d:seed=3' % (total + 2), '-f', 'lavfi', '-i',
   'anoisesrc=color=pink:amplitude=0.3:duration=%d:seed=9' % (total + 2), '-filter_complex',
   '[0]lowpass=f=650,highpass=f=50,tremolo=f=0.13:d=0.35[a];[1]highpass=f=1200,lowpass=f=3500,tremolo=f=0.55:d=0.8,volume=0.10[b];[a][b]amix=inputs=2:normalize=0,volume=0.9,afade=t=in:d=2', S + 'river.wav')
sh('ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i',
   'aevalsrc=0.30*sin(2*PI*110*t)+0.20*sin(2*PI*164.81*t)+0.15*sin(2*PI*220*t)+0.10*sin(2*PI*261.63*t)*(0.5+0.5*sin(2*PI*0.07*t)):d=%d:s=48000' % (total + 2),
   '-af', 'lowpass=f=900,tremolo=f=0.1:d=0.25,afade=t=in:d=4,afade=t=out:st=%d:d=4' % (total - 4), S + 'pad.wav')

cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-i', S + 'river.wav', '-i', S + 'pad.wav']
fc = ['[0:a]volume=0.55[r]', '[1:a]volume=0.22[p]']
mix = ['[r]', '[p]']
k = 2
for name, shot, off in CUES:
    ms = int((start[shot] + off) * 1000)
    cmd += ['-i', A + name + '_n.wav']
    fx = 'aecho=0.8:0.55:70:0.22,equalizer=f=160:t=h:width=200:g=2,' if name.startswith('god') else ''
    fc.append('[%d:a]%sadelay=%d|%d[v%d]' % (k, fx, ms, ms, k))
    mix.append('[v%d]' % k)
    k += 1
for name, shot, off in SFX:
    ms = int((start[shot] + off) * 1000)
    cmd += ['-i', S + name + '.wav']
    fc.append('[%d:a]volume=0.8,adelay=%d|%d[v%d]' % (k, ms, ms, k))
    mix.append('[v%d]' % k)
    k += 1
fc.append(''.join(mix) + 'amix=inputs=%d:normalize=0:duration=longest,loudnorm=I=-16:TP=-1.5,atrim=0:%.2f[a]' % (len(mix), total))
sh(*(cmd + ['-filter_complex', ';'.join(fc), '-map', '[a]', '-c:a', 'pcm_s16le', '/workspace/anime/mix.wav']))

vf = "subtitles=/workspace/anime/ep1.srt:original_size=1080x1920:force_style='FontName=DejaVu Sans,FontSize=9,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=1.3,Shadow=0,Alignment=2,MarginV=62,MarginL=14,MarginR=14'"
sh('ffmpeg', '-y', '-loglevel', 'error', '-i', '/tmp/v_all.mp4', '-i', '/workspace/anime/mix.wav', '-vf', vf, '-map', '0:v', '-map', '1:a',
   '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', OUT)
print('length %.1f s' % total)
