import json

SYSTEM_PROMPT = (
    "Você é o coordenador de logística de um sistema hospitalar responsável "
    "pela distribuição de medicamentos e insumos entre unidades de saúde e "
    "atendimentos domiciliares. Você recebe rotas otimizadas por um algoritmo "
    "genético e sua função é comunicá-las de forma clara e segura para as "
    "equipes de entrega. Responda sempre em português do Brasil. "
    "Baseie-se APENAS nos dados fornecidos no contexto; se a informação não "
    "estiver no contexto, diga que não tem essa informação. "
    "Entregas com prioridade 'critical' envolvem medicamentos críticos "
    "(insulina, hemoderivados, oncológicos) e exigem atenção especial a "
    "temperatura, lacres e conferência na entrega."
)


def _context_block(solution_context: dict) -> str:
    return (
        "### DADOS DAS ROTAS (JSON)\n"
        "```json\n"
        + json.dumps(solution_context, ensure_ascii=False, indent=1)
        + "\n```"
    )


def instructions_prompt(solution_context: dict, vehicle_id=None) -> str:
    scope = (
        f"apenas para o veículo de id {vehicle_id}"
        if vehicle_id is not None
        else "para cada veículo da frota"
    )
    return (
        f"{_context_block(solution_context)}\n\n"
        f"Gere instruções de entrega detalhadas {scope}.\n"
        "Formato esperado, em Markdown:\n"
        "- Um título com o nome do veículo, carga total e distância total;\n"
        "- A sequência numerada de paradas, com nome da unidade, peso a "
        "entregar e prioridade;\n"
        "- Destaques de atenção para entregas críticas (conferência, "
        "temperatura, lacre);\n"
        "- Uma observação final sobre o retorno ao Hospital Central.\n"
        "Seja objetivo: o texto será lido por motoristas antes de sair para a rota."
    )


def report_prompt(solution_context: dict, period: str = "diário", comparison: dict = None) -> str:
    comparison_block = ""
    if comparison:
        comparison_block = (
            "\n### COMPARATIVO COM HEURÍSTICA BASELINE (Nearest Neighbor)\n"
            "```json\n" + json.dumps(comparison, ensure_ascii=False, indent=1) + "\n```\n"
        )
    return (
        f"{_context_block(solution_context)}\n"
        f"{comparison_block}\n"
        f"Escreva um relatório {period} de eficiência logística para a "
        "coordenação do hospital, em Markdown, contendo:\n"
        "1. Resumo executivo (2-3 frases);\n"
        "2. Indicadores: distância total, nº de entregas, distribuição por "
        "prioridade, ocupação da frota (carga vs capacidade);\n"
        "3. Economia estimada em relação à rota baseline, se houver dados de comparação;\n"
        "4. Riscos e pontos de atenção (ex.: veículos próximos do limite de "
        "autonomia ou capacidade, entregas críticas no fim da rota);\n"
        "5. Três sugestões de melhoria do processo baseadas nos padrões observados."
    )


def qa_prompt(solution_context: dict, question: str) -> str:
    return (
        f"{_context_block(solution_context)}\n\n"
        "Responda à pergunta abaixo usando somente os dados acima. "
        "Se precisar calcular algo (somas, médias), calcule passo a passo "
        "internamente e apresente só o resultado final de forma clara.\n\n"
        f"Pergunta: {question}"
    )
