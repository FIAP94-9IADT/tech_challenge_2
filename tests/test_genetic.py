from hospital_routes.genetic import GAConfig, GeneticOptimizer
from hospital_routes.models import flatten


def test_crossover_preserves_permutation(problem):
    optimizer = GeneticOptimizer(problem, GAConfig(population_size=10, generations=2))
    parent1 = list(range(len(problem.deliveries)))
    parent2 = list(reversed(parent1))
    child = optimizer.order_crossover(parent1, parent2)
    assert sorted(child) == parent1
    assert len(set(child)) == len(child)


def test_decoder_visits_each_delivery_once(problem):
    optimizer = GeneticOptimizer(problem, GAConfig(population_size=10, generations=2))
    solution = optimizer.evaluate(list(range(len(problem.deliveries))))
    assert sorted(flatten(solution.routes)) == list(range(len(problem.deliveries)))


def test_optimizer_is_reproducible_and_improves_initial_population(problem):
    config = GAConfig(population_size=30, generations=35, stagnation_limit=20, seed=7)
    first = GeneticOptimizer(problem, config)
    initial = GeneticOptimizer(problem, config)
    initial_best = min(initial.evaluate(c).fitness for c in initial._initial_population())
    result1 = first.run()
    result2 = GeneticOptimizer(problem, config).run()
    assert result1.fitness <= initial_best + 1e-9
    assert result1.fitness == result2.fitness
    assert len(first.history) > 1


def test_penalty_marks_infeasible_solution(problem):
    optimizer = GeneticOptimizer(problem, GAConfig(population_size=10, generations=2))
    routes = [list(range(len(problem.deliveries))), [], []]
    solution = optimizer.evaluate_routes(routes)
    assert not solution.feasible
    assert solution.metrics[0].capacity_excess_kg > 0
