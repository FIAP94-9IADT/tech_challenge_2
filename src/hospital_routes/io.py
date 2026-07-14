"""Leitura e persistência dos dados da aplicação."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import Delivery, Depot, Problem, Solution, Vehicle


def load_problem(path: str | Path) -> Problem:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return Problem(
        depot=Depot(**data["depot"]),
        deliveries=tuple(Delivery(**item) for item in data["deliveries"]),
        vehicles=tuple(Vehicle(**item) for item in data["vehicles"]),
    )


def save_solution(path: str | Path, problem: Problem, solution: Solution) -> None:
    payload = {
        "fitness": solution.fitness,
        "generation": solution.generation,
        "feasible": solution.feasible,
        "total_distance_km": solution.total_distance_km,
        "routes": [
            {
                "vehicle": asdict(problem.vehicles[i]),
                "deliveries": [asdict(problem.deliveries[j]) for j in route],
                "metrics": asdict(solution.metrics[i]),
            }
            for i, route in enumerate(solution.routes)
        ],
    }
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
