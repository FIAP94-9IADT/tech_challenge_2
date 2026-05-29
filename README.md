# Tech Challenge Fase 2 — Otimização de Diagnóstico para Saúde da Mulher

Projeto da FIAP PosTech que utiliza **algoritmos genéticos** para otimizar hiperparâmetros de modelos de machine learning para diagnóstico de câncer de mama, integrado com **Claude (Anthropic)** para geração de interpretações clínicas em linguagem natural.

## Estrutura do Projeto

```
tech-challege-2/
├── src/
│   ├── data/loader.py          # Dataset breast cancer + grupos etários
│   ├── models/classifier.py    # Random Forest, SVM, Regressão Logística
│   ├── genetic/
│   │   ├── chromosome.py       # Representação genética dos hiperparâmetros
│   │   ├── operators.py        # Seleção, crossover, mutação
│   │   ├── fitness.py          # Função fitness (sensibilidade, especificidade, F1, equidade)
│   │   └── algorithm.py        # Loop principal do AG
│   ├── llm/
│   │   ├── interpreter.py      # Claude API + persistência de respostas
│   │   └── prompts.py          # Prompt engineering para contexto médico feminino
│   └── utils/metrics.py        # Métricas e comparações
├── app/streamlit_app.py        # Interface visual interativa
├── experiments/run_experiments.py  # 3 experimentos com configs diferentes
├── tests/                      # Testes unitários (pytest)
├── data/results/               # Respostas LLM salvas (base para Fase 3)
└── docs/architecture.md        # Diagramas e decisões de design
```

## Instalação

```bash
# Com Poetry (recomendado)
pip install poetry
poetry install
poetry shell

# Ou com venv
python -m venv .venv
source .venv/bin/activate
pip install scikit-learn numpy pandas matplotlib seaborn anthropic streamlit python-dotenv plotly imbalanced-learn
```

## Configuração

```bash
cp .env.example .env
# Edite .env e adicione sua OPENAI_API_KEY
```

> Sem a chave, o sistema funciona em modo demonstração com respostas mock.

## Uso

### Interface Streamlit (recomendado)

```bash
streamlit run app/streamlit_app.py
```

### Executar os 3 experimentos

```bash
python experiments/run_experiments.py
```

### Testes automatizados

```bash
pytest tests/ -v
```

## Algoritmo Genético

| Operador | Implementação |
|----------|---------------|
| Representação | Dicionário de hiperparâmetros (genes discretos) |
| Seleção | Torneio (k=3) |
| Crossover | Uniforme (p=0.80) |
| Mutação | Reset aleatório por gene |
| Elitismo | Preserva 2 melhores por geração |

### Função Fitness

```
fitness = 0.40 × sensibilidade + 0.25 × especificidade + 0.25 × F1 + 0.10 × equidade
```

### 3 Experimentos Realizados

| Experimento | População | Gerações | Taxa Mutação | Crossover |
|-------------|-----------|----------|--------------|-----------|
| 1 — Exploração | 30 | 20 | 0.10 | 0.85 |
| 2 — Equilíbrio | 60 | 30 | 0.20 | 0.75 |
| 3 — Convergência | 100 | 50 | 0.15 | 0.80 |

## Integração LLM (ChatGPT)

- **Modelo**: `gpt-4o-mini`
- **Uso**: Interpretação de diagnósticos individuais + análise de experimentos
- **Prompt Engineering**: Contexto médico feminino, sensibilidade de gênero, privacidade
- **Persistência**: Respostas salvas em `data/results/*.json` para fine-tuning na Fase 3

## Considerações Éticas

- **Privacidade**: Sistema não armazena dados pessoais identificáveis
- **Equidade**: Função fitness penaliza modelos com desempenho desigual entre grupos etários
- **Transparência**: Métricas de confiabilidade do modelo exibidas junto às interpretações
- **Autonomia médica**: Sistema apoia, não substitui, o profissional de saúde

## Dataset

**Wisconsin Breast Cancer** (sklearn): 569 amostras, 30 features, 2 classes (maligno/benigno).
Grupos etários sintéticos adicionados para simulação de equidade demográfica.
