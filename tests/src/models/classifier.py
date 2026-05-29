from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression

# Domínios de hiperparâmetros por tipo de modelo
HYPERPARAMETER_DOMAINS: dict[str, dict] = {
    "random_forest": {
        "n_estimators": [50, 100, 150, 200, 300, 500],
        "max_depth": [None, 5, 10, 15, 20],
        "min_samples_split": [2, 5, 10, 20],
        "min_samples_leaf": [1, 2, 4, 8],
        "max_features": ["sqrt", "log2"],
        "class_weight": ["balanced", None],
    },
    "svm": {
        "C": [0.01, 0.1, 1, 10, 100],
        "kernel": ["rbf", "linear", "poly"],
        "gamma": ["scale", "auto"],
        "class_weight": ["balanced", None],
    },
    "logistic_regression": {
        "C": [0.001, 0.01, 0.1, 1, 10, 100],
        "max_iter": [200, 500, 1000],
        "solver": ["lbfgs", "saga"],
        "class_weight": ["balanced", None],
    },
}

# Hiperparâmetros padrão (baseline sem otimização)
DEFAULT_PARAMS: dict[str, dict] = {
    "random_forest": {"n_estimators": 100, "random_state": 42},
    "svm": {"probability": True, "random_state": 42},
    "logistic_regression": {"max_iter": 200, "random_state": 42},
}


def build_model(model_type: str, params: dict | None = None):
    """Constrói um modelo sklearn com os hiperparâmetros fornecidos."""
    base = DEFAULT_PARAMS.get(model_type, {}).copy()
    if params:
        base.update(params)

    if model_type == "random_forest":
        return RandomForestClassifier(**base)
    elif model_type == "svm":
        base["probability"] = True
        return SVC(**base)
    elif model_type == "logistic_regression":
        return LogisticRegression(**base)
    else:
        raise ValueError(f"Tipo de modelo desconhecido: {model_type}")


def get_model_display_name(model_type: str) -> str:
    names = {
        "random_forest": "Random Forest",
        "svm": "SVM",
        "logistic_regression": "Regressão Logística",
    }
    return names.get(model_type, model_type)
