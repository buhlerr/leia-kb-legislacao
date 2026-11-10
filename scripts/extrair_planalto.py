"""Extrai artigos de legislacao compilada do Planalto para JSONL (um registro por artigo).

Uso:
  uv run --no-project --with beautifulsoup4 python -I extrair_planalto.py \
      --slug lei-8245-1991 --arquivo <html> --norma "Lei 8.245/1991" --url <url> \
      --faixas todos [--extra '{"aplicabilidade":"restrita_locacao"}'] --saida <jsonl>

Imprime em stdout um JSON com estatisticas (faltantes, revogados, vetados, anotacoes).
"""
import argparse
import codecs
import json
import re

from bs4 import BeautifulSoup

DATA_COLETA = "2026-11-09"


def _latin1_fallback(e):
    return (e.object[e.start:e.end].decode("latin-1"), e.end)


codecs.register_error("latin1fb", _latin1_fallback)

STRIKE_TAGS = {"strike", "s", "del"}
BR_SENTINEL = " "

# Anotacoes editoriais do Planalto: "(Redacao dada pela Lei ...)", "(Incluido ...)", "(Vide ...)" etc.
ANNOT_RE = re.compile(
    r"\((?:Reda[cç][aã]o|Inclu[ií]d[oa]s?|Acrescid[oa]s?|Acrescentad[oa]s?|Vide\b|Vig[eê]ncia|"
    r"Revogad[oa]s?|VETAD[OA]S?|Vetad[oa]s?|Renumerad[oa]s?|Alterad[oa]s?|Suprimid[oa]s?|"
    r"Express[aã]o|Regulament[oa]|Produ[cç][aã]o|Include|Inclu[ií]da)[^()]*\)"
)
REF_RE = re.compile(
    r"(?:Lei Complementar|Lei|Medida Provis[oó]ria|Decreto-Lei|Decreto|Emenda Constitucional)"
    r"\s+(?:n\s?[º°o]\.?\s*)?\d[\d.\-/]*(?:,?\s+de\s+[^,;()]*?\d{4})?"
)
# Anotacoes que so marcam situacao, sem referencia a norma: nao entram em alteracoes.
MARCA_PURA_RE = re.compile(r"^(VETADO|Vetado|Vig[eê]ncia|Revogad[oa])\.?$")
ART_RE = re.compile(r"^Art\.\s*(\d{1,4}(?:\.\d{3})?)(?:\s*-\s*([A-Z]))?(?=[\s.º°o]|$)")
ART_NUM_RE = re.compile(r"Art\.\s*(\d{1,4}(?:\.\d{3})?)(?:\s*-\s*([A-Z]))?(?=[\s.º°o]|$)")
HEAD_RE = re.compile(
    r"^(LIVRO|T[ÍI]TULO|CAP[ÍI]TULO|Se[cç][aã]o|SE[CÇ][AÃ]O|Subse[cç][aã]o|SUBSE[CÇ][AÃ]O)"
    r"\s+([IVXLCDM]+\b|[ÚU]NIC[OA]\b|\d+[ºo°]?)"
)
TERM_RE = re.compile(
    r"^(Este texto n[aã]o substitui|Bras[ií]lia,|Senado Federal,|Presid[eê]ncia da Rep[uú]blica|"
    r"Publicad[oa] no|O PRESIDENTE|Mensagem de veto)"
)
# Paragrafo que ficou so com o rotulo depois de tirar a anotacao (ex.: "§ 2º (Revogado ...)").
ROTULO_SOZINHO_RE = re.compile(r"^(§\s*\d+[º°o]?\.?|Par[aá]grafo [uú]nico\.?|[IVXLCDM]+\s*[-–.]?)$")
LEVELS = {"livro": 0, "título": 1, "titulo": 1, "capítulo": 2, "capitulo": 2,
          "seção": 3, "secao": 3, "subseção": 4, "subsecao": 4}
LEVEL_NAMES = ["Livro", "Título", "Capítulo", "Seção", "Subseção"]


def normalizar(s):
    return re.sub(r"\s+", " ", s).strip()


