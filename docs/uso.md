# Guia de uso

## Dados de entrada

O arquivo JSON possui três grupos principais: `depot`, `vehicles` e `deliveries`. A
prioridade varia de 1 a 3. Demanda, capacidade e autonomia devem ser positivas, e as
coordenadas são informadas em graus decimais.

## Linha de comando

```bash
python -m hospital_routes.cli --input data/deliveries.json --output outputs --seed 42
```

A execução cria os seguintes arquivos:

- `solution.json`: rotas e métricas em formato estruturado;
- `routes_map.html`: mapa interativo;
- `convergence.png`: gráficos de convergência;
- `daily_report.md`: instruções para a equipe de entrega.

O Gemini é usado por padrão. Para configurá-lo, copie `.env.example` para `.env` e
informe uma chave criada no Google AI Studio. O arquivo `.env` não é versionado. Para
gerar um relatório local, sem chamada externa, use `--llm local`.

## Perguntas em linguagem natural

O módulo `reporting` oferece a função `answer_question`. Ela reutiliza o contexto
estruturado das rotas e limita a pergunta a mil caracteres.

```python
from hospital_routes.reporting import GeminiReportGenerator, answer_question

generator = GeminiReportGenerator()
resposta = answer_question(
    generator,
    problem,
    solution,
    "Qual veículo atende as entregas críticas?",
)
print(resposta)
```

No exemplo, `problem` e `solution` correspondem ao cenário carregado e à solução
produzida pelo otimizador.

## Ajuste do algoritmo

Os principais parâmetros ficam em `GAConfig`: população, gerações, taxas dos
operadores, elitismo, semente e pesos da função de aptidão. Registre a semente usada e
altere um grupo de parâmetros por vez; assim, o efeito de cada mudança fica mais claro.
