import re

_P = r"[A-ZÀ-Ý][A-Za-zÀ-ÿ'´-]+"
_L = r"(?:\s+(?:de|da|do|dos|das|e|DE|DA|DO|DOS|DAS|E))?"
_NC = rf"{_P}(?:{_L}\s+{_P}){{1,7}}"
_Q = r"(?i:brasileir[oa]|portugues[a]?|argentin[oa]|uruguai[oa]|estrangeir[oa]|naturalizad[oa]|solteir[oa]|casad[oa]|divorciad[oa]|vi[úu]v[oa]|separad[oa]|maior\s+e\s+capaz)"
_R = r"(?i:nome(?:\s+completo)?|locador[a]?|locat[áa]ri[oa]|fiador[a]?|c[ôo]njuge|testemunha(?:\s*\d)?|propriet[áa]ri[oa]|inquilin[oa]|representante(?:\s+legal)?|respons[áa]vel|assinante)"
_NAME_RULES = [re.compile(rf"({_NC})(?=\s*,\s*{_Q})"), re.compile(rf"{_R}\s*:\s*({_NC})"), re.compile(rf"(?i:\bSr[a]?\.|\bSenhor[a]?)\s+({_NC})")]
_IGNORE = re.compile(r"(?i)^(contrato|cl[áa]usula|locador|locat[áa]ri|fiador|parte|partes|pessoa|imobili[áa]ria|administradora|empresa|ltda|s\.?a\.?)\b")
_RULES = [
    (re.compile(r"(?i)\b(residente\s+e\s+domiciliad[oa]\s+(?:na|no|em|à|a)\s+)[^;\n]{5,180}"), r"\1[ENDERECO]"),
    (re.compile(r"(?i)\b(?:rua|r\.|avenida|av\.|alameda|travessa|estrada|rodovia|pra[çc]a|largo)\s+[^,\n]{2,80},?\s*(?:n[º°o.]*\s*)?\d{1,6}\b"), "[ENDERECO]"),
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


import hashlib
from lfx.custom.custom_component.component import Component
from lfx.io import HandleInput, Output, StrInput
from lfx.schema.data import Data


class MascararDadosPessoais(Component):
    display_name = "Mascarar Dados Pessoais"
    description = "Mascara nome, CPF, CNPJ, RG, e-mail, telefone, endereco, CEP e dados bancarios antes dos embeddings."
    icon = "shield"
    name = "MascararDadosPessoais"

    inputs = [
        HandleInput(name="input_value", display_name="Documento", input_types=["Message", "Data", "JSON"], required=True),
        StrInput(name="doc_name", display_name="Nome do documento", info="Apelido gravado no banco. Vazio: gera um codigo a partir do nome do arquivo.", value=""),
    ]
    outputs = [Output(display_name="Documento mascarado", name="masked", method="mask")]

    def mask(self) -> Data:
        doc = self.input_value
        texto = doc.get_text() if hasattr(doc, "get_text") else getattr(doc, "text", str(doc))
        origem = (getattr(doc, "data", {}) or {}).get("filename", "documento")
        ext = origem.rsplit(".", 1)[-1] if "." in origem else "txt"
        nome = self.doc_name or "documento-" + hashlib.sha256(origem.encode("utf-8")).hexdigest()[:8] + "." + ext
        self.status = f"{nome}: {len(texto)} caracteres"
        return Data(data={"text": mascarar(texto), "filename": nome})
