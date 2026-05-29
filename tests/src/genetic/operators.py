import random
from src.genetic.chromosome import Chromosome
from src.models.classifier import HYPERPARAMETER_DOMAINS


def tournament_selection(population: list[Chromosome], k: int = 3) -> Chromosome:
    """Seleção por torneio: escolhe k indivíduos aleatórios e retorna o melhor."""
    candidates = random.sample(population, min(k, len(population)))
    return max(candidates, key=lambda c: c.fitness)


def uniform_crossover(parent1: Chromosome, parent2: Chromosome) -> tuple[Chromosome, Chromosome]:
    """
    Crossover uniforme: para cada gene, sorteia de qual pai herdar.
    Gera dois filhos.
    """
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


def mutate(chromosome: Chromosome, mutation_rate: float) -> Chromosome:
    """
    Mutação por reset aleatório: cada gene muta com probabilidade mutation_rate,
    sendo substituído por um valor aleatório do seu domínio.
    """
    domain = HYPERPARAMETER_DOMAINS[chromosome.model_type]
    mutated = chromosome.copy()
    for param, values in domain.items():
        if random.random() < mutation_rate:
            mutated.genes[param] = random.choice(values)
    mutated.fitness = 0.0
    return mutated
