'''Join the finished clips into one cut and mix in the river sound and the spoken lines.

Run on the Pod from ComfyUI/output. Needs audio/river.wav and audio/<line>_n.wav in /workspace/balaam.
Shots 03 and 04 are slowed to half speed so the spoken lines fit over them.
'''
import glob, os, subprocess

A = '/workspace/balaam/audio/'
order = '01 02 00 03 04 05 06 07 08a 08b 09 10 11 12 13 14 15 16'.split()
slow = ('03', '04')
# Shots cut off where the video model starts adding people who are not in the shot (seconds kept).
TRIM = {'13': 1.8, '14': 2.2, '16': 1.0}
lines = ['god1', 'god2', 'bal1', 'god3']


def sh(*a):
    subprocess.run(a, check=True)


def dur(p):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]))


os.makedirs('/tmp/cut', exist_ok=True)
parts = []
for i in order:
    src = sorted(glob.glob('shots/%s_s*.mp4' % i))[0]
    dst = '/tmp/cut/%s.mp4' % i
    vf = 'setpts=2*PTS,minterpolate=fps=16:mi_mode=mci' if i in slow else 'fps=16'
    tr = ['-t', str(TRIM[i])] if i in TRIM else []
    sh('ffmpeg', '-y', '-loglevel', 'error', '-i', src, *tr, '-vf', vf + ',format=yuv420p', '-c:v', 'libx264', '-crf', '18', '-an', dst)
    parts.append(dst)
start = sum(dur(p) for p in parts[:order.index('03')])
open('/tmp/cut/list.txt', 'w').write(''.join("file '%s'\n" % p for p in parts))
sh('ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', '/tmp/cut/list.txt', '-c', 'copy', '/tmp/cut/video.mp4')

t = start + 1.0
cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-i', '/tmp/cut/video.mp4', '-i', A + 'river.wav']
fc = ['[1:a]volume=0.55[r]']
mix = ['[r]']
for n, name in enumerate(lines):
    ms = int(t * 1000)
    cmd += ['-i', A + name + '_n.wav']
    fc.append('[%d:a]adelay=%d|%d[v%d]' % (n + 2, ms, ms, n))
    mix.append('[v%d]' % n)
    print(name, 'starts at %.1f s' % t)
    t += dur(A + name + '_n.wav') + 0.9
fc.append(''.join(mix) + 'amix=inputs=%d:normalize=0,loudnorm=I=-16[a]' % len(mix))
cmd += ['-filter_complex', ';'.join(fc), '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', 'episode01_rough_cut_v3.mp4']
sh(*cmd)
print('shot 03 starts at %.1f s, final length %.1f s' % (start, dur('episode01_rough_cut_v3.mp4')))
