"""Converte a jurisprudencia curada em registros da base (saida/jurisprudencia.jsonl).

Le levantamento/jurisprudencia-curada.jsonl e saida/sumulas-stj.jsonl. Mantem apenas itens
oficiais, vigentes, de prioridade alta ou media e de fonte que nao seja noticia institucional
do STJ; sumulas cujo numero ja exista na base de sumulas sao ignoradas. Imprime quantos
registros entraram e quantos ficaram de fora, por motivo.

Uso: python3 converter_jurisprudencia.py
"""
import json
import re

ENTRADA = "levantamento/jurisprudencia-curada.jsonl"
SUMULAS = "saida/sumulas-stj.jsonl"
SAIDA = "saida/jurisprudencia.jsonl"
DATA_COLETA = "2026-11-09"
PRIORIDADES = ("alta", "media")
FONTE_EXCLUIDA = "noticia_institucional_stj"
TIPOS_LEGIVEIS = {
    "sumula": "Súmula",
    "repercussao_geral": "Repercussão geral",
    "tema_repetitivo": "Tema repetitivo",
    "tema_repetitivo_afetado": "Tema repetitivo afetado",
    "acordao": "Acórdão",
    "tese": "Tese",
}


def carregar(caminho):
    with open(caminho, encoding="utf-8") as fh:
        return [json.loads(linha) for linha in fh if linha.strip()]


def normalizar(numero):
    return re.sub(r"[^0-9a-z]+", "-", numero.lower()).strip("-")


def nome_tipo(tipo):
    return TIPOS_LEGIVEIS.get(tipo, tipo.replace("_", " "))


def numeros_da_base(registros):
    numeros = set()
    for r in registros:
        m = re.search(r"S[uú]mula\s*(\d+)", r["artigo"])
        if m:
            numeros.add(m.group(1))
    return numeros


def montar_registro(item):
    tribunal = item["tribunal"]
    tipo = item["tipo"]
    numero = item["numero"]
    return {
        "id": f"jurisprudencia-{tribunal.lower()}-{tipo}-{normalizar(numero)}",
        "fonte": "jurisprudencia",
        "norma": f"{tribunal} {nome_tipo(tipo)} {numero}",
        "artigo": numero,
        "estrutura": "",
        "texto": item["tese_literal"],
        "alteracoes": [],
        "url": item["url"],
        "data_coleta": DATA_COLETA,
        "prioridade": item["prioridade"],
        "riscos": item.get("riscos", []),
    }


def motivo_exclusao(item, sumulas_na_base):
    if item.get("oficial") is not True:
        return "nao_oficial"
    if item.get("situacao") != "vigente":
        return "situacao_diferente_de_vigente"
    if item.get("prioridade") not in PRIORIDADES:
        return "prioridade_baixa"
    if item.get("fonte") == FONTE_EXCLUIDA:
        return "fonte_noticia_institucional"
    if item["tipo"] == "sumula" and item["numero"] in sumulas_na_base:
        return "sumula_ja_na_base"
    return None


def main():
    curados = carregar(ENTRADA)
    sumulas_na_base = numeros_da_base(carregar(SUMULAS))

    registros, excluidos, ids = [], {}, set()
    for item in curados:
        motivo = motivo_exclusao(item, sumulas_na_base)
        if motivo:
            excluidos[motivo] = excluidos.get(motivo, 0) + 1
            continue
        registro = montar_registro(item)
        if registro["id"] in ids:
            raise SystemExit(f"erro: id duplicado: {registro['id']}")
        ids.add(registro["id"])
        registros.append(registro)

    with open(SAIDA, "w", encoding="utf-8", newline="\n") as fh:
        for r in registros:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(json.dumps({"lidos": len(curados), "entraram": len(registros),
                      "ficaram_de_fora": sum(excluidos.values()),
                      "motivos": excluidos}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