def parse_faixas(spec):
    if spec == "todos":
        return None
    faixas = []
    for parte in spec.split(","):
        parte = parte.strip()
        if "-" in parte:
            a, b = parte.split("-")
            faixas.append((int(a), int(b)))
        else:
            faixas.append((int(parte), int(parte)))
    return faixas


def dentro(base, faixas):
    return faixas is None or any(a <= base <= b for a, b in faixas)


def rotulo_de(m):
    numero = m.group(1).replace(".", "")
    return numero + (f"-{m.group(2)}" if m.group(2) else "")


def remover_riscados(soup):
    """Remove redacoes revogadas (strike/s/del/line-through). Devolve textos riscados (para o relatorio)."""
    alvos = [t for t in soup.find_all(True)
             if t.name in STRIKE_TAGS or "line-through" in (t.get("style") or "").lower()]
    textos = [t.get_text(" ") for t in alvos]
    for t in alvos:
        t.extract()
    return len(alvos), textos


def linhas_do_bloco(p):
    for br in p.find_all("br"):
        br.replace_with(BR_SENTINEL)
    # Sem separador: sup/u/i/font etc. nao podem gerar espacos espurios ("4<sup>o</sup>" -> "4o").
    bruto = p.get_text("")
    segs = [normalizar(s) for s in bruto.split(BR_SENTINEL)]
    return [s for s in segs if s]


def limpar_linha(linha, refs, marcas):
    """Tira anotacoes da linha, guarda referencias em refs e marcas (REVOGADO/VETADO) em marcas."""
    def sub(m):
        inner = normalizar(m.group(0)[1:-1])
        achados = [normalizar(r) for r in REF_RE.findall(inner)]
        if not achados and not MARCA_PURA_RE.match(inner):
            achados = [inner]
        achados = [re.sub(r"n\s([º°o])", r"n\1", r) for r in achados]
        for r in achados:
            if r not in refs:
                refs.append(r)
        if re.search(r"Revogad", inner):
            marcas.add("revogado")
        if re.search(r"VETAD|Vetad", inner):
            marcas.add("vetado")
        return " "
    return normalizar(ANNOT_RE.sub(sub, linha))


def ordinal_limpo(texto):
    # Superescrito "o" de ordinal (ex.: "2o", "1o") vira "º".
    texto = re.sub(r"(?<=\d)o(?=\s|,|\.|;|\)|$)", "º", texto)
    return re.sub(r"((?:§|Art\.)\s*\d+)\s?o(?=\s|,|\.|;|\)|$)", r"\1º", texto)


