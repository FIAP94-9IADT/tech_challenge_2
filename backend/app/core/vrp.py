from typing import Dict, List, Sequence, Tuple

from .fitness import evaluate_routes
from .models import DeliveryPoint, Depot, Route, Solution, Vehicle


def split_tour(
    tour: Sequence[int],
    points_by_id: Dict[int, DeliveryPoint],
    vehicles: Sequence[Vehicle],
    dist: List[List[float]],
) -> Tuple[List[Route], List[int]]:
    """Divisão gulosa de uma rota gigante em uma rota por veículo."""
    routes: List[Route] = [Route(vehicle_id=v.id) for v in vehicles]
    unassigned: List[int] = []

    v_idx = 0
    load = 0.0
    travelled = 0.0
    prev = 0  # índice do depósito na matriz de distâncias

    for stop in tour:
        placed = False
        while v_idx < len(vehicles):
            vehicle = vehicles[v_idx]
            point = points_by_id[stop]
            idx = stop + 1

            new_load = load + point.demand_kg
            # distância se adicionarmos essa parada e depois voltarmos ao depósito
            new_travelled = travelled + dist[prev][idx]
            dist_with_return = new_travelled + dist[idx][0]

            if new_load <= vehicle.capacity_kg and dist_with_return <= vehicle.max_range_km:
                routes[v_idx].stops.append(stop)
                load = new_load
                travelled = new_travelled
                prev = idx
                placed = True
                break

            # veículo atual está cheio (ou fora de alcance): fecha e tenta o próximo
            v_idx += 1
            load = 0.0
            travelled = 0.0
            prev = 0

        if not placed:
            unassigned.append(stop)

    return routes, unassigned


def decode(
    tour: Sequence[int],
    points_by_id: Dict[int, DeliveryPoint],
    vehicles_by_id: Dict[int, Vehicle],
    vehicles: Sequence[Vehicle],
    dist: List[List[float]],
) -> Solution:
    """Divide a rota e a avalia, retornando uma Solution completa."""
    routes, unassigned = split_tour(tour, points_by_id, vehicles, dist)
    fitness, total_distance, feasible = evaluate_routes(
        routes, unassigned, points_by_id, vehicles_by_id, dist
    )
    return Solution(
        routes=routes,
        total_distance_km=total_distance,
        fitness=fitness,
        feasible=feasible,
        unassigned=unassigned,
    )
