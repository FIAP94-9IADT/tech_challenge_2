import random
from dataclasses import dataclass, field
from typing import Callable

from src.genetic.chromosome import Chromosome, create_population
from src.genetic.operators import tournament_selection, uniform_crossover, mutate
from src.genetic.fitness import evaluate_chromosome


@dataclass
class GAConfig:
    population_size: int = 50
    generations: int = 30
    crossover_rate: float = 0.8
    mutation_rate: float = 0.15
    elitism_count: int = 2
    tournament_k: int = 3
    random_state: int = 42


@dataclass
class GAResult:
    best_chromosome: Chromosome
    best_fitness_per_gen: list[float] = field(default_factory=list)
    avg_fitness_per_gen: list[float] = field(default_factory=list)
    generations_run: int = 0


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
    """
    Executa o algoritmo genético para otimização de hiperparâmetros.

    Args:
        progress_callback: função chamada a cada geração com (geração, total, melhor_fitness)
    """
    if config is None:
        config = GAConfig()

    random.seed(config.random_state)

    population = create_population(model_type, config.population_size)

    for chrom in population:
        chrom.fitness = evaluate_chromosome(chrom, X_train, y_train, X_val, y_val, age_val)

    result = GAResult(best_chromosome=max(population, key=lambda c: c.fitness))

    for gen in range(config.generations):
        population.sort(key=lambda c: c.fitness, reverse=True)

        # Elitismo: preserva os melhores indivíduos
        new_population = [population[i].copy() for i in range(config.elitism_count)]

        while len(new_population) < config.population_size:
            parent1 = tournament_selection(population, config.tournament_k)
            parent2 = tournament_selection(population, config.tournament_k)

            if random.random() < config.crossover_rate:
                child1, child2 = uniform_crossover(parent1, parent2)
            else:
                child1, child2 = parent1.copy(), parent2.copy()

            child1 = mutate(child1, config.mutation_rate)
            child2 = mutate(child2, config.mutation_rate)

            child1.fitness = evaluate_chromosome(child1, X_train, y_train, X_val, y_val, age_val)
            child2.fitness = evaluate_chromosome(child2, X_train, y_train, X_val, y_val, age_val)

            new_population.extend([child1, child2])

        population = new_population[: config.population_size]

        best_gen = max(population, key=lambda c: c.fitness)
        avg_fitness = sum(c.fitness for c in population) / len(population)

        result.best_fitness_per_gen.append(best_gen.fitness)
        result.avg_fitness_per_gen.append(avg_fitness)

        if best_gen.fitness > result.best_chromosome.fitness:
            result.best_chromosome = best_gen.copy()

        if progress_callback:
            progress_callback(gen + 1, config.generations, best_gen.fitness)

    result.generations_run = config.generations
    return result
