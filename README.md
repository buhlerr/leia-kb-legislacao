# leia-kb-legislacao

Base normativa, levantamento de riscos e agente de análise de minutas de locação residencial da LEIA, executado no Langflow.

> Apoio à análise jurídica. A matriz de riscos e as criticidades não foram validadas por advogado, e a revisão humana continua obrigatória.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `raw/` | HTML oficial baixado do Planalto e do STJ |
| `saida/` | Registros por artigo, súmula ou precedente, em JSONL |
| `levantamento/` | Matriz de riscos, normas faltantes, jurisprudência e revisão independente |
| `avaliacao/` | Perguntas com gabarito e medições da busca |
| `scripts/` | Extração das normas e correção da matriz |
| `scripts/langflow/` | Implantação do agente, indexação e avaliação |

## O agente

Fluxo `LEIA - Analisar Minuta`:

1. Lê o arquivo e mascara dados pessoais.
2. O Jev identifica o tipo de minuta e interrompe se não for suportado.
3. A ficha do contrato é montada: o código encontra datas e valores, e o Jev escolhe os corretos.
4. O Jev confirma, em cada cláusula, os riscos da matriz do tema dela.
5. A busca vetorial em `legislacao_v2`, ordenada pelo Jev, traz as normas.
6. O Mistral Small redige a explicação, sem poder remover um risco.
7. A validação sem IA confere o trecho literal e gera o relatório e a trilha.

Criticidade e fundamentos vêm da matriz, não do modelo de texto.

## Como executar

Os scripts de `scripts/langflow/` rodam a partir dessa pasta e usam a senha de `C:\Users\Vitor\langflow-credentials.txt`. Dependem de três arquivos locais, fora do git: `ids.json`, `cf_account.txt` e `all.json` (catálogo de `GET /api/v1/all`).

```bash
cd scripts/langflow
python indexar_v2.py                      # recria legislacao_v2 e mede a busca vetorial
python avaliar_busca_jev.py               # mede a busca com o Jev
python deploy_agente.py 'locacao-02*3'    # atualiza o fluxo e roda 3 vezes
uv run --no-project --with openpyxl python gerar_gabarito.py
```

Para atualizar a base, rode `scripts/rodar_planalto.sh` e depois `scripts/rodar_fase2.sh`. O `scripts/aplicar_correcoes_matriz.py` é idempotente.

## Dados e privacidade

- Use somente minutas mascaradas enquanto a retenção de dados do Jev não for confirmada. A máscara cobre formatos conhecidos, e nomes ou endereços podem escapar.
- Ficam fora do git os resultados com texto de contrato: `avaliacao/agente-*`, `gabarito-*` e `relatorio-*`.
- Chaves ficam como variáveis `Credential` no Langflow, nunca neste repositório.
