SYSTEM_PROMPT = """Você é um assistente médico especializado em oncologia feminina e saúde da mulher.
Seu papel é interpretar resultados de diagnósticos de câncer de mama de forma clara, empática e eticamente responsável.

Diretrizes:
- Use linguagem acessível, mas clinicamente precisa
- Seja sensível ao impacto emocional do diagnóstico
- Respeite a autonomia e privacidade da paciente
- Considere fatores sociais e contextuais específicos da saúde feminina
- Nunca faça diagnóstico definitivo — você apoia o profissional de saúde
- Oriente para a busca de confirmação médica especializada
- Mantenha tom encorajador sem minimizar a seriedade
"""

DIAGNOSIS_PROMPT_TEMPLATE = """
Analise o seguinte resultado de triagem de câncer de mama e gere uma interpretação clínica especializada:

**Dados da Paciente:**
- Grupo etário: {age_group}
- Resultado do modelo: {diagnosis_label}
- Probabilidade de malignidade: {probability_malignant:.1%}
- Probabilidade de benignidade: {probability_benign:.1%}

**Principais características clínicas identificadas:**
{top_features}

**Métricas do modelo (contexto de confiabilidade):**
- Sensibilidade do modelo: {sensitivity:.1%}
- Especificidade do modelo: {specificity:.1%}
- F1-Score: {f1:.1%}

Por favor, gere:
1. **Interpretação do resultado** (2-3 parágrafos): explique o que esse resultado significa clinicamente
2. **Fatores de risco contextuais**: considerando o grupo etário e as características identificadas
3. **Próximos passos recomendados**: orientações práticas baseadas no resultado
4. **Nota de confidencialidade**: lembrete sobre privacidade e encaminhamento adequado

Responda em português brasileiro, com linguagem sensível e empática.
"""

EXPERIMENT_SUMMARY_PROMPT = """
Como especialista em machine learning para saúde feminina, analise os resultados da otimização via algoritmo genético:

**Modelo:** {model_type}
**Dataset:** Wisconsin Breast Cancer (câncer de mama)

**Resultados da Otimização:**
{results_table}

**Melhores hiperparâmetros encontrados:**
{best_params}

**Comparação com baseline:**
- Sensibilidade baseline: {baseline_sensitivity:.1%} → Otimizado: {opt_sensitivity:.1%}
- Especificidade baseline: {baseline_specificity:.1%} → Otimizado: {opt_specificity:.1%}
- F1-Score baseline: {baseline_f1:.1%} → Otimizado: {opt_f1:.1%}

Gere uma análise técnica em português cobrindo:
1. Impacto clínico das melhorias (em termos de pacientes afetadas)
2. Trade-offs entre sensibilidade e especificidade para rastreamento de câncer de mama
3. Considerações de equidade entre grupos demográficos
4. Recomendações para implementação clínica
"""

ROUTE_QUERY_PROMPT = """
Você é um assistente de análise de diagnósticos médicos. Responda à seguinte pergunta com base nos resultados:

Contexto: {context}

Pergunta: {question}

Responda de forma direta e objetiva em português.
"""


def build_diagnosis_prompt(
    age_group: str,
    diagnosis_label: str,
    prob_malignant: float,
    top_features: list[tuple[str, float]],
    metrics: dict,
) -> str:
    features_text = "\n".join(
        f"  - {name}: {value:.4f}" for name, value in top_features[:5]
    )
    return DIAGNOSIS_PROMPT_TEMPLATE.format(
        age_group=age_group,
        diagnosis_label=diagnosis_label,
        probability_malignant=prob_malignant,
        probability_benign=1.0 - prob_malignant,
        top_features=features_text,
        sensitivity=metrics.get("sensibilidade", 0),
        specificity=metrics.get("especificidade", 0),
        f1=metrics.get("f1_score", 0),
    )
