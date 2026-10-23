"""Confere os ajustes pedidos pelo RI em cada bloco revisado do 3T26.

Uso: python -I verifica_ajustes.py <pasta_dos_blocos> [blocos=P1,P2,Q1,Q2]
Cada bloco X precisa de X_entrada.txt (transcrição crua) e X_saida.txt (texto revisado) na pasta.
Para cada bloco: números do texto revisado que não aparecem na transcrição crua (não falados),
traços usados como pontuação no meio das falas e, nos blocos de Q&A, parágrafos de continuação
(texto fora de uma linha "@"). Conversões de formato conhecidas são aceitas.
"""
import re
import sys

BASE = sys.argv[1].rstrip("/\\") + "/"
BLOCOS = sys.argv[2].split(",") if len(sys.argv) > 2 else ["P1", "P2", "Q1", "Q2"]
NUM = re.compile(r"\d+(?:[.,]\d+)*")
# mesmo valor falado de outro jeito: "1 trilhão 150 bilhões", "7 bilhões e 109 milhões", "em 27", "de 25"...
FORMATO = {"1150", "1.150", "7,109", "2024", "2025", "2026", "2027", "2028", "97443", "8238", "3T26", "4T26"}


def norm(n):
    n = n.replace(".", ",") if re.fullmatch(r"\d+\.\d{1,2}", n) else n
    return n.replace(".", "")


for b in BLOCOS:
    crua = open(BASE + f"{b}_entrada.txt", encoding="utf-8").read()
    crua = re.sub(r"\[\d\d:\d\d:\d\d(?:-\d\d:\d\d:\d\d)?\]", " ", crua)
    ditos = {norm(x) for x in NUM.findall(crua)}
    rev = open(BASE + f"{b}_saida.txt", encoding="utf-8").read().splitlines()
    nao_ditos, tracos, cont = [], [], 0
    for l in rev:
        if l.startswith("#"):
            continue
        corpo = l.split("|", 1)[1] if l.startswith("@") else l
        for m in NUM.finditer(corpo):
            n = norm(m.group())
            if n not in ditos and n not in FORMATO and not re.fullmatch(r"\d", n):
                nao_ditos.append(f"{m.group()} …{corpo[max(0, m.start() - 50): m.end() + 30]}…")
        tracos += [corpo[max(0, t.start() - 40): t.end() + 40] for t in re.finditer(r"\S\s[–—]\s\S|\S\s-\s\S", corpo)]
        if b.startswith("Q") and l.strip() and not l.startswith("@"):
            cont += 1
    print(f"== {b}: números não falados: {len(nao_ditos)} | traços no texto: {len(tracos)}"
          + (f" | parágrafos de continuação no Q&A: {cont}" if b.startswith("Q") else ""))
    for x in nao_ditos:
        print("   nº  ", x)
    for x in tracos:
        print("   traço …" + x + "…")
