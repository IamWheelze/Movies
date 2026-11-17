'''Upscale a 720p clip to 1080p with an ESRGAN model (4x, then scaled down to 1920x1080).

python3 upscale.py MODEL.pth IN.mp4 OUT.mp4
'''
import subprocess, sys
import numpy as np
import torch
from spandrel import ModelLoader

model_path, src, dst = sys.argv[1:4]
model = ModelLoader().load_from_file(model_path).cuda().eval().half()
w, h = 1280, 720
rd = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-i', src, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
wr = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1920x1080', '-r', '16', '-i', '-',
                       '-c:v', 'libx264', '-crf', '14', '-pix_fmt', 'yuv420p', dst], stdin=subprocess.PIPE)
n = 0
while True:
    buf = rd.stdout.read(w * h * 3)
    if len(buf) < w * h * 3:
        break
    x = torch.from_numpy(np.frombuffer(buf, np.uint8).reshape(h, w, 3).copy()).cuda().permute(2, 0, 1)[None].half() / 255
    with torch.no_grad():
        y = model(x)
        y = torch.nn.functional.interpolate(y.float(), size=(1080, 1920), mode='bicubic', antialias=True).clamp(0, 1)
    wr.stdin.write((y[0].permute(1, 2, 0) * 255).round().byte().cpu().numpy().tobytes())
    n += 1
wr.stdin.close()
wr.wait()
print('frames', n)
