'''Join the anime clips in order and mix in the river sound and the spoken lines.

Run in /workspace/runpod-slim/ComfyUI/output. Needs /workspace/anime/audio/*.wav and the
upscaled clips in /workspace/anime/up (see upscale.py). Clips are smoothed from 16 to 24 fps.
'''
import glob, subprocess

A = '/workspace/anime/audio/'
order = ['01', '02', '03', '04', '05', '06']
# (line, seconds after the start of shot 03)
lines = [('god1', 0.5), ('god2', 3.0), ('bal1', 9.5), ('god3', 12.2)]


def sh(*a):
    subprocess.run(a, check=True)


def dur(p):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]))


parts = []
for i in order:
    src = '/workspace/anime/up/%s.mp4' % i
    dst = '/tmp/a_%s.mp4' % i
    sh('ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-vf', 'minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:vsbmc=1,format=yuv420p',
       '-c:v', 'libx264', '-crf', '16', '-an', dst)
    parts.append(dst)
start = sum(dur(p) for p in parts[:2])
open('/tmp/a_list.txt', 'w').write(''.join('file %s' % p + chr(10) for p in parts))
sh('ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', '/tmp/a_list.txt', '-c', 'copy', '/tmp/a_video.mp4')

cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-i', '/tmp/a_video.mp4', '-i', A + 'river.wav']
fc = ['[1:a]volume=0.5[r]']
mix = ['[r]']
for n, (name, off) in enumerate(lines):
    ms = int((start + off) * 1000)
    cmd += ['-i', A + name + '_n.wav']
    fc.append('[%d:a]adelay=%d|%d[v%d]' % (n + 2, ms, ms, n))
    mix.append('[v%d]' % n)
fc.append(''.join(mix) + 'amix=inputs=%d:normalize=0,loudnorm=I=-16[a]' % len(mix))
cmd += ['-filter_complex', ';'.join(fc), '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', 'balaam_opening_anime.mp4']
sh(*cmd)
print('shot 03 starts at %.1f s, length %.1f s' % (start, dur('balaam_opening_anime.mp4')))
