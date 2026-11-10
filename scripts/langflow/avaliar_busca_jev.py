import base64, json, uuid, urllib.request
import lf

ids = json.load(open("ids.json"))
t = lf.token()
aid = open("cf_account.txt").read().strip()
Q = [json.loads(l) for l in open(r"D:\dev\leia-kb-legislacao\avaliacao\perguntas-v1.jsonl", encoding="utf-8") if l.strip()]

CODE = r'''
import base64, json
from lfx.custom.custom_component.component import Component
from lfx.io import Output, SecretStrInput, StrInput
from lfx.schema.data import Data
from lfx.utils.connection_string_parser import transform_connection_string
from langchain_community.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings
import sqlalchemy as sa

SQL = """
WITH q AS (SELECT to_tsquery('portuguese', replace(plainto_tsquery('portuguese', :p)::text, ' & ', ' | ')) AS q)
SELECT e.document, e.cmetadata->>'id', ts_rank(to_tsvector('portuguese', e.document), q.q, 1)
FROM langchain_pg_embedding e JOIN langchain_pg_collection c ON c.uuid = e.collection_id, q
WHERE c.name = 'legislacao_v2' AND to_tsvector('portuguese', e.document) @@ q.q
ORDER BY 3 DESC LIMIT 40
"""


INSTR = "`consulta` traz uma duvida juridica sobre locacao de imovel. `trecho` e um dispositivo de lei ou sumula. O dispositivo em `trecho` e o que regula especificamente a duvida de `consulta`?"
CRIT = {"true": "O dispositivo estabelece a regra especifica que responde a duvida.", "false": "O dispositivo trata apenas de tema parecido, sem responder a duvida."}


def jev(comp, pergunta, itens):
    import time, urllib.error, urllib.request
    from concurrent.futures import ThreadPoolExecutor

    def um(it):
        corpo = json.dumps({"model": "jev-1.14.0", "state": {"consulta": pergunta, "trecho": it[0]}, "questions": {"regula": {"type": "noul", "instructions": INSTR, "criteria": CRIT}}}).encode("utf-8")
        for t in range(6):
            try:
                req = urllib.request.Request("https://api.typesafe.ai/v1/systemone", data=corpo, method="POST", headers={"Authorization": "Bearer " + comp.jev, "Content-Type": "application/json", "User-Agent": "leia-kb-avaliacao"})
                with urllib.request.urlopen(req, timeout=30) as r:
                    d = json.load(r)
                return d["answers"]["regula"]["noul"], d["usage"]["input_tokens"]
            except urllib.error.HTTPError as e:
                if e.code not in (429, 529) or t == 5:
                    raise
                time.sleep(1 + t)
    with ThreadPoolExecutor(max_workers=8) as ex:
        res = list(ex.map(um, itens))
    return [x[0] for x in res], sum(x[1] for x in res)


def pais(seq):
    out = []
    for x in seq:
        if x not in out:
            out.append(x)
    return out[:10]


def rrf(vec, fts, peso, k=60):
    s, pai = {}, {}
    for i, (doc, p) in enumerate(vec):
        s[doc] = s.get(doc, 0) + 1 / (k + i + 1)
        pai[doc] = p
    for i, (doc, p) in enumerate(fts):
        s[doc] = s.get(doc, 0) + peso / (k + i + 1)
        pai[doc] = p
    return pais(pai[d] for d in sorted(s, key=s.get, reverse=True))


class HibridoTemp(Component):
    display_name = "HibridoTemp"
    name = "HibridoTemp"
    inputs = [
        SecretStrInput(name="url", display_name="url", value="PGVECTOR_CONTRACTS_URL"),
        SecretStrInput(name="key", display_name="key", value="CLOUDFLARE_WORKERS_AI_TOKEN"),
        SecretStrInput(name="jev", display_name="jev", value="TYPESAFE_API_KEY"),
        StrInput(name="base", display_name="base", value=""),
        StrInput(name="payload", display_name="payload", value=""),
    ]
    outputs = [Output(display_name="r", name="r", method="r")]

    def r(self) -> Data:
        qs = json.loads(base64.b64decode(self.payload).decode("utf-8"))
        conn = transform_connection_string(self.url)
        emb = OpenAIEmbeddings(model="@cf/baai/bge-m3", base_url=self.base, api_key=self.key, check_embedding_ctx_length=False, chunk_size=40)
        store = PGVector(connection_string=conn, embedding_function=emb, collection_name="legislacao_v2")
        engine = sa.create_engine(conn)
        out = []
        with engine.connect() as c:
            for q in qs:
                vres = store.similarity_search_with_score(q["pergunta"], k=40)
                vec = [(d.page_content, d.metadata["id"]) for d, _ in vres]
                scores, tokens = jev(self, q["pergunta"], vec)
                ordem = sorted(range(len(vec)), key=lambda i: -scores[i])
                rr40 = [vec[i] for i in ordem]
                ordem15 = sorted(range(15), key=lambda i: -scores[i])
                rr15 = [vec[i] for i in ordem15]
                listas = [pais(p for _, p in vec), pais(p for _, p in rr40), pais(p for _, p in rr15 + vec[15:]), rrf(vec, rr40, 1.0), rrf(vec, rr40, 0.5)]
                ranks = [next((i + 1 for i, x in enumerate(l) if x in q["esperado"]), 0) for l in listas]
                out.append([q["id"], *ranks, round(float(max(scores)), 4), tokens, listas[1][0] if not 1 <= ranks[1] <= 3 else ""])
        return Data(data={"text": json.dumps(out, ensure_ascii=True)})
'''

