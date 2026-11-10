import glob, json, uuid, urllib.request
import lf

ids = json.load(open("ids.json"))
t = lf.token()
aid = open("cf_account.txt").read().strip()

recs = [json.loads(l) for p in sorted(glob.glob(r"D:\dev\leia-kb-legislacao\saida\*.jsonl")) for l in open(p, encoding="utf-8") if l.strip()]
assert len(recs) == 330, len(recs)

CODE = r'''
import json
from lfx.custom.custom_component.component import Component
from lfx.io import Output, SecretStrInput, StrInput
from lfx.schema.data import Data
from lfx.utils.connection_string_parser import transform_connection_string
from langchain_community.vectorstores import PGVector
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
import sqlalchemy as sa

KB = "legislacao-v1"
PROBES = [
    "o aluguel pode ser reajustado a cada seis meses", "contrato com obrigacao desproporcional por inexperiencia", "imovel alugado que esta alienado fiduciariamente ao banco", "clausula elegendo foro em cidade sem relacao com as partes", "precisa de aviso de recebimento para negativar o inquilino", "a casa do fiador pode ser penhorada em locacao residencial", "prazo para cobrar alugueis atrasados", "arbitragem em contrato de adesao",
    "multa quando o locatario devolve o imovel antes do prazo",
    "fiador responde por aditamento que nao assinou",
    "reducao de clausula penal manifestamente excessiva",
    "renuncia a indenizacao por benfeitorias",
    "penhora do bem de familia do fiador",
]


class KbLoadTemp(Component):
    display_name = "KbLoadTemp"
    name = "KbLoadTemp"
    inputs = [
        SecretStrInput(name="url", display_name="url", value="PGVECTOR_CONTRACTS_URL"),
        SecretStrInput(name="key", display_name="key", value="CLOUDFLARE_WORKERS_AI_TOKEN"),
        StrInput(name="base", display_name="base", value=""),
        StrInput(name="payload", display_name="payload", value=""),
    ]
    outputs = [Output(display_name="r", name="r", method="r")]

    def r(self) -> Data:
        conn = transform_connection_string(self.url)
        recs = json.loads(__import__("base64").b64decode(self.payload).decode("utf-8"))
        emb = OpenAIEmbeddings(model="@cf/baai/bge-m3", base_url=self.base, api_key=self.key, check_embedding_ctx_length=False, chunk_size=10)
        docs = []
        for r in recs:
            citacao = r["norma"] if r["fonte"] == "jurisprudencia" else r["norma"] + ", " + (r["artigo"] if r["artigo"].startswith("Súmula") else "art. " + r["artigo"])
            meta = {"kb": KB, "citacao": citacao, "id": r["id"], "fonte": r["fonte"], "norma": r["norma"], "artigo": r["artigo"], "estrutura": r.get("estrutura") or "", "alteracoes": r.get("alteracoes") or [], "url": r["url"], "data_coleta": r["data_coleta"]}
            if r.get("aplicabilidade"):
                meta["aplicabilidade"] = r["aplicabilidade"]
            docs.append(Document(page_content=citacao + chr(10) + r["texto"], metadata=meta))
        engine = sa.create_engine(conn)
        with engine.begin() as c:
            c.execute(sa.text("DELETE FROM langchain_pg_embedding WHERE cmetadata->>'kb' = :k"), {"k": KB})
        store = PGVector.from_documents(embedding=emb, documents=docs, collection_name="legislacao", connection_string=conn)
        with engine.begin() as c:
            n = c.execute(sa.text("SELECT count(*) FROM langchain_pg_embedding WHERE cmetadata->>'kb' = :k"), {"k": KB}).scalar()
            if n != len(docs):
                raise ValueError(f"contagem divergente: {n} != {len(docs)}")
            removed = c.execute(sa.text("DELETE FROM langchain_pg_embedding WHERE cmetadata->>'filename' = 'cdc-2013.pdf'")).rowcount
            rows = c.execute(sa.text("SELECT c.name, coalesce(e.cmetadata->>'fonte', e.cmetadata->>'filename'), count(*), max(length(e.document)) FROM langchain_pg_embedding e JOIN langchain_pg_collection c ON c.uuid = e.collection_id GROUP BY 1, 2 ORDER BY 1, 2")).fetchall()
        probes = {q: [d.metadata.get("citacao") for d in store.similarity_search(q, k=3)] for q in PROBES}
        return Data(data={"text": json.dumps({"inseridos": n, "cdc_antigo_removidos": removed, "rows": [list(r) for r in rows], "probes": probes}, ensure_ascii=True)})
'''

d = lf.call("POST", "/api/v1/custom_component", t, {"code": CODE, "frontend_node": None})["data"]
tp = d["template"]
tp["url"]["value"] = "PGVECTOR_CONTRACTS_URL"
tp["url"]["load_from_db"] = True
tp["key"]["value"] = "CLOUDFLARE_WORKERS_AI_TOKEN"
tp["key"]["load_from_db"] = True
tp["base"]["value"] = f"https://api.cloudflare.com/client/v4/accounts/{aid}/ai/v1"
import base64
tp["payload"]["value"] = base64.b64encode(json.dumps(recs, ensure_ascii=False).encode("utf-8")).decode("ascii")
nid = "KbLoadTemp-" + uuid.uuid4().hex[:5]
n = {"id": nid, "type": "genericNode", "position": {"x": 0, "y": 0}, "data": {"id": nid, "type": "KbLoadTemp", "node": d}}
job = lf.call("POST", f"/api/v1/build/{ids['ingest']}/flow", t, {"data": {"nodes": [n], "edges": [], "viewport": {"x": 0, "y": 0, "zoom": 1}}})["job_id"]
req = urllib.request.Request(lf.BASE + f"/api/v1/build/{job}/events?stream=true", headers={**lf.UA, "Authorization": "Bearer " + t})
with urllib.request.urlopen(req, timeout=500) as r:
    for raw in r:
        if not raw.strip():
            continue
        ev = json.loads(raw)
        if ev.get("event") == "end_vertex":
            bd = ev["data"]["build_data"]
            out = json.dumps(bd["data"]["outputs"], ensure_ascii=True)
            print("valid", bd["valid"])
            print(out[:3500].replace(aid, "<acct>"))
        elif ev.get("event") == "end":
            break
