"""Separação de falantes rápida: um embedding de voz por trecho de fala do Whisper + agrupamento.

Uso: python diarize_fast.py <wav_16k_mono> <whisper.json> <modelo_embedding.onnx> <saida_prefixo>
         [limiar_cosseno=0.55] [inicio_seg=0] [fim_seg=fim]
Gera <saida_prefixo>.json (trechos com falante) e <saida_prefixo>.txt (turnos legíveis).
Os trechos são cortados em pausas >= 0,35 s entre palavras, que é onde a troca de falante
costuma acontecer numa teleconferência moderada.
"""
import json
import sys
import time
from collections import defaultdict

import numpy as np
import sherpa_onnx
import soundfile as sf
from sklearn.cluster import AgglomerativeClustering

wav, wjson, emb_model, out = sys.argv[1:5]
thr = float(sys.argv[5]) if len(sys.argv) > 5 else 0.55
t_ini = float(sys.argv[6]) if len(sys.argv) > 6 else 0.0
t_fim = float(sys.argv[7]) if len(sys.argv) > 7 else 1e9
GAP, MAXDUR, MINEMB = 0.35, 8.0, 1.2

audio, sr = sf.read(wav, dtype="float32")
assert sr == 16000 and audio.ndim == 1
words = [w for s in json.load(open(wjson, encoding="utf-8"))["segments"] for w in s["words"]
         if t_ini <= w["s"] < t_fim]

# 1) trechos: corta em pausas e limita a duração
units, cur = [], []
for w in words:
    if cur and (w["s"] - cur[-1]["e"] >= GAP or w["e"] - cur[0]["s"] > MAXDUR):
        units.append(cur)
        cur = []
    cur.append(w)
if cur:
    units.append(cur)

# 2) embedding por trecho (trechos curtos ganham uma janela mínima centrada)
cfg = sherpa_onnx.SpeakerEmbeddingExtractorConfig(model=emb_model, num_threads=4)
ext = sherpa_onnx.SpeakerEmbeddingExtractor(cfg)
t0 = time.time()
embs = []
for u in units:
    s, e = u[0]["s"], u[-1]["e"]
    if e - s < MINEMB:
        mid = (s + e) / 2
        s, e = mid - MINEMB / 2, mid + MINEMB / 2
    seg = audio[max(0, int(s * sr)): int(e * sr)]
    st = ext.create_stream()
    st.accept_waveform(sample_rate=sr, waveform=seg)
    st.input_finished()
    v = np.array(ext.compute(st), dtype=np.float32)
    embs.append(v / (np.linalg.norm(v) + 1e-9))
embs = np.stack(embs)
print(f"{len(units)} trechos, embeddings em {time.time() - t0:.0f}s", flush=True)
np.save(out + "_emb.npy", embs)

# 3) agrupamento por similaridade de voz
lab = AgglomerativeClustering(n_clusters=None, metric="cosine", linkage="average",
                              distance_threshold=thr).fit_predict(embs)
# renumera os falantes pela ordem em que aparecem
ordem = {}
for l in lab:
    ordem.setdefault(l, len(ordem))
lab = [ordem[l] for l in lab]


def hms(t):
    t = int(t)
    return f"{t // 3600:02d}:{t % 3600 // 60:02d}:{t % 60:02d}"


recs = [{"s": u[0]["s"], "e": u[-1]["e"], "spk": int(k), "text": "".join(w["w"] for w in u).strip()}
        for u, k in zip(units, lab)]
json.dump(recs, open(out + ".json", "w", encoding="utf-8"), ensure_ascii=False)

turns = []
for r in recs:
    if turns and turns[-1]["spk"] == r["spk"]:
        turns[-1]["e"] = r["e"]
        turns[-1]["text"] += " " + r["text"]
    else:
        turns.append(dict(r))
tot, first = defaultdict(float), {}
for t in turns:
    tot[t["spk"]] += t["e"] - t["s"]
    first.setdefault(t["spk"], t["s"])
with open(out + ".txt", "w", encoding="utf-8") as f:
    f.write(f"# limiar {thr} | falante: minutos de fala | primeira fala\n")
    for k in sorted(tot, key=lambda k: first[k]):
        f.write(f"# S{k:02d}: {tot[k] / 60:5.1f} min | {hms(first[k])}\n")
    f.write("\n")
    for t in turns:
        f.write(f"[{hms(t['s'])}] S{t['spk']:02d}: {t['text']}\n")
print(f"{len(set(lab))} falantes, {len(turns)} turnos -> {out}.txt", flush=True)
