import random
from typing import List, Optional, Tuple

from ..core.models import DeliveryPoint, Depot, Priority, Vehicle

DEFAULT_CENTER = (-23.5505, -46.6333)  # centro de São Paulo
SPREAD_DEG = 0.12  # ~13 km de espalhamento ao redor do centro

NEIGHBORHOODS = [
    "Vila Esperança", "Jardim das Flores", "Santa Cecília", "Bela Vista",
    "Vila Nova", "Parque das Árvores", "Jardim América", "Vila Progresso",
    "Centro", "Alto da Colina", "Jardim Paulista", "Vila Industrial",
    "Parque Central", "Vila São José", "Jardim Europa", "Vila Aurora",
    "Bairro da Luz", "Vila Mariana", "Jardim Botânico", "Vila Formosa",
    "Santa Rita", "Vila Palmeiras", "Jardim Primavera", "Vila Regina",
    "Parque dos Ipês", "Vila Antônio", "Jardim Alvorada", "Vila Carmem",
    "Alto do Mirante", "Vila Fátima",
]

KIND_PREFIX = {
    "ubs": "UBS",
    "clinic": "Clínica",
    "home_care": "Atendimento Domiciliar",
}

# distribuição de prioridades: a maioria das entregas é de insumos
# regulares, uma parcela menor é de medicamento crítico
PRIORITY_CHOICES = [Priority.CRITICAL, Priority.HIGH, Priority.NORMAL]
PRIORITY_WEIGHTS = [0.15, 0.25, 0.60]

KIND_CHOICES = ["ubs", "clinic", "home_care"]
KIND_WEIGHTS = [0.45, 0.30, 0.25]


def generate_scenario(
    n_points: int = 20,
    n_vehicles: int = 3,
    seed: Optional[int] = 42,
    center: Tuple[float, float] = DEFAULT_CENTER,
) -> Tuple[Depot, List[DeliveryPoint], List[Vehicle]]:
    rng = random.Random(seed)

    depot = Depot(name="Hospital Central", lat=center[0], lon=center[1])

    points: List[DeliveryPoint] = []
    names_pool = list(NEIGHBORHOODS)
    rng.shuffle(names_pool)

    for i in range(n_points):
        kind = rng.choices(KIND_CHOICES, weights=KIND_WEIGHTS, k=1)[0]
        priority = rng.choices(PRIORITY_CHOICES, weights=PRIORITY_WEIGHTS, k=1)[0]
        neighborhood = names_pool[i % len(names_pool)]
        suffix = "" if i < len(names_pool) else f" {i // len(names_pool) + 1}"

        # pontos críticos tendem a carregar cargas mais leves e de maior valor
        if priority == Priority.CRITICAL:
            demand = round(rng.uniform(1.0, 15.0), 1)
        else:
            demand = round(rng.uniform(5.0, 50.0), 1)

        points.append(
            DeliveryPoint(
                id=i,
                name=f"{KIND_PREFIX[kind]} {neighborhood}{suffix}",
                lat=center[0] + rng.uniform(-SPREAD_DEG, SPREAD_DEG),
                lon=center[1] + rng.uniform(-SPREAD_DEG, SPREAD_DEG),
                demand_kg=demand,
                priority=priority,
                kind=kind,
            )
        )

    # dimensionamento da frota: capacidade total recebe uma folga de
    # 20-60% sobre a demanda total, senão o cenário seria inviável por construção
    total_demand = sum(p.demand_kg for p in points)
    base_capacity = total_demand / n_vehicles

    vehicles: List[Vehicle] = []
    for v in range(n_vehicles):
        vehicles.append(
            Vehicle(
                id=v,
                name=f"Van {v + 1}",
                capacity_kg=round(base_capacity * rng.uniform(1.2, 1.6), 0),
                max_range_km=round(rng.uniform(90.0, 160.0), 0),
            )
        )

    return depot, points, vehicles
