# Algoritmo Genético — Arquitetura e Implementação

Documentação do módulo `src/genetic/`, baseada nos conceitos da Aula 3 — Introdução ao Algoritmo Genético (FIAP PosTech).

---

## Estrutura do Módulo

```
src/genetic/
├── chromosome.py   # Representação do indivíduo (codificação)
├── operators.py    # Seleção, crossover e mutação
├── fitness.py      # Função de aptidão e métricas de diversidade
└── algorithm.py    # Loop principal, GAConfig e GAResult
```

---

## Representação dos Indivíduos (Codificação)

Cada indivíduo (`Chromosome`) representa uma solução candidata — um conjunto de hiperparâmetros para um modelo de ML. A codificação é **híbrida**: parâmetros numéricos discretos e parâmetros categóricos convivem no mesmo cromossomo.

```python
@dataclass
class Chromosome:
    model_type: str          # "random_forest" | "svm" | "logistic_regression"
    genes: dict              # hiperparâmetros como dicionário
    fitness: float = 0.0
```

**Exemplo de genes para Random Forest:**

| Gene | Tipo | Domínio |
|------|------|---------|
| `n_estimators` | Numérico | `[50, 100, 150, 200, 300, 500]` |
| `max_depth` | Numérico | `[None, 5, 10, 15, 20]` |
| `min_samples_split` | Numérico | `[2, 5, 10, 20]` |
| `min_samples_leaf` | Numérico | `[1, 2, 4, 8]` |
| `max_features` | Categórico | `["sqrt", "log2"]` |
| `class_weight` | Categórico | `["balanced", None]` |

---

## Inicialização da População

Suportados dois métodos conforme a Aula 3:

### Aleatória (padrão)
Cada cromossomo tem seus genes amostrados uniformemente do domínio de cada parâmetro. Promove diversidade inicial e evita convergência prematura para ótimos locais.

### Hotstart
Quando `hotstart_params` é fornecido no `GAConfig`, o primeiro indivíduo é inicializado com esses parâmetros (por exemplo, resultado de uma busca anterior). Os demais são gerados aleatoriamente. Útil quando já existe uma boa aproximação da solução.

```python
config = GAConfig(
    hotstart_params={"n_estimators": 200, "max_depth": 10, ...}
)
```

---

## Função de Aptidão (Fitness)

A função fitness avalia quão bem o cromossomo resolve o problema clínico:

```
fitness = 0.40 × sensibilidade   (minimiza falsos negativos — câncer não detectado)
        + 0.25 × especificidade  (minimiza alarmes falsos)
        + 0.25 × F1-score        (equilíbrio precisão/sensibilidade)
        + 0.10 × equidade        (1 − σ(balanced_accuracy por faixa etária))
```

O modelo é treinado em `X_train` e avaliado em `X_val` a cada chamada.

---

## Operadores Genéticos

### Seleção por Torneio
`k` indivíduos são amostrados aleatoriamente da população; o de maior fitness é selecionado. Evita dominância de um único indivíduo enquanto mantém pressão seletiva.

### Crossover

Dois métodos disponíveis, configuráveis via `GAConfig.crossover_method`:

#### Uniforme (`"uniform"`)
Para cada gene, sorteia-se aleatoriamente de qual pai herdar (probabilidade 0,5). Não faz distinção entre tipos de parâmetro.

#### Aritmético (`"arithmetic"`)
Aplica combinação linear por índice para parâmetros **numéricos**; troca aleatória para **categóricos**.

```
filho1[i] = round(α × idx_pai1[i] + (1−α) × idx_pai2[i])
filho2[i] = round((1−α) × idx_pai1[i] + α × idx_pai2[i])
```

`α` é amostrado uniformemente em `[0, 1]` a cada cruzamento. Isso gera filhos com valores intermediários entre os pais, explorando o espaço de busca de forma mais suave.

**Quando usar:** problemas onde parâmetros numéricos têm ordenação significativa (e.g., `n_estimators`, `C`).

### Mutação

Dois métodos disponíveis, configuráveis via `GAConfig.mutation_method`:

#### Reset Aleatório (`"random_reset"`)
Cada gene é substituído por um valor aleatório do seu domínio com probabilidade `mutation_rate`. Implementa exploração ampla.

#### Gaussiana (`"gaussian"`)
Para parâmetros **numéricos**: desloca o índice atual por `round(N(0, intensity))`, garantindo que o novo valor pertença ao domínio. Para **categóricos**: reset aleatório.

```
novo_idx = clamp(idx_atual + round(N(0, intensity)), 0, len(domínio)−1)
```

`intensity` controla a magnitude da perturbação:
- `intensity = 0.5` → pequenos ajustes locais (refinamento)
- `intensity = 2.0` → saltos maiores (exploração)

