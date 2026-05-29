import random
from dataclasses import dataclass, field
from typing import Callable

from src.genetic.chromosome import Chromosome, create_population
from src.genetic.operators import (
    tournament_selection,
    uniform_crossover,
    arithmetic_crossover,
    mutate,
    gaussian_mutate,
)
from src.genetic.fitness import (
    evaluate_chromosome,
    genetic_entropy,
    fitness_std,
)


@dataclass
class GAConfig:
    population_size: int = 50
    generations: int = 30
    crossover_rate: float = 0.8
    mutation_rate: float = 0.15
    elitism_count: int = 2
    tournament_k: int = 3
    random_state: int = 42
    # Métodos dos operadores (PDF Aula 3)
    crossover_method: str = "uniform"       # "uniform" | "arithmetic"
    mutation_method: str = "random_reset"   # "random_reset" | "gaussian"
    mutation_intensity: float = 1.0         # intensidade da mutação gaussiana
    # Ajuste dinâmico de taxas (PDF Aula 3 — Adaptação Dinâmica)
    adaptive: bool = False
    # Inicialização hotstart (PDF Aula 3 — Hotstart)
    hotstart_params: dict | None = None


@dataclass
class GAResult:
    best_chromosome: Chromosome
    best_fitness_per_gen: list[float] = field(default_factory=list)
    avg_fitness_per_gen: list[float] = field(default_factory=list)
    # Métricas de convergência e diversidade (PDF Aula 3)
    std_fitness_per_gen: list[float] = field(default_factory=list)
    diversity_per_gen: list[float] = field(default_factory=list)
    generations_run: int = 0


def _apply_crossover(
    method: str,
    parent1: Chromosome,
    parent2: Chromosome,
) -> tuple[Chromosome, Chromosome]:
    if method == "arithmetic":
        return arithmetic_crossover(parent1, parent2)
    return uniform_crossover(parent1, parent2)


def _apply_mutation(
    method: str,
    chromosome: Chromosome,
    rate: float,
    intensity: float,
) -> Chromosome:
    if method == "gaussian":
        return gaussian_mutate(chromosome, rate, intensity)
    return mutate(chromosome, rate)


def _adaptive_rates(
    base_mutation: float,
    base_crossover: float,
    diversity: float,
    max_entropy: float,
) -> tuple[float, float]:
    """
    Ajusta dinamicamente as taxas com base na diversidade atual (PDF Aula 3).
    Baixa diversidade → aumenta mutação e crossover para explorar mais.
    Alta diversidade → reduz para aproveitar boas soluções encontradas.
    """
    ratio = diversity / max_entropy if max_entropy > 0 else 0.5
    # Quando diversidade cai abaixo de 30 % do máximo, aumenta mutação
    if ratio < 0.3:
        mut = min(0.40, base_mutation * 2.0)
        cx = min(0.95, base_crossover * 1.1)
    # Quando diversidade está acima de 70 %, reduz mutação
    elif ratio > 0.7:
        mut = max(0.05, base_mutation * 0.7)
        cx = max(0.50, base_crossover * 0.9)
    else:
        mut = base_mutation
        cx = base_crossover
    return mut, cx


def run_genetic_algorithm(
    model_type: str,
    X_train,
    y_train,
    X_val,
    y_val,
    age_val=None,
    config: GAConfig | None = None,
    progress_callback: Callable[[int, int, float], None] | None = None,
) -> GAResult:
    """Executa o algoritmo genético para otimização de hiperparâmetros."""
    if config is None:
        config = GAConfig()

    random.seed(config.random_state)

    # Entropia máxima teórica: log2(population_size)
    import math
    max_entropy = math.log2(config.population_size) if config.population_size > 1 else 1.0

    # Inicialização (aleatória ou hotstart — PDF Aula 3)
    population = create_population(
        model_type, config.population_size, config.hotstart_params
    )

    for chrom in population:
        chrom.fitness = evaluate_chromosome(chrom, X_train, y_train, X_val, y_val, age_val)

    result = GAResult(best_chromosome=max(population, key=lambda c: c.fitness))

    current_mutation_rate = config.mutation_rate
    current_crossover_rate = config.crossover_rate

    for gen in range(config.generations):
        population.sort(key=lambda c: c.fitness, reverse=True)

        # Métricas de convergência e diversidade (PDF Aula 3)
        best_gen = population[0]
        avg_fitness = sum(c.fitness for c in population) / len(population)
        std = fitness_std(population)
        diversity = genetic_entropy(population)

        result.best_fitness_per_gen.append(best_gen.fitness)
        result.avg_fitness_per_gen.append(avg_fitness)
        result.std_fitness_per_gen.append(std)
        result.diversity_per_gen.append(diversity)

        if best_gen.fitness > result.best_chromosome.fitness:
            result.best_chromosome = best_gen.copy()

        if progress_callback:
            progress_callback(gen + 1, config.generations, best_gen.fitness)

        # Ajuste dinâmico de taxas (PDF Aula 3 — Adaptação Dinâmica)
        if config.adaptive:
            current_mutation_rate, current_crossover_rate = _adaptive_rates(
                config.mutation_rate,
                config.crossover_rate,
                diversity,
                max_entropy,
            )

        # Elitismo: preserva os melhores indivíduos
        new_population = [population[i].copy() for i in range(config.elitism_count)]

        while len(new_population) < config.population_size:
            parent1 = tournament_selection(population, config.tournament_k)
            parent2 = tournament_selection(population, config.tournament_k)

            if random.random() < current_crossover_rate:
                child1, child2 = _apply_crossover(config.crossover_method, parent1, parent2)
            else:
                child1, child2 = parent1.copy(), parent2.copy()

            child1 = _apply_mutation(
                config.mutation_method, child1, current_mutation_rate, config.mutation_intensity
            )
            child2 = _apply_mutation(
                config.mutation_method, child2, current_mutation_rate, config.mutation_intensity
            )

            child1.fitness = evaluate_chromosome(child1, X_train, y_train, X_val, y_val, age_val)
            child2.fitness = evaluate_chromosome(child2, X_train, y_train, X_val, y_val, age_val)

            new_population.extend([child1, child2])

        population = new_population[: config.population_size]

    result.generations_run = config.generations
    return result
