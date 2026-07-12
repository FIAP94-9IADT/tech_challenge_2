from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Tuple


class Priority(str, Enum):
    CRITICAL = "critical"  # ex.: medicamento crítico (insulina, hemoderivados)
    HIGH = "high"          # ex.: insumos urgentes
    NORMAL = "normal"      # ex.: insumos regulares


# peso usado pela função de fitness: entregas críticas atendidas
# tarde custam mais que entregas normais
PRIORITY_WEIGHT = {
    Priority.CRITICAL: 1.0,
    Priority.HIGH: 0.4,
    Priority.NORMAL: 0.0,
}


@dataclass
class DeliveryPoint:
    id: int
    name: str
    lat: float
    lon: float
    demand_kg: float
    priority: Priority
    kind: str = "ubs"  # ubs | clinic | home_care

    @property
    def coords(self) -> Tuple[float, float]:
        return (self.lat, self.lon)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["priority"] = self.priority.value
        return d


@dataclass
class Depot:
    name: str
    lat: float
    lon: float

    @property
    def coords(self) -> Tuple[float, float]:
        return (self.lat, self.lon)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Vehicle:
    id: int
    name: str
    capacity_kg: float
    max_range_km: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Route:
    vehicle_id: int
    stops: List[int] = field(default_factory=list)  # ids dos pontos de entrega, na ordem de visita
    distance_km: float = 0.0
    load_kg: float = 0.0

    def to_dict(self) -> dict:
        return {
            "vehicle_id": self.vehicle_id,
            "stops": list(self.stops),
            "distance_km": round(self.distance_km, 3),
            "load_kg": round(self.load_kg, 3),
        }


@dataclass
class Solution:
    routes: List[Route]
    total_distance_km: float
    fitness: float
    feasible: bool
    unassigned: List[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "routes": [r.to_dict() for r in self.routes],
            "total_distance_km": round(self.total_distance_km, 3),
            "fitness": round(self.fitness, 3),
            "feasible": self.feasible,
            "unassigned": list(self.unassigned),
        }
