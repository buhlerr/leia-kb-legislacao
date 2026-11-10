import base64, collections, glob, json, statistics, uuid, urllib.request
import lf

UNITS_SRC = r'''
import re
NL = chr(10)
def citacao_de(r):
    if r["fonte"] == "jurisprudencia":
        return r["norma"]
    if r["artigo"].startswith("Súmula"):
        return r["norma"] + ", " + r["artigo"]
    return r["norma"] + ", art. " + r["artigo"]

def unidades(r):
    cit = citacao_de(r)
    linhas = [l.strip() for l in r["texto"].split(NL) if l.strip()]
    if r["fonte"] in ("jurisprudencia", "sumulas-stj") or len(linhas) == 1:
        return [("", cit + NL + r["texto"])]
    morto = re.compile(r"^.{0,40}\((revogad[oa]|vetado)\)[.;]?$", re.I)
    caput = linhas[0]
    res = [("", cit + NL + caput)]
    cab, rot, atual = caput, "", None
    def fecha():
        nonlocal atual
        if atual and not morto.match(atual["t"]):
            ctx = atual["ctx"] + NL if atual["ctx"] else ""
            res.append((atual["rot"], cit + atual["rot"] + NL + ctx + atual["t"]))
        atual = None
    for l in linhas[1:]:
        par = re.match(r"(§\s*\d+[º°o]?|Parágrafo único)", l, re.I)
        inc = re.match(r"([IVXLCDM]+)\s*[-–—]\s*", l)
        ali = re.match(r"[a-z]\)", l)
        if ali and atual is not None:
            atual["t"] += NL + l
        elif par:
            fecha()
            cab, rot = l, ", " + re.sub(r"\s+", " ", par.group(1))
            atual = {"rot": rot, "t": l, "ctx": caput[:200]}
        elif inc:
            fecha()
            atual = {"rot": rot + ", " + inc.group(1), "t": l, "ctx": cab[:240]}
        elif atual is not None:
            atual["t"] += NL + l
        else:
            res[0] = ("", res[0][1] + NL + l)
    fecha()
    return res
'''

CODE = UNITS_SRC + r'''
import base64, json
from lfx.custom.custom_component.component import Component
from lfx.io import Output, SecretStrInput, StrInput
from lfx.schema.data import Data
from lfx.utils.connection_string_parser import transform_connection_string
from langchain_community.vectorstores import PGVector
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings


class IndexV2Temp(Component):
    display_name = "IndexV2Temp"
    name = "IndexV2Temp"
    inputs = [
        SecretStrInput(name="url", display_name="url", value="PGVECTOR_CONTRACTS_URL"),
        SecretStrInput(name="key", display_name="key", value="CLOUDFLARE_WORKERS_AI_TOKEN"),
        StrInput(name="base", display_name="base", value=""),
        StrInput(name="payload", display_name="payload", value=""),
    ]
    outputs = [Output(display_name="r", name="r", method="r")]

    def r(self) -> Data:
        p = json.loads(base64.b64decode(self.payload).decode("utf-8"))
        conn = transform_connection_string(self.url)
        emb = OpenAIEmbeddings(model="@cf/baai/bge-m3", base_url=self.base, api_key=self.key, check_embedding_ctx_length=False, chunk_size=40)
        docs = []
        for r in p["recs"]:
            for rot, texto in unidades(r):
                meta = {"kb": "legislacao-v2", "citacao": citacao_de(r) + rot, "id": r["id"], "unidade": rot, "fonte": r["fonte"], "norma": r["norma"], "artigo": r["artigo"], "url": r["url"], "data_coleta": r["data_coleta"], "texto_artigo": r["texto"]}
                if r.get("aplicabilidade"):
                    meta["aplicabilidade"] = r["aplicabilidade"]
                docs.append(Document(page_content=texto, metadata=meta))
        store = PGVector.from_documents(embedding=emb, documents=docs, collection_name="legislacao_v2", connection_string=conn, pre_delete_collection=True)
        out = []
        for q in p["perguntas"]:
            pais, d0 = [], None
            for d, s in store.similarity_search_with_score(q["pergunta"], k=40):
                if d0 is None:
                    d0 = round(s, 3)
                if d.metadata["id"] not in pais:
                    pais.append(d.metadata["id"])
            top = pais[:10]
            rank = next((i + 1 for i, x in enumerate(top) if x in q["esperado"]), 0)
            out.append([q["id"], rank, d0, top[0]])
        return Data(data={"text": json.dumps({"unidades": len(docs), "rows": out}, ensure_ascii=True)})
'''

g = {}
exec(UNITS_SRC, g)
recs = [json.loads(l) for p in sorted(glob.glob(r"D:\dev\leia-kb-legislacao\saida\*.jsonl")) for l in open(p, encoding="utf-8") if l.strip()]
assert len(recs) == 330, len(recs)
un = {r["id"]: g["unidades"](r) for r in recs}
total = sum(len(v) for v in un.values())
print("artigos", len(recs), "unidades", total, "maior", max(len(t) for v in un.values() for _, t in v))
print("art22", [rot for rot, _ in un["lei-8245-1991-art-22"]][:18])
print("10192", [rot for rot, _ in un["lei-10192-2001-art-2"]])

