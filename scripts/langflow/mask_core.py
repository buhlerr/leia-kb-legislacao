import re

_P = r"[A-ZÀ-Ý][A-Za-zÀ-ÿ'´-]+"
_L = r"(?:\s+(?:de|da|do|dos|das|e|DE|DA|DO|DOS|DAS|E))?"
_NC = rf"{_P}(?:{_L}\s+{_P}){{1,7}}"
_Q = r"(?i:brasileir[oa]|portugues[a]?|argentin[oa]|uruguai[oa]|estrangeir[oa]|naturalizad[oa]|solteir[oa]|casad[oa]|divorciad[oa]|vi[úu]v[oa]|separad[oa]|maior\s+e\s+capaz)"
_R = r"(?i:nome(?:\s+completo)?|locador[a]?|locat[áa]ri[oa]|fiador[a]?|c[ôo]njuge|testemunha(?:\s*\d)?|propriet[áa]ri[oa]|inquilin[oa]|representante(?:\s+legal)?|respons[áa]vel|assinante)"
_NAME_RULES = [re.compile(rf"({_NC})(?=\s*,\s*{_Q})"), re.compile(rf"{_R}\s*:\s*({_NC})"), re.compile(rf"(?i:\bSr[a]?\.|\bSenhor[a]?)\s+({_NC})"), re.compile(rf"({_NC})\s*,?\s*(?i:inscrit[oa]\s+no\s+|portador[a]?\s+do\s+)?C\.?P\.?F\b")]
_IGNORE = re.compile(r"(?i)^(contrato|cl[áa]usula|locador|locat[áa]ri|fiador|parte|partes|pessoa|imobili[áa]ria|administradora|empresa|ltda|s\.?a\.?)\b")
_RULES = [
    (re.compile(r"(?i)\b(endere[çc]o(?:\s+completo)?\s*:)\s*[^●]{3,120}?(?=\s*(?:●|\bCNH\b|\bCPF\b|\bRG\b|\[))"), r"\1 [ENDERECO]"),
    (re.compile(r"(?i)\b((?:situad[oa]|localizad[oa])\s+(?:na|no|em|à|a)\s+)(?=[^.;]{0,160}\d)[^.;]{5,160}"), r"\1[ENDERECO]"),
    (re.compile(r"(?i)\b(residente\s+e\s+domiciliad[oa]\s+(?:na|no|em|à|a)\s+)[^;\n]{5,180}"), r"\1[ENDERECO]"),
    (re.compile(r"(?i)\b(?:rua|r\.|avenida|av\.|alameda|travessa|estrada|rodovia|pra[çc]a|largo)\s+[^,]{2,80},?\s*(?:n[º°o.]*\s*)?\d{1,6}\b"), "[ENDERECO]"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[EMAIL]"),
    (re.compile(r"(?<![\d./-])\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}(?![\d/-])"), "[CNPJ]"),
    (re.compile(r"(?<![\d./-])\d{3}[.\s]?\d{3}[.\s]?\d{3}[-\s]?\d{2}(?![\d/-])"), "[CPF]"),
    (re.compile(r"(?i)\b((?:RG|R\.G\.|identidade|C\.I\.)(?:\s*(?:n[º°o.]*|sob o|:))*\s*)[\dXx][\dXx.\-]{3,14}"), r"\1[RG]"),
    (re.compile(r"(?:\+?55[\s-]?)?\(\d{2}\)\s?9?\d{4}[\s-]?\d{4}\b|(?<![\d.,/-])\d{2}\s9\d{4}-\d{4}\b"), "[TELEFONE]"),
    (re.compile(r"(?<![\d-])\d{2}\.?\d{3}-\d{3}(?![\d-])"), "[CEP]"),
    (re.compile(r"(?i)\b((?:ag[êe]ncia|conta(?:\s+corrente)?|c/c)\s*(?:n[º°o.]*|:)?\s*)[\d][\d.\-]{2,}"), r"\1[DADO_BANCARIO]"),
]

def mascarar(texto):
    nomes = set()
    for regra in _NAME_RULES:
        for m in regra.finditer(texto):
            nome = m.group(1).strip()
            if not _IGNORE.match(nome):
                nomes.add(nome)
    for nome in sorted(nomes, key=len, reverse=True):
        padrao = r"\s+".join(re.escape(p) for p in nome.split())
        texto = re.sub(padrao, "[NOME]", texto, flags=re.IGNORECASE)
    for regra, troca in _RULES:
        texto = regra.sub(troca, texto)
    return texto
