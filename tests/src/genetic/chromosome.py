import random
from dataclasses import dataclass, field
from src.models.classifier import HYPERPARAMETER_DOMAINS


@dataclass
class Chromosome:
    """
    Representa um indivíduo no algoritmo genético.
    Cada gene corresponde a um hiperparâmetro do modelo.
    """

    model_type: str
    genes: dict = field(default_factory=dict)
    fitness: float = 0.0

    def __post_init__(self):
        if not self.genes:
            self.genes = self._random_init()

    def _random_init(self) -> dict:
        domain = HYPERPARAMETER_DOMAINS[self.model_type]
        return {param: random.choice(values) for param, values in domain.items()}

    def copy(self) -> "Chromosome":
        return Chromosome(
            model_type=self.model_type,
            genes=self.genes.copy(),
            fitness=self.fitness,
        )

    def __repr__(self) -> str:
        return f"Chromosome(fitness={self.fitness:.4f}, genes={self.genes})"


def create_population(model_type: str, size: int) -> list[Chromosome]:
    """Cria uma população inicial de cromossomos aleatórios."""
    return [Chromosome(model_type=model_type) for _ in range(size)]
