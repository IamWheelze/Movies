'''Speak every Episode 1 line with Kokoro (one fixed voice per character) and write 48 kHz mono WAVs
into /workspace/anime/audio/. Also prints each line's length in seconds so shots can be timed to it.

python3 voices.py
'''
import json, os, subprocess
import numpy as np, soundfile as sf
from kokoro import KPipeline

OUT = '/workspace/anime/audio'
os.makedirs(OUT, exist_ok=True)
# voice per character: God is deep and calm, Balaam is warm, Hadan is grounded
VOICE = {'god': ('b', 'bm_george', 0.88), 'bal': ('a', 'am_michael', 0.95), 'had': ('a', 'am_adam', 0.95),
         'old': ('b', 'bm_lewis', 0.92), 'mom': ('a', 'af_sarah', 0.95), 'str': ('b', 'bm_fable', 0.95)}
# name, speaker, text
LINES = [
    ('god01', 'god', 'Balaam, son of Beor. Before the moon clears the ridge...'),
    ('god02', 'god', '...the water will reach those roofs. Wake them.'),
    ('bal03', 'bal', "They'll ask how I know."),
    ('god04', 'god', 'Go.'),
    ('bal05', 'bal', 'To the high bank. Leave the sacks.'),
    ('had06', 'had', 'I have him!'),
    ('old09', 'old', 'Balaam. Son of Beor. He came back for me.'),
    ('had10', 'had', 'Enough to pay your debt...'),
    ('had11', 'had', "...and build a boat. Tell them God says it's safe."),
    ('mom12', 'mom', 'Did God tell you?'),
    ('bal12', 'bal', 'Yes.'),
    ('bal13', 'bal', 'Wait. I never heard God say that.'),
    ('bal15', 'bal', 'I used your name. Forgive me.'),
    ('god15', 'god', 'I forgive you.'),
    ('god16', 'god', "Three knocks at dawn. Blue thread. He'll bring silver."),
    ('str17', 'str', "My brother's missing."),
    ('str18', 'str', 'Is he alive?'),
]
pipes = {}
lens = {}
for name, who, text in LINES:
    lang, voice, speed = VOICE[who]
    if lang not in pipes:
        pipes[lang] = KPipeline(lang_code=lang)
    parts = [np.asarray(a) for _, _, a in pipes[lang](text, voice=voice, speed=speed)]
    audio = np.concatenate(parts)
    raw = '%s/%s_raw.wav' % (OUT, name)
    sf.write(raw, audio, 24000)
    # 48 kHz mono, gentle band-limit and level so every voice sits at the same loudness
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-ar', '48000', '-ac', '1', '-af',
                    'highpass=f=80,loudnorm=I=-18:TP=-2', '%s/%s_n.wav' % (OUT, name)], check=True)
    lens[name] = round(len(audio) / 24000, 2)
    print(name, who, voice, lens[name], 's', flush=True)
json.dump(lens, open(OUT + '/lengths.json', 'w'))
open(OUT + '/voices.done', 'w').write('ok')
