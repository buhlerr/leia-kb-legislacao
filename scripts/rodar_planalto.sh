#!/usr/bin/env bash
# Reexecuta a extracao das quatro fontes do Planalto e valida as saidas.
set -e
cd /d/dev/leia-kb-legislacao
R="uv run --no-project --with beautifulsoup4 python -I"
S=scripts/extrair_planalto.py
$R $S --slug lei-8245-1991 --arquivo raw/lei-8245-1991/l8245.htm --norma "Lei 8.245/1991" --url https://www.planalto.gov.br/ccivil_03/leis/l8245.htm --faixas todos --saida saida/lei-8245-1991.jsonl > scripts/stats-lei-8245-1991.json
$R $S --slug codigo-civil-2002 --arquivo raw/codigo-civil-2002/l10406compilada.htm --norma "Lei 10.406/2002" --url https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm --faixas "113,166-184,389-480,565-578,818-839" --saida saida/codigo-civil-2002.jsonl > scripts/stats-codigo-civil-2002.json
$R $S --slug lei-8009-1990 --arquivo raw/lei-8009-1990/l8009.htm --norma "Lei 8.009/1990" --url https://www.planalto.gov.br/ccivil_03/leis/l8009.htm --faixas todos --saida saida/lei-8009-1990.jsonl > scripts/stats-lei-8009-1990.json
$R $S --slug cdc-1990 --arquivo raw/cdc-1990/l8078compilado.htm --norma "Lei 8.078/1990" --url https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm --faixas "46-54" --extra '{"aplicabilidade":"restrita_locacao"}' --saida saida/cdc-1990.jsonl > scripts/stats-cdc-1990.json
for f in lei-8245-1991 codigo-civil-2002 lei-8009-1990 cdc-1990; do PYTHONIOENCODING=utf-8 uv run --no-project python -I scripts/validar.py saida/$f.jsonl; done
