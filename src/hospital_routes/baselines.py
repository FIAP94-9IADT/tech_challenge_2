"""Abordagens de referência para comparação com o algoritmo genético."""

from __future__ import annotations

from itertools import permutations

from .genetic import GeneticOptimizer
from .models import Solution


def nearest_neighbor(optimizer: GeneticOptimizer) -> Solution:
    return optimizer.evaluate(optimizer._nearest_neighbor_seed())


def brute_force(optimizer: GeneticOptimizer, max_deliveries: int = 9) -> Solution:
    n = len(optimizer.problem.deliveries)
    if n > max_deliveries:
        raise ValueError(f"Força bruta limitada a {max_deliveries} entregas devido ao custo fatorial")
    return min((optimizer.evaluate(list(p)) for p in permutations(range(n))), key=lambda s: s.fitness)
