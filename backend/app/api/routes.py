import logging
import time

from flask import Blueprint, jsonify, request

from ..core.baseline import solve_nearest_neighbor
from ..core.genetic_algorithm import GAConfig, run_ga
from ..data.synthetic import generate_scenario
from ..services import llm_service

logger = logging.getLogger(__name__)

api = Blueprint("api", __name__, url_prefix="/api")

# estado em memória da última execução
_state = {
    "scenario": None,   # (depot, points, vehicles)
    "result": None,     # GAResult
    "baseline": None,   # Solution (nearest neighbor)
    "elapsed_s": None,
}


def _bad_request(message: str):
    return jsonify({"error": message}), 400


def _get_int(data, key, default, lo, hi):
    value = data.get(key, default)
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"'{key}' deve ser um inteiro")
    if not (lo <= value <= hi):
        raise ValueError(f"'{key}' deve estar entre {lo} e {hi}")
    return value


def _get_float(data, key, default, lo, hi):
    value = data.get(key, default)
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"'{key}' deve ser um número")
    if not (lo <= value <= hi):
        raise ValueError(f"'{key}' deve estar entre {lo} e {hi}")
    return value


def _scenario_dict():
    depot, points, vehicles = _state["scenario"]
    return {
        "depot": depot.to_dict(),
        "points": [p.to_dict() for p in points],
        "vehicles": [v.to_dict() for v in vehicles],
    }


def _solution_context():
    """Contexto JSON compacto entregue aos prompts do LLM."""
    depot, points, vehicles = _state["scenario"]
    result = _state["result"]
    points_by_id = {p.id: p for p in points}
    vehicles_by_id = {v.id: v for v in vehicles}

    routes = []
    for route in result.best_solution.routes:
        vehicle = vehicles_by_id[route.vehicle_id]
        routes.append(
            {
                "veiculo": vehicle.name,
                "capacidade_kg": vehicle.capacity_kg,
                "autonomia_km": vehicle.max_range_km,
                "carga_total_kg": round(route.load_kg, 1),
                "distancia_km": round(route.distance_km, 1),
                "paradas": [
                    {
                        "ordem": i + 1,
                        "unidade": points_by_id[s].name,
                        "tipo": points_by_id[s].kind,
                        "peso_kg": points_by_id[s].demand_kg,
                        "prioridade": points_by_id[s].priority.value,
                    }
                    for i, s in enumerate(route.stops)
                ],
            }
        )

    return {
        "deposito": depot.name,
        "distancia_total_km": round(result.best_solution.total_distance_km, 1),
        "solucao_viavel": result.best_solution.feasible,
        "entregas_nao_alocadas": len(result.best_solution.unassigned),
        "rotas": routes,
    }


def _comparison_dict():
    result = _state["result"]
    baseline = _state["baseline"]
    if not (result and baseline):
        return None
    ga_d = result.best_solution.total_distance_km
    nn_d = baseline.total_distance_km
    return {
        "distancia_ga_km": round(ga_d, 1),
        "distancia_nearest_neighbor_km": round(nn_d, 1),
        "economia_km": round(nn_d - ga_d, 1),
        "economia_pct": round((nn_d - ga_d) / nn_d * 100, 1) if nn_d else 0,
    }


@api.get("/health")
def health():
    return jsonify({"status": "ok"})


@api.get("/scenario")
def scenario():
    try:
        n_points = _get_int(request.args, "n_points", 20, 3, 100)
        n_vehicles = _get_int(request.args, "n_vehicles", 3, 1, 10)
        seed = _get_int(request.args, "seed", 42, 0, 10**9)
    except ValueError as exc:
        return _bad_request(str(exc))

    _state["scenario"] = generate_scenario(n_points=n_points, n_vehicles=n_vehicles, seed=seed)
    _state["result"] = None
    _state["baseline"] = None
    return jsonify(_scenario_dict())


@api.post("/optimize")
def optimize():
    data = request.get_json(silent=True) or {}
    try:
        n_points = _get_int(data, "n_points", 20, 3, 100)
        n_vehicles = _get_int(data, "n_vehicles", 3, 1, 10)
        seed = _get_int(data, "seed", 42, 0, 10**9)
        population_size = _get_int(data, "population_size", 150, 10, 1000)
        generations = _get_int(data, "generations", 400, 10, 5000)
        mutation_probability = _get_float(data, "mutation_probability", 0.3, 0.0, 1.0)
        elitism = _get_int(data, "elitism", 2, 0, 50)
        selection = data.get("selection", "tournament")
        if selection not in ("tournament", "roulette"):
            return _bad_request("'selection' deve ser 'tournament' ou 'roulette'")
    except ValueError as exc:
        return _bad_request(str(exc))

    # reaproveita o cenário quando a requisição corresponde ao atual
    if _state["scenario"] is None or data.get("new_scenario", True):
        _state["scenario"] = generate_scenario(n_points=n_points, n_vehicles=n_vehicles, seed=seed)

    depot, points, vehicles = _state["scenario"]

    config = GAConfig(
        population_size=population_size,
        generations=generations,
        mutation_probability=mutation_probability,
        elitism=elitism,
        selection=selection,
        seed=seed,
    )

    logger.info(
        "optimize: %d points, %d vehicles, pop=%d, gen=%d, mut=%.2f, sel=%s",
        len(points), len(vehicles), population_size, generations, mutation_probability, selection,
    )

    start = time.perf_counter()
    result = run_ga(depot, points, vehicles, config)
    elapsed = time.perf_counter() - start

    _state["result"] = result
    _state["baseline"] = solve_nearest_neighbor(depot, points, vehicles)
    _state["elapsed_s"] = elapsed

    logger.info(
        "optimize done in %.2fs: fitness=%.1f distance=%.1fkm feasible=%s",
        elapsed, result.best_solution.fitness,
        result.best_solution.total_distance_km, result.best_solution.feasible,
    )

    return jsonify(
        {
            "scenario": _scenario_dict(),
            "result": result.to_dict(),
            "baseline": _state["baseline"].to_dict(),
            "comparison": _comparison_dict(),
            "elapsed_s": round(elapsed, 2),
        }
    )


def _require_solution():
    if _state["result"] is None:
        return jsonify({"error": "Nenhuma otimização executada ainda. Chame POST /api/optimize primeiro."}), 409
    return None


@api.post("/llm/instructions")
def llm_instructions():
    guard = _require_solution()
    if guard:
        return guard
    data = request.get_json(silent=True) or {}
    vehicle_id = data.get("vehicle_id")
    try:
        text = llm_service.generate_instructions(_solution_context(), vehicle_id)
    except llm_service.LLMNotConfiguredError as exc:
        return jsonify({"error": str(exc)}), 503
    return jsonify({"instructions": text})


@api.post("/llm/report")
def llm_report():
    guard = _require_solution()
    if guard:
        return guard
    data = request.get_json(silent=True) or {}
    period = data.get("period", "diário")
    try:
        text = llm_service.generate_report(_solution_context(), period, _comparison_dict())
    except llm_service.LLMNotConfiguredError as exc:
        return jsonify({"error": str(exc)}), 503
    return jsonify({"report": text})


@api.post("/llm/ask")
def llm_ask():
    guard = _require_solution()
    if guard:
        return guard
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return _bad_request("'question' é obrigatória")
    try:
        text = llm_service.answer_question(_solution_context(), question)
    except llm_service.LLMNotConfiguredError as exc:
        return jsonify({"error": str(exc)}), 503
    return jsonify({"answer": text})
