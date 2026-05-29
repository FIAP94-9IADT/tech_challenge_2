"""
Otimização por Força Bruta (Grid Search).
Equivalente ao método exato descrito no PDF — testa todas as combinações possíveis
de hiperparâmetros e garante o melhor resultado dentro do grid definido.
Complexidade: O(n^k) onde n = valores por parâmetro, k = número de parâmetros.
"""

import numpy as np
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import make_scorer, f1_score

from src.models.classifier import build_model
from src.genetic.fitness import get_detailed_metrics, calculate_fitness

# Grid reduzido para manter tempo viável (força bruta real seria impraticável)
PARAM_GRIDS: dict[str, dict] = {
    "random_forest": {
        "n_estimators": [50, 100, 200],
        "max_depth": [None, 10, 20],
        "min_samples_split": [2, 5, 10],
        "class_weight": ["balanced", None],
    },
    "svm": {
        "C": [0.1, 1, 10],
        "kernel": ["rbf", "linear"],
        "gamma": ["scale", "auto"],
        "class_weight": ["balanced", None],
    },
    "logistic_regression": {
        "C": [0.01, 0.1, 1, 10],
        "max_iter": [200, 500],
        "class_weight": ["balanced", None],
    },
}


def run_grid_search(
    model_type: str,
    X_train,
    y_train,
    X_test,
    y_test,
    cv: int = 3,
) -> dict:
    """
    Executa Grid Search completo sobre o espaço de hiperparâmetros.
    Retorna os melhores parâmetros e métricas no conjunto de teste.
    """
    base_model = build_model(model_type)
    scorer = make_scorer(f1_score, zero_division=0)

    grid = GridSearchCV(
        estimator=base_model,
        param_grid=PARAM_GRIDS[model_type],
        scoring=scorer,
        cv=cv,
        n_jobs=-1,
        refit=True,
    )
    grid.fit(X_train, y_train)

    best_model = grid.best_estimator_
    y_pred = best_model.predict(X_test)
    metrics = get_detailed_metrics(y_test.values, y_pred)

    total_combinations = 1
    for v in PARAM_GRIDS[model_type].values():
        total_combinations *= len(v)

    return {
        "method": "Grid Search (Força Bruta)",
        "best_params": grid.best_params_,
        "best_cv_score": grid.best_score_,
        "test_metrics": metrics,
        "combinations_tested": total_combinations,
        "fitness": calculate_fitness(y_test.values, y_pred),
    }
