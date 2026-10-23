"""Separa falantes (diarização) com sherpa-onnx e salva os turnos em JSON.

Uso: python diarize.py <wav_16k_mono> <saida.json> <modelo_embedding.onnx> [limiar|-N falantes]
  limiar (ex.: 0.6) -> clustering por distância; valor negativo (ex.: -16) -> número fixo de falantes
"""
import json
import os
import sys
import time

import sherpa_onnx
import soundfile as sf

wav, out, emb_model = sys.argv[1], sys.argv[2], sys.argv[3]
arg = float(sys.argv[4]) if len(sys.argv) > 4 else 0.6
models = os.path.join(os.path.dirname(os.path.abspath(emb_model)))
seg_model = os.path.join(models, "sherpa-onnx-pyannote-segmentation-3-0", "model.onnx")

num_clusters, threshold = (-1, arg) if arg > 0 else (int(-arg), 0.5)
config = sherpa_onnx.OfflineSpeakerDiarizationConfig(
    segmentation=sherpa_onnx.OfflineSpeakerSegmentationModelConfig(
        pyannote=sherpa_onnx.OfflineSpeakerSegmentationPyannoteModelConfig(model=seg_model),
        num_threads=8,
    ),
    embedding=sherpa_onnx.SpeakerEmbeddingExtractorConfig(model=emb_model, num_threads=8),
    clustering=sherpa_onnx.FastClusteringConfig(num_clusters=num_clusters, threshold=threshold),
    min_duration_on=0.3,
    min_duration_off=0.5,
)
assert config.validate(), "config inválida"
sd = sherpa_onnx.OfflineSpeakerDiarization(config)

audio, sr = sf.read(wav, dtype="float32", always_2d=True)
audio = audio[:, 0]
assert sr == sd.sample_rate, f"esperado {sd.sample_rate} Hz"

t0 = time.time()
last = [0]


def cb(done, total):
    pct = int(done / total * 100)
    if pct >= last[0] + 10:
        last[0] = pct
        print(f"{pct}% ({time.time() - t0:.0f}s)", flush=True)
    return 0


result = sd.process(audio, callback=cb).sort_by_start_time()
turns = [{"s": round(r.start, 2), "e": round(r.end, 2), "spk": r.speaker} for r in result]
with open(out, "w", encoding="utf-8") as f:
    json.dump(turns, f)
spk = sorted({t["spk"] for t in turns})
print(f"pronto: {len(turns)} turnos, {len(spk)} falantes, {time.time() - t0:.0f}s", flush=True)
