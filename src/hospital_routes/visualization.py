"""Visualizações da solução e da convergência."""

from __future__ import annotations

from pathlib import Path

from .genetic import GenerationStats
from .models import Problem, Solution


def save_route_map(problem: Problem, solution: Solution, path: str | Path) -> None:
    import folium

    colors = ["blue", "green", "purple", "orange", "darkred", "cadetblue"]
    map_ = folium.Map(location=[problem.depot.latitude, problem.depot.longitude], zoom_start=12)
    folium.Marker(
        [problem.depot.latitude, problem.depot.longitude],
        tooltip=problem.depot.name,
        icon=folium.Icon(color="red", icon="home"),
    ).add_to(map_)
    for i, route in enumerate(solution.routes):
        color = colors[i % len(colors)]
        points = [[problem.depot.latitude, problem.depot.longitude]]
        for order, gene in enumerate(route, 1):
            d = problem.deliveries[gene]
            points.append([d.latitude, d.longitude])
            folium.Marker(
                points[-1],
                tooltip=f"{order}. {d.name} | prioridade {d.priority} | {d.demand_kg} kg",
                icon=folium.Icon(color=color, icon="plus-sign"),
            ).add_to(map_)
        points.append(points[0])
        if route:
            folium.PolyLine(points, color=color, weight=4, tooltip=problem.vehicles[i].id).add_to(map_)
    map_.save(str(path))


def save_convergence_plot(history: list[GenerationStats], path: str | Path) -> None:
    import matplotlib.pyplot as plt

    generations = [item.generation for item in history]
    fig, (best_ax, mean_ax) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    best_ax.plot(generations, [item.best for item in history], color="#24966f")
    best_ax.set(ylabel="Melhor fitness", title="Convergência do algoritmo genético")
    best_ax.grid(alpha=0.25)
    mean_ax.plot(generations, [item.mean for item in history], color="#657f9f")
    mean_ax.set(xlabel="Geração", ylabel="Fitness médio")
    mean_ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
