import os
from typing import Optional

from . import prompts

DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


class LLMNotConfiguredError(RuntimeError):
    """Lançada quando OPENAI_API_KEY está ausente."""


def _get_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise LLMNotConfiguredError(
            "OPENAI_API_KEY não configurada. Defina a variável de ambiente "
            "(ou o arquivo backend/.env) para habilitar os recursos de LLM."
        )
    from openai import OpenAI

    return OpenAI(api_key=api_key)


def _chat(user_prompt: str, temperature: float = 0.4) -> str:
    client = _get_client()
    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        temperature=temperature,
        messages=[
            {"role": "system", "content": prompts.SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content


def generate_instructions(solution_context: dict, vehicle_id: Optional[int] = None) -> str:
    """Instruções de entrega para os motoristas, por veículo."""
    return _chat(prompts.instructions_prompt(solution_context, vehicle_id))


def generate_report(solution_context: dict, period: str = "diário", comparison: Optional[dict] = None) -> str:
    """Relatório de eficiência diário/semanal com sugestões de melhoria."""
    return _chat(prompts.report_prompt(solution_context, period, comparison))


def answer_question(solution_context: dict, question: str) -> str:
    """Perguntas e respostas em linguagem natural sobre as rotas atuais."""
    return _chat(prompts.qa_prompt(solution_context, question), temperature=0.2)
