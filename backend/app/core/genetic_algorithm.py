import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from .models import DeliveryPoint, Depot, Solution, Vehicle
from .fitness import build_distance_matrix
from .operators import mutate, order_crossover, roulette_selection, tournament_selection
from .vrp import decode


@dataclass
class GAConfig:
    population_size: int = 100
    generations: int = 300
    mutation_probability: float = 0.3
    elitism: int = 2
    selection: str = "tournament"  # "tournament" | "roulette"
    tournament_k: int = 3
    stagnation_limit: int = 80  # para se não houver melhoria após N gerações (0 = desligado)
    seed: Optional[int] = None


@dataclass
class GAResult:
    best_solution: Solution
    best_tour: List[int]
    history: List[float] = field(default_factory=list)  # melhor fitness por geração
    generations_run: int = 0

    def to_dict(self) -> dict:
        return {
            "best_solution": self.best_solution.to_dict(),
            "history": [round(f, 3) for f in self.history],
            "generations_run": self.generations_run,
        }


def run_ga(
    depot: Depot,
    points: Sequence[DeliveryPoint],
    vehicles: Sequence[Vehicle],
    config: GAConfig,
) -> GAResult:
    if config.seed is not None:
        random.seed(config.seed)

    points_by_id: Dict[int, DeliveryPoint] = {p.id: p for p in points}
    vehicles_by_id: Dict[int, Vehicle] = {v.id: v for v in vehicles}
    dist = build_distance_matrix(depot, points)

    ids = [p.id for p in points]

    # população inicial: permutações aleatórias (mesma ideia do código base)
    population: List[List[int]] = [random.sample(ids, len(ids)) for _ in range(config.population_size)]

    def evaluate(tour: List[int]) -> Solution:
        return decode(tour, points_by_id, vehicles_by_id, vehicles, dist)

    history: List[float] = []
    best_tour: List[int] = population[0]
    best_solution: Solution = evaluate(best_tour)
    stagnation = 0
    generation = 0

    for generation in range(1, config.generations + 1):
        solutions = [evaluate(tour) for tour in population]
        fitnesses = [s.fitness for s in solutions]

        # ordena a população por fitness (crescente, menor é melhor)
        order = sorted(range(len(population)), key=lambda i: fitnesses[i])
        population = [population[i] for i in order]
        solutions = [solutions[i] for i in order]
        fitnesses = [fitnesses[i] for i in order]

        if fitnesses[0] < best_solution.fitness - 1e-9:
            best_solution = solutions[0]
            best_tour = list(population[0])
            stagnation = 0
        else:
            stagnation += 1

        history.append(best_solution.fitness)

        if config.stagnation_limit and stagnation >= config.stagnation_limit:
            break

        # elitismo: mantém os N melhores indivíduos sem alteração
        new_population: List[List[int]] = [list(t) for t in population[: config.elitism]]

        while len(new_population) < config.population_size:
            if config.selection == "roulette":
                parent1 = roulette_selection(population, fitnesses)
                parent2 = roulette_selection(population, fitnesses)
            else:
                parent1 = tournament_selection(population, fitnesses, config.tournament_k)
                parent2 = tournament_selection(population, fitnesses, config.tournament_k)

            child = order_crossover(parent1, parent2)
            child = mutate(child, config.mutation_probability)
            new_population.append(child)

        population = new_population

    return GAResult(
        best_solution=best_solution,
        best_tour=best_tour,
        history=history,
        generations_run=generation,
    )
