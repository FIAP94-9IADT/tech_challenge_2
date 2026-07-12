from typing import Dict, List, Sequence

from .fitness import build_distance_matrix
from .models import DeliveryPoint, Depot, Solution, Vehicle
from .vrp import decode


def nearest_neighbor_tour(points: Sequence[DeliveryPoint], dist: List[List[float]]) -> List[int]:
    unvisited = {p.id for p in points}
    tour: List[int] = []
    current = 0  # índice do depósito na matriz

    while unvisited:
        nearest = min(unvisited, key=lambda pid: dist[current][pid + 1])
        tour.append(nearest)
        unvisited.remove(nearest)
        current = nearest + 1

    return tour


def solve_nearest_neighbor(
    depot: Depot,
    points: Sequence[DeliveryPoint],
    vehicles: Sequence[Vehicle],
) -> Solution:
    points_by_id: Dict[int, DeliveryPoint] = {p.id: p for p in points}
    vehicles_by_id: Dict[int, Vehicle] = {v.id: v for v in vehicles}
    dist = build_distance_matrix(depot, points)
    tour = nearest_neighbor_tour(points, dist)
    return decode(tour, points_by_id, vehicles_by_id, vehicles, dist)
