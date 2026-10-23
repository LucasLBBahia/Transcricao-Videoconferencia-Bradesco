"""Transcrição no modo sequencial do faster-whisper (mais fiel que o modo em lote; não pula fala).

Uso: python transcribe_seq.py <wav_16k_mono> <saida_prefixo> [prompt.txt]
Gera <saida_prefixo>.json (segmentos com palavras e tempos) e <saida_prefixo>.txt.
"""
import json
import os
import site
import sys
import time

for sp in site.getsitepackages():
    for sub in ("nvidia/cublas/bin", "nvidia/cudnn/bin", "nvidia/cuda_nvrtc/bin"):
        d = os.path.join(sp, sub)
        if os.path.isdir(d):
            os.add_dll_directory(d)
            os.environ["PATH"] = d + os.pathsep + os.environ["PATH"]

import soundfile as sf  # noqa: E402
from faster_whisper import WhisperModel  # noqa: E402

wav, out = sys.argv[1], sys.argv[2]
prompt = open(sys.argv[3], encoding="utf-8").read().strip() if len(sys.argv) > 3 else None


def hms(t):
    t = int(t)
    return f"{t // 3600:02d}:{t % 3600 // 60:02d}:{t % 60:02d}"


audio, sr = sf.read(wav, dtype="float32")
assert sr == 16000 and audio.ndim == 1
t0 = time.time()
model = WhisperModel("large-v3", device="cuda", compute_type="int8_float16")
segments, info = model.transcribe(
    audio, language="pt", beam_size=5, word_timestamps=True, initial_prompt=prompt,
    condition_on_previous_text=False,  # evita loops de repetição em áudio longo
    vad_filter=True,
    vad_parameters={"threshold": 0.35, "min_silence_duration_ms": 1000, "speech_pad_ms": 400},
)
data = []
with open(out + ".txt", "w", encoding="utf-8") as f:
    for s in segments:
        words = [{"s": round(w.start, 2), "e": round(w.end, 2), "w": w.word, "p": round(w.probability, 3)}
                 for w in (s.words or [])]
        data.append({"s": round(s.start, 2), "e": round(s.end, 2), "t": s.text.strip(), "words": words})
        f.write(f"[{hms(s.start)}] {s.text.strip()}\n")
        if len(data) % 200 == 0:
            print(f"{hms(s.end)} de {hms(info.duration)} ({time.time() - t0:.0f}s)", flush=True)
json.dump({"duration": info.duration, "segments": data}, open(out + ".json", "w", encoding="utf-8"),
          ensure_ascii=False)
print(f"pronto: {len(data)} segmentos em {time.time() - t0:.0f}s", flush=True)
