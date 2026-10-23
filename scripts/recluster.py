"""Reagrupa os embeddings salvos por diarize_fast.py com outro limiar (sem recalcular).
Uso: python recluster.py <prefixo> <limiar> [min_falantes_min=0.3]"""
import json, sys
from collections import defaultdict
import numpy as np
from sklearn.cluster import AgglomerativeClustering
pre, thr = sys.argv[1], float(sys.argv[2])
recs = json.load(open(pre + ".json", encoding="utf-8")); embs = np.load(pre + "_emb.npy")
lab = AgglomerativeClustering(n_clusters=None, metric="cosine", linkage="average", distance_threshold=thr).fit_predict(embs)
ordem = {}
for l in lab: ordem.setdefault(l, len(ordem))
tot, first = defaultdict(float), {}
for r, l in zip(recs, lab):
    k = ordem[l]; r["spk"] = k; tot[k] += r["e"] - r["s"]; first.setdefault(k, r["s"])
hms = lambda t: f"{int(t)//3600:02d}:{int(t)%3600//60:02d}:{int(t)%60:02d}"
print(f"limiar {thr}: {len(tot)} grupos; com >= 0,3 min de fala: {sum(1 for v in tot.values() if v >= 18)}")
for k in sorted(tot, key=lambda k: first[k]):
    if tot[k] >= 18: print(f"  S{k:02d}: {tot[k]/60:5.1f} min | {hms(first[k])}")
json.dump(recs, open(pre + f"_t{thr}.json", "w", encoding="utf-8"), ensure_ascii=False)
