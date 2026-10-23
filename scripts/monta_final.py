"""Junta os blocos revisados num único texto marcado e padroniza o espaçamento entre blocos.

Uso: python -I monta_final.py <saida.txt> <bloco1.txt> [<bloco2.txt> ...]
Regras: uma linha vazia antes de cada fala (@), título de slide (##) e título do Q&A (#!);
nenhuma linha vazia logo depois de título ou subtítulo; no máximo uma linha vazia seguida.
Também confere marcações desbalanceadas (== e *) e lista os rótulos de falante usados.
"""
import re
import sys
from collections import Counter

saida, blocos = sys.argv[1], sys.argv[2:]
linhas = []
for b in blocos:
    linhas += [l.rstrip() for l in open(b, encoding="utf-8").read().splitlines()]
    linhas.append("")

out = []
for l in linhas:
    if not l.strip():
        if out and out[-1] != "" and not out[-1].startswith(("##", "#!")):
            out.append("")
        continue
    inicio_bloco = l.startswith(("@", "##", "#!")) and not l.startswith("###")
    if inicio_bloco and out and out[-1] != "" and not out[-1].startswith(("##", "#!")):
        out.append("")
    if out and out[-1] == "" and len(out) > 1 and out[-2].startswith(("##", "#!")) and not inicio_bloco:
        out.pop()  # texto colado ao título
    out.append(l)
while out and out[-1] == "":
    out.pop()
while out and out[0] == "":
    out.pop(0)
open(saida, "w", encoding="utf-8").write("\n".join(out) + "\n")

problemas = [f"linha {i + 1}: '==' desbalanceado" for i, l in enumerate(out) if l.count("==") % 2]
problemas += [f"linha {i + 1}: '*' desbalanceado" for i, l in enumerate(out) if l.count("*") % 2]
rotulos = Counter(re.sub(r"==", "", l[1:].split("|")[0]).strip() for l in out if l.startswith("@"))
print(f"{len(out)} linhas; {sum(1 for l in out if l.startswith('## '))} títulos de slide; "
      f"{sum(rotulos.values())} falas; {sum(l.count('==') // 2 for l in out)} realces")
print("Falantes:", "; ".join(f"{k} ({v})" for k, v in rotulos.most_common()))
print("Problemas de marcação:", "; ".join(problemas) if problemas else "nenhum")
