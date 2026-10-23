"""Compara uma transcrição automática com a versão publicada pelo RI.

Uso: python compare.py <oficial.txt> <candidata.json> <relatorio.txt>
Mede:
 1) cobertura: % das palavras de conteúdo da versão publicada que aparecem, na mesma ordem,
    na transcrição automática (a versão publicada é editada, então 100% não é esperado);
 2) trechos longos da versão publicada sem correspondente (fala perdida ou texto acrescentado
    na edição) – listados para inspeção;
 3) números da versão publicada encontrados na transcrição.
"""
import difflib
import json
import re
import sys
from collections import Counter

STOP = set("""a o e é de do da dos das que em no na nos nas um uma uns umas para pra por com como mais
mas ao aos à às se ou já também isso isto esse essa este esta esses essas estes estas aqui ali lá
eu nós você vocês ele ela eles elas me te lhe muito bem não sim foi ser ter tem temos está estão
são era há vai vamos então porque quando onde qual quais quem pelo pela pelos pelas sobre entre até
sua seu suas seus nossa nosso nossas nossos minha meu gente né tá aí assim só ainda o os as""".split())
LABEL = re.compile(r"^(Marcelo Noronha|André Carvalho|Cassiano Scarpelli|Ney Ferraz Dias|"
                   r"[A-ZÀ-Ú][\wà-ú]+ [A-ZÀ-Ú][\w\-à-ú]+ \([^)]+\))\s*[–-]\s*")
TOK = re.compile(r"\d[ts]\d\d|\d+(?:[.,]\d+)*%?|[a-zà-úç]+")

oficial_txt, cand_json, saida = sys.argv[1:4]

# --- versão publicada: tira títulos de slide, subtítulos e rótulos de falante
linhas, prev_slide = [], False
for l in open(oficial_txt, encoding="utf-8").read().splitlines():
    if re.match(r"^Slide \d+", l) or l.startswith("Sessão de perguntas"):
        prev_slide = True
        continue
    if prev_slide and not re.search(r"[.:;?!,]$", l) and len(l.split()) < 14:
        prev_slide = False  # subtítulo do slide (texto do deck, não fala)
        continue
    prev_slide = False
    linhas.append(LABEL.sub("", l))
of_all = TOK.findall(" ".join(linhas).lower())

cand = json.load(open(cand_json, encoding="utf-8"))
cd_all = TOK.findall("".join(w["w"] for s in cand["segments"] for w in s["words"]).lower())


def conteudo(toks):
    return [(t, i) for i, t in enumerate(toks) if t not in STOP and not re.fullmatch(r"\d[ts]\d\d", t)]


of_c, cd_c = conteudo(of_all), conteudo(cd_all)
sm = difflib.SequenceMatcher(None, [t for t, _ in of_c], [t for t, _ in cd_c], autojunk=False)
blocos = sm.get_matching_blocks()
casadas = sum(b.size for b in blocos)

# trechos longos sem correspondente
lacunas, pos = [], 0
for b in blocos:
    if b.a - pos >= 12:
        ini, fim = of_c[pos][1], of_c[b.a - 1][1]
        lacunas.append((b.a - pos, " ".join(of_all[ini:fim + 1])))
    pos = b.a + b.size


def num(t):
    t = t.rstrip("%")
    return t.replace(".", "") if re.fullmatch(r"\d{1,3}(\.\d{3})+", t) else t


nums_of = [(num(t), i) for i, t in enumerate(of_all) if t[0].isdigit() and not re.fullmatch(r"\d[ts]\d\d", t)]
estoque = Counter(num(t) for t in cd_all if t[0].isdigit())
achados, faltando = 0, []
for n, i in nums_of:
    if estoque[n] > 0:
        estoque[n] -= 1
        achados += 1
    else:
        faltando.append(f"{n}  ←  …{' '.join(of_all[max(0, i - 6): i + 4])}…")

with open(saida, "w", encoding="utf-8") as f:
    f.write(f"Palavras de conteúdo na versão publicada: {len(of_c)}\n")
    f.write(f"Cobertura (mesma ordem): {casadas / len(of_c):.1%}\n")
    f.write(f"Números da versão publicada encontrados: {achados}/{len(nums_of)} ({achados / len(nums_of):.1%})\n")
    tot = sum(n for n, _ in lacunas)
    f.write(f"Trechos longos (>=12 palavras de conteúdo) sem correspondente: {len(lacunas)} "
            f"({tot} palavras, {tot / len(of_c):.1%})\n\n")
    for n, txt in sorted(lacunas, reverse=True):
        f.write(f"[{n}] {txt}\n\n")
    f.write("\nNúmeros não encontrados:\n" + "\n".join(faltando) + "\n")
print(open(saida, encoding="utf-8").read().split("\n\n")[0])
