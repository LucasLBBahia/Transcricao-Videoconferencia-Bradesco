"""Confere se a revisão não deixou conteúdo para trás: compara o texto revisado com a transcrição crua.

Uso: python qa_cobertura.py <entrada_crua.txt> <saida_revisada.txt>
Mostra a % das palavras de conteúdo da transcrição crua que aparecem, na mesma ordem, no texto
revisado, os trechos longos da crua sem correspondente (possível omissão) e os números da crua que
não aparecem na revisão (aceitando 1.234 = 1234 e 3.9 = 3,9).
"""
import difflib
import re
import sys

STOP = set("""a o e é de do da dos das que em no na nos nas um uma uns umas para pra por com como mais
mas ao aos à às se ou já também isso isto esse essa este esta esses essas estes estas aqui ali lá
eu nós você vocês ele ela eles elas me te lhe muito bem não sim foi ser ter tem temos está estão
são era há vai vamos então porque quando onde qual quais quem pelo pela pelos pelas sobre entre até
sua seu suas seus nossa nosso nossas nossos minha meu gente né tá aí assim só ainda os as olha
certo pessoal veja vejam aqui""".split())
TOK = re.compile(r"\d+(?:[.,]\d+)*|[a-zà-úç]+")

crua_txt = open(sys.argv[1], encoding="utf-8").read()
crua_txt = re.sub(r"\[\d\d:\d\d:\d\d(?:-\d\d:\d\d:\d\d)?\]\s*(S\d\d:)?", " ", crua_txt)
crua_txt = re.sub(r"\[TRECHO RECUPERADO[^\]]*\]", " ", crua_txt)
rev_txt = open(sys.argv[2], encoding="utf-8").read()
rev_txt = re.sub(r"[@#*=|]", " ", rev_txt)

crua = TOK.findall(crua_txt.lower())
rev = TOK.findall(rev_txt.lower())
cc = [(t, i) for i, t in enumerate(crua) if t not in STOP]
rc = [t for t in rev if t not in STOP]
sm = difflib.SequenceMatcher(None, [t for t, _ in cc], rc, autojunk=False)
blocos = sm.get_matching_blocks()
casadas = sum(b.size for b in blocos)
print(f"Cobertura da transcrição crua no texto revisado: {casadas / max(1, len(cc)):.0%} "
      f"({len(cc)} palavras de conteúdo)")
pos, lac = 0, []
for b in blocos:
    if b.a - pos >= 12:
        ini, fim = cc[pos][1], cc[b.a - 1][1]
        lac.append((b.a - pos, " ".join(crua[ini:fim + 1])))
    pos = b.a + b.size
print(f"Trechos longos da crua sem correspondente: {len(lac)}")
for n, t in lac:
    print(f"  [{n}] {t[:400]}")


def norm(n):
    n = n.replace(".", ",") if re.fullmatch(r"\d+\.\d{1,2}", n) else n
    return n.replace(".", "")


nums_rev = {norm(t) for t in rev if t[0].isdigit()}
falt = sorted({t for t in crua if t[0].isdigit() and norm(t) not in nums_rev}, key=lambda x: (len(x), x))
print("Números da crua ausentes na revisão:", ", ".join(falt) if falt else "nenhum")
