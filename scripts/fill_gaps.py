"""Segunda passada: retranscreve os "buracos" deixados pelo modo em lote do Whisper.

Uso: python fill_gaps.py <wav_16k_mono> <whisper.json> <saida_prefixo> [prompt.txt] [gap_min=2.0]
Procura pausas longas entre palavras, retranscreve cada janela no modo sequencial (sem VAD,
que é onde a fala costuma se perder) e insere só as palavras que caem dentro do buraco.
Gera <saida_prefixo>.json/.txt (transcrição completa) e <saida_prefixo>_recuperado.txt (relatório).
"""
import json
import os
import site
import sys

for sp in site.getsitepackages():
    for sub in ("nvidia/cublas/bin", "nvidia/cudnn/bin", "nvidia/cuda_nvrtc/bin"):
        d = os.path.join(sp, sub)
        if os.path.isdir(d):
            os.add_dll_directory(d)
            os.environ["PATH"] = d + os.pathsep + os.environ["PATH"]

import soundfile as sf  # noqa: E402
from faster_whisper import WhisperModel  # noqa: E402

wav, wjson, out = sys.argv[1:4]
prompt = open(sys.argv[4], encoding="utf-8").read().strip() if len(sys.argv) > 4 else ""
GAP = float(sys.argv[5]) if len(sys.argv) > 5 else 2.0
PAD = 1.0

audio, sr = sf.read(wav, dtype="float32")
data = json.load(open(wjson, encoding="utf-8"))
words = [w for s in data["segments"] for w in s["words"]]
# o Whisper às vezes "estica" uma palavra por cima da fala perdida; por isso cada palavra
# conta no máximo 0,8 s ao medir o buraco até a próxima
gaps = []
for i in range(len(words) - 1):
    fim = min(words[i]["e"], words[i]["s"] + 0.8)
    if words[i + 1]["s"] - fim >= GAP:
        gaps.append((fim, words[i + 1]["s"], i))

model = WhisperModel("large-v3", device="cuda", compute_type="int8_float16")


def hms(t):
    t = int(t)
    return f"{t // 3600:02d}:{t % 3600 // 60:02d}:{t % 60:02d}"


novos, rel = [], []
for g0, g1, i in gaps:
    a, b = max(0.0, g0 - PAD), g1 + PAD
    contexto = "".join(w["w"] for w in words[max(0, i - 40): i + 1]).strip()
    segs, _ = model.transcribe(audio[int(a * sr): int(b * sr)], language="pt", beam_size=5,
                               word_timestamps=True, vad_filter=False,
                               condition_on_previous_text=False,
                               initial_prompt=(prompt + " " + contexto).strip())
    achados = []
    for s in segs:
        for w in s.words or []:
            ws, we = w.start + a, w.end + a
            if ws >= g0 - 0.15 and we <= g1 + 0.15:
                achados.append({"s": round(ws, 2), "e": round(we, 2), "w": w.word, "p": round(w.probability, 3)})
    texto = "".join(w["w"] for w in achados).strip()
    if achados and len(achados) >= 2:
        novos.extend(achados)
        rel.append(f"[{hms(g0)}] buraco de {g1 - g0:.0f}s -> RECUPERADO: {texto}")
    else:
        rel.append(f"[{hms(g0)}] buraco de {g1 - g0:.0f}s -> sem fala (silêncio){': ' + texto if texto else ''}")

todas = sorted(words + novos, key=lambda w: w["s"])
# remonta em blocos de ~30 s para manter o mesmo formato de saída
segs_out, cur = [], []
for w in todas:
    if cur and w["s"] - cur[0]["s"] > 30:
        segs_out.append(cur)
        cur = []
    cur.append(w)
if cur:
    segs_out.append(cur)
res = {"duration": data["duration"],
       "segments": [{"s": c[0]["s"], "e": c[-1]["e"], "t": "".join(w["w"] for w in c).strip(), "words": c}
                    for c in segs_out]}
json.dump(res, open(out + ".json", "w", encoding="utf-8"), ensure_ascii=False)
with open(out + ".txt", "w", encoding="utf-8") as f:
    for s in res["segments"]:
        f.write(f"[{hms(s['s'])}] {s['t']}\n")
with open(out + "_recuperado.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(rel) + "\n")
print(f"{len(gaps)} buracos analisados, {sum('RECUPERADO' in r for r in rel)} com fala recuperada "
      f"({len(novos)} palavras) -> {out}.json")
