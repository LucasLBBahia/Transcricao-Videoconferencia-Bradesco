"""Transcreve um áudio com faster-whisper (GPU) e salva JSON + TXT com timestamps.

Uso: python transcribe.py <audio> <saida_prefixo> [modelo] [compute_type] [batch_size] [prompt.txt]
"""
import json
import os
import site
import sys
import time

# DLLs do CUDA (cuBLAS/cuDNN) instaladas via pip ficam em site-packages/nvidia/*/bin
for sp in site.getsitepackages():
    for sub in ("nvidia/cublas/bin", "nvidia/cudnn/bin", "nvidia/cuda_nvrtc/bin"):
        d = os.path.join(sp, sub)
        if os.path.isdir(d):
            os.add_dll_directory(d)
            os.environ["PATH"] = d + os.pathsep + os.environ["PATH"]

import soundfile as sf  # noqa: E402
from faster_whisper import BatchedInferencePipeline, WhisperModel  # noqa: E402

audio = sys.argv[1]
out = sys.argv[2]
model_name = sys.argv[3] if len(sys.argv) > 3 else "large-v3"
compute_type = sys.argv[4] if len(sys.argv) > 4 else "float16"
batch_size = int(sys.argv[5]) if len(sys.argv) > 5 else 4
prompt = None
if len(sys.argv) > 6:
    with open(sys.argv[6], encoding="utf-8") as f:
        prompt = f.read().strip()


def hms(t):
    t = int(t)
    return f"{t // 3600:02d}:{t % 3600 // 60:02d}:{t % 60:02d}"


t0 = time.time()
model = WhisperModel(model_name, device="cuda", compute_type=compute_type)
pipe = BatchedInferencePipeline(model=model)
print(f"modelo carregado em {time.time() - t0:.0f}s", flush=True)

# o PyAV recente não abre áudio pelo faster-whisper; lemos o WAV 16 kHz mono direto
samples, sr = sf.read(audio, dtype="float32")
assert sr == 16000 and samples.ndim == 1, "use WAV 16 kHz mono (ffmpeg -ac 1 -ar 16000)"

segments, info = pipe.transcribe(
    samples,
    language="pt",
    batch_size=batch_size,
    beam_size=5,
    word_timestamps=True,
    initial_prompt=prompt,
    vad_filter=True,
)

data = []
with open(out + ".txt", "w", encoding="utf-8") as ftxt:
    for s in segments:
        words = [
            {"s": round(w.start, 2), "e": round(w.end, 2), "w": w.word, "p": round(w.probability, 3)}
            for w in (s.words or [])
        ]
        data.append({"s": round(s.start, 2), "e": round(s.end, 2), "t": s.text.strip(), "words": words})
        ftxt.write(f"[{hms(s.start)}] {s.text.strip()}\n")
        if len(data) % 50 == 0:
            print(f"{hms(s.end)} de {hms(info.duration)} ({time.time() - t0:.0f}s)", flush=True)

with open(out + ".json", "w", encoding="utf-8") as fj:
    json.dump({"duration": info.duration, "segments": data}, fj, ensure_ascii=False)

print(f"pronto: {len(data)} segmentos em {time.time() - t0:.0f}s", flush=True)
