# Arquitetura do Sistema — Tech Challenge Fase 2

## Visão Geral

```
┌─────────────────────────────────────────────────────────────────┐
│                    Interface Streamlit (app/)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Overview │ │  GA Opt  │ │ Compare  │ │LLM+Query │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐   ┌────────▼───────┐  ┌───────▼──────┐
│  src/genetic │   │   src/models   │  │   src/llm    │
│              │   │                │  │              │
│ chromosome   │   │ classifier.py  │  │ interpreter  │
│ operators    │   │ (RF, SVM, LR)  │  │ prompts      │
│ fitness      │   └────────────────┘  └──────┬───────┘
│ algorithm    │                              │
└───────┬──────┘                     ┌────────▼───────┐
        │                            │  Anthropic API │
┌───────▼──────┐                     │  Claude Haiku  │
│  src/data    │                     └────────────────┘
│              │
│  loader.py   │──── sklearn breast_cancer dataset
└──────────────┘

        data/results/  ← respostas LLM salvas (base Fase 3)
```

## Fluxo do Algoritmo Genético

```
Inicialização
     │
     ▼
Avaliação da população inicial
(treina modelo → calcula fitness)
     │
     ▼
┌────┤ Loop de Gerações ├────────────────────────────────┐
│                                                         │
│  Ordenação por fitness (decrescente)                    │
│         │                                               │
│         ▼                                               │
│  Elitismo → preserva N melhores                         │
│         │                                               │
│         ▼                                               │
│  Seleção por Torneio (k=3)                              │
│         │                                               │
│         ▼                                               │
│  Crossover Uniforme (p=0.80)                            │
│  → troca genes aleatoriamente entre pais                │
│         │                                               │
│         ▼                                               │
│  Mutação por Reset (p=0.15)                             │
│  → substitui gene por valor aleatório do domínio        │
│         │                                               │
│         ▼                                               │
│  Avaliação da nova população                            │
│         │                                               │
└─────────┴─── até N gerações ───────────────────────────┘
     │
     ▼
Melhor cromossomo (hiperparâmetros ótimos)
```

## Função Fitness

```
fitness = 0.40 × sensibilidade   (recall — minimiza falsos negativos)
        + 0.25 × especificidade  (minimiza alarmes falsos)
        + 0.25 × F1-score        (equilíbrio precisão/sensibilidade)
        + 0.10 × equidade        (1 - std(accuracy por grupo etário))
```

**Justificativa dos pesos:**
- Sensibilidade recebe maior peso pois falsos negativos (câncer não detectado) são clinicamente mais graves que falsos positivos
- Equidade garante que o modelo não discrimine por faixa etária

## Representação Genética (Exemplo: Random Forest)

| Gene | Domínio |
|------|---------|
| n_estimators | [50, 100, 150, 200, 300, 500] |
| max_depth | [None, 5, 10, 15, 20] |
| min_samples_split | [2, 5, 10, 20] |
| min_samples_leaf | [1, 2, 4, 8] |
| max_features | ['sqrt', 'log2'] |
| class_weight | ['balanced', None] |

## Integração com LLM (Claude)

```
Resultado do Modelo
       │
       ▼
Construção do Prompt
(contexto médico feminino +
 dados da paciente +
 métricas do modelo)
       │
       ▼
Claude Haiku API
(system prompt especializado)
       │
       ▼
Interpretação em Linguagem Natural
       │
  ┌────┴────┐
  │         │
  ▼         ▼
Exibição  Salvo em
no app    data/results/
          (base Fase 3)
```

## Estrutura de Pastas

```
tech-challege-2/
├── src/
│   ├── data/        # Carregamento e pré-processamento
│   ├── models/      # Definição e fábrica de modelos
│   ├── genetic/     # Cromossomo, operadores, fitness, AG
│   ├── llm/         # Integração Claude + prompt engineering
│   └── utils/       # Métricas e utilitários
├── app/
│   └── streamlit_app.py   # Interface visual
├── experiments/
│   └── run_experiments.py # 3 experimentos comparativos
├── tests/                 # Testes unitários (pytest)
├── data/results/          # Respostas LLM persistidas
└── docs/                  # Esta documentação
```

## Decisões de Design

1. **Cromossomo como dataclass**: facilita cópia imutável e serialização
2. **Elitismo + Torneio**: combina preservação dos melhores com diversidade genética
3. **Fitness ponderado**: reflete prioridades clínicas reais do rastreamento oncológico
4. **Grupos etários sintéticos**: simula diversidade demográfica para avaliação de equidade
5. **Respostas LLM persistidas**: prepara dataset para fine-tuning na Fase 3
6. **Graceful degradation sem API key**: sistema funciona com mock responses para demonstração
