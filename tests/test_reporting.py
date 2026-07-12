from hospital_routes.genetic import GAConfig, GeneticOptimizer
from hospital_routes.reporting import LocalReportGenerator, build_prompt


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