def extrair(args):
    faixas = parse_faixas(args.faixas)
    with open(args.arquivo, "rb") as fh:
        html = fh.read().decode("cp1252", errors="latin1fb")
    soup = BeautifulSoup(html, "html.parser")

    n_riscados, textos_riscados = remover_riscados(soup)
    numeros_riscados = set()
    for txt in textos_riscados:
        for m in ART_NUM_RE.finditer(txt):
            numeros_riscados.add(rotulo_de(m))

    arts = []
    estrutura = {}
    atual = None
    encerrado = False
    refs_todas = []

    def fechar():
        nonlocal atual
        if atual is not None:
            arts.append(atual)
        atual = None

    for p in soup.find_all("p"):
        if encerrado:
            break
        linhas = linhas_do_bloco(p)
        if not linhas:
            continue
        # Assinatura/fecho ("Senado Federal, ...") pode vir na mesma <p> do ultimo artigo: corta ali.
        corte = next((i for i, l in enumerate(linhas) if TERM_RE.match(l)), None)
        if corte is not None and (arts or atual is not None):
            linhas = linhas[:corte]
            encerrado = True
            if not linhas:
                continue
        primeira = linhas[0]
        # Cabecalho do Planalto ("Este texto nao substitui...") vem antes do texto; so encerra apos artigos.
        if TERM_RE.match(primeira) and (arts or atual is not None):
            fechar()
            encerrado = True
            break

        mh = HEAD_RE.match(primeira)
        if mh and not ART_RE.match(primeira):
            fechar()
            nivel = LEVELS[mh.group(1).lower()]
            num = mh.group(2)
            if re.fullmatch(r"[IVXLCDM]+", num):
                num_fmt = num
            else:
                num_fmt = num.capitalize()  # "Único", "1º"
            estrutura[nivel] = f"{LEVEL_NAMES[nivel]} {num_fmt}"
            for k in [k for k in estrutura if k > nivel]:
                del estrutura[k]
            continue

        ma = ART_RE.match(primeira)
        if ma:
            fechar()
            atual = {
                "rotulo": rotulo_de(ma),
                "base": int(ma.group(1).replace(".", "")),
                "estrutura": " > ".join(estrutura[k] for k in sorted(estrutura)),
                "linhas": [],
                "alteracoes": [],
                "marcas": set(),
            }

        if atual is None:
            continue  # preambulo da lei fora de artigo

        for linha in linhas:
            refs, marcas = [], set()
            limpo = limpar_linha(linha, refs, marcas)
            refs_todas.extend(refs)
            # Linha que restou so com rotulo (ex.: "§ 2º") e perdeu o texto para anotacao: descarta.
            if refs or marcas:
                if not limpo or ROTULO_SOZINHO_RE.match(limpo):
                    atual["alteracoes"].extend(r for r in refs if r not in atual["alteracoes"])
                    atual["marcas"] |= marcas
                    continue
            if limpo:
                atual["linhas"].append(limpo)
            atual["alteracoes"].extend(r for r in refs if r not in atual["alteracoes"])
            atual["marcas"] |= marcas
    fechar()

    finais, vistos, duplicados, revogados, vetados, vazios = [], set(), [], [], [], []
    for a in arts:
        if not dentro(a["base"], faixas):
            continue
        linhas = [ordinal_limpo(x) for x in a["linhas"]]
        texto = "\n".join(linhas)
        corpo = re.sub(r"^Art\.\s*\d[\d.]*(?:-[A-Z])?\s*[º°.]*\s*", "", texto).strip(" .\n")
        if not corpo:
            if "revogado" in a["marcas"]:
                revogados.append(a["rotulo"])
            elif "vetado" in a["marcas"]:
                vetados.append(a["rotulo"])
            else:
                vazios.append(a["rotulo"])
            continue
        if a["rotulo"] in vistos:
            duplicados.append(a["rotulo"])
            continue
        vistos.add(a["rotulo"])
        finais.append({
            "id": f"{args.slug}-art-{a['rotulo'].lower()}",
            "fonte": args.slug,
            "norma": args.norma,
            "artigo": a["rotulo"],
            "estrutura": a["estrutura"],
            "texto": texto,
            "alteracoes": a["alteracoes"],
            "url": args.url,
            "data_coleta": DATA_COLETA,
            **(json.loads(args.extra) if args.extra else {}),
        })

    with open(args.saida, "w", encoding="utf-8", newline="\n") as fh:
        for r in finais:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    bases = sorted({int(re.match(r"\d+", r["artigo"]).group(0)) for r in finais})
    if faixas is None:
        esperados = set(range(1, bases[-1] + 1)) if bases else set()
    else:
        esperados = set()
        for a, b in faixas:
            esperados.update(range(a, b + 1))
    relatorio = {
        "slug": args.slug,
        "registros": len(finais),
        "riscados_removidos": n_riscados,
        "faixas": args.faixas,
        "faltantes_numeros_base": sorted(esperados - set(bases)),
        "revogados_no_texto": sorted(revogados),
        "vetados": sorted(vetados),
        "vazios_sem_marca": sorted(vazios),
        "duplicados_descartados": sorted(duplicados),
        "so_em_texto_riscado_sem_versao_vigente": sorted(numeros_riscados - {r["artigo"] for r in finais}),
        "anotacoes_distintas": len(set(refs_todas)),
        "encerrou_em_termo": encerrado,
        "sufixados": sorted(r["artigo"] for r in finais if "-" in r["artigo"]),
    }
    print(json.dumps(relatorio, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--arquivo", required=True)
    ap.add_argument("--norma", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--faixas", required=True, help='"todos" ou lista como 113,166-184')
    ap.add_argument("--extra", default="", help="JSON com campos extras (ex.: aplicabilidade)")
    ap.add_argument("--saida", required=True)
    extrair(ap.parse_args())
