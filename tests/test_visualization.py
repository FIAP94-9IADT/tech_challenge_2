from hospital_routes.genetic import GAConfig, GeneticOptimizer
from hospital_routes.visualization import create_route_map, save_route_map


def test_route_map_is_saved_and_returned_for_notebook_display(problem, tmp_path):
    optimizer = GeneticOptimizer(problem, GAConfig(population_size=10, generations=2))
    solution = optimizer.evaluate(list(range(len(problem.deliveries))))
    path = tmp_path / "routes_map.html"

    route_map = save_route_map(problem, solution, path)

    assert path.exists()
    assert "Hospital Central" in path.read_text(encoding="utf-8")
    assert callable(getattr(route_map, "_repr_html_", None))

    interactive_map = create_route_map(problem, solution)
    assert callable(getattr(interactive_map, "_repr_html_", None))
