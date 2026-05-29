"""
Otimização Estocástica (Random Search).
Baseado no conceito de Otimização Estocástica do PDF — incorpora aleatoriedade
na busca, amostrando aleatoriamente o espaço de hiperparâmetros sem testá-lo todo.
Mais eficiente que força bruta em espaços de alta dimensionalidade.
"""

import numpy as np
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import make_scorer, f1_score
from scipy.stats import randint, uniform

from src.models.classifier import build_model
from src.genetic.fitness import get_detailed_metrics, calculate_fitness

# Distribuições de hiperparâmetros para amostragem aleatória
PARAM_DISTRIBUTIONS: dict[str, dict] = {
    "random_forest": {
        "n_estimators": randint(50, 500),
        "max_depth": [None, 5, 10, 15, 20, 25],
        "min_samples_split": randint(2, 20),
        "min_samples_leaf": randint(1, 8),
        "max_features": ["sqrt", "log2"],
        "class_weight": ["balanced", None],
    },
    "svm": {
        "C": uniform(0.01, 100),
        "kernel": ["rbf", "linear", "poly"],
        "gamma": ["scale", "auto"],
        "class_weight": ["balanced", None],
    },
    "logistic_regression": {
        "C": uniform(0.001, 100),
        "max_iter": randint(100, 1000),
        "solver": ["lbfgs", "saga"],
        "class_weight": ["balanced", None],
    },
}


def run_random_search(
    model_type: str,
    X_train,
    y_train,
    X_test,
    y_test,
    n_iter: int = 50,
    cv: int = 3,
    random_state: int = 42,
) -> dict:
    """
    Executa Random Search com n_iter amostras aleatórias do espaço de hiperparâmetros.
    Retorna os melhores parâmetros e métricas no conjunto de teste.
    """
    base_model = build_model(model_type)
    scorer = make_scorer(f1_score, zero_division=0)

    rs = RandomizedSearchCV(
        estimator=base_model,
        param_distributions=PARAM_DISTRIBUTIONS[model_type],
        n_iter=n_iter,
        scoring=scorer,
        cv=cv,
        n_jobs=-1,
        refit=True,
        random_state=random_state,
    )
    rs.fit(X_train, y_train)

    best_model = rs.best_estimator_
    y_pred = best_model.predict(X_test)
    metrics = get_detailed_metrics(y_test.values, y_pred)

    return {
        "method": "Random Search (Estocástico)",
        "best_params": rs.best_params_,
        "best_cv_score": rs.best_score_,
        "test_metrics": metrics,
        "combinations_tested": n_iter,
        "fitness": calculate_fitness(y_test.values, y_pred),
    }
