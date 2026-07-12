from hospital_routes.genetic import GAConfig, GeneticOptimizer
from hospital_routes.baselines import brute_force, nearest_neighbor
from hospital_routes.models import Delivery, Depot, Problem, Vehicle, flatten


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


def test_priority_term_favors_critical_delivery_first():
    scenario = Problem(
        depot=Depot("Hospital", 0.0, 0.0),
        deliveries=(
            Delivery("C", "Crítica", 0.0, 0.01, 1.0, priority=3),
            Delivery("R", "Regular", 0.0, 0.02, 1.0, priority=1),
        ),
        vehicles=(Vehicle("V1", capacity_kg=10.0, max_distance_km=100.0),),
    )
    optimizer = GeneticOptimizer(scenario, GAConfig(population_size=10, generations=2))
    critical_first = optimizer.evaluate_routes([[0, 1]])
    regular_first = optimizer.evaluate_routes([[1, 0]])
    assert critical_first.total_distance_km == regular_first.total_distance_km
    assert critical_first.fitness < regular_first.fitness


def test_zero_elitism_is_supported(problem):
    config = GAConfig(population_size=20, generations=5, elite_size=0, seed=9)
    result = GeneticOptimizer(problem, config).run()
    assert sorted(flatten(result.routes)) == list(range(len(problem.deliveries)))


def test_brute_force_is_not_worse_than_nearest_neighbor(problem):
    reduced = Problem(problem.depot, problem.deliveries[:6], problem.vehicles)
    optimizer = GeneticOptimizer(reduced, GAConfig(population_size=10, generations=2))
    assert brute_force(optimizer).fitness <= nearest_neighbor(optimizer).fitness