ids = json.load(open("ids.json"))
t = lf.token()
aid = open("cf_account.txt").read().strip()
Q = [json.loads(l) for l in open(r"D:\dev\leia-kb-legislacao\avaliacao\perguntas-v1.jsonl", encoding="utf-8") if l.strip()]
d = lf.call("POST", "/api/v1/custom_component", t, {"code": CODE, "frontend_node": None})["data"]
tp = d["template"]
tp["url"]["value"] = "PGVECTOR_CONTRACTS_URL"
tp["url"]["load_from_db"] = True
tp["key"]["value"] = "CLOUDFLARE_WORKERS_AI_TOKEN"
tp["key"]["load_from_db"] = True
tp["base"]["value"] = f"https://api.cloudflare.com/client/v4/accounts/{aid}/ai/v1"
payload = {"recs": recs, "perguntas": [{"id": q["id"], "pergunta": q["pergunta"], "esperado": q["esperado"]} for q in Q]}
tp["payload"]["value"] = base64.b64encode(json.dumps(payload, ensure_ascii=False).encode("utf-8")).decode("ascii")
nid = "IndexV2Temp-" + uuid.uuid4().hex[:5]
n = {"id": nid, "type": "genericNode", "position": {"x": 0, "y": 0}, "data": {"id": nid, "type": "IndexV2Temp", "node": d}}
job = lf.call("POST", f"/api/v1/build/{ids['ingest']}/flow", t, {"data": {"nodes": [n], "edges": [], "viewport": {"x": 0, "y": 0, "zoom": 1}}})["job_id"]
req = urllib.request.Request(lf.BASE + f"/api/v1/build/{job}/events?stream=true", headers={**lf.UA, "Authorization": "Bearer " + t})
bd = None
with urllib.request.urlopen(req, timeout=520) as r:
    for raw in r:
        if not raw.strip():
            continue
        ev = json.loads(raw)
        if ev.get("event") == "end_vertex":
            bd = ev["data"]["build_data"]
        elif ev.get("event") == "end":
            break
if not bd["valid"]:
    print(json.dumps(bd["data"]["outputs"], ensure_ascii=True)[:1200].replace(aid, "<acct>"))
    raise SystemExit(1)
out = json.loads(bd["data"]["outputs"]["r"]["message"]["text"])
rows = out["rows"]
by = {r[0]: r for r in rows}
assert len(rows) == len(Q)


def metr(items):
    n = len(items)
    rk = [by[q["id"]][1] for q in items]
    return {"n": n, "top1": round(sum(1 for r in rk if r == 1) / n, 3), "top3": round(sum(1 for r in rk if 1 <= r <= 3) / n, 3), "top5": round(sum(1 for r in rk if 1 <= r <= 5) / n, 3), "top10": round(sum(1 for r in rk if 1 <= r <= 10) / n, 3), "mrr": round(sum(1 / r for r in rk if r) / n, 3)}


gab = [q for q in Q if q["esperado"]]
neg = [q for q in Q if not q["esperado"]]
res = {
    "unidades_indexadas": out["unidades"],
    "geral": metr(gab),
    "por_tipo": {k: metr([q for q in gab if q["tipo"] == k]) for k in sorted({q["tipo"] for q in gab})},
    "por_categoria": {k: metr([q for q in gab if q["categoria"] == k]) for k in sorted({q["categoria"] for q in gab})},
    "distancia_top1_com_gabarito_mediana": round(statistics.median(by[q["id"]][2] for q in gab), 3),
    "distancia_top1_com_gabarito_max": max(by[q["id"]][2] for q in gab),
    "distancia_top1_negativas": {q["id"]: by[q["id"]][2] for q in neg},
    "fora_do_top3": [{"id": q["id"], "categoria": q["categoria"], "tipo": q["tipo"], "rank": by[q["id"]][1], "esperado": q["esperado"], "top1": by[q["id"]][3]} for q in gab if not 1 <= by[q["id"]][1] <= 3],
    "por_pergunta": rows,
}
json.dump(res, open(r"D:\dev\leia-kb-legislacao\avaliacao\resultado-v2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
v1 = json.load(open(r"D:\dev\leia-kb-legislacao\avaliacao\resultado-v1.json", encoding="utf-8"))
print("V1", v1["geral"])
print("V2", res["geral"])
for k in res["por_tipo"]:
    print(k, "top3", v1["por_tipo"][k]["top3"], "->", res["por_tipo"][k]["top3"])
for k in res["por_categoria"]:
    print(k, "top3", v1["por_categoria"][k]["top3"], "->", res["por_categoria"][k]["top3"])
print({k: res[k] for k in ("unidades_indexadas", "distancia_top1_com_gabarito_mediana", "distancia_top1_com_gabarito_max", "distancia_top1_negativas")})
print("fora_top3", [(x["id"], x["rank"], x["top1"]) for x in res["fora_do_top3"]])
