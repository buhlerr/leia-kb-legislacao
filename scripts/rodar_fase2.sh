#!/usr/bin/env bash
# Reexecuta a extracao das fontes da fase 2 e valida as saidas.
set -e
cd /d/dev/leia-kb-legislacao
R="uv run --no-project --with beautifulsoup4 python -I"
S=scripts/extrair_planalto.py
$R $S --slug codigo-civil-2002 --arquivo raw/codigo-civil-2002/l10406compilada.htm --norma "Lei 10.406/2002" --url https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm --faixas "113,156,157,166-184,187,206,389-480,565-578,653,661,684,818-839,940,1336,1337,1647" --saida saida/codigo-civil-2002.jsonl > scripts/stats-codigo-civil-2002.json
$R $S --slug cdc-1990 --arquivo raw/cdc-1990/l8078compilado.htm --norma "Lei 8.078/1990" --url https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm --faixas "2,3,6,22,39,42,43,46-54" --extra '{"aplicabilidade":"restrita_locacao"}' --saida saida/cdc-1990.jsonl > scripts/stats-cdc-1990.json
$R $S --slug cpc-2015 --arquivo raw/cpc-2015/l13105.htm --norma "Lei 13.105/2015 (CPC)" --url https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm --faixas "63,85,190,246,247,334,539,784,917" --saida saida/cpc-2015.jsonl > scripts/stats-cpc-2015.json
$R $S --slug lgpd-2018 --arquivo raw/lgpd-2018/l13709.htm --norma "Lei 13.709/2018 (LGPD)" --url https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm --faixas "5,6,7,8,9,11,18,42" --saida saida/lgpd-2018.jsonl > scripts/stats-lgpd-2018.json
$R $S --slug lei-10192-2001 --arquivo raw/lei-10192-2001/l10192.htm --norma "Lei 10.192/2001" --url https://www.planalto.gov.br/ccivil_03/leis/leis_2001/l10192.htm --faixas "1,2" --saida saida/lei-10192-2001.jsonl > scripts/stats-lei-10192-2001.json
$R $S --slug lei-15040-2024 --arquivo raw/lei-15040-2024/l15040.htm --norma "Lei 15.040/2024" --url https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/lei/l15040.htm --faixas "1,20,44,45,46,94,126,134" --saida saida/lei-15040-2024.jsonl > scripts/stats-lei-15040-2024.json
$R $S --slug lei-9307-1996 --arquivo raw/lei-9307-1996/l9307.htm --norma "Lei 9.307/1996" --url https://www.planalto.gov.br/ccivil_03/leis/l9307.htm --faixas "1,4,8" --saida saida/lei-9307-1996.jsonl > scripts/stats-lei-9307-1996.json
$R $S --slug lei-9514-1997 --arquivo raw/lei-9514-1997/l9514.htm --norma "Lei 9.514/1997" --url https://www.planalto.gov.br/ccivil_03/leis/l9514.htm --faixas "27,30,37" --saida saida/lei-9514-1997.jsonl > scripts/stats-lei-9514-1997.json
for f in codigo-civil-2002 cdc-1990 cpc-2015 lgpd-2018 lei-10192-2001 lei-15040-2024 lei-9307-1996 lei-9514-1997; do PYTHONIOENCODING=utf-8 uv run --no-project python -I scripts/validar.py saida/$f.jsonl; done
