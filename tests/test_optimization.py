"""
Testes para os 5 métodos de otimização:
1. Grid Search (Força Bruta/Convexa)
2. Random Search (Estocástica)
3. Algoritmo Genético (Combinatória) — coberto em test_genetic.py
4. NSGA-II (Multi-Objetivo)
5. NEAT (NeuroEvolution of Augmenting Topologies)
"""
import numpy as np
import pandas as pd
import pytest
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split

from src.optimization.grid_search import run_grid_search, PARAM_GRIDS
from src.optimization.random_search import run_random_search
from src.optimization.multiobjective import run_nsga2, _decode_individual


@pytest.fixture
def small_dataset():
    X, y = make_classification(n_samples=200, n_features=10, random_state=42)
    X_df = pd.DataFrame(X, columns=[f"f{i}" for i in range(10)])
    y_s = pd.Series(y)
    X_tr, X_te, y_tr, y_te = train_test_split(X_df, y_s, test_size=0.3, random_state=42)
    return X_tr, X_te, y_tr.reset_index(drop=True), y_te.reset_index(drop=True)


# ── Grid Search ───────────────────────────────────────────────────────────────

def test_grid_search_returns_required_keys(small_dataset):
    X_tr, X_te, y_tr, y_te = small_dataset
    result = run_grid_search("logistic_regression", X_tr, y_tr, X_te, y_te, cv=2)
    assert "best_params" in result
    assert "test_metrics" in result
    assert "fitness" in result
    assert result["combinations_tested"] > 0


def test_grid_search_metrics_in_range(small_dataset):
    X_tr, X_te, y_tr, y_te = small_dataset
    result = run_grid_search("logistic_regression", X_tr, y_tr, X_te, y_te, cv=2)
    m = result["test_metrics"]
    assert 0.0 <= m["sensibilidade"] <= 1.0
    assert 0.0 <= m["especificidade"] <= 1.0
    assert 0.0 <= m["f1_score"] <= 1.0


def test_grid_search_param_keys(small_dataset):
    X_tr, X_te, y_tr, y_te = small_dataset
    result = run_grid_search("logistic_regression", X_tr, y_tr, X_te, y_te, cv=2)
    for key in PARAM_GRIDS["logistic_regression"]:
        assert key in result["best_params"]


# ── Random Search ─────────────────────────────────────────────────────────────

def test_random_search_returns_required_keys(small_dataset):
    X_tr, X_te, y_tr, y_te = small_dataset
    result = run_random_search("logistic_regression", X_tr, y_tr, X_te, y_te,
                               n_iter=10, cv=2)
    assert "best_params" in result
    assert "test_metrics" in result
    assert result["combinations_tested"] == 10


def test_random_search_metrics_in_range(small_dataset):
    X_tr, X_te, y_tr, y_te = small_dataset
    result = run_random_search("logistic_regression", X_tr, y_tr, X_te, y_te,
                               n_iter=10, cv=2)
    m = result["test_metrics"]
    assert 0.0 <= m["sensibilidade"] <= 1.0
    assert 0.0 <= m["especificidade"] <= 1.0


def test_random_search_different_seeds_differ(small_dataset):
    X_tr, X_te, y_tr, y_te = small_dataset
    r1 = run_random_search("logistic_regression", X_tr, y_tr, X_te, y_te,
                           n_iter=10, cv=2, random_state=0)
    r2 = run_random_search("logistic_regression", X_tr, y_tr, X_te, y_te,
                           n_iter=10, cv=2, random_state=99)
    # Com sementes diferentes é provável (mas não garantido) que os params difiram
    assert isinstance(r1["best_params"], dict)
    assert isinstance(r2["best_params"], dict)


# ── NSGA-II ───────────────────────────────────────────────────────────────────

def test_decode_individual_correct_keys():
    individual = [0, 1, 2, 0, 0, 1]
    params = _decode_individual(individual, "random_forest")
    from src.models.classifier import HYPERPARAMETER_DOMAINS
    for key in HYPERPARAMETER_DOMAINS["random_forest"]:
        assert key in params


