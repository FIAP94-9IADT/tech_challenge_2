import numpy as np
import pytest
from src.genetic.fitness import sensitivity, specificity, equity_score, calculate_fitness, get_detailed_metrics


Y_TRUE_PERFECT = np.array([1, 0, 1, 0, 1, 0])
Y_PRED_PERFECT = np.array([1, 0, 1, 0, 1, 0])
Y_PRED_ALL_POS = np.array([1, 1, 1, 1, 1, 1])
Y_PRED_ALL_NEG = np.array([0, 0, 0, 0, 0, 0])


def test_sensitivity_perfect():
    assert sensitivity(Y_TRUE_PERFECT, Y_PRED_PERFECT) == pytest.approx(1.0)


def test_sensitivity_all_positive_pred():
    # all positives are caught but no negatives
    assert sensitivity(Y_TRUE_PERFECT, Y_PRED_ALL_POS) == pytest.approx(1.0)


def test_sensitivity_all_negative_pred():
    assert sensitivity(Y_TRUE_PERFECT, Y_PRED_ALL_NEG) == pytest.approx(0.0)


def test_specificity_perfect():
    assert specificity(Y_TRUE_PERFECT, Y_PRED_PERFECT) == pytest.approx(1.0)


def test_specificity_all_positive_pred():
    # no true negatives caught
    assert specificity(Y_TRUE_PERFECT, Y_PRED_ALL_POS) == pytest.approx(0.0)


def test_specificity_all_negative_pred():
    assert specificity(Y_TRUE_PERFECT, Y_PRED_ALL_NEG) == pytest.approx(1.0)


def test_equity_score_perfect():
    y_true = np.array([1, 0, 1, 0, 1, 0, 1, 0, 1, 0])
    y_pred = np.array([1, 0, 1, 0, 1, 0, 1, 0, 1, 0])
    age_groups = np.array(["jovem", "jovem", "meia_idade", "meia_idade", "senior",
                           "jovem", "jovem", "meia_idade", "senior", "senior"])
    score = equity_score(y_true, y_pred, age_groups)
    assert 0.0 <= score <= 1.0


def test_equity_score_single_group():
    y_true = np.array([1, 0, 1, 0])
    y_pred = np.array([1, 0, 1, 0])
    age_groups = np.array(["jovem", "jovem", "jovem", "jovem"])
    assert equity_score(y_true, y_pred, age_groups) == 1.0


def test_calculate_fitness_bounds():
    fit = calculate_fitness(Y_TRUE_PERFECT, Y_PRED_PERFECT)
    assert 0.0 <= fit <= 1.0


def test_calculate_fitness_perfect_is_high():
    fit_perfect = calculate_fitness(Y_TRUE_PERFECT, Y_PRED_PERFECT)
    fit_bad = calculate_fitness(Y_TRUE_PERFECT, Y_PRED_ALL_NEG)
    assert fit_perfect > fit_bad


def test_get_detailed_metrics_keys():
    metrics = get_detailed_metrics(Y_TRUE_PERFECT, Y_PRED_PERFECT)
    expected_keys = {"sensibilidade", "especificidade", "f1_score", "precisao",
                     "acuracia", "falsos_negativos", "falsos_positivos",
                     "verdadeiros_positivos", "verdadeiros_negativos"}
    assert expected_keys.issubset(metrics.keys())


def test_get_detailed_metrics_perfect_values():
    metrics = get_detailed_metrics(Y_TRUE_PERFECT, Y_PRED_PERFECT)
    assert metrics["sensibilidade"] == pytest.approx(1.0)
    assert metrics["especificidade"] == pytest.approx(1.0)
    assert metrics["falsos_negativos"] == 0
    assert metrics["falsos_positivos"] == 0
