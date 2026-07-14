"""Ponto de entrada do experimento no Azure Machine Learning."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hospital_routes.genetic import GAConfig, GeneticOptimizer  # noqa: E402
from hospital_routes.baselines import nearest_neighbor  # noqa: E402
from hospital_routes.io import load_problem, save_solution  # noqa: E402
from hospital_routes.reporting import (  # noqa: E402
    GeminiReportGenerator,
    LocalReportGenerator,
    comparison_metrics,
)
from hospital_routes.visualization import save_convergence_plot, save_route_map  # noqa: E402


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--population-size", type=int, default=120)
    parser.add_argument("--generations", type=int, default=300)
    parser.add_argument("--crossover-rate", type=float, default=0.90)
    parser.add_argument("--mutation-rate", type=float, default=0.20)
    parser.add_argument("--elite-size", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def log_experiment(config: GAConfig, optimizer: GeneticOptimizer, solution) -> None:
    """Registra dados no Azure quando MLflow estiver disponível."""
    try:
        import mlflow
    except ImportError:
        return
    mlflow.log_params(
        {
            "population_size": config.population_size,
            "generations": config.generations,
            "crossover_rate": config.crossover_rate,
            "mutation_rate": config.mutation_rate,
            "elite_size": config.elite_size,
            "seed": config.seed,
        }
    )
    # O nome deve coincidir exatamente com a métrica principal do sweep.
    mlflow.log_metric("fitness", float(solution.fitness))
    mlflow.log_metric("total_distance_km", float(solution.total_distance_km))
    mlflow.log_metric("feasible", int(solution.feasible))
    mlflow.log_metric("best_generation", int(solution.generation))
    for item in optimizer.history:
        mlflow.log_metric("best_fitness_by_generation", item.best, step=item.generation)
        mlflow.log_metric("mean_fitness_by_generation", item.mean, step=item.generation)


def main() -> None:
    args = arguments()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    problem = load_problem(args.input)
    config = GAConfig(
        population_size=args.population_size,
        generations=args.generations,
        crossover_rate=args.crossover_rate,
        mutation_rate=args.mutation_rate,
        elite_size=args.elite_size,
        seed=args.seed,
    )
    optimizer = GeneticOptimizer(problem, config)
    baseline = nearest_neighbor(optimizer)
    solution = optimizer.run()
    comparison = comparison_metrics(solution, baseline)

    save_solution(output / "solution.json", problem, solution)
    save_route_map(problem, solution, output / "routes_map.html")
    save_convergence_plot(optimizer.history, output / "convergence.png")
    try:
        report = GeminiReportGenerator().generate(problem, solution, comparison=comparison)
    except RuntimeError as exc:
        # A otimização e os demais artefatos não dependem da disponibilidade do Gemini.
        report = LocalReportGenerator().generate(problem, solution, comparison=comparison)
        report += f"\n\n> O relatório local foi usado porque o Gemini não estava disponível: {exc}"
    (output / "daily_report.md").write_text(report, encoding="utf-8")
    with (output / "history.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["generation", "best_fitness", "mean_fitness", "fitness_std"])
        writer.writerows(
            (item.generation, item.best, item.mean, item.standard_deviation)
            for item in optimizer.history
        )
    log_experiment(config, optimizer, solution)
    print(f"fitness={solution.fitness:.6f}; distance_km={solution.total_distance_km:.6f}; feasible={solution.feasible}")


if __name__ == "__main__":
    main()
