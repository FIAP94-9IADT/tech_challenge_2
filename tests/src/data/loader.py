import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


def load_dataset(test_size: float = 0.2, random_state: int = 42, scale: bool = True):
    """
    Carrega o dataset Wisconsin Breast Cancer e adiciona grupos de idade sintéticos
    para avaliação de equidade demográfica.
    """
    raw = load_breast_cancer()
    X = pd.DataFrame(raw.data, columns=raw.feature_names)
    y = pd.Series(raw.target, name="target")  # 0=malignant, 1=benign

    # Inverte para que 1=malignant (positivo clínico relevante)
    y = 1 - y

    rng = np.random.default_rng(random_state)
    n = len(X)
    # Grupos etários simulados: jovem (18-40), meia-idade (41-60), sênior (61+)
    age_groups = rng.choice(["jovem", "meia_idade", "senior"], size=n, p=[0.25, 0.45, 0.30])
    X["age_group"] = age_groups

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    age_train = X_train["age_group"].values
    age_test = X_test["age_group"].values
    X_train = X_train.drop(columns=["age_group"])
    X_test = X_test.drop(columns=["age_group"])

    if scale:
        scaler = StandardScaler()
        X_train = pd.DataFrame(scaler.fit_transform(X_train), columns=X_train.columns)
        X_test = pd.DataFrame(scaler.transform(X_test), columns=X_test.columns)
    else:
        scaler = None

    return {
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train.reset_index(drop=True),
        "y_test": y_test.reset_index(drop=True),
        "age_train": age_train,
        "age_test": age_test,
        "feature_names": list(raw.feature_names),
        "scaler": scaler,
        "description": raw.DESCR,
    }


def get_feature_description() -> dict:
    """Retorna descrição clínica das principais features do dataset."""
    return {
        "mean radius": "Raio médio do núcleo celular",
        "mean texture": "Desvio padrão de intensidade em escala de cinza",
        "mean perimeter": "Perímetro médio do núcleo",
        "mean area": "Área média do núcleo celular",
        "mean smoothness": "Variação local no comprimento dos raios",
        "mean compactness": "Compacidade média (perímetro²/área - 1)",
        "mean concavity": "Severidade das porções côncavas do contorno",
        "mean concave points": "Número de porções côncavas do contorno",
        "mean symmetry": "Simetria do núcleo",
        "mean fractal dimension": "Dimensão fractal ('aproximação da linha costeira')",
    }
