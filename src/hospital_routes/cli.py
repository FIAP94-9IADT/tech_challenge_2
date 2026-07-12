"""Interface de linha de comando para executar o fluxo completo."""

from __future__ import annotations

import argparse
from pathlib import Path

from .baselines import nearest_neighbor
from .genetic import GAConfig, GeneticOptimizer
from .io import load_problem, save_solution
from .reporting import GeminiReportGenerator, LocalReportGenerator, comparison_metrics
from .visualization import save_convergence_plot, save_route_map


def main() -> None:
    parser = argparse.ArgumentParser(description="Otimiza rotas hospitalares")
    parser.add_argument("--input", default="data/deliveries.json")
    parser.add_argument("--output", default="outputs")
    parser.add_argument("--llm", choices=("local", "gemini"), default="gemini")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--generations", type=int, default=300)
    args = parser.parse_args()

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    problem = load_problem(args.input)
    optimizer = GeneticOptimizer(problem, GAConfig(seed=args.seed, generations=args.generations))
    baseline = nearest_neighbor(optimizer)
    solution = optimizer.run()
    comparison = comparison_metrics(solution, baseline)

    save_solution(output / "solution.json", problem, solution)
    save_route_map(problem, solution, output / "routes_map.html")
    save_convergence_plot(optimizer.history, output / "convergence.png")
    try:
        generator = GeminiReportGenerator() if args.llm == "gemini" else LocalReportGenerator()
        report = generator.generate(problem, solution, comparison=comparison)
    except RuntimeError as exc:
        report = LocalReportGenerator().generate(problem, solution, comparison=comparison)
        report += f"\n\n> Relatório local utilizado porque o Gemini ficou indisponível: {exc}"
        print(f"Aviso: {exc}")
    (output / "daily_report.md").write_text(report, encoding="utf-8")
    improvement = 100 * (baseline.fitness - solution.fitness) / baseline.fitness
    print(f"Fitness: {solution.fitness:.2f} | Distância: {solution.total_distance_km:.2f} km | Viável: {solution.feasible}")
    print(f"Variação frente ao vizinho mais próximo: {improvement:+.2f}% | Saída: {output.resolve()}")


if __name__ == "__main__":
    main()
