"""Procura trechos mudos (corte de áudio) num WAV, sinal de que a transmissão perdeu o som.

Uso: python verificar_cortes.py <audio_16k.wav> [segundos_minimos=3] [limiar_rms=0.0015]
No 3T26 o canal em português ficou mudo por 1min45 aos 15:40; a fala foi recuperada do canal
"Áudio Original", que no YouTube estava ~25 s adiantado em relação ao canal em português.
Pausas curtas e o fim da transmissão também aparecem aqui; confira cada trecho listado.
"""
import sys

import numpy as np
import soundfile as sf

arq = sys.argv[1]
minimo = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
limiar = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0015

a, sr = sf.read(arq, dtype="float32")
if a.ndim > 1:
    a = a.mean(axis=1)
win = sr // 2  # janelas de 0,5 s
n = len(a) // win
rms = np.sqrt((a[: n * win].reshape(n, win) ** 2).mean(axis=1))


def hms(t):
    t = int(t)
    return f"{t // 3600:02d}:{t % 3600 // 60:02d}:{t % 60:02d}"


cortes, i = [], 0
while i < n:
    if rms[i] < limiar:
        j = i
        while j < n and rms[j] < limiar:
            j += 1
        if (j - i) * 0.5 >= minimo:
            cortes.append((i * 0.5, (j - i) * 0.5))
        i = j
    else:
        i += 1

print(f"{arq}: {len(a) / sr / 60:.1f} min; trechos mudos >= {minimo:.0f} s: {len(cortes)}")
for ini, dur in cortes:
    print(f"  {hms(ini)}  ({dur:.0f} s)")
