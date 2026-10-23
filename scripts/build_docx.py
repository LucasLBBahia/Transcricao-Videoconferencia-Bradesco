"""Gera a transcrição em .docx usando o arquivo do trimestre anterior como modelo.

Uso: python -I build_docx.py <modelo.docx> <texto_marcado.txt> <saida.docx> <linha1> <linha2> <linha3> [pt|en]
  ex. PT: ... "Transcrição da Videoconferência" "Resultados do 3T26" "23 de outubro de 2026" pt
  ex. EN: ... "Video Conference Transcript" "3Q26 Results" "October 23^rd^, 2026" en
  (^texto^ no cabeçalho sai sobrescrito, como o "th" de "August 6th")

Mantém faixa vermelha, logo, rodapé, estilos e página do modelo; troca o corpo e as três
linhas do cabeçalho. Em "en", o idioma padrão do documento vira inglês (corretor ortográfico).

Marcação (uma linha = um parágrafo):
  ## Slide 2 – Destaques              título de slide (negrito)
  ### Subtítulo                        subtítulo do slide (negrito)
  #! Sessão de perguntas e respostas   título em vermelho (negrito, C00000)
  @Nome (Instituição) | texto          fala: nome em negrito + " – " + texto
  texto                                parágrafo comum
  (linha vazia)                        parágrafo vazio
Dentro do texto: *itálico*  e  ==realce amarelo== (trecho a conferir)
"""
import datetime
import re
import sys
import zipfile

modelo, texto, saida, linha1, linha2, linha3 = sys.argv[1:7]
idioma = sys.argv[7] if len(sys.argv) > 7 else "pt"

PPR = '<w:pPr><w:spacing w:after="120" w:line="240" w:lineRule="auto"/><w:jc w:val="both"/>{rpr}</w:pPr>'


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def run(text, b=False, i=False, color=None, hl=False):
    props = ""
    if b:
        props += "<w:b/><w:bCs/>"
    if i:
        props += "<w:i/><w:iCs/>"
    if color:
        props += f'<w:color w:val="{color}"/>'
    if hl:
        props += '<w:highlight w:val="yellow"/>'
    rpr = f"<w:rPr>{props}</w:rPr>" if props else ""
    return f'<w:r>{rpr}<w:t xml:space="preserve">{esc(text)}</w:t></w:r>'


def inline(s, b=False, color=None):
    """Converte *itálico* e ==realce== em runs."""
    out, buf, it, hl, k = [], "", False, False, 0
    while k < len(s):
        if s.startswith("==", k):
            if buf:
                out.append(run(buf, b, it, color, hl))
            buf, hl, k = "", not hl, k + 2
        elif s[k] == "*":
            if buf:
                out.append(run(buf, b, it, color, hl))
            buf, it, k = "", not it, k + 1
        else:
            buf += s[k]
            k += 1
    if buf:
        out.append(run(buf, b, it, color, hl))
    return "".join(out)


def par(runs="", bold_mark=False):
    rpr = "<w:rPr><w:b/><w:bCs/></w:rPr>" if bold_mark else ""
    return f"<w:p>{PPR.format(rpr=rpr)}{runs}</w:p>"


paras = []
for line in open(texto, encoding="utf-8").read().splitlines():
    line = line.rstrip()
    if not line.strip():
        paras.append(par())
    elif line.startswith("#!"):
        paras.append(par(inline(line[2:].strip(), b=True, color="C00000"), True))
    elif line.startswith("###"):
        paras.append(par(inline(line[3:].strip(), b=True), True))
    elif line.startswith("##"):
        paras.append(par(inline(line[2:].strip(), b=True), True))
    elif line.startswith("@"):
        nome, _, fala = line[1:].partition("|")
        paras.append(par(inline(nome.strip() + " – ", b=True) + inline(fala.strip())))
    else:
        paras.append(par(inline(line.strip())))
body = "".join(paras)

# as três linhas da caixa de texto do cabeçalho, em PT ou EN
PADROES = [
    (r"Transcrição da Videoconferência|Video Conference Transcript", linha1),
    (r"Resultados do \S+|\S+ Results", linha2),
    (r"\d{1,2} de \w+ de \d{4}|\w+ \d{1,2}(st|nd|rd|th)?, \d{4}", linha3),
]


def header_runs(rpr, texto_linha):
    """Gera os runs da linha do cabeçalho; trechos entre ^...^ saem sobrescritos."""
    out = []
    for k, parte in enumerate(texto_linha.split("^")):
        if not parte:
            continue
        r = rpr
        if k % 2 == 1:  # sobrescrito: vertAlign vem antes de lang na ordem do schema
            sup = '<w:vertAlign w:val="superscript"/>'
            r = (r.replace("<w:lang", sup + "<w:lang", 1) if "<w:lang" in r
                 else r.replace("</w:rPr>", sup + "</w:rPr>") if r else f"<w:rPr>{sup}</w:rPr>")
        out.append(f'<w:r>{r}<w:t xml:space="preserve">{esc(parte)}</w:t></w:r>')
    return "".join(out)


def fix_header(xml):
    def fix_par(m):
        p = m.group(0)
        full = "".join(re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", p)).strip()
        for padrao, novo in PADROES:
            if re.fullmatch(padrao, full):
                abre = re.match(r"<w:p(?: [^>]*)?>", p).group(0)
                ppr = re.search(r"<w:pPr>.*?</w:pPr>", p, re.S)
                rpr = re.search(r"<w:r(?: [^>]*)?>(<w:rPr>.*?</w:rPr>)", p, re.S)
                return (abre + (ppr.group(0) if ppr else "")
                        + header_runs(rpr.group(1) if rpr else "", novo) + "</w:p>")
        return p

    return re.sub(r"<w:p(?: [^>]*)?>(?:(?!<w:p[ >]).)*?</w:p>", fix_par, xml, flags=re.S)


zin = zipfile.ZipFile(modelo)
with zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        dados = zin.read(item.filename)
        if item.filename == "word/document.xml":
            x = dados.decode("utf-8")
            ini = x.index("<w:body>") + len("<w:body>")
            fim = x.rindex("<w:sectPr")
            dados = (x[:ini] + body + x[fim:]).encode("utf-8")
        elif re.fullmatch(r"word/header\d+\.xml", item.filename):
            dados = fix_header(dados.decode("utf-8")).encode("utf-8")
        elif item.filename == "word/styles.xml" and idioma == "en":
            x = dados.decode("utf-8")
            x = re.sub(r'(<w:docDefaults>.*?<w:lang w:val=")pt-BR(")', r"\1en-US\2", x, count=1, flags=re.S)
            dados = x.encode("utf-8")
        elif item.filename == "docProps/core.xml":
            agora = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            x = dados.decode("utf-8")
            x = re.sub(r"(<dcterms:modified[^>]*>)[^<]*", r"\g<1>" + agora, x)
            dados = x.encode("utf-8")
        zout.writestr(item, dados)
print(f"ok: {len(paras)} parágrafos -> {saida}")
