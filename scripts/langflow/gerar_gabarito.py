import datetime, html, json
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.worksheet.datavalidation import DataValidation

AV = "D:/dev/leia-kb-legislacao/avaliacao/"
e = json.load(open(AV + "agente-locacao-02.json", encoding="utf-8"))
tr = json.load(open(AV + "agente-locacao-02-trilha.json", encoding="utf-8"))
AL = e["content"]["alerts"]
assert len(AL) == 14, len(AL)
cont = e["content"]["counts"]
ROT = {"red": "Vermelho", "yellow": "Amarelo", "green": "Verde"}
AC = {"vigencia":"vigência","prorrogacao":"prorrogação","indexacao":"indexação","caucao":"caução","preferencia":"preferência","alienacao":"alienação","imovel":"imóvel","condominio":"condomínio","convencao":"convenção","devolucao":"devolução","pre":"pré"}
tema = lambda t: " ".join(AC.get(p, p) for p in t.split("_")).capitalize()
seguro = lambda s: "'" + s if s[:1] in "=+-@" else s

NAVY, PAPER, LINE = "16324F", "F4F1EA", "D9D3C7"
SOFT = {"red": "F5E1E1", "yellow": "F6EDD6", "green": "E3EFE8"}
TXT = {"red": "8B2E2E", "yellow": "8A6A1F", "green": "2F6B4F"}
F = "Arial"
borda = Border(*[Side(style="thin", color=LINE)] * 4)
ENTRADA = PatternFill("solid", start_color="FFFCF7")


def cab(ws, linha, nomes, larguras, preencher=()):
    for i, (n, w) in enumerate(zip(nomes, larguras), 1):
        c = ws.cell(linha, i, n)
        c.font = Font(name=F, bold=True, color="FFFFFF", size=10)
        c.fill = PatternFill("solid", start_color="1F6F7A" if n in preencher else NAVY)
        c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        c.border = borda
        ws.column_dimensions[L(i)].width = w
    ws.row_dimensions[linha].height = 42


