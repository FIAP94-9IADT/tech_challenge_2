"""Experimentos com diferentes configurações do AG.

Executa o AG com várias configurações sobre o mesmo cenário (seed fixa)
e compara a convergência e os resultados finais, incluindo o baseline
Nearest Neighbor. Saídas:
- docs/img/convergencia.png       (curvas de convergência)
- docs/img/comparativo.png        (gráfico de barras da distância final)
- tabela markdown impressa no stdout (colo no relatório)

Uso (a partir de backend/):
    .venv/bin/python experiments/run_experiments.py
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from app.core.baseline import solve_nearest_neighbor
from app.core.genetic_algorithm import GAConfig, run_ga
from app.data.synthetic import generate_scenario

DOCS_IMG = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "img")

SCENARIO = dict(n_points=25, n_vehicles=3, seed=42)

# pelo menos 3 configurações, conforme pedido no desafio
CONFIGS = {
    "A - pop=50, mut=0.1, torneio": GAConfig(
        population_size=50, generations=400, mutation_probability=0.1,
        elitism=2, selection="tournament", stagnation_limit=0, seed=42,
    ),
    "B - pop=150, mut=0.3, torneio": GAConfig(
        population_size=150, generations=400, mutation_probability=0.3,
        elitism=2, selection="tournament", stagnation_limit=0, seed=42,
    ),
    "C - pop=150, mut=0.3, roleta": GAConfig(
        population_size=150, generations=400, mutation_probability=0.3,
        elitism=2, selection="roulette", stagnation_limit=0, seed=42,
    ),
    "D - pop=300, mut=0.5, torneio": GAConfig(
        population_size=300, generations=400, mutation_probability=0.5,
        elitism=4, selection="tournament", stagnation_limit=0, seed=42,
    ),
}


def main():
    os.makedirs(DOCS_IMG, exist_ok=True)

    depot, points, vehicles = generate_scenario(**SCENARIO)
    print(f"Cenário: {len(points)} entregas, {len(vehicles)} veículos, seed={SCENARIO['seed']}\n")

    baseline = solve_nearest_neighbor(depot, points, vehicles)
    print(f"Baseline Nearest Neighbor: distância={baseline.total_distance_km:.1f} km, "
          f"fitness={baseline.fitness:.1f}, viável={baseline.feasible}\n")

    results = {}
    for label, config in CONFIGS.items():
        start = time.perf_counter()
        result = run_ga(depot, points, vehicles, config)
        elapsed = time.perf_counter() - start
        results[label] = (result, elapsed)
        best = result.best_solution
        print(f"{label}: fitness={best.fitness:.1f}, distância={best.total_distance_km:.1f} km, "
              f"viável={best.feasible}, gerações={result.generations_run}, tempo={elapsed:.1f}s")

    # --- gráfico de convergência
    plt.figure(figsize=(10, 6))
    for label, (result, _) in results.items():
        plt.plot(result.history, label=label)
    plt.axhline(baseline.fitness, color="gray", linestyle="--", label="Nearest Neighbor (baseline)")
    plt.xlabel("Geração")
    plt.ylabel("Melhor fitness")
    plt.title("Convergência do AG por configuração")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    path = os.path.join(DOCS_IMG, "convergencia.png")
    plt.savefig(path, dpi=150)
    print(f"\nGráfico salvo em {os.path.abspath(path)}")

    # --- gráfico de barras da distância final
    labels = ["Nearest\nNeighbor"] + [l.split(" - ")[0] for l in results]
    distances = [baseline.total_distance_km] + [r.best_solution.total_distance_km for r, _ in results.values()]
    plt.figure(figsize=(8, 5))
    bars = plt.bar(labels, distances, color=["gray"] + ["#2b6cb0"] * len(results))
    for bar, d in zip(bars, distances):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{d:.0f} km",
                 ha="center", va="bottom")
    plt.ylabel("Distância total (km)")
    plt.title("Distância final por abordagem")
    plt.tight_layout()
    path = os.path.join(DOCS_IMG, "comparativo.png")
    plt.savefig(path, dpi=150)
    print(f"Gráfico salvo em {os.path.abspath(path)}")

    # --- tabela markdown para o relatório
    print("\n### Tabela para o relatório\n")
    print("| Configuração | População | Mutação | Seleção | Fitness | Distância (km) | Viável | Gerações | Tempo (s) |")
    print("|---|---|---|---|---|---|---|---|---|")
    print(f"| Nearest Neighbor | - | - | - | {baseline.fitness:.1f} | {baseline.total_distance_km:.1f} | "
          f"{'sim' if baseline.feasible else 'não'} | - | <0.1 |")
    for label, (result, elapsed) in results.items():
        config = CONFIGS[label]
        best = result.best_solution
        print(f"| {label.split(' - ')[0]} | {config.population_size} | {config.mutation_probability} | "
              f"{config.selection} | {best.fitness:.1f} | {best.total_distance_km:.1f} | "
              f"{'sim' if best.feasible else 'não'} | {result.generations_run} | {elapsed:.1f} |")


if __name__ == "__main__":
    main()
