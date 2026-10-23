"""Lista os parágrafos de um document.xml com formatação resumida (para estudar o modelo).

Uso: python -I dump_docx.py <document.xml> [max_paragrafos]
"""
import re
import sys
import xml.etree.ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
path = sys.argv[1]
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10**9

body = ET.parse(path).getroot().find(W + "body")
n = 0
for el in body:
    tag = el.tag.replace(W, "")
    if tag != "p":
        print(f"<{tag}>")
        continue
    n += 1
    if n > limit:
        break
    ppr = el.find(W + "pPr")
    pinfo = []
    if ppr is not None:
        st = ppr.find(W + "pStyle")
        if st is not None:
            pinfo.append("style=" + st.get(W + "val"))
        sp = ppr.find(W + "spacing")
        if sp is not None:
            pinfo.append("sp=" + ",".join(f"{k.replace(W, '')}:{v}" for k, v in sp.attrib.items()))
        jc = ppr.find(W + "jc")
        if jc is not None:
            pinfo.append("jc=" + jc.get(W + "val"))
        if ppr.find(W + "sectPr") is not None:
            pinfo.append("SECTPR")
    parts = []
    for r in el.iter(W + "r"):
        rpr = r.find(W + "rPr")
        fmt = ""
        if rpr is not None:
            if rpr.find(W + "b") is not None:
                fmt += "B"
            if rpr.find(W + "i") is not None:
                fmt += "I"
            c = rpr.find(W + "color")
            if c is not None:
                fmt += "#" + c.get(W + "val")
            sz = rpr.find(W + "sz")
            if sz is not None:
                fmt += "sz" + sz.get(W + "val")
            hl = rpr.find(W + "highlight")
            if hl is not None:
                fmt += "HL" + hl.get(W + "val")
        txt = "".join(t.text or "" for t in r.findall(W + "t"))
        if txt:
            parts.append(f"[{fmt}]{txt}" if fmt else txt)
    text = "".join(parts)
    text = re.sub(r"\s+", " ", text)
    print(f"{n:04d} {' '.join(pinfo)} | {text[:260]}")
