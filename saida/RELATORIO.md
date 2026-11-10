# Relatório de coleta: legislação brasileira em registros por artigo

Data da coleta: 2026-11-09. Fontes oficiais: planalto.gov.br e processo.stj.jus.br.
Saídas: `saida/<slug>.jsonl`, um objeto JSON por linha, UTF-8.

## Resumo

| slug | norma | registros | situação |
|---|---|---|---|
| lei-8245-1991 | Lei 8.245/1991 (Inquilinato) | 89 | completo; arts. 87 e 88 vetados |
| codigo-civil-2002 | Lei 10.406/2002 (Código Civil) | 148 | completo nas faixas; art. 456 revogado |
| lei-8009-1990 | Lei 8.009/1990 (Bem de família) | 8 | completo |
| cdc-1990 | Lei 8.078/1990 (CDC), arts. 46 a 54 | 15 | completo; art. 54-E vetado |
| sumulas-stj | Súmulas do STJ 214, 268, 335, 549 | 4 | completo |

Total: 264 registros.

## Por fonte

### lei-8245-1991
- URL: https://www.planalto.gov.br/ccivil_03/leis/l8245.htm
- HTML: `raw/lei-8245-1991/l8245.htm`
- Registros: 89 (arts. 1 a 90, com 54-A incluído).
- Vetados (não entram): arts. 87 e 88, marcados "(Vetado)" na página.
- Revogados: nenhum.
- Sufixados incluídos: 54-A.
- Redações riscadas removidas: 23 elementos.

### codigo-civil-2002
- URL: https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm
- HTML: `raw/codigo-civil-2002/l10406compilada.htm`
- Faixas pedidas: 113; 166 a 184; 389 a 480; 565 a 578; 818 a 839.
- Registros: 148 (147 números base mais o sufixo 421-A).
- Revogados: art. 456, marcado "(Revogado pela Lei nº 13.105, de 2015)".
- Vetados (não entram): art. 819-A, marcado "(VETADO)".
- Faltantes nas faixas, sem explicação: nenhum.
- Redações riscadas removidas: 2 elementos.

### lei-8009-1990
- URL: https://www.planalto.gov.br/ccivil_03/leis/l8009.htm
- HTML: `raw/lei-8009-1990/l8009.htm`
- Registros: 8 (arts. 1 a 8). Sem faltantes.
- Redações riscadas removidas: 5 elementos.
- Observação: a página não tem cabeçalhos de Título/Capítulo, então o campo `estrutura` fica vazio.

### cdc-1990
- URL: https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm
- HTML: `raw/cdc-1990/l8078compilado.htm`
- Faixa pedida: 46 a 54. Campo extra `aplicabilidade: "restrita_locacao"` em todos os registros.
- Registros: 15 (arts. 46 a 54, mais 54-A, 54-B, 54-C, 54-D, 54-F, 54-G).
- Vetado (não entra): art. 54-E, marcado "(VETADO)".
- Redações riscadas removidas: 2 elementos.

### sumulas-stj
- URLs usadas (uma página de consulta por súmula, em processo.stj.jus.br):
  - https://processo.stj.jus.br/SCON/sumstj/doc.jsp?&b=SUMU&p=false&l=10&i=1&ordenacao=-@NUM,-@DOCN&h=true&livre=%40NUM%3D%22214%22 (e análogas para 268, 335 e 549)
- Índice consultado: https://processo.stj.jus.br/SCON/sumstj/toc.jsp?tipo=sumula+ou+su
- HTML: `raw/sumulas-stj/s_214.html`, `s_268.html`, `s_335.html`, `s_549.html`, além de `toc*.html` (índice).
- Registros: 4, com o enunciado do campo de texto integral de cada súmula. A citação (órgão julgador, datas de julgamento e DJ) não foi gravada, porque o formato não tem campo para ela.
- Tentativa que falhou: scon.stj.jus.br respondeu HTTP 403 a requisições automatizadas. Os dados vieram do processo.stj.jus.br, que é o mesmo domínio oficial.

## Validação

Executada por `scripts/validar.py` sobre os quatro JSONL do Planalto, e verificada por inspeção das saídas.

- Contagem por fonte: confere com a expectativa (ver tabela acima).
- Artigos faltantes ou excluídos, todos explicados:
  - Lei 8.245: 87 e 88 (vetados).
  - Código Civil: 456 (revogado) e 819-A (vetado; não está nas faixas numeradas).
  - CDC: 54-E (vetado).
- Duplicados: nenhum (ids e números de artigo únicos).
- Textos sem tags HTML, sem a string "Redação dada", sem sobra de anotação editorial ("Incluído", "Vide", "Revogado", "VETADO") e sem codificação quebrada (Ã seguido de caractere de controle, U+FFFD). Confirmado para todos os registros.
- Todo `texto` começa com o próprio número do artigo.
- Referências de controle:
  - Art. 4 da Lei 8.245: começa com "Art. 4º". Não contém a redação antiga riscada. Alteração registrada: "Lei nº 12.744, de 2012".
  - Art. 37 da Lei 8.245: começa com "Art. 37".
  - Art. 413 do Código Civil: começa com "Art. 413".
- Súmulas: os quatro enunciados conferem com o texto da página oficial, sem tags e com acentos corretos.

## Observações

- Os textos mantêm a grafia da fonte. Por exemplo, o art. 413 do Código Civil traz "eqüitativamente", com trema, que era a ortografia anterior a 2009.
- A linha de citação do CDC diz "Redação dada pela nº 11.785, de 2008", sem a palavra "Lei". Mantive como está na fonte e não completei.
- As alterações são referências textuais do Planalto (ex.: "Lei nº 9.256, de 9.1.1996"). Não foram conferidas uma a uma contra a norma citada.
- O `id` de artigos sufixados usa minúsculas: `codigo-civil-2002-art-421-a`.
- Nada foi gravado em banco de dados nem commitado.
- Scripts: `scripts/extrair_planalto.py`, `scripts/extrair_sumulas.py`, `scripts/validar.py`, `scripts/rodar_planalto.sh`. Estatísticas brutas em `scripts/stats-*.json`.
