"""
Otimização Multi-Objetivo via NSGA-II (DEAP).
Implementa o conceito de Otimização Multi-Objetivo do PDF — busca simultaneamente
maximizar SENSIBILIDADE e ESPECIFICIDADE, gerando a Fronteira de Pareto.
Cada ponto da fronteira representa um trade-off ótimo entre os dois objetivos.
"""

import random
import numpy as np
from dataclasses import dataclass

from deap import base, creator, tools, algorithms

from src.models.classifier import HYPERPARAMETER_DOMAINS, build_model
from src.genetic.fitness import sensitivity, specificity, get_detailed_metrics

# DEAP usa estado global — garante criação única das classes
if not hasattr(creator, "FitnessMulti"):
    creator.create("FitnessMulti", base.Fitness, weights=(1.0, 1.0))
if not hasattr(creator, "IndividualMulti"):
    creator.create("IndividualMulti", list, fitness=creator.FitnessMulti)


def _decode_individual(individual: list, model_type: str) -> dict:
    """Converte lista de índices em dicionário de hiperparâmetros."""
    domain = HYPERPARAMETER_DOMAINS[model_type]
    return {
        param: values[idx % len(values)]
        for (param, values), idx in zip(domain.items(), individual)
    }


def _make_evaluate(model_type, X_train, y_train, X_val, y_val):
    """Retorna função de avaliação bi-objetivo (sensibilidade, especificidade)."""
    def evaluate(individual):
        params = _decode_individual(individual, model_type)
        try:
            model = build_model(model_type, params)
            model.fit(X_train, y_train)
            y_pred = model.predict(X_val)
            s = sensitivity(y_val.values, y_pred)
            sp = specificity(y_val.values, y_pred)
            return s, sp
        except Exception:
            return 0.0, 0.0
    return evaluate


@dataclass
class NSGAIIResult:
    pareto_front: list[dict]
    all_generations_stats: list[dict]
    best_balanced: dict


def run_nsga2(
    model_type: str,
    X_train,
    y_train,
    X_val,
    y_val,
    X_test,
    y_test,
    population_size: int = 40,
    generations: int = 20,
    crossover_prob: float = 0.8,
    mutation_prob: float = 0.2,
    random_state: int = 42,
) -> NSGAIIResult:
    """
    Executa NSGA-II para otimização bi-objetivo de hiperparâmetros.

    Objetivos:
        1. Maximizar Sensibilidade (recall) — detectar todos os casos de câncer
        2. Maximizar Especificidade — evitar alarmes falsos
    """
    random.seed(random_state)
    np.random.seed(random_state)

    # eaMuPlusLambda exige mu divisível por 4 para selNSGA2 interno
    population_size = max(4, (population_size + 3) // 4 * 4)

    domain = HYPERPARAMETER_DOMAINS[model_type]
    domain_sizes = [len(v) for v in domain.values()]

    toolbox = base.Toolbox()
    toolbox.register(
        "individual",
        tools.initIterate,
        creator.IndividualMulti,
        lambda: [random.randint(0, s - 1) for s in domain_sizes],
    )
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", _make_evaluate(model_type, X_train, y_train, X_val, y_val))
    toolbox.register("mate", tools.cxUniform, indpb=0.5)
    toolbox.register("mutate", _bounded_mutation, domain_sizes=domain_sizes, indpb=0.3)
    toolbox.register("select", tools.selNSGA2)

    pop = toolbox.population(n=population_size)

    # Avalia população inicial
    for ind, fit in zip(pop, map(toolbox.evaluate, pop)):
        ind.fitness.values = fit

    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", lambda vals: np.mean(vals, axis=0).tolist())
    stats.register("max", lambda vals: np.max(vals, axis=0).tolist())

    # eaMuPlusLambda é o loop oficial do DEAP para NSGA-II —
    # lida corretamente com crowding_dist internamente
    pop, logbook = algorithms.eaMuPlusLambda(
        pop,
        toolbox,
        mu=population_size,
        lambda_=population_size,
        cxpb=crossover_prob,
        mutpb=mutation_prob,
        ngen=generations,
        stats=stats,
        halloffame=None,
        verbose=False,
    )

    gen_stats = [dict(r) for r in logbook]

    # Extrai fronteira de Pareto final
    pareto = tools.sortNondominated(pop, len(pop), first_front_only=True)[0]

    pareto_results = []
    for ind in pareto:
        params = _decode_individual(ind, model_type)
        m = build_model(model_type, params)
        m.fit(X_train, y_train)
        y_pred_test = m.predict(X_test)
        metrics = get_detailed_metrics(y_test.values, y_pred_test)
        pareto_results.append({
            "params": params,
            "val_sensitivity": ind.fitness.values[0],
            "val_specificity": ind.fitness.values[1],
            "test_metrics": metrics,
        })

    pareto_results.sort(key=lambda x: x["val_sensitivity"] + x["val_specificity"], reverse=True)

    return NSGAIIResult(
        pareto_front=pareto_results,
        all_generations_stats=gen_stats,
        best_balanced=pareto_results[0] if pareto_results else {},
    )


def _bounded_mutation(individual, domain_sizes, indpb):
    """Mutação com reset aleatório mantendo índices dentro dos limites do domínio."""
    for i, size in enumerate(domain_sizes):
        if random.random() < indpb:
            individual[i] = random.randint(0, size - 1)
    return (individual,)
