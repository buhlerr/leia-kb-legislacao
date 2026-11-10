"""Aplica as correcoes curadas na matriz de riscos (levantamento/matriz-riscos.jsonl).

Le a matriz em UTF-8, aplica as correcoes por id e reescreve o arquivo em UTF-8, um objeto
por linha, mantendo a ordem. A aplicacao e idempotente: rodar duas vezes nao duplica normas
nem o registro R185.

Uso: python3 aplicar_correcoes_matriz.py [caminho-da-matriz]
"""
import json
import re
import sys

MATRIZ_PADRAO = "levantamento/matriz-riscos.jsonl"
CHAVE_NORMA = ("norma", "artigo", "por_que")

NORMA_CPC_FORO = {
    "norma": "Lei 13.105/2015 (CPC)",
    "artigo": "63, §§ 1º e 5º",
    "status": "ausente_confirmada",
    "por_que": "Eleição de foro sem pertinência com domicílio das partes ou com o negócio é "
               "abusiva; se o foro for o da situação do imóvel, o risco é baixo.",
}
NORMA_CPC_784_VIII = {
    "norma": "Lei 13.105/2015 (CPC)",
    "artigo": "784, VIII",
    "status": "ausente_confirmada",
    "por_que": "Crédito documentalmente comprovado de aluguel e encargos é título executivo "
               "extrajudicial, sem exigir testemunhas.",
}
NORMA_SUMULA_404 = {
    "norma": "Súmulas do STJ",
    "artigo": "Súmula 404",
    "status": "ausente_confirmada",
    "por_que": "Dispensa o aviso de recebimento na comunicação ao consumidor; a notificação "
               "prévia segue a Súmula 359.",
}
OBSERVACAO_SEGURO = (
    "Os arts. 757 a 802 do Código Civil foram revogados pela Lei 15.040/2024, em vigor um ano "
    "após a publicação. Contratos anteriores podem seguir o regime antigo; questão de direito "
    "intertemporal a validar."
)
R185 = {
    "id": "R185",
    "tema": "alienacao_e_preferencia",
    "subtema": "Alienação fiduciária anterior",
    "risco": "Imóvel objeto de alienação fiduciária anterior, com locação por mais de um ano sem "
             "concordância escrita do credor fiduciário: a locação é ineficaz perante ele e o "
             "locatário pode ter de desocupar em prazo curto.",
    "parte_prejudicada": "locatario",
    "criticidade_sugerida": "vermelho",
    "normas": [
        {
            "norma": "Lei 9.514/1997",
            "artigo": "27, § 7º",
            "status": "ausente_confirmada",
            "por_que": "Permite denunciar a locação com trinta dias para desocupação, salvo "
                       "aquiescência escrita do fiduciário.",
        },
        {
            "norma": "Lei 9.514/1997",
            "artigo": "37-B",
            "status": "ausente_confirmada",
            "por_que": "Declara ineficaz perante o fiduciário a locação por prazo superior a um "
                       "ano sem concordância escrita.",
        },
    ],
    "precisa_jurisprudencia": False,
    "questao_jurisprudencial": "",
    "aparece_em_minutas": [],
}

NORMAS_POR_ID = {
    "R138": [NORMA_CPC_FORO],
    "R024": [NORMA_CPC_784_VIII],
    "R093": [NORMA_CPC_784_VIII],
    "R113": [NORMA_CPC_784_VIII],
    "R162": [NORMA_CPC_784_VIII],
}
PARTE_FIADOR = ["R041", "R042", "R044", "R045"]
COM_OBSERVACAO = ["R058", "R059", "R060"]
TRECHO_404_AR = re.compile(r"notifica[çc][ãa]o por AR \(S[uú]mula 404, a confirmar\)")


def carregar(caminho):
    with open(caminho, encoding="utf-8") as fh:
        return [json.loads(linha) for linha in fh if linha.strip()]


def adicionar_norma(registro, norma):
    chave = tuple(norma[c] for c in CHAVE_NORMA)
    if any(tuple(n[c] for c in CHAVE_NORMA) == chave for n in registro["normas"]):
        return 0
    registro["normas"].append(dict(norma))
    return 1


def reescrever_404(texto):
    """Troca o trecho que exige AR pela informacao de que a Sumula 404 o dispensa."""
    if not texto or not re.search(r"S[uú]mula 404", texto) or "dispens" in texto.lower():
        return texto
    if not re.search(r"\bAR\b|aviso de recebimento", texto):
        return texto
    novo = TRECHO_404_AR.sub("notificação prévia, dispensado o AR pela Súmula 404", texto)
    if novo != texto:
        return novo
    return re.sub(r"\(S[uú]mula 404[^)]*\)", "(a Súmula 404 dispensa o AR)", texto)


def aplicar(registros):
    por_id = {r["id"]: r for r in registros}
    exigidos = set(NORMAS_POR_ID) | set(PARTE_FIADOR) | set(COM_OBSERVACAO) | {"R089"}
    faltando = sorted(i for i in exigidos if i not in por_id)
    if faltando:
        raise SystemExit(f"erro: id nao encontrado na matriz: {', '.join(faltando)}")

    resumo = {
        "criticidade_sugerida": 0,
        "normas_adicionadas": 0,
        "parte_prejudicada": 0,
        "observacao": 0,
        "sumula_404_reescrita": 0,
        "registro_R185": 0,
    }

    if por_id["R138"]["criticidade_sugerida"] != "amarelo":
        por_id["R138"]["criticidade_sugerida"] = "amarelo"
        resumo["criticidade_sugerida"] += 1

    for rid, normas in NORMAS_POR_ID.items():
        for norma in normas:
            resumo["normas_adicionadas"] += adicionar_norma(por_id[rid], norma)

    resumo["normas_adicionadas"] += adicionar_norma(por_id["R089"], NORMA_SUMULA_404)
    r089 = por_id["R089"]
    for campo in ("risco", "questao_jurisprudencial"):
        novo = reescrever_404(r089.get(campo, ""))
        if novo != r089.get(campo, ""):
            r089[campo] = novo
            resumo["sumula_404_reescrita"] += 1

    for rid in PARTE_FIADOR:
        if por_id[rid]["parte_prejudicada"] != "fiador":
            por_id[rid]["parte_prejudicada"] = "fiador"
            resumo["parte_prejudicada"] += 1

    for rid in COM_OBSERVACAO:
        if por_id[rid].get("observacao") != OBSERVACAO_SEGURO:
            por_id[rid]["observacao"] = OBSERVACAO_SEGURO
            resumo["observacao"] += 1

    if "R185" not in por_id:
        registros.append(dict(R185))
        resumo["registro_R185"] += 1

    return resumo


def main(caminho):
    registros = carregar(caminho)
    resumo = aplicar(registros)
    with open(caminho, "w", encoding="utf-8", newline="\n") as fh:
        for r in registros:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps({"alteracoes": resumo, "total": sum(resumo.values())},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else MATRIZ_PADRAO)