def lista(ws, opcoes, faixa):
    dv = DataValidation(type="list", formula1='"' + ",".join(opcoes) + '"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(faixa)


wb = Workbook()
ws = wb.active
ws.title = "Alertas"
ws["A1"] = "Gabarito da análise: locacao-02 (minuta mascarada)"
ws["A1"].font = Font(name=F, bold=True, size=14, color=NAVY)
ws["A2"] = "Preencha as colunas em azul-petróleo. A criticidade é a sugerida pela matriz de riscos, ainda não validada por advogado."
ws["A2"].font = Font(name=F, size=10, color="5C6570")
NOMES = ["Nº", "Criticidade do agente", "ID do risco", "Tema", "Cláusula (ordem na divisão)", "Trecho da minuta", "Resumo do alerta", "Explicação", "Fundamento", "Nota de confirmação (Jev)", "O alerta está certo?", "Criticidade correta", "Fundamento está certo?", "Comentário do revisor"]
PREENCHER = NOMES[10:]
cab(ws, 4, NOMES, [5, 12, 9, 22, 11, 46, 34, 58, 30, 12, 13, 13, 13, 40], PREENCHER)
for i, a in enumerate(AL, 1):
    v = [i, ROT[a["severity"]], a["risk_id"], tema(a["theme"]), a["clause_index"], seguro(a["excerpt"]), seguro(a["summary"]), seguro(a["detail"]), "; ".join(a["legal_basis"]), a["confirmation_score"], None, None, None, None]
    r = 4 + i
    for j, x in enumerate(v, 1):
        c = ws.cell(r, j, x)
        c.font = Font(name=F, size=10)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        c.border = borda
        if j > 10:
            c.fill = ENTRADA
    s = ws.cell(r, 2)
    s.fill = PatternFill("solid", start_color=SOFT[a["severity"]])
    s.font = Font(name=F, size=10, bold=True, color=TXT[a["severity"]])
    ws.cell(r, 10).number_format = "0.00"
    ws.row_dimensions[r].height = max(90, 15 * (len(a["detail"]) // 58 + 2))
fim = 4 + len(AL)
lista(ws, ["Certo", "Parcial", "Errado"], f"K5:K{fim}")
lista(ws, ["Vermelho", "Amarelo", "Verde", "Não é risco"], f"L5:L{fim}")
lista(ws, ["Sim", "Parcial", "Não"], f"M5:M{fim}")
ws.freeze_panes = "C5"
ws.auto_filter.ref = f"A4:N{fim}"
ws.page_setup.orientation = "landscape"
ws.page_setup.fitToWidth = 1
ws.page_setup.fitToHeight = 0
ws.sheet_properties.pageSetUpPr.fitToPage = True

w2 = wb.create_sheet("Riscos que faltaram")
w2["A1"] = "Cláusulas sem alerta e riscos não apontados"
w2["A1"].font = Font(name=F, bold=True, size=14, color=NAVY)
w2["A2"] = "Marque se alguma destas cláusulas tinha risco. Use as linhas em branco ao final para riscos que não dependem de uma cláusula, como omissões do contrato."
w2["A2"].font = Font(name=F, size=10, color="5C6570")
N2 = ["Cláusula (ordem na divisão)", "Tema atribuído", "Texto da cláusula", "Tinha risco?", "Qual o risco?", "Criticidade correta", "Fundamento", "Comentário do revisor"]
cab(w2, 4, N2, [11, 24, 70, 11, 42, 13, 30, 40], N2[3:])
sem = [c for c in tr["clausulas"] if c["resultado"] != "alerta"]
r = 5
for c in sem:
    for j, x in enumerate([c["n"], tema(c["triagem"]["tema"]), seguro(c["texto"]), None, None, None, None, None], 1):
        d = w2.cell(r, j, x)
        d.font = Font(name=F, size=10)
        d.alignment = Alignment(wrap_text=True, vertical="top")
        d.border = borda
        if j > 3:
            d.fill = ENTRADA
    w2.row_dimensions[r].height = max(45, 15 * (len(c["texto"]) // 70 + 1))
    r += 1
fs = r - 1
for _ in range(8):
    for j, x in enumerate(["—", "Risco adicional", None, "Sim", None, None, None, None], 1):
        d = w2.cell(r, j, x)
        d.font = Font(name=F, size=10)
        d.alignment = Alignment(wrap_text=True, vertical="top")
        d.border = borda
        if j >= 3:
            d.fill = ENTRADA
    w2.cell(r, 4).value = None
    w2.row_dimensions[r].height = 45
    r += 1
fa = r - 1
lista(w2, ["Sim", "Não"], f"D5:D{fa}")
lista(w2, ["Vermelho", "Amarelo", "Verde"], f"F5:F{fa}")
w2.freeze_panes = "A5"

w3 = wb.create_sheet("Resumo")
w3["A1"] = "Resumo do gabarito"
w3["A1"].font = Font(name=F, bold=True, size=14, color=NAVY)
A = f"Alertas!$K$5:$K${fim}"
linhas = [
    ("Alertas gerados", f"=COUNTA(Alertas!$A$5:$A${fim})", "0"),
    ("Alertas avaliados", f"=COUNTA({A})", "0"),
    ("Certos", f'=COUNTIF({A},"Certo")', "0"),
    ("Parciais", f'=COUNTIF({A},"Parcial")', "0"),
    ("Errados", f'=COUNTIF({A},"Errado")', "0"),
    ("Precisão (só certos)", '=IF(B4=0,"-",B5/B4)', "0.0%"),
    ("Precisão (certos + parciais)", '=IF(B4=0,"-",(B5+B6)/B4)', "0.0%"),
    ("Criticidade igual à do agente", f'=IF(COUNTA(Alertas!$L$5:$L${fim})=0,"-",SUMPRODUCT(--(Alertas!$L$5:$L${fim}=Alertas!$B$5:$B${fim}))/COUNTA(Alertas!$L$5:$L${fim}))', "0.0%"),
    ("Riscos que faltaram", f"=COUNTIF('Riscos que faltaram'!$D$5:$D${fa},\"Sim\")", "0"),
    ("Cobertura (certos sobre certos + faltantes)", '=IF(B5+B11=0,"-",B5/(B5+B11))', "0.0%"),
]
cab(w3, 2, ["Medida", "Valor"], [44, 14])
for i, (n, fx, fmt) in enumerate(linhas, 3):
    a = w3.cell(i, 1, n)
    b = w3.cell(i, 2, fx)
    a.font = b.font = Font(name=F, size=10)
    a.border = b.border = borda
    b.number_format = fmt
    b.alignment = Alignment(horizontal="right")
from openpyxl.workbook.properties import CalcProperties
wb.calculation = CalcProperties(fullCalcOnLoad=True)
wb.save(AV + "gabarito-locacao-02.xlsx")

# ---------- relatorio HTML ----------
E = lambda s: html.escape(str(s or ""), quote=True)
total = len(AL)
pct = lambda n: round(100 * n / total, 1)
CIR = 188.5
seg = []
off = 0
for k, cor in (("red", "var(--bad)"), ("yellow", "var(--warn-cor)"), ("green", "var(--ok)")):
    tam = CIR * cont[k] / total
    seg.append(f'<circle cx="42" cy="42" r="30" fill="none" stroke="{cor}" stroke-width="8" stroke-dasharray="{tam:.1f} {CIR}" stroke-dashoffset="{-off:.1f}" transform="rotate(-90 42 42)"/>')
    off += tam
ALT = {"red": "bad", "yellow": "warn", "green": "ok"}
ROTL = {"red": "Crítico", "yellow": "Atenção", "green": "Informativo"}
ICO = {"red": '<path d="M8 1.5h8l5.5 5.5v8.5L16 22H8l-5.5-6.5V7z"/><path d="M12 7v6M12 16.5v.5"/>', "yellow": '<path d="M12 3 22 20H2z"/><path d="M12 10v4M12 17v.5"/>', "green": '<circle cx="12" cy="12" r="9.5"/><path d="m8 12 3 3 5-6"/>'}
icone = lambda k: f'<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICO[k]}</svg>'
primeiro = {}
for i, a in enumerate(AL):
    primeiro.setdefault(a["clause_index"], f"a{i}")
mapa = {}
for a in AL:
    atual = mapa.get(a["clause_index"])
    if atual is None or list(ROT).index(a["severity"]) < list(ROT).index(atual):
        mapa[a["clause_index"]] = a["severity"]
heat = ""
for c in tr["clausulas"]:
    s = mapa.get(c["n"])
    if s:
        heat += f'<a class="heat heat--{ALT[s]}" href="#{primeiro[c["n"]]}" title="Cláusula {c["n"]}: {ROTL[s]}">{c["n"]}</a>'
    else:
        heat += f'<span class="heat" title="Cláusula {c["n"]}: sem risco da matriz">{c["n"]}</span>'
cards = ""
for i, a in enumerate(AL):
    k = ALT[a["severity"]]
    leis = "".join(f"<li>{E(x)}</li>" for x in a["legal_basis"]) or "<li>Sem norma na base</li>"
    cards += f'''<article class="alerta alerta--{k}" id="a{i}" data-sev="{a["severity"]}">
<button class="alerta__cabeca" aria-expanded="false" aria-controls="p{i}"><span class="alerta__ic">{icone(a["severity"])}</span><span class="alerta__tit"><b>{E(a["summary"])}</b><small>{E(tema(a["theme"]))} · cláusula {a["clause_index"]} · {E(a["risk_id"])}</small></span><span class="seta" aria-hidden="true">▾</span></button>
<div class="alerta__corpo" id="p{i}" hidden><p class="rot">Trecho da minuta</p><blockquote>{E(a["excerpt"])}</blockquote><dl><dt>Risco</dt><dd>{E(a["risk"])}</dd><dt>Por que importa</dt><dd>{E(a["detail"])}</dd><dt>Referência legal</dt><dd><ul>{leis}</ul></dd><dt>Confirmação</dt><dd>{a["confirmation_score"]:.2f} no Jev</dd></dl></div></article>'''
fi = e["ficha"]
conf = tr.get("ficha_confianca") or {}
FICHA = [("Início", fi["data_inicio"], conf.get("data_inicio")), ("Prazo", fi["prazo"].capitalize(), conf.get("prazo")), ("Aluguel", fi["valor_aluguel"], conf.get("valor_aluguel")), ("Garantia", tema(fi["garantia"]), conf.get("garantia")), ("Índice", fi["indice"].upper(), conf.get("indice"))]
fic = "".join(f'<div class="fi"><dt>{E(n)}</dt><dd>{E(v)}{" <small>confiança baixa</small>" if c is not None and c < 0.6 else ""}</dd></div>' for n, v, c in FICHA)
quando = datetime.datetime.fromisoformat(e["timestamp"]).astimezone(datetime.timezone(datetime.timedelta(hours=-3))).strftime("%d/%m/%Y às %H:%M")
obs = "".join(f"<li>{E(x)}</li>" for x in ["A revisão humana continua obrigatória: este resultado é apoio à análise.", "A criticidade vem da matriz de riscos, ainda não validada por advogado.", "O agente só aponta riscos descritos na matriz.", "Texto com dados pessoais mascarados."])
veredito = f'Revisar: {cont["red"]} críticos' if cont["red"] else "Sem críticos"
H = f'''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>LEIA · Relatório locacao-02</title>
<style>
:root{{--paper:#f4f1ea;--card:#fffcf7;--ink:#1b2430;--muted:#5c6570;--navy:#16324f;--line:#d9d3c7;--accent:#1f6f7a;--accent-soft:#e1eff0;--ok:#2f6b4f;--ok-soft:#e3efe8;--warn:#8a6a1f;--warn-soft:#f6edd6;--warn-cor:#c19a2e;--bad:#8b2e2e;--bad-soft:#f5e1e1}}
*{{box-sizing:border-box;margin:0;padding:0}}
html{{-webkit-text-size-adjust:100%}}
body{{background:var(--paper);color:var(--ink);font:16px/1.5 Geist,ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}}
h1,h2{{text-wrap:balance}}p,li,dd{{text-wrap:pretty}}::selection{{background:var(--accent-soft)}}
.topo{{background:var(--navy);color:#fff;padding:20px 0}}.topo h1{{font-size:20px;font-weight:650}}.topo p{{font-size:13px;color:#c8d4de}}
.w{{max-width:960px;margin:0 auto;padding:0 20px}}
.veredito{{position:sticky;top:0;z-index:5;background:var(--card);border-bottom:1px solid var(--line);box-shadow:0 2px 6px rgba(27,36,48,.08);padding:12px 0}}
.linha{{display:flex;align-items:center;justify-content:space-between;gap:12px}}.vt{{font-size:16px;font-weight:700;color:var(--bad)}}.vm{{font-size:13px;color:var(--muted)}}
.bar{{display:flex;gap:2px;height:6px;border-radius:99px;overflow:hidden;margin-top:8px}}
.chips{{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}}
.chip{{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--line);background:var(--card);border-radius:999px;padding:5px 12px;font:600 12px/1.3 inherit;font-family:inherit;color:var(--navy);cursor:pointer}}
.chip--bad{{background:var(--bad-soft);border-color:rgba(139,46,46,.3);color:var(--bad)}}.chip--warn{{background:var(--warn-soft);border-color:rgba(138,106,31,.3);color:var(--warn)}}.chip--ok{{background:var(--ok-soft);border-color:rgba(47,107,79,.3);color:var(--ok)}}
.chip[aria-pressed=true]{{outline:2px solid var(--accent);outline-offset:1px}}
button:focus-visible,a:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
main.w{{padding:20px 20px 40px}}section{{margin-top:20px}}h2{{font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:8px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:14px;box-shadow:0 1px 2px rgba(27,36,48,.05)}}
.hero{{display:grid;grid-template-columns:150px 1fr;gap:12px}}.donut{{display:flex;align-items:center;justify-content:center;padding:12px}}
.tiles{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}.tile{{padding:14px;display:flex;flex-direction:column;gap:4px;justify-content:center}}.tile b{{font-size:26px;line-height:1;font-weight:650;color:var(--navy)}}.tile small{{font-size:12px;color:var(--muted);font-weight:600}}
.ficha{{display:grid;grid-template-columns:repeat(5,1fr);gap:0;padding:6px 8px}}.fi{{padding:8px 10px}}.fi dt{{font-size:11px;font-weight:650;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}}.fi dd{{font-size:14px;font-weight:600}}.fi small{{display:block;font-size:11px;font-weight:600;color:var(--warn)}}
.mapa{{display:flex;flex-wrap:wrap;gap:4px;padding:12px}}.heat{{flex:1 0 34px;height:36px;display:flex;align-items:center;justify-content:center;border:1px solid var(--line);border-radius:6px;font-size:12px;font-weight:700;color:var(--muted);text-decoration:none}}.heat--bad{{background:var(--bad-soft);color:var(--bad);border-color:rgba(139,46,46,.3)}}.heat--warn{{background:var(--warn-soft);color:var(--warn);border-color:rgba(193,154,46,.4)}}.heat--ok{{background:var(--ok-soft);color:var(--ok);border-color:rgba(47,107,79,.3)}}
.legenda{{font-size:12px;color:var(--muted);margin-top:6px}}
.alerta{{border:1px solid;border-radius:12px;margin-top:10px;overflow:hidden;scroll-margin-top:130px}}.alerta--bad{{border-color:rgba(139,46,46,.3);background:rgba(245,225,225,.55)}}.alerta--warn{{border-color:rgba(138,106,31,.3);background:rgba(246,237,214,.55)}}.alerta--ok{{border-color:rgba(47,107,79,.3);background:rgba(227,239,232,.55)}}
.alerta--bad .alerta__ic{{color:var(--bad)}}.alerta--warn .alerta__ic{{color:var(--warn)}}.alerta--ok .alerta__ic{{color:var(--ok)}}
.alerta__cabeca{{width:100%;text-align:left;display:flex;gap:10px;padding:12px 14px;align-items:flex-start;background:none;border:0;font:inherit;color:inherit;cursor:pointer}}.alerta__ic{{margin-top:3px}}.alerta__tit{{flex:1;display:flex;flex-direction:column;gap:2px}}.alerta__tit b{{font-size:15px;font-weight:600;line-height:1.35}}.alerta__tit small{{font-size:12px;color:var(--muted);font-weight:500}}.seta{{color:var(--muted);transition:transform .25s cubic-bezier(.32,.72,0,1)}}[aria-expanded=true] .seta{{transform:rotate(180deg)}}
.alerta__corpo{{border-top:1px solid rgba(27,36,48,.08);background:var(--card);padding:14px 16px;font-size:14px}}.rot{{font-size:11px;font-weight:650;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin-bottom:4px}}blockquote{{border-left:3px solid var(--line);padding:2px 12px;font-style:italic}}dl.d,.alerta__corpo dl{{display:grid;grid-template-columns:130px 1fr;gap:8px 12px;margin-top:12px}}.alerta__corpo dt{{font-weight:650;font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;padding-top:2px}}.alerta__corpo ul{{list-style:none}}
.obs{{padding:12px 16px;font-size:13px;color:var(--muted)}}.obs ul{{padding-left:18px}}
@media(max-width:640px){{.hero{{grid-template-columns:1fr}}.tiles{{grid-template-columns:1fr 1fr}}.ficha{{grid-template-columns:1fr 1fr}}.alerta__corpo dl{{grid-template-columns:1fr;gap:2px}}.alerta__corpo dd{{margin-bottom:8px}}}}
@media print{{.veredito{{position:static;box-shadow:none}}.chips,.seta{{display:none}}.alerta__corpo[hidden]{{display:block}}.alerta{{break-inside:avoid}}body{{background:#fff}}}}
</style></head><body>
<header class="topo"><div class="w"><h1>Contrato de locação residencial</h1><p>{E(e["minuta_id"])} · analisado em {quando} · confiança do tipo {e["score_tipo"]:.0%}</p></div></header>
<div class="veredito"><div class="w"><div class="linha"><span class="vt">{veredito}</span><span class="vm">{total} alertas em {tr["stats"]["clausulas_total"]} cláusulas</span></div>
<div class="bar" role="img" aria-label="{cont["red"]} críticos, {cont["yellow"]} de atenção, {cont["green"]} informativos"><span style="width:{pct(cont["red"])}%;background:var(--bad)"></span><span style="width:{pct(cont["yellow"])}%;background:var(--warn-cor)"></span><span style="width:{pct(cont["green"])}%;background:var(--ok)"></span></div>
<div class="chips" role="group" aria-label="Filtrar por severidade"><button class="chip" aria-pressed="true" data-f="">Todos {total}</button><button class="chip chip--bad" aria-pressed="false" data-f="red">{icone("red")} Crítico {cont["red"]}</button><button class="chip chip--warn" aria-pressed="false" data-f="yellow">{icone("yellow")} Atenção {cont["yellow"]}</button><button class="chip chip--ok" aria-pressed="false" data-f="green">{icone("green")} Informativo {cont["green"]}</button></div></div></div>
<main class="w">
<section style="margin-top:0"><div class="hero"><div class="card donut"><svg viewBox="0 0 84 84" width="110" height="110" role="img" aria-label="Distribuição dos alertas"><circle cx="42" cy="42" r="30" fill="none" stroke="var(--line)" stroke-width="8" opacity=".4"/>{"".join(seg)}<text x="42" y="44" text-anchor="middle" font-weight="700" font-size="18" fill="var(--bad)">{cont["red"]}</text><text x="42" y="54" text-anchor="middle" font-size="7.5" fill="var(--muted)">críticos</text></svg></div>
<div class="tiles"><div class="card tile"><b>{cont["red"]}</b><small>críticos</small></div><div class="card tile"><b>{cont["yellow"]}</b><small>de atenção</small></div><div class="card tile"><b>{cont["green"]}</b><small>informativos</small></div></div></div></section>
<section><h2>Ficha do contrato</h2><dl class="card ficha">{fic}</dl></section>
<section><h2>Mapa do documento</h2><div class="card mapa">{heat}</div><p class="legenda">Cada bloco é uma cláusula. Selecione uma cláusula colorida para ir ao alerta.</p></section>
<section><h2>Alertas</h2><div id="lista">{cards}</div></section>
<section><h2>Observações</h2><div class="card obs"><ul>{obs}</ul></div></section>
</main>
<script>
document.querySelectorAll(".alerta__cabeca").forEach(b=>b.addEventListener("click",()=>{{const p=b.nextElementSibling;p.hidden=!p.hidden;b.setAttribute("aria-expanded",String(!p.hidden))}}));
const cs=[...document.querySelectorAll(".chip[data-f]")];
cs.forEach(b=>b.addEventListener("click",()=>{{const f=b.dataset.f;cs.forEach(x=>x.setAttribute("aria-pressed",String(x===b)));document.querySelectorAll(".alerta").forEach(a=>a.style.display=!f||a.dataset.sev===f?"":"none")}}));
document.querySelectorAll(".heat[href]").forEach(a=>a.addEventListener("click",()=>{{const t=document.querySelector(a.getAttribute("href"));cs[0].click();const b=t.querySelector(".alerta__cabeca");if(b.getAttribute("aria-expanded")==="false")b.click()}}));
</script></body></html>'''
open(AV + "relatorio-locacao-02.html", "w", encoding="utf-8", newline="\n").write(H)
print("ok", len(AL), "sem_alerta", len(sem), "html_kb", len(H) // 1024)