d = lf.call("POST", "/api/v1/custom_component", t, {"code": CODE, "frontend_node": None})["data"]
tp = d["template"]
tp["url"]["value"] = "PGVECTOR_CONTRACTS_URL"
tp["url"]["load_from_db"] = True
tp["key"]["value"] = "CLOUDFLARE_WORKERS_AI_TOKEN"
tp["key"]["load_from_db"] = True
tp["jev"]["value"] = "TYPESAFE_API_KEY"
tp["jev"]["load_from_db"] = True
tp["base"]["value"] = f"https://api.cloudflare.com/client/v4/accounts/{aid}/ai/v1"
tp["payload"]["value"] = base64.b64encode(json.dumps([{"id": q["id"], "pergunta": q["pergunta"], "esperado": q["esperado"]} for q in Q], ensure_ascii=False).encode("utf-8")).decode("ascii")
nid = "HibridoTemp-" + uuid.uuid4().hex[:5]
n = {"id": nid, "type": "genericNode", "position": {"x": 0, "y": 0}, "data": {"id": nid, "type": "HibridoTemp", "node": d}}
job = lf.call("POST", f"/api/v1/build/{ids['ingest']}/flow", t, {"data": {"nodes": [n], "edges": [], "viewport": {"x": 0, "y": 0, "zoom": 1}}})["job_id"]
req = urllib.request.Request(lf.BASE + f"/api/v1/build/{job}/events?stream=true", headers={**lf.UA, "Authorization": "Bearer " + t})
bd = None
with urllib.request.urlopen(req, timeout=500) as r:
    for raw in r:
        if not raw.strip():
            continue
        ev = json.loads(raw)
        if ev.get("event") == "end_vertex":
            bd = ev["data"]["build_data"]
        elif ev.get("event") == "end":
            break
if not bd["valid"]:
    print(json.dumps(bd["data"]["outputs"], ensure_ascii=True)[:1500].replace(aid, "<acct>"))
    raise SystemExit(1)
rows = json.loads(bd["data"]["outputs"]["r"]["message"]["text"])
assert len(rows) == len(Q)
by = {r[0]: r for r in rows}
gab = [q for q in Q if q["esperado"]]
neg = [q for q in Q if not q["esperado"]]
NOMES = {"vetorial": 1, "jev_40": 2, "jev_15": 3, "blend_1.0": 4, "blend_0.5": 5}


def metr(items, col):
    n = len(items)
    rk = [by[q["id"]][col] for q in items]
    return {"n": n, "top1": round(sum(1 for r in rk if r == 1) / n, 3), "top3": round(sum(1 for r in rk if 1 <= r <= 3) / n, 3), "top5": round(sum(1 for r in rk if 1 <= r <= 5) / n, 3), "top10": round(sum(1 for r in rk if 1 <= r <= 10) / n, 3), "mrr": round(sum(1 / r for r in rk if r) / n, 3)}


res = {
    "variantes": {k: metr(gab, c) for k, c in NOMES.items()},
    "por_tipo": {k: {v: metr([q for q in gab if q["tipo"] == k], c)["top3"] for v, c in NOMES.items()} for k in sorted({q["tipo"] for q in gab})},
    "por_categoria_rerank_40": {k: metr([q for q in gab if q["categoria"] == k], 2)["top3"] for k in sorted({q["categoria"] for q in gab})},
    "tokens_jev_total": sum(r[7] for r in rows),
    "negativas_score_rerank": {q["id"]: by[q["id"]][6] for q in neg},
    "score_rerank_com_gabarito_min": min(by[q["id"]][6] for q in gab),
    "score_rerank_com_gabarito_mediana": sorted(by[q["id"]][6] for q in gab)[len(gab) // 2],
    "fora_do_top3_rerank_40": [(q["id"], by[q["id"]][2], by[q["id"]][8]) for q in gab if not 1 <= by[q["id"]][2] <= 3],
    "por_pergunta": rows,
}
json.dump(res, open(r"D:\dev\leia-kb-legislacao\avaliacao\resultado-v5-jev.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "por_pergunta"}, ensure_ascii=True)[:6000])
print("q70", by["q70"][:6], "q65", by["q65"][:6], "q06", by["q06"][:6], "q10", by["q10"][:6])
