'''Pod: build the training folder from culled images. python3 prep_train.py "balaam_c:00_0,01_0,... mother_c:... girl_c:..."'''
import glob, json, os, shutil, sys
D = '/workspace/t/trainset/'
shutil.rmtree(D, ignore_errors=True); os.makedirs(D)
rows = []
for spec in sys.argv[1].split():
    c, ids = spec.split(':')
    for i in ids.split(','):
        f = glob.glob('/workspace/runpod-slim/ComfyUI/output/ds/%s_%s_*.png' % (c, i))[0]
        cap = json.load(open('/workspace/t/ds_%s_%s.txt' % (c, i)))
        name = '%s_%s.png' % (c, i)
        shutil.copy(f, D + name)
        rows.append(json.dumps({'file_name': name, 'text': cap}))
open(D + 'metadata.jsonl', 'w').write('\n'.join(rows) + '\n')
print(len(rows), 'images')
