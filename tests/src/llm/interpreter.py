import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from src.llm.prompts import SYSTEM_PROMPT, build_diagnosis_prompt, ROUTE_QUERY_PROMPT

load_dotenv()

RESULTS_DIR = Path(__file__).parent.parent.parent / "data" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

OPENAI_MODEL = "gpt-4o-mini"


def _get_client():
    """Retorna cliente OpenAI se a chave estiver disponível."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key)
    except ImportError:
        return None


def _chat(client, prompt: str, max_tokens: int = 1024) -> str:
    """Chama a API ChatGPT e retorna o texto da resposta."""
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content


def generate_diagnosis_interpretation(
    age_group: str,
    diagnosis_label: str,
    prob_malignant: float,
    top_features: list[tuple[str, float]],
    metrics: dict,
    save_response: bool = True,
) -> str:
    """
    Gera interpretação clínica do diagnóstico via ChatGPT.
    Salva a resposta para uso futuro no fine-tuning (Fase 3).
    """
    client = _get_client()
    prompt = build_diagnosis_prompt(age_group, diagnosis_label, prob_malignant, top_features, metrics)

    if client is None:
        response_text = _mock_diagnosis_response(diagnosis_label, age_group, prob_malignant)
    else:
        response_text = _chat(client, prompt, max_tokens=1024)

    if save_response:
        _save_response(
            prompt_type="diagnosis",
            prompt=prompt,
            response=response_text,
            metadata={
                "age_group": age_group,
                "diagnosis": diagnosis_label,
                "prob_malignant": prob_malignant,
            },
        )

    return response_text


def generate_experiment_analysis(
    model_type: str,
    results_table: str,
    best_params: dict,
    baseline_metrics: dict,
    optimized_metrics: dict,
    save_response: bool = True,
) -> str:
    """Gera análise técnica comparativa dos experimentos."""
    from src.llm.prompts import EXPERIMENT_SUMMARY_PROMPT

    client = _get_client()
    prompt = EXPERIMENT_SUMMARY_PROMPT.format(
        model_type=model_type,
        results_table=results_table,
        best_params=json.dumps(best_params, ensure_ascii=False, indent=2),
        baseline_sensitivity=baseline_metrics.get("sensibilidade", 0),
        baseline_specificity=baseline_metrics.get("especificidade", 0),
        baseline_f1=baseline_metrics.get("f1_score", 0),
        opt_sensitivity=optimized_metrics.get("sensibilidade", 0),
        opt_specificity=optimized_metrics.get("especificidade", 0),
        opt_f1=optimized_metrics.get("f1_score", 0),
    )

    if client is None:
        response_text = _mock_analysis_response(baseline_metrics, optimized_metrics)
    else:
        response_text = _chat(client, prompt, max_tokens=1500)

    if save_response:
        _save_response(
            prompt_type="experiment_analysis",
            prompt=prompt,
            response=response_text,
            metadata={"model_type": model_type, "best_params": best_params},
        )

    return response_text


def answer_natural_language_query(question: str, context: str, save_response: bool = True) -> str:
    """Responde perguntas em linguagem natural sobre diagnósticos."""
    client = _get_client()
    prompt = ROUTE_QUERY_PROMPT.format(context=context, question=question)

    if client is None:
        response_text = f"[Modo offline] Pergunta recebida: '{question}'. Configure OPENAI_API_KEY para respostas reais."
    else:
        response_text = _chat(client, prompt, max_tokens=512)

    if save_response:
        _save_response("query", prompt, response_text, {"question": question})

    return response_text


def _save_response(prompt_type: str, prompt: str, response: str, metadata: dict):
    """Persiste prompt + resposta para base de dados da Fase 3."""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": prompt_type,
        "prompt": prompt,
        "response": response,
        "metadata": metadata,
    }
    filename = RESULTS_DIR / f"{prompt_type}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)


def _mock_diagnosis_response(label: str, age_group: str, prob: float) -> str:
    return f"""**[Modo demonstração — configure OPENAI_API_KEY para respostas reais]**

**Interpretação do Resultado**

O modelo de triagem indicou resultado **{label}** para a paciente do grupo etário **{age_group}**, com probabilidade estimada de malignidade de **{prob:.1%}**.

Este resultado foi obtido por um modelo Random Forest otimizado via algoritmo genético, com alta sensibilidade para minimizar casos não detectados. É fundamental que este resultado seja confirmado por exame histopatológico e avaliação clínica especializada.

**Fatores de Risco Contextuais**

Independentemente do resultado, recomenda-se manutenção de exames periódicos conforme protocolo para o grupo etário. Fatores como histórico familiar, densidade mamária e estilo de vida devem ser considerados pelo profissional responsável.

**Próximos Passos Recomendados**

1. Encaminhamento imediato para mastologista ou oncologista
2. Realização de biópsia para confirmação histopatológica
3. Exames complementares: ultrassonografia e/ou ressonância magnética
4. Suporte psicológico especializado durante o processo diagnóstico

**Nota de Confidencialidade**

Este resultado é estritamente confidencial. O acesso deve ser restrito à paciente e à equipe médica responsável, em conformidade com a LGPD e os princípios de privacidade médica.
"""


def _mock_analysis_response(baseline: dict, optimized: dict) -> str:
    delta_s = optimized.get("sensibilidade", 0) - baseline.get("sensibilidade", 0)
    return f"""**[Modo demonstração — configure OPENAI_API_KEY para análise completa]**

**Análise do Impacto Clínico**

A otimização via algoritmo genético resultou em melhoria de **{delta_s:+.1%}** na sensibilidade do modelo. Em um cenário real com 10.000 pacientes rastreadas anualmente, isso representaria potencialmente dezenas de casos adicionais detectados precocemente.

**Trade-offs Sensibilidade vs Especificidade**

Para rastreamento de câncer de mama, priorizar sensibilidade é clinicamente justificado: um falso negativo (câncer não detectado) tem consequências muito mais graves que um falso positivo (biópsia desnecessária). O modelo otimizado mantém equilíbrio adequado entre os dois critérios.

**Considerações de Equidade**

O score de equidade avalia se o modelo performa de forma consistente entre grupos etários. Modelos com alta variância entre grupos indicam potencial viés que deve ser investigado com dados mais representativos.

**Recomendações para Implementação**

- Validação em dataset multicêntrico brasileiro antes de implementação clínica
- Monitoramento contínuo das métricas por grupo demográfico
- Revisão periódica dos hiperparâmetros com novos dados
"""
