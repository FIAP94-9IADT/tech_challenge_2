# Guia de uso

## Dados de entrada

O arquivo JSON contém `depot`, `vehicles` e `deliveries`. Prioridade aceita valores de
1 a 3; demanda, capacidade e autonomia devem ser positivas. Coordenadas usam graus
decimais.

## Linha de comando

```bash
python -m hospital_routes.cli --input data/deliveries.json --output outputs --seed 42
```

Arquivos gerados:

- `solution.json`: rotas e métricas estruturadas;
- `routes_map.html`: mapa interativo;
- `convergence.png`: evolução da aptidão;
- `daily_report.md`: instruções para a equipe.

A integração Gemini é o modo padrão. Copie `.env.example` para `.env` e informe uma
chave criada no Google AI Studio; `.env` não é versionado. Para uma execução
determinística e sem acesso externo, acrescente `--llm local`.

## Perguntas em linguagem natural

O módulo `reporting` expõe `answer_question`. A resposta recebe o mesmo contexto
estruturado da rota e a pergunta é limitada a mil caracteres. Exemplo:

```python
from hospital_routes.reporting import GeminiReportGenerator, answer_question

answer_question(generator, problem, solution, "Qual veículo atende as entregas críticas?")
```

## Ajuste do algoritmo

Parâmetros como população, gerações, taxas, elite e pesos ficam em `GAConfig`. Registre
a semente e altere um grupo de parâmetros por vez para que o efeito seja interpretável.
