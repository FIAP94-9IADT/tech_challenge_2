"""Prompts, cliente de LLM e relatórios operacionais."""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import asdict

from .models import Problem, Solution


SYSTEM_INSTRUCTION = """Você é um analista de logística hospitalar. Use somente os dados
fornecidos. Não invente endereços, tempos, ocorrências ou economias. Escreva em português
brasileiro, com instruções objetivas. Sinalize explicitamente restrições violadas."""


def route_context(problem: Problem, solution: Solution) -> dict:
    return {
        "deposito": asdict(problem.depot),
        "distancia_total_km": round(solution.total_distance_km, 2),
        "solucao_viavel": solution.feasible,
        "rotas": [
            {
                "veiculo": asdict(problem.vehicles[i]),
                "paradas_na_ordem": [asdict(problem.deliveries[j]) for j in route],
                "metricas": asdict(solution.metrics[i]),
            }
            for i, route in enumerate(solution.routes)
        ],
    }


def build_prompt(problem: Problem, solution: Solution, task: str = "daily") -> str:
    requests = {
        "daily": "Gere instruções por veículo e um resumo diário de eficiência.",
        "weekly": "Gere um relatório semanal e sugestões prudentes de melhoria.",
        "qa": "Responda à pergunta usando exclusivamente o contexto.",
    }
    return (
        f"{SYSTEM_INSTRUCTION}\n\nTarefa: {requests.get(task, task)}\n"
        f"Contexto estruturado:\n{json.dumps(route_context(problem, solution), ensure_ascii=False, indent=2)}"
    )


class ReportGenerator(ABC):
    @abstractmethod
    def generate(self, problem: Problem, solution: Solution, task: str = "daily") -> str: ...


class LocalReportGenerator(ReportGenerator):
    """Fallback auditável para execução acadêmica sem credenciais externas."""

    def generate(self, problem: Problem, solution: Solution, task: str = "daily") -> str:
        lines = ["# Plano operacional de entregas", "", f"Distância total: {solution.total_distance_km:.2f} km."]
        lines.append("Todas as restrições foram atendidas." if solution.feasible else "Atenção: há restrições violadas; revise o planejamento.")
        for i, route in enumerate(solution.routes):
            vehicle, metric = problem.vehicles[i], solution.metrics[i]
            lines.extend(["", f"## {vehicle.id}", f"Carga: {metric.load_kg:.1f}/{vehicle.capacity_kg:.1f} kg; percurso: {metric.distance_km:.2f}/{vehicle.max_distance_km:.2f} km."])
            if not route:
                lines.append("Veículo não utilizado.")
                continue
            for order, gene in enumerate(route, 1):
                delivery = problem.deliveries[gene]
                label = "CRÍTICA" if delivery.priority == 3 else ("ALTA" if delivery.priority == 2 else "REGULAR")
                lines.append(f"{order}. {delivery.name} — {delivery.demand_kg:.1f} kg — prioridade {label}.")
            lines.append(f"{len(route) + 1}. Retornar ao depósito {problem.depot.name}.")
        lines.extend(["", "## Recomendações", "Confirmar disponibilidade da carga antes da saída e registrar horários reais para comparar planejado e realizado."])
        return "\n".join(lines)


class GeminiReportGenerator(ReportGenerator):
    """Integração REST com um modelo Gemini pré-treinado."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        if not self.api_key:
            raise ValueError("Defina GEMINI_API_KEY para utilizar a LLM")

    def generate(self, problem: Problem, solution: Solution, task: str = "daily") -> str:
        model = urllib.parse.quote(self.model, safe="")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        body = {
            "contents": [{"parts": [{"text": build_prompt(problem, solution, task)}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2048},
        }
        request = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                data = json.load(response)
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (OSError, KeyError, IndexError) as exc:
            raise RuntimeError(f"Falha ao gerar relatório pela LLM: {exc}") from exc


def answer_question(generator: ReportGenerator, problem: Problem, solution: Solution, question: str) -> str:
    safe_question = question.strip()[:1000]
    return generator.generate(problem, solution, f"Responda: {safe_question}")
