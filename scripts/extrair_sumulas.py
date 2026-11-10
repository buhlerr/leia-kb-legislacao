"""Extrai o enunciado das Sumulas do STJ (214, 268, 335, 549, 332, 359, 404, 548, 656) das paginas oficiais do processo.stj.jus.br.

Cada pagina de consulta (sumstj/doc.jsp) traz o texto integral da sumula num <textarea>
id="textSemformatacao<N>", seguido da citacao "(Sumula n. N, ...)". Grava so o enunciado.

Uso: uv run --no-project --with beautifulsoup4 python -I extrair_sumulas.py <pasta_raw> <saida.jsonl>
"""
import json
import re
import sys

from bs4 import BeautifulSoup

DATA_COLETA = "2026-11-09"
NUMEROS = [214, 268, 335, 549, 332, 359, 404, 548, 656]
URL_BASE = "https://processo.stj.jus.br/SCON/sumstj/doc.jsp?&b=SUMU&p=false&l=10&i=1&ordenacao=-@NUM,-@DOCN&h=true&livre=%40NUM%3D%22{n}%22"


def decodificar(bruto):
    try:
        return bruto.decode("utf-8")
    except UnicodeDecodeError:
        return bruto.decode("iso-8859-1")


def main(pasta, saida):
    registros = []
    relatorio = {}
    for n in NUMEROS:
        caminho = f"{pasta}/s_{n}.html"
        with open(caminho, "rb") as fh:
            html = decodificar(fh.read())
        soup = BeautifulSoup(html, "html.parser")
        area = soup.find("textarea", id=f"textSemformatacao{n}")
        if area is None:
            relatorio[n] = "textarea nao encontrada"
            continue
        texto_bruto = re.sub(r"\s+", " ", area.get_text(" ")).strip()
        m = re.match(r"^(.*?)\s*\(S[úu]mula n\.\s*%d\b" % n, texto_bruto)
        if not m:
            relatorio[n] = "citacao nao encontrada"
            continue
        enunciado = m.group(1).strip()
        if not enunciado.endswith("."):
            relatorio[n] = "enunciado sem ponto final, revisar"
            continue
        registros.append({
            "id": f"sumulas-stj-sumula-{n}",
            "fonte": "sumulas-stj",
            "norma": "Súmulas do STJ",
            "artigo": f"Súmula {n}",
            "estrutura": "",
            "texto": enunciado,
            "alteracoes": [],
            "url": URL_BASE.format(n=n),
            "data_coleta": DATA_COLETA,
        })
        relatorio[n] = "ok"
    with open(saida, "w", encoding="utf-8", newline="\n") as fh:
        for r in registros:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps({"registros": len(registros), "status": relatorio}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
