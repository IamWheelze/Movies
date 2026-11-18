'''Run the stock ComfyUI LTX-2.3 image-to-video(+audio) template headless.

python3 ltx_run.py IMAGE.png "prompt text" OUTNAME [--seconds 6] [--seed 1]

It flattens the template's subgraph into an API-format graph (widget names come from /object_info), swaps in the
given image, prompt, length and seed, adds a SaveVideo on the decoded result and runs it.
'''
import json, sys, time, urllib.request

D = '/usr/local/lib/python3.12/dist-packages/comfyui_workflow_templates_json/templates/video_ltx2_3_i2v.json'
HOST = 'http://127.0.0.1:8188'
img, prompt, name = sys.argv[1:4]
opt = dict(zip(sys.argv[4::2], sys.argv[5::2]))
secs = float(opt.get('--seconds', 6))
seed = int(opt.get('--seed', 1))
FPS = 24
frames = int(round(secs * FPS / 8)) * 8 + 1  # LTX wants 8k+1


def api(path, body=None):
    req = urllib.request.Request(HOST + path, json.dumps(body).encode() if body is not None else None, {'Content-Type': 'application/json'})
    try:
        return json.load(urllib.request.urlopen(req))
    except urllib.error.HTTPError as e:
        print(e.read().decode()[:3000])
        sys.exit(1)


info = api('/object_info')
j = json.load(open(D))
sg = j['definitions']['subgraphs'][0]
nodes = {n['id']: n for n in sg['nodes']}
links = {l['id']: l for l in sg['links']} if isinstance(sg['links'][0], dict) else {l[0]: dict(id=l[0], origin_id=l[1], origin_slot=l[2], target_id=l[3], target_slot=l[4]) for l in sg['links']}
sg_in = sg['inputs']
# values for the subgraph's own inputs (by name); others fall back to the node's saved widget value
OV = {'value': prompt, 'noise_seed': seed}


def widget_values(n):
    spec = info.get(n['type'])
    if not spec:
        return {}
    order = list(spec['input_order'].get('required', [])) + list(spec['input_order'].get('optional', []))
    allin = {**spec['input'].get('required', {}), **spec['input'].get('optional', {})}
    wv = list(n.get('widgets_values') or [])
    out, k = {}, 0
    for nm in order:
        t = allin[nm]
        typ = t[0]
        opts = t[1] if len(t) > 1 else {}
        if isinstance(typ, str) and not any(p in ('INT', 'FLOAT', 'STRING', 'BOOLEAN', 'COMBO') for p in typ.split(',')):
            continue  # a socket (types like "FLOAT,INT" are still widgets)
        if k < len(wv):
            out[nm] = wv[k]
            k += 1
            if opts.get('control_after_generate'):
                k += 1
    return out


def resolve(oid, oslot):
    while oid in nodes and nodes[oid]['type'] == 'Reroute':
        lk = links[nodes[oid]['inputs'][0]['link']]
        oid, oslot = lk['origin_id'], lk['origin_slot']
    return oid, oslot


g = {}
for nid, n in nodes.items():
    if n['type'] in ('Reroute', 'MarkdownNote', 'Note', 'PreviewAny'):
        continue
    ins = widget_values(n)
    for inp in n.get('inputs', []):
        lid = inp.get('link')
        if lid is None:
            continue
        lk = links[lid]
        oid, oslot = resolve(lk['origin_id'], lk['origin_slot'])
        if oid == -10:
            nm = sg_in[oslot]['name']
            if nm == 'input':
                ins[inp['name']] = ['IMG', 0]
            elif nm in OV:
                ins[inp['name']] = OV[nm]
            # else keep the node's saved value
        else:
            ins[inp['name']] = [str(oid), oslot]
    g[str(nid)] = {'class_type': n['type'], 'inputs': ins}
# drop dangling references to removed nodes
for nid, n in g.items():
    for k, v in list(n['inputs'].items()):
        if isinstance(v, list) and len(v) == 2 and isinstance(v[0], str) and v[0] != 'IMG' and v[0] not in g:
            del n['inputs'][k]
g['IMG'] = {'class_type': 'LoadImage', 'inputs': {'image': img}}
# the template computes length from seconds x fps; seconds is the primitive saved as 5, the size primitives are 1280 / 720
W, H = int(opt.get('--w', 640)), int(opt.get('--h', 1152))  # vertical; both must stay multiples of 64
for nid, n in g.items():
    if n['class_type'] == 'PrimitiveInt':
        v = n['inputs'].get('value')
        if v == 5:
            n['inputs']['value'] = int(secs)
        elif v == 1280:
            n['inputs']['value'] = W
        elif v == 720:
            n['inputs']['value'] = H
    if n['class_type'] == 'ResizeImageMaskNode':
        n['inputs'] = {'input': ['IMG', 0], 'resize_type': 'scale dimensions', 'resize_type.width': n['inputs']['resize_type.width'],
                       'resize_type.height': n['inputs']['resize_type.height'], 'resize_type.crop': 'center', 'scale_method': 'lanczos'}
g['OUT'] = {'class_type': 'SaveVideo', 'inputs': {'video': ['310', 0], 'filename_prefix': 'ltx/' + name, 'format': 'auto', 'codec': 'auto'}}
json.dump(g, open('/workspace/t/last_graph.json', 'w'), indent=1)
pid = api('/prompt', {'prompt': g})['prompt_id']
print('queued', pid, flush=True)
t0 = time.time()
while True:
    time.sleep(4)
    h = api('/history/' + pid)
    if pid in h:
        st = h[pid]['status']
        print(st['status_str'], round(time.time() - t0), 's', json.dumps(st)[:600] if st['status_str'] != 'success' else '')
        break