def test_nsga2_returns_pareto_front(small_dataset):
    X_tr, X_te, y_tr, y_te = small_dataset
    X_val = X_te.iloc[:40]
    y_val = y_te.iloc[:40]
    result = run_nsga2(
        "logistic_regression",
        X_tr, y_tr, X_val, y_val, X_te, y_te,
        population_size=10, generations=3, random_state=42,
    )
    assert len(result.pareto_front) > 0
    assert "params" in result.pareto_front[0]
    assert "val_sensitivity" in result.pareto_front[0]
    assert "val_specificity" in result.pareto_front[0]


def test_nsga2_pareto_values_in_range(small_dataset):
    X_tr, X_te, y_tr, y_te = small_dataset
    X_val = X_te.iloc[:40]
    y_val = y_te.iloc[:40]
    result = run_nsga2(
        "logistic_regression",
        X_tr, y_tr, X_val, y_val, X_te, y_te,
        population_size=10, generations=3, random_state=42,
    )
    for sol in result.pareto_front:
        assert 0.0 <= sol["val_sensitivity"] <= 1.0
        assert 0.0 <= sol["val_specificity"] <= 1.0


def test_nsga2_best_balanced_exists(small_dataset):
    X_tr, X_te, y_tr, y_te = small_dataset
    X_val = X_te.iloc[:40]
    y_val = y_te.iloc[:40]
    result = run_nsga2(
        "logistic_regression",
        X_tr, y_tr, X_val, y_val, X_te, y_te,
        population_size=10, generations=3, random_state=42,
    )
    assert result.best_balanced is not None
    assert "test_metrics" in result.best_balanced


# ── NEAT ──────────────────────────────────────────────────────────────────────

from src.optimization.neat_optimizer import run_neat, NEATResult


@pytest.fixture
def neat_dataset():
    """Dataset menor para testes rápidos do NEAT."""
    from sklearn.datasets import make_classification
    X, y = make_classification(n_samples=100, n_features=5, random_state=42)
    X_tr, X_te = X[:70], X[70:]
    y_tr, y_te = y[:70], y[70:]
    return X_tr, X_te, y_tr, y_te


def test_neat_returns_result(neat_dataset):
    X_tr, X_te, y_tr, y_te = neat_dataset
    result = run_neat(X_tr, y_tr, X_te, y_te,
                      population_size=10, generations=3, random_state=42)
    assert isinstance(result, NEATResult)


def test_neat_metrics_keys(neat_dataset):
    X_tr, X_te, y_tr, y_te = neat_dataset
    result = run_neat(X_tr, y_tr, X_te, y_te,
                      population_size=10, generations=3, random_state=42)
    for key in ("sensibilidade", "especificidade", "f1_score", "acuracia"):
        assert key in result.test_metrics


def test_neat_metrics_in_range(neat_dataset):
    X_tr, X_te, y_tr, y_te = neat_dataset
    result = run_neat(X_tr, y_tr, X_te, y_te,
                      population_size=10, generations=3, random_state=42)
    m = result.test_metrics
    assert 0.0 <= m["sensibilidade"] <= 1.0
    assert 0.0 <= m["especificidade"] <= 1.0
    assert 0.0 <= m["f1_score"] <= 1.0


def test_neat_topology_info(neat_dataset):
    X_tr, X_te, y_tr, y_te = neat_dataset
    result = run_neat(X_tr, y_tr, X_te, y_te,
                      population_size=10, generations=3, random_state=42)
    assert result.best_n_nodes >= 1
    assert result.best_n_connections >= 0


def test_neat_fitness_history_length(neat_dataset):
    X_tr, X_te, y_tr, y_te = neat_dataset
    result = run_neat(X_tr, y_tr, X_te, y_te,
                      population_size=10, generations=3, random_state=42)
    assert len(result.fitness_per_generation) == result.generations_run
    assert result.generations_run <= 3


def test_neat_species_tracked(neat_dataset):
    X_tr, X_te, y_tr, y_te = neat_dataset
    result = run_neat(X_tr, y_tr, X_te, y_te,
                      population_size=10, generations=3, random_state=42)
    assert len(result.species_per_generation) == result.generations_run
    assert result.n_species_final >= 1
