"""Valida os JSONL gerados: chaves, unicidade, HTML, anotacoes, codificacao e artigos de referencia.

Uso: uv run --no-project python -I validar.py <arquivo.jsonl> [<arquivo.jsonl> ...]
"""
import json
import re
import sys

CHAVES = {"id", "fonte", "norma", "artigo", "estrutura", "texto", "alteracoes", "url", "data_coleta"}
TAG_RE = re.compile(r"</?[a-zA-Z][^>]*>")
MOJIBAKE_RE = re.compile(r"Ã[\x80-\xbf]|Â[\x80-\xbf]|�")
ANOT_LEFT_RE = re.compile(r"Reda[cç][aã]o dada|\((?:Inclu[ií]d|Vide|Revogad|VETAD|Vetad|Acrescid)", re.I)
ESPERADO_INICIO = {
    "lei-8245-1991": {"4": "Art. 4º", "37": "Art. 37"},
    "codigo-civil-2002": {"413": "Art. 413"},
}


def validar(caminho):
    registros = []
    erros = []
    with open(caminho, encoding="utf-8") as fh:
        for n, linha in enumerate(fh, 1):
            obj = json.loads(linha)
            registros.append(obj)
            if set(obj) != CHAVES and not CHAVES <= set(obj):
                erros.append(f"linha {n}: chaves faltando {CHAVES - set(obj)}")
            t = obj["texto"]
            if TAG_RE.search(t):
                erros.append(f"{obj['id']}: tag HTML no texto")
            if "Redação dada" in t or "Redacao dada" in t:
                erros.append(f"{obj['id']}: 'Redação dada' no texto")
            if MOJIBAKE_RE.search(t):
                erros.append(f"{obj['id']}: codificacao quebrada")
            if ANOT_LEFT_RE.search(t):
                erros.append(f"{obj['id']}: anotacao editorial sobrou no texto")
            m = re.match(r"Art\. (\d+)(-[A-Z])?(?=\D|$)", t)
            if not m or (m.group(1) + (m.group(2) or "")) != obj["artigo"]:
                erros.append(f"{obj['id']}: texto nao comeca com o artigo {obj['artigo']} ({t[:25]!r})")
            if "\n" not in t and len(t) < 30:
                erros.append(f"{obj['id']}: texto muito curto")
            if not isinstance(obj["alteracoes"], list) or len(set(obj["alteracoes"])) != len(obj["alteracoes"]):
                erros.append(f"{obj['id']}: alteracoes invalidas/duplicadas")

    ids = [r["id"] for r in registros]
    arts = [r["artigo"] for r in registros]
    dup_ids = sorted({i for i in ids if ids.count(i) > 1})
    dup_arts = sorted({a for a in arts if arts.count(a) > 1})
    if dup_ids:
        erros.append(f"ids duplicados: {dup_ids}")
    if dup_arts:
        erros.append(f"artigos duplicados: {dup_arts}")

    ref = {}
    slug = registros[0]["fonte"] if registros else ""
    for art, inicio in ESPERADO_INICIO.get(slug, {}).items():
        achados = [r for r in registros if r["artigo"] == art]
        if not achados:
            erros.append(f"artigo de referencia {art} ausente")
        else:
            ok = achados[0]["texto"].startswith(inicio)
            ref[art] = ok
            if not ok:
                erros.append(f"artigo {art} nao comeca com {inicio!r}")

    print(f"== {caminho}")
    print(f"registros: {len(registros)}  unicos: {len(set(arts))}")
    print(f"artigos de referencia: {ref if ref else 'n/a'}")
    print("erros:" if erros else "erros: nenhum")
    for e in erros:
        print("  -", e)
    return registros


if __name__ == "__main__":
    for c in sys.argv[1:]:
        validar(c)
