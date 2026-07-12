import math
from typing import Dict, List, Sequence, Tuple

from .models import PRIORITY_WEIGHT, DeliveryPoint, Depot, Route, Vehicle

EARTH_RADIUS_KM = 6371.0

# pesos das penalidades (ajustados empiricamente, ver relatorio_tecnico.md)
CAPACITY_PENALTY_PER_KG = 50.0
RANGE_PENALTY_PER_KM = 50.0
UNASSIGNED_PENALTY = 1000.0
PRIORITY_COEF = 0.30  # peso do termo de prioridade em relação à distância


def haversine(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """Distância em linha reta (km) entre dois pontos (lat, lon)."""
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(h))


def build_distance_matrix(depot: Depot, points: Sequence[DeliveryPoint]) -> List[List[float]]:
    """Matriz de distâncias onde o índice 0 é o depósito e o índice i (>=1)
    é o ponto de entrega com id == i - 1... na verdade, para simplificar,
    mapeio os ids dos pontos diretamente: matrix[0] = depósito,
    matrix[p.id + 1] = ponto. Espera-se que os pontos tenham ids 0..n-1.
    """
    coords = [depot.coords] + [p.coords for p in sorted(points, key=lambda p: p.id)]
    n = len(coords)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine(coords[i], coords[j])
            matrix[i][j] = d
            matrix[j][i] = d
    return matrix


def route_distance(route_stops: Sequence[int], dist: List[List[float]]) -> float:
    """Distância total de uma rota: depósito -> paradas... -> depósito.

    route_stops contém ids dos pontos de entrega (base 0); o depósito é a
    linha 0 da matriz, então o ponto com id p mapeia para o índice p + 1.
    """
    if not route_stops:
        return 0.0
    total = dist[0][route_stops[0] + 1]
    for i in range(len(route_stops) - 1):
        total += dist[route_stops[i] + 1][route_stops[i + 1] + 1]
    total += dist[route_stops[-1] + 1][0]
    return total


def evaluate_routes(
    routes: List[Route],
    unassigned: List[int],
    points_by_id: Dict[int, DeliveryPoint],
    vehicles_by_id: Dict[int, Vehicle],
    dist: List[List[float]],
) -> Tuple[float, float, bool]:
    """Calcula (fitness, distância_total, viável) para uma solução decodificada.

    fitness = distância_total
              + violações de capacidade * CAPACITY_PENALTY_PER_KG
              + violações de autonomia * RANGE_PENALTY_PER_KM
              + termo de prioridade (distância acumulada até cada parada,
                ponderada pela prioridade da parada)
              + UNASSIGNED_PENALTY por entrega não alocada
    """
    total_distance = 0.0
    penalty = 0.0
    priority_term = 0.0
    feasible = len(unassigned) == 0

    for route in routes:
        vehicle = vehicles_by_id[route.vehicle_id]
        d = route_distance(route.stops, dist)
        route.distance_km = d
        route.load_kg = sum(points_by_id[s].demand_kg for s in route.stops)
        total_distance += d

        # violação de capacidade
        over_capacity = route.load_kg - vehicle.capacity_kg
        if over_capacity > 1e-9:
            penalty += over_capacity * CAPACITY_PENALTY_PER_KG
            feasible = False

        # violação de autonomia (alcance)
        over_range = d - vehicle.max_range_km
        if over_range > 1e-9:
            penalty += over_range * RANGE_PENALTY_PER_KM
            feasible = False

        # termo de prioridade: distância acumulada percorrida até cada
        # parada, ponderada pela prioridade da parada. Entregas críticas
        # feitas tarde na rota aumentam o fitness (pior).
        cumulative = 0.0
        prev = 0  # índice do depósito na matriz
        for stop in route.stops:
            idx = stop + 1
            cumulative += dist[prev][idx]
            weight = PRIORITY_WEIGHT[points_by_id[stop].priority]
            priority_term += weight * cumulative
            prev = idx

    penalty += len(unassigned) * UNASSIGNED_PENALTY

    fitness = total_distance + penalty + PRIORITY_COEF * priority_term
    return fitness, total_distance, feasible
