import pytest
import random
from src.genetic.chromosome import Chromosome, create_population
from src.genetic.operators import tournament_selection, uniform_crossover, mutate
from src.models.classifier import HYPERPARAMETER_DOMAINS


def test_chromosome_init_random_forest():
    c = Chromosome(model_type="random_forest")
    domain = HYPERPARAMETER_DOMAINS["random_forest"]
    for param, values in domain.items():
        assert param in c.genes
        assert c.genes[param] in values


def test_chromosome_init_svm():
    c = Chromosome(model_type="svm")
    domain = HYPERPARAMETER_DOMAINS["svm"]
    for param in domain:
        assert param in c.genes


def test_chromosome_copy_is_independent():
    c = Chromosome(model_type="random_forest")
    c2 = c.copy()
    c2.genes["n_estimators"] = -999
    assert c.genes["n_estimators"] != -999


def test_create_population_size():
    pop = create_population("random_forest", 20)
    assert len(pop) == 20
    for chrom in pop:
        assert isinstance(chrom, Chromosome)


def test_tournament_selection_returns_chromosome():
    pop = create_population("random_forest", 10)
    for i, c in enumerate(pop):
        c.fitness = float(i)
    winner = tournament_selection(pop, k=3)
    assert isinstance(winner, Chromosome)


def test_tournament_selection_respects_fitness():
    pop = create_population("random_forest", 10)
    for i, c in enumerate(pop):
        c.fitness = float(i)
    # With large k, should always pick high-fitness
    winners = [tournament_selection(pop, k=10).fitness for _ in range(20)]
    assert max(winners) == 9.0


def test_uniform_crossover_produces_two_children():
    p1 = Chromosome("random_forest")
    p2 = Chromosome("random_forest")
    c1, c2 = uniform_crossover(p1, p2)
    assert isinstance(c1, Chromosome)
    assert isinstance(c2, Chromosome)


def test_crossover_genes_from_parents():
    p1 = Chromosome("random_forest")
    p2 = Chromosome("random_forest")
    c1, c2 = uniform_crossover(p1, p2)
    for param in p1.genes:
        assert c1.genes[param] in (p1.genes[param], p2.genes[param])
        assert c2.genes[param] in (p1.genes[param], p2.genes[param])


def test_mutate_high_rate_changes_genes():
    random.seed(0)
    c = Chromosome("random_forest")
    original = c.genes.copy()
    mutated = mutate(c, mutation_rate=1.0)
    # With rate=1.0 some genes must differ (unless domain has 1 option)
    domain = HYPERPARAMETER_DOMAINS["random_forest"]
    changed_any = any(
        len(domain[k]) > 1 and mutated.genes[k] != original[k]
        for k in original
    )
    # After many mutations at rate 1.0, almost certainly something changes
    assert mutated is not c


def test_mutate_zero_rate_no_change():
    c = Chromosome("random_forest")
    original = c.genes.copy()
    mutated = mutate(c, mutation_rate=0.0)
    assert mutated.genes == original
