import io
import json

import pytest

from hospital_routes.genetic import GAConfig, GeneticOptimizer
from hospital_routes.reporting import (
    GeminiReportGenerator,
    LocalReportGenerator,
    build_prompt,
    comparison_metrics,
)


def test_prompt_contains_grounding_and_route_data(problem):
    solution = GeneticOptimizer(problem, GAConfig(population_size=10, generations=2)).evaluate(list(range(10)))
    prompt = build_prompt(problem, solution)
    assert "Não invente" in prompt
    assert "Hospital Central" in prompt
    assert "paradas_na_ordem" in prompt


def test_local_report_lists_vehicles(problem):
    solution = GeneticOptimizer(problem, GAConfig(population_size=10, generations=2)).evaluate(list(range(10)))
    report = LocalReportGenerator().generate(problem, solution)
    assert "Plano operacional" in report
    assert all(vehicle.id in report for vehicle in problem.vehicles)


def test_comparison_is_grounded_in_observed_metrics(problem):
    optimizer = GeneticOptimizer(problem, GAConfig(population_size=10, generations=2))
    baseline = optimizer.evaluate(list(range(10)))
    solution = optimizer.evaluate(list(reversed(range(10))))
    comparison = comparison_metrics(solution, baseline)
    prompt = build_prompt(problem, solution, comparison=comparison)
    assert "comparacao_de_eficiencia" in prompt
    assert "Não converta distância em tempo ou dinheiro" in prompt
    assert "tempo real" in comparison["observacao"]


def test_gemini_joins_all_visible_response_parts(problem, monkeypatch):
    solution = GeneticOptimizer(problem, GAConfig(population_size=10, generations=2)).evaluate(list(range(10)))
    payload = {
        "candidates": [{
            "finishReason": "STOP",
            "content": {"parts": [
                {"text": "raciocínio interno", "thought": True},
                {"text": "Primeira seção."},
                {"text": "Segunda seção concluída."},
            ]},
        }]
    }

    class Response(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *_): return False

    monkeypatch.setattr("urllib.request.urlopen", lambda *_args, **_kwargs: Response(json.dumps(payload).encode()))
    report = GeminiReportGenerator(api_key="chave-de-teste").generate(problem, solution)
    assert report == "Primeira seção.\nSegunda seção concluída."
    assert "raciocínio interno" not in report


def test_gemini_rejects_truncated_response(problem, monkeypatch):
    solution = GeneticOptimizer(problem, GAConfig(population_size=10, generations=2)).evaluate(list(range(10)))
    payload = {"candidates": [{"finishReason": "MAX_TOKENS", "content": {"parts": [{"text": "incompleto"}]}}]}

    class Response(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *_): return False

    monkeypatch.setattr("urllib.request.urlopen", lambda *_args, **_kwargs: Response(json.dumps(payload).encode()))
    with pytest.raises(RuntimeError, match="limite de tokens"):
        GeminiReportGenerator(api_key="chave-de-teste").generate(problem, solution)