**Quando usar:** quando a busca já está próxima de uma boa região e se quer refinar sem destruir boas soluções.

---

## Métricas de Convergência e Diversidade

Registradas por geração em `GAResult`:

### Desvio Padrão da Aptidão (`std_fitness_per_gen`)
```
σ(fitness) por geração
```
Redução ao longo das gerações indica convergência — a população está se tornando mais homogênea.

### Entropia Genética (`diversity_per_gen`)
```
H = −∑ pᵢ · log₂(pᵢ)
```
onde `pᵢ` é a proporção de indivíduos com genes idênticos na população.

- **H alto** → população diversificada, exploração ativa
- **H baixo** → convergência, aproveitamento de boas soluções

Valor máximo teórico: `log₂(population_size)` (todos os indivíduos distintos).

---

## Ajuste Dinâmico de Taxas (Adaptativo)

Quando `GAConfig.adaptive = True`, as taxas de mutação e crossover são ajustadas a cada geração com base na entropia atual em relação à entropia máxima:

| Situação | Ação |
|----------|------|
| Entropia < 30 % do máximo | Aumenta mutação (×2) e crossover (×1.1) — reintroduz diversidade |
| Entropia > 70 % do máximo | Reduz mutação (×0.7) e crossover (×0.9) — aproveita boas soluções |
| 30 %–70 % | Mantém taxas base |

As taxas ajustadas são sempre limitadas a intervalos seguros (`[0.05, 0.40]` para mutação, `[0.50, 0.95]` para crossover).

---

## Configuração Completa (GAConfig)

```python
@dataclass
class GAConfig:
    population_size: int = 50          # tamanho da população
    generations: int = 30              # número de gerações
    crossover_rate: float = 0.8        # probabilidade de crossover
    mutation_rate: float = 0.15        # probabilidade de mutação por gene
    elitism_count: int = 2             # indivíduos preservados por elitismo
    tournament_k: int = 3              # tamanho do torneio de seleção
    random_state: int = 42             # semente para reprodutibilidade

    crossover_method: str = "uniform"      # "uniform" | "arithmetic"
    mutation_method: str = "random_reset"  # "random_reset" | "gaussian"
    mutation_intensity: float = 1.0        # intensidade da mutação gaussiana

    adaptive: bool = False             # ajuste dinâmico de taxas
    hotstart_params: dict | None = None    # inicialização com solução prévia
```

---

## Fluxo Completo do Algoritmo

```
INÍCIO
  │
  ▼
Inicialização da população
(aleatória ou hotstart)
  │
  ▼
Avaliação: treina modelo → calcula fitness para cada indivíduo
  │
  ▼
┌──────────────── Loop de Gerações ─────────────────────────┐
│                                                            │
│  1. Ordenação por fitness (decrescente)                    │
│                                                            │
│  2. Registro de métricas por geração:                      │
│     · melhor fitness, média, desvio padrão                 │
│     · entropia genética (diversidade)                      │
│                                                            │
│  3. Ajuste dinâmico de taxas (se adaptive=True)            │
│                                                            │
│  4. Elitismo: copia os N melhores direto para próx. geração│
│                                                            │
│  5. Até completar população:                               │
│     a. Seleção por torneio (×2 pais)                       │
│     b. Crossover (uniforme ou aritmético)                  │
│     c. Mutação (reset ou gaussiana)                        │
│     d. Avaliação dos filhos                                │
│                                                            │
│  6. Substitui população antiga                             │
│                                                            │
└──────── até N gerações ────────────────────────────────────┘
  │
  ▼
Retorna GAResult com o melhor cromossomo
e histórico completo de métricas
```

---

## Resultado (GAResult)

```python
@dataclass
class GAResult:
    best_chromosome: Chromosome        # melhor solução encontrada
    best_fitness_per_gen: list[float]  # melhor fitness por geração
    avg_fitness_per_gen: list[float]   # fitness médio por geração
    std_fitness_per_gen: list[float]   # desvio padrão por geração
    diversity_per_gen: list[float]     # entropia genética por geração
    generations_run: int               # gerações executadas
```

---

## Trade-offs dos Parâmetros

| Parâmetro | Aumentar | Diminuir |
|-----------|----------|----------|
| `population_size` | Mais diversidade, custo computacional maior | Convergência mais rápida, risco de ótimo local |
| `mutation_rate` | Mais exploração, risco de destruir boas soluções | Mais aproveitamento, risco de convergência prematura |
| `crossover_rate` | Mais combinação entre soluções (exploração) | Mais preservação dos pais (aproveitamento) |
| `mutation_intensity` | Saltos maiores no espaço de busca | Refinamento local suave |
| `elitism_count` | Preserva mais boas soluções | Maior diversidade entre gerações |
| `tournament_k` | Maior pressão seletiva | Seleção mais aleatória |
