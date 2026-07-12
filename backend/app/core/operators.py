import random
from typing import List, Sequence

Chromosome = List[int]  # permutation of delivery point ids


def order_crossover(parent1: Chromosome, parent2: Chromosome) -> Chromosome:
    """Crossover de ordem (OX): copia um trecho aleatório do parent1 e
    preenche as posições restantes com os genes do parent2, preservando
    a ordem relativa deles."""
    length = len(parent1)
    if length < 2:
        return list(parent1)

    start = random.randint(0, length - 2)
    end = random.randint(start + 1, length)

    child_slice = parent1[start:end]
    in_slice = set(child_slice)
    remaining = [gene for gene in parent2 if gene not in in_slice]

    child = remaining[:start] + child_slice + remaining[start:]
    return child


def swap_mutation(chromosome: Chromosome, probability: float) -> Chromosome:
    """Mutação do código base: troca dois genes adjacentes."""
    mutated = list(chromosome)
    if random.random() < probability and len(mutated) >= 2:
        i = random.randint(0, len(mutated) - 2)
        mutated[i], mutated[i + 1] = mutated[i + 1], mutated[i]
    return mutated


def inversion_mutation(chromosome: Chromosome, probability: float, max_segment: int = 0) -> Chromosome:
    """Inverte um segmento aleatório do cromossomo (movimento estilo 2-opt).

    Este era o TODO deixado no código base. Inverter um segmento é um
    movimento muito mais forte para problemas de roteamento do que uma
    simples troca, pois pode remover cruzamentos de caminho em um único
    passo.
    """
    mutated = list(chromosome)
    n = len(mutated)
    if random.random() < probability and n >= 2:
        if max_segment and max_segment >= 2:
            seg_len = random.randint(2, min(max_segment, n))
        else:
            seg_len = random.randint(2, n)
        start = random.randint(0, n - seg_len)
        mutated[start:start + seg_len] = reversed(mutated[start:start + seg_len])
    return mutated


def mutate(chromosome: Chromosome, probability: float) -> Chromosome:
    """Aplica inversão 70% das vezes e troca adjacente 30% das vezes."""
    if random.random() < 0.7:
        return inversion_mutation(chromosome, probability)
    return swap_mutation(chromosome, probability)


def tournament_selection(population: Sequence[Chromosome], fitnesses: Sequence[float], k: int = 3) -> Chromosome:
    """Escolhe k indivíduos aleatórios e retorna o melhor (menor fitness)."""
    contenders = random.sample(range(len(population)), min(k, len(population)))
    best = min(contenders, key=lambda i: fitnesses[i])
    return population[best]


def roulette_selection(population: Sequence[Chromosome], fitnesses: Sequence[float]) -> Chromosome:
    """Seleção proporcional ao fitness usando o inverso do fitness
    (menor fitness = maior chance). Mesma ideia esboçada no tsp.py
    base com numpy, mas sem a dependência."""
    weights = [1.0 / f if f > 0 else 1.0 for f in fitnesses]
    return random.choices(population, weights=weights, k=1)[0]
