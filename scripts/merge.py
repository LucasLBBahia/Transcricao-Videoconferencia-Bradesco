"""Junta a transcrição (palavras com tempo) com a diarização e gera os turnos de fala.

Uso: python merge.py <whisper.json> <diar.json> <saida.txt> [inicio_seg] [fim_seg]
Cada palavra recebe o falante cujo trecho mais se sobrepõe a ela; palavras seguidas
do mesmo falante viram um turno. Também lista o tempo total de fala por falante.
"""
import bisect
import json
import sys
from collections import defaultdict

wj, dj, out = sys.argv[1], sys.argv[2], sys.argv[3]
t_ini = float(sys.argv[4]) if len(sys.argv) > 4 else 0
t_fim = float(sys.argv[5]) if len(sys.argv) > 5 else 1e9

segs = json.load(open(wj, encoding="utf-8"))["segments"]
turns = json.load(open(dj, encoding="utf-8"))
starts = [t["s"] for t in turns]


def speaker_at(s, e):
    best, best_ov = None, 0.0
    i = max(0, bisect.bisect_right(starts, s) - 3)
    while i < len(turns) and turns[i]["s"] < e:
        ov = min(e, turns[i]["e"]) - max(s, turns[i]["s"])
        if ov > best_ov:
            best, best_ov = turns[i]["spk"], ov
        i += 1
    if best is None:  # palavra fora de qualquer trecho: usa o trecho mais próximo
        mid = (s + e) / 2
        j = bisect.bisect_right(starts, mid)
        cands = [turns[k] for k in (j - 1, j) if 0 <= k < len(turns)]
        best = min(cands, key=lambda t: min(abs(mid - t["s"]), abs(mid - t["e"])))["spk"]
    return best


words = []
for sg in segs:
    for w in sg["words"]:
        if t_ini <= w["s"] < t_fim:
            words.append((w["s"], w["e"], w["w"], speaker_at(w["s"], w["e"])))

out_turns = []
for s, e, w, spk in words:
    if out_turns and out_turns[-1]["spk"] == spk:
        out_turns[-1]["e"] = e
        out_turns[-1]["text"] += w
    else:
        out_turns.append({"spk": spk, "s": s, "e": e, "text": w})


def hms(t):
    t = int(t)
    return f"{t // 3600:02d}:{t % 3600 // 60:02d}:{t % 60:02d}"


tot = defaultdict(float)
first = {}
for t in out_turns:
    tot[t["spk"]] += t["e"] - t["s"]
    first.setdefault(t["spk"], t["s"])

with open(out, "w", encoding="utf-8") as f:
    f.write("# falante: tempo total de fala (min) | primeira fala\n")
    for spk in sorted(tot, key=lambda k: first[k]):
        f.write(f"# S{spk:02d}: {tot[spk] / 60:6.1f} min | {hms(first[spk])}\n")
    f.write("\n")
    for t in out_turns:
        f.write(f"[{hms(t['s'])}-{hms(t['e'])}] S{t['spk']:02d}: {t['text'].strip()}\n")
print(f"{len(out_turns)} turnos, {len(tot)} falantes -> {out}")
