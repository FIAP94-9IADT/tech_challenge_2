import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from src.genetic.fitness import get_detailed_metrics, equity_score


def full_report(y_true, y_pred, y_prob=None, age_groups=None) -> dict:
    """Relatório completo de métricas para avaliação de modelos em saúde feminina."""
    report = get_detailed_metrics(y_true, y_pred)

    if y_prob is not None:
        try:
            report["auc_roc"] = roc_auc_score(y_true, y_prob)
        except Exception:
            report["auc_roc"] = None

    if age_groups is not None:
        report["equidade"] = equity_score(y_true, y_pred, age_groups)
        report["metricas_por_grupo"] = per_group_metrics(y_true, y_pred, age_groups)

    return report


def per_group_metrics(y_true, y_pred, age_groups) -> dict:
    """Calcula métricas separadamente por grupo etário."""
    groups = np.unique(age_groups)
    result = {}
    for g in groups:
        mask = age_groups == g
        if mask.sum() < 5:
            continue
        result[g] = get_detailed_metrics(y_true[mask], y_pred[mask])
    return result


def compare_models(baseline_metrics: dict, optimized_metrics: dict) -> pd.DataFrame:
    """Gera tabela comparativa entre modelo baseline e otimizado."""
    keys = ["sensibilidade", "especificidade", "f1_score", "precisao", "acuracia"]
    rows = []
    for k in keys:
        b = baseline_metrics.get(k, 0)
        o = optimized_metrics.get(k, 0)
        rows.append({
            "Métrica": k.replace("_", " ").title(),
            "Baseline": f"{b:.4f}",
            "Otimizado": f"{o:.4f}",
            "Delta": f"{o - b:+.4f}",
            "Melhoria %": f"{((o - b) / b * 100) if b > 0 else 0:+.1f}%",
        })
    return pd.DataFrame(rows)
