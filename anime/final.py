'''Join the upscaled clips of an episode and mix in the river sound, spoken lines and door knocks.

python3 final.py EPISODE.txt CUES.txt OUT.mp4
EPISODE.txt holds one shot per line (id|still prompt|motion prompt), in story order. The upscaled clips
are /workspace/anime/up/<id>.mp4. CUES.txt lines: sound|shot id|seconds after the start of that shot.
Clips are smoothed from 16 to 24 fps.
'''
import subprocess, sys
from concurrent.futures import ThreadPoolExecutor

A = '/workspace/anime/audio/'
episode, cues_file, out = sys.argv[1:4]
order = [line.split('|')[0] for line in open(episode) if line.strip()]
cues = [line.strip().split('|') for line in open(cues_file) if line.strip()]


def sh(*a):
    subprocess.run(a, check=True)


def dur(p):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]))


def smooth(i):
    dst = '/tmp/a_%s.mp4' % i
    sh('ffmpeg', '-y', '-loglevel', 'error', '-i', '/workspace/anime/up/%s.mp4' % i, '-vf',
       'minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:vsbmc=1,format=yuv420p', '-c:v', 'libx264', '-crf', '16', '-an', dst)
    return dst


with ThreadPoolExecutor(6) as ex:
    parts = list(ex.map(smooth, order))
starts = {}
t = 0.0
for i, p in zip(order, parts):
    starts[i] = t
    t += dur(p)
open('/tmp/a_list.txt', 'w').write(''.join('file %s' % p + chr(10) for p in parts))
sh('ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', '/tmp/a_list.txt', '-c', 'copy', '/tmp/a_video.mp4')

cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-i', '/tmp/a_video.mp4', '-i', A + 'river.wav']
fc = ['[1:a]volume=0.5[r]']
mix = ['[r]']
for n, (name, shot, off) in enumerate(cues):
    ms = int((starts[shot] + float(off)) * 1000)
    cmd += ['-i', A + name + '_n.wav']
    fc.append('[%d:a]adelay=%d|%d[v%d]' % (n + 2, ms, ms, n))
    mix.append('[v%d]' % n)
fc.append(''.join(mix) + 'amix=inputs=%d:normalize=0,loudnorm=I=-16[a]' % len(mix))
cmd += ['-filter_complex', ';'.join(fc), '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', out]
sh(*cmd)
print('shots', len(order), 'length %.1f s' % dur(out))
