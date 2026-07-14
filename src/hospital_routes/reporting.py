"""Prompts, cliente de LLM e relatórios operacionais."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import asdict
from pathlib import Path

from .models import Problem, Solution


SYSTEM_INSTRUCTION = """Você é um analista de logística hospitalar. Use somente os dados
fornecidos. Não invente endereços, tempos, ocorrências ou economias. Escreva em português
brasileiro, com instruções objetivas. Avise com clareza quando houver alguma restrição violada."""

PROJECT_GEMINI_MODEL = "gemini-3.1-flash-lite"


def _load_local_key() -> str | None:
    """Lê a chave de um `.env` local ignorado pelo Git."""
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return None
    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() in {"GOOGLE_API_KEY", "GEMINI_API_KEY"}:
            values[name.strip()] = value.strip().strip("'\"")
    return values.get("GOOGLE_API_KEY") or values.get("GEMINI_API_KEY") or None


def configured_gemini_key() -> str | None:
    """Prioriza variáveis do processo e usa `.env` somente no ambiente local."""
    return os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or _load_local_key()


def comparison_metrics(solution: Solution, baseline: Solution) -> dict:
    """Compara duas soluções sem inferir tempo ou custo não observados."""
    fitness_reduction = 100 * (baseline.fitness - solution.fitness) / baseline.fitness
    distance_reduction = baseline.total_distance_km - solution.total_distance_km
    distance_reduction_pct = (
        100 * distance_reduction / baseline.total_distance_km
        if baseline.total_distance_km
        else 0.0
    )
    return {
        "referencia": "vizinho mais próximo",
        "fitness_referencia": round(baseline.fitness, 4),
        "fitness_solucao": round(solution.fitness, 4),
        "reducao_fitness_percentual": round(fitness_reduction, 2),
        "distancia_referencia_km": round(baseline.total_distance_km, 4),
        "distancia_solucao_km": round(solution.total_distance_km, 4),
        "reducao_distancia_km": round(distance_reduction, 4),
        "reducao_distancia_percentual": round(distance_reduction_pct, 2),
        "observacao": (
            "Não há dados de velocidade, tempo real ou custo monetário; "
            "essas economias não devem ser estimadas."
        ),
    }


def route_context(
    problem: Problem,
    solution: Solution,
    comparison: dict | None = None,
) -> dict:
    context = {
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
    if comparison:
        context["comparacao_de_eficiencia"] = comparison
    return context


def build_prompt(
    problem: Problem,
    solution: Solution,
    task: str = "daily",
    comparison: dict | None = None,
) -> str:
    requests = {
        "daily": "Gere instruções por veículo e um resumo diário de eficiência.",
        "weekly": "Gere um relatório semanal e sugestões prudentes de melhoria.",
        "qa": "Responda à pergunta usando exclusivamente o contexto.",
    }
    return (
        f"{SYSTEM_INSTRUCTION}\n\nTarefa: {requests.get(task, task)}\n"
        "Não converta distância em tempo ou dinheiro sem dados observados.\n"
        f"Contexto estruturado:\n{json.dumps(route_context(problem, solution, comparison), ensure_ascii=False, indent=2)}"
    )


class ReportGenerator(ABC):
    @abstractmethod
    def generate(
        self,
        problem: Problem,
        solution: Solution,
        task: str = "daily",
        comparison: dict | None = None,
    ) -> str: ...


class LocalReportGenerator(ReportGenerator):
    """Gera um relatório determinístico quando a integração externa não está disponível."""

    def generate(
        self,
        problem: Problem,
        solution: Solution,
        task: str = "daily",
        comparison: dict | None = None,
    ) -> str:
        lines = ["# Plano operacional de entregas", "", f"Distância total: {solution.total_distance_km:.2f} km."]
        lines.append("Todas as restrições foram atendidas." if solution.feasible else "Atenção: há restrições violadas; revise o planejamento.")
        if comparison:
            lines.extend([
                "",
                "## Comparação de eficiência",
                (
                    f"Em comparação com {comparison['referencia']}, o fitness variou "
                    f"{comparison['reducao_fitness_percentual']:.2f}% e a distância variou "
                    f"{comparison['reducao_distancia_km']:.2f} km."
                ),
                comparison["observacao"],
            ])
        for i, route in enumerate(solution.routes):
            vehicle, metric = problem.vehicles[i], solution.metrics[i]
            lines.extend([
                "",
                f"## {vehicle.id}",
                (
                    f"Carga: {metric.load_kg:.1f} kg de {vehicle.capacity_kg:.1f} kg; "
                    f"percurso: {metric.distance_km:.2f} km de {vehicle.max_distance_km:.2f} km."
                ),
            ])
            if not route:
                lines.append("Veículo não utilizado.")
                continue
            for order, gene in enumerate(route, 1):
                delivery = problem.deliveries[gene]
                label = "CRÍTICA" if delivery.priority == 3 else ("ALTA" if delivery.priority == 2 else "REGULAR")
                lines.append(f"{order}. {delivery.name} — {delivery.demand_kg:.1f} kg — prioridade {label}.")
            lines.append(f"{len(route) + 1}. Retornar ao depósito {problem.depot.name}.")
        lines.extend([
            "",
            "## Recomendações",
            (
                "Confirme a disponibilidade da carga antes da saída e registre os horários reais "
                "para comparar o planejamento com a operação realizada."
            ),
        ])
        return "\n".join(lines)


class GeminiReportGenerator(ReportGenerator):
    """Integração REST com um modelo Gemini pré-treinado."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or configured_gemini_key()
        self.model = model or PROJECT_GEMINI_MODEL
        if not self.api_key:
            raise RuntimeError(
                "A chave do Gemini não foi encontrada. Defina GOOGLE_API_KEY ou GEMINI_API_KEY "
                "no ambiente, no kernel ou em um arquivo .env local."
            )

    def generate(
        self,
        problem: Problem,
        solution: Solution,
        task: str = "daily",
        comparison: dict | None = None,
    ) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        body = {
            "contents": [{"parts": [{"text": build_prompt(problem, solution, task, comparison)}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 8192},
        }
        request = urllib.request.Request(
            url,
            json.dumps(body).encode(),
            {"Content-Type": "application/json", "x-goog-api-key": self.api_key},
        )
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                data = json.load(response)
            candidate = data["candidates"][0]
            parts = candidate["content"]["parts"]
            visible_parts = [part["text"] for part in parts if "text" in part and not part.get("thought")]
            if not visible_parts:
                visible_parts = [part["text"] for part in parts if "text" in part]
            result = "\n".join(visible_parts).strip()
            if not result:
                raise RuntimeError("O Gemini retornou uma resposta sem conteúdo textual.")
            if candidate.get("finishReason") == "MAX_TOKENS":
                raise RuntimeError(
                    "O Gemini interrompeu o relatório por limite de tokens. "
                    "Reduza o cenário ou solicite um relatório mais conciso."
                )
            return result
        except urllib.error.HTTPError as exc:
            try:
                detail = json.loads(exc.read().decode("utf-8"))["error"]["message"]
            except (ValueError, KeyError, UnicodeDecodeError):
                detail = str(exc)
            raise RuntimeError(f"Gemini recusou a requisição (HTTP {exc.code}): {detail}") from exc
        except (OSError, KeyError, IndexError) as exc:
            raise RuntimeError(f"Falha ao gerar relatório pela LLM: {exc}") from exc


def answer_question(generator: ReportGenerator, problem: Problem, solution: Solution, question: str) -> str:
    safe_question = question.strip()[:1000]
    return generator.generate(problem, solution, f"Responda: {safe_question}")
