"""Algoritmo genético especializado para o VRP hospitalar."""

from __future__ import annotations

import random
from dataclasses import dataclass
from statistics import mean, pstdev

from .models import Problem, RouteMetrics, Solution, build_distance_matrix


@dataclass(frozen=True)
class GAConfig:
    population_size: int = 120
    generations: int = 300
    crossover_rate: float = 0.90
    mutation_rate: float = 0.20
    elite_size: int = 4
    tournament_size: int = 4
    capacity_penalty: float = 1_000.0
    autonomy_penalty: float = 1_000.0
    priority_weight: float = 0.35
    stagnation_limit: int = 70
    seed: int = 42

    def __post_init__(self) -> None:
        if self.population_size < 4 or self.elite_size >= self.population_size:
            raise ValueError("Tamanho de população ou elite inválido")
        if not 0 <= self.crossover_rate <= 1 or not 0 <= self.mutation_rate <= 1:
            raise ValueError("As taxas devem estar entre zero e um")


@dataclass
class GenerationStats:
    generation: int
    best: float
    mean: float
    standard_deviation: float


class GeneticOptimizer:
    """Minimiza distância, atraso de prioridade e violações de restrições."""

    def __init__(self, problem: Problem, config: GAConfig | None = None):
        self.problem = problem
        self.config = config or GAConfig()
        self.rng = random.Random(self.config.seed)
        self.distances = build_distance_matrix(problem)
        self.history: list[GenerationStats] = []

    def _decode(self, chromosome: list[int]) -> list[list[int]]:
        """Distribui a permutação entre veículos por carga, preservando a ordem."""
        routes: list[list[int]] = [[] for _ in self.problem.vehicles]
        loads = [0.0] * len(routes)
        distances = [0.0] * len(routes)
        last = [0] * len(routes)

        for gene in chromosome:
            delivery = self.problem.deliveries[gene]
            candidates: list[tuple[float, int]] = []
            for i, vehicle in enumerate(self.problem.vehicles):
                projected_load = loads[i] + delivery.demand_kg
                projected_distance = (
                    distances[i]
                    + self.distances[last[i]][gene + 1]
                    + self.distances[gene + 1][0]
                )
                load_ratio = projected_load / vehicle.capacity_kg
                distance_ratio = projected_distance / vehicle.max_distance_km
                violation = max(0.0, load_ratio - 1) + max(0.0, distance_ratio - 1)
                candidates.append((violation * 100 + load_ratio + distance_ratio, i))
            _, chosen = min(candidates)
            if routes[chosen]:
                distances[chosen] -= self.distances[last[chosen]][0]
            distances[chosen] += self.distances[last[chosen]][gene + 1] + self.distances[gene + 1][0]
            routes[chosen].append(gene)
            loads[chosen] += delivery.demand_kg
            last[chosen] = gene + 1
        return routes

    def evaluate_routes(self, routes: list[list[int]]) -> Solution:
        metrics: list[RouteMetrics] = []
        total_cost = 0.0
        for i, route in enumerate(routes):
            vehicle = self.problem.vehicles[i]
            distance = 0.0
            priority_delay = 0.0
            previous = 0
            cumulative = 0.0
            for gene in route:
                leg = self.distances[previous][gene + 1]
                distance += leg
                cumulative += leg
                # Entregas críticas (3) sofrem penalidade maior quando visitadas tarde.
                priority_delay += cumulative * self.problem.deliveries[gene].priority
                previous = gene + 1
            if route:
                distance += self.distances[previous][0]
            load = sum(self.problem.deliveries[j].demand_kg for j in route)
            capacity_excess = max(0.0, load - vehicle.capacity_kg)
            autonomy_excess = max(0.0, distance - vehicle.max_distance_km)
            metric = RouteMetrics(distance, load, priority_delay, capacity_excess, autonomy_excess)
            metrics.append(metric)
            total_cost += (
                distance
                + self.config.priority_weight * priority_delay
                + self.config.capacity_penalty * capacity_excess
                + self.config.autonomy_penalty * autonomy_excess
            )
        return Solution(routes=routes, fitness=total_cost, metrics=metrics)

    def evaluate(self, chromosome: list[int]) -> Solution:
        return self.evaluate_routes(self._decode(chromosome))

    def _initial_population(self) -> list[list[int]]:
        genes = list(range(len(self.problem.deliveries)))
        # Hotstart simples: prioridades maiores primeiro e vizinho mais próximo.
        priority_seed = sorted(genes, key=lambda i: -self.problem.deliveries[i].priority)
        population = [priority_seed, self._nearest_neighbor_seed()]
        while len(population) < self.config.population_size:
            individual = genes.copy()
            self.rng.shuffle(individual)
            population.append(individual)
        return population

    def _nearest_neighbor_seed(self) -> list[int]:
        remaining = set(range(len(self.problem.deliveries)))
        result, current = [], 0
        while remaining:
            chosen = min(
                remaining,
                key=lambda j: self.distances[current][j + 1]
                / self.problem.deliveries[j].priority,
            )
            result.append(chosen)
            remaining.remove(chosen)
            current = chosen + 1
        return result

    def _select(self, population: list[list[int]], fitness: list[float]) -> list[int]:
        candidates = self.rng.sample(range(len(population)), self.config.tournament_size)
        return population[min(candidates, key=lambda i: fitness[i])]

    def order_crossover(self, parent1: list[int], parent2: list[int]) -> list[int]:
        """OX1: mantém um segmento e completa o filho na ordem do segundo pai."""
        if len(parent1) < 2:
            return parent1.copy()
        start, end = sorted(self.rng.sample(range(len(parent1)), 2))
        child: list[int | None] = [None] * len(parent1)
        child[start : end + 1] = parent1[start : end + 1]
        missing = [gene for gene in parent2 if gene not in child]
        positions = list(range(end + 1, len(child))) + list(range(0, start))
        for position, gene in zip(positions, missing):
            child[position] = gene
        return [int(gene) for gene in child]

    def mutate(self, chromosome: list[int]) -> None:
        if len(chromosome) < 2 or self.rng.random() >= self.config.mutation_rate:
            return
        a, b = sorted(self.rng.sample(range(len(chromosome)), 2))
        if self.rng.random() < 0.5:
            chromosome[a], chromosome[b] = chromosome[b], chromosome[a]
        else:
            chromosome[a : b + 1] = reversed(chromosome[a : b + 1])

    def evolve(self):
        """Executa a evolução e entrega o melhor resultado após cada geração."""
        population = self._initial_population()
        best_solution: Solution | None = None
        stagnant = 0
        self.history.clear()

        for generation in range(self.config.generations):
            solutions = [self.evaluate(individual) for individual in population]
            fitness = [solution.fitness for solution in solutions]
            order = sorted(range(len(population)), key=lambda i: fitness[i])
            self.history.append(GenerationStats(generation, fitness[order[0]], mean(fitness), pstdev(fitness)))

            if best_solution is None or solutions[order[0]].fitness < best_solution.fitness:
                best_solution = solutions[order[0]]
                best_solution.generation = generation
                stagnant = 0
            else:
                stagnant += 1
            yield self.history[-1], best_solution
            if stagnant >= self.config.stagnation_limit:
                break

            next_population = [population[i].copy() for i in order[: self.config.elite_size]]
            while len(next_population) < self.config.population_size:
                parent1 = self._select(population, fitness)
                parent2 = self._select(population, fitness)
                child = (
                    self.order_crossover(parent1, parent2)
                    if self.rng.random() < self.config.crossover_rate
                    else parent1.copy()
                )
                self.mutate(child)
                next_population.append(child)
            population = next_population

    def run(self) -> Solution:
        best_solution: Solution | None = None
        for _, best_solution in self.evolve():
            pass
        assert best_solution is not None
        return best_solution
