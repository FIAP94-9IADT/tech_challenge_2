import random
from src.genetic.chromosome import Chromosome
from src.models.classifier import HYPERPARAMETER_DOMAINS


def _is_numerical(values: list) -> bool:
    return all(isinstance(v, (int, float)) for v in values)


def tournament_selection(population: list[Chromosome], k: int = 3) -> Chromosome:
    """Seleção por torneio: escolhe k indivíduos aleatórios e retorna o melhor."""
    candidates = random.sample(population, min(k, len(population)))
    return max(candidates, key=lambda c: c.fitness)


def uniform_crossover(parent1: Chromosome, parent2: Chromosome) -> tuple[Chromosome, Chromosome]:
    """Crossover uniforme: para cada gene, sorteia de qual pai herdar."""
    genes1, genes2 = {}, {}
    for param in parent1.genes:
        if random.random() < 0.5:
            genes1[param] = parent1.genes[param]
            genes2[param] = parent2.genes[param]
        else:
            genes1[param] = parent2.genes[param]
            genes2[param] = parent1.genes[param]

    child1 = Chromosome(model_type=parent1.model_type, genes=genes1)
    child2 = Chromosome(model_type=parent1.model_type, genes=genes2)
    return child1, child2


def arithmetic_crossover(
    parent1: Chromosome, parent2: Chromosome, alpha: float | None = None
) -> tuple[Chromosome, Chromosome]:
    """
    Crossover aritmético (PDF Aula 3 — Codificação Real).
    Para parâmetros numéricos: filho[i] = alpha*p1[i] + (1-alpha)*p2[i] → índice mais próximo.
    Para parâmetros categóricos: escolha aleatória entre os pais.
    """
    if alpha is None:
        alpha = random.random()

    domain = HYPERPARAMETER_DOMAINS[parent1.model_type]
    genes1, genes2 = {}, {}

    for param, values in domain.items():
        v1 = parent1.genes[param]
        v2 = parent2.genes[param]

        if _is_numerical(values):
            idx1 = values.index(v1)
            idx2 = values.index(v2)
            ni1 = max(0, min(len(values) - 1, round(alpha * idx1 + (1 - alpha) * idx2)))
            ni2 = max(0, min(len(values) - 1, round((1 - alpha) * idx1 + alpha * idx2)))
            genes1[param] = values[ni1]
            genes2[param] = values[ni2]
        else:
            if random.random() < 0.5:
                genes1[param], genes2[param] = v1, v2
            else:
                genes1[param], genes2[param] = v2, v1

    return (
        Chromosome(model_type=parent1.model_type, genes=genes1),
        Chromosome(model_type=parent1.model_type, genes=genes2),
    )


def mutate(chromosome: Chromosome, mutation_rate: float) -> Chromosome:
    """Mutação por reset aleatório: cada gene muta com prob. mutation_rate."""
    domain = HYPERPARAMETER_DOMAINS[chromosome.model_type]
    mutated = chromosome.copy()
    for param, values in domain.items():
        if random.random() < mutation_rate:
            mutated.genes[param] = random.choice(values)
    mutated.fitness = 0.0
    return mutated


def gaussian_mutate(
    chromosome: Chromosome, mutation_rate: float, intensity: float = 1.0
) -> Chromosome:
    """
    Mutação gaussiana (PDF Aula 3 — Codificação Real).
    Parâmetros numéricos: perturbação de índice amostrada de N(0, intensity).
    Parâmetros categóricos: reset aleatório.
    intensity maior → maior exploração; menor → refinamento local.
    """
    domain = HYPERPARAMETER_DOMAINS[chromosome.model_type]
    mutated = chromosome.copy()

    for param, values in domain.items():
        if random.random() < mutation_rate:
            if _is_numerical(values):
                current_idx = values.index(mutated.genes[param])
                delta = int(round(random.gauss(0, intensity)))
                new_idx = max(0, min(len(values) - 1, current_idx + delta))
                mutated.genes[param] = values[new_idx]
            else:
                mutated.genes[param] = random.choice(values)

    mutated.fitness = 0.0
    return mutated
