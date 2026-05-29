import math
from collections import Counter

import numpy as np
from sklearn.metrics import (
    recall_score,
    f1_score,
    confusion_matrix,
    balanced_accuracy_score,
)
from src.genetic.chromosome import Chromosome
from src.models.classifier import build_model


def sensitivity(y_true, y_pred) -> float:
    """Recall/Sensibilidade — prioridade máxima para câncer (minimiza falsos negativos)."""
    return recall_score(y_true, y_pred, zero_division=0)


def specificity(y_true, y_pred) -> float:
    """Especificidade — evitar alarmes falsos em triagem."""
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    return tn / (tn + fp) if (tn + fp) > 0 else 0.0


def equity_score(y_true, y_pred, age_groups) -> float:
    """
    Equidade entre grupos demográficos.
    Penaliza modelos com alta variância de desempenho entre grupos etários.
    Score = 1 - desvio_padrão(balanced_accuracy por grupo)
    """
    groups = np.unique(age_groups)
    if len(groups) < 2:
        return 1.0

    scores = []
    for g in groups:
        mask = age_groups == g
        if mask.sum() < 5:
            continue
        ba = balanced_accuracy_score(y_true[mask], y_pred[mask])
        scores.append(ba)

    if not scores:
        return 1.0

    return max(0.0, 1.0 - np.std(scores))


def calculate_fitness(
    y_true,
    y_pred,
    age_groups=None,
    w_sensitivity: float = 0.40,
    w_specificity: float = 0.25,
    w_f1: float = 0.25,
    w_equity: float = 0.10,
) -> float:
    """
    Função fitness ponderada para diagnóstico de câncer de mama.
    Pesos refletem as prioridades clínicas da saúde feminina.
    """
    s = sensitivity(y_true, y_pred)
    sp = specificity(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    eq = equity_score(y_true, y_pred, age_groups) if age_groups is not None else 1.0

    return w_sensitivity * s + w_specificity * sp + w_f1 * f1 + w_equity * eq


def evaluate_chromosome(
    chromosome: Chromosome,
    X_train,
    y_train,
    X_val,
    y_val,
    age_val=None,
) -> float:
    """Treina o modelo do cromossomo e retorna seu fitness."""
    try:
        model = build_model(chromosome.model_type, chromosome.genes)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_val)
        return calculate_fitness(y_val.values, y_pred, age_val)
    except Exception:
        return 0.0


def genetic_entropy(population: list[Chromosome]) -> float:
    """
    Entropia genética da população (PDF Aula 3 — Diversidade).
    H = -sum(p_i * log2(p_i))
    Valor alto → população diversificada; valor baixo → convergência.
    """
    if not population:
        return 0.0
    counts = Counter(str(sorted(c.genes.items())) for c in population)
    n = len(population)
    return -sum((cnt / n) * math.log2(cnt / n) for cnt in counts.values())


def fitness_std(population: list[Chromosome]) -> float:
    """Desvio padrão da aptidão na população (PDF Aula 3 — Convergência)."""
    fitnesses = [c.fitness for c in population]
    return float(np.std(fitnesses))


def get_detailed_metrics(y_true, y_pred) -> dict:
    """Retorna todas as métricas relevantes para saúde feminina."""
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    return {
        "sensibilidade": sensitivity(y_true, y_pred),
        "especificidade": specificity(y_true, y_pred),
        "f1_score": f1_score(y_true, y_pred, zero_division=0),
        "precisao": tp / (tp + fp) if (tp + fp) > 0 else 0.0,
        "acuracia": (tp + tn) / (tp + tn + fp + fn),
        "falsos_negativos": int(fn),
        "falsos_positivos": int(fp),
        "verdadeiros_positivos": int(tp),
        "verdadeiros_negativos": int(tn),
    }
