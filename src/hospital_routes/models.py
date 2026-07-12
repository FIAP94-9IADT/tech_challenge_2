"""Entidades e validações do problema de roteamento."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import asin, cos, radians, sin, sqrt
from typing import Iterable


@dataclass(frozen=True)
class Delivery:
    id: str
    name: str
    latitude: float
    longitude: float
    demand_kg: float
    priority: int = 1
    service_minutes: int = 10

    def __post_init__(self) -> None:
        if self.demand_kg <= 0:
            raise ValueError("A demanda deve ser positiva")
        if self.priority not in (1, 2, 3):
            raise ValueError("A prioridade deve estar entre 1 e 3")


@dataclass(frozen=True)
class Vehicle:
    id: str
    capacity_kg: float
    max_distance_km: float

    def __post_init__(self) -> None:
        if self.capacity_kg <= 0 or self.max_distance_km <= 0:
            raise ValueError("Capacidade e autonomia devem ser positivas")


@dataclass(frozen=True)
class Depot:
    name: str
    latitude: float
    longitude: float


@dataclass(frozen=True)
class Problem:
    depot: Depot
    deliveries: tuple[Delivery, ...]
    vehicles: tuple[Vehicle, ...]

    def __post_init__(self) -> None:
        if not self.deliveries or not self.vehicles:
            raise ValueError("O cenário requer entregas e veículos")
        if len({d.id for d in self.deliveries}) != len(self.deliveries):
            raise ValueError("Os identificadores das entregas devem ser únicos")


@dataclass
class RouteMetrics:
    distance_km: float
    load_kg: float
    priority_delay: float
    capacity_excess_kg: float
    autonomy_excess_km: float


@dataclass
class Solution:
    routes: list[list[int]]
    fitness: float
    metrics: list[RouteMetrics] = field(default_factory=list)
    generation: int = 0

    @property
    def feasible(self) -> bool:
        return all(
            m.capacity_excess_kg <= 1e-9 and m.autonomy_excess_km <= 1e-9
            for m in self.metrics
        )

    @property
    def total_distance_km(self) -> float:
        return sum(m.distance_km for m in self.metrics)


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Distância geodésica aproximada entre dois pontos."""
    lat1, lon1, lat2, lon2 = map(radians, (*a, *b))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * 6371.0088 * asin(sqrt(h))


def build_distance_matrix(problem: Problem) -> list[list[float]]:
    points = [(problem.depot.latitude, problem.depot.longitude)] + [
        (d.latitude, d.longitude) for d in problem.deliveries
    ]
    return [[haversine_km(a, b) for b in points] for a in points]


def flatten(routes: Iterable[Iterable[int]]) -> list[int]:
    return [gene for route in routes for gene in route]
