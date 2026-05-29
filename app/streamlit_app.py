"""
Interface Streamlit — Tech Challenge Fase 2
Otimização de modelos de diagnóstico para saúde da mulher
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(_ROOT / "tests"))  # src/ lives inside tests/

from src.data.loader import load_dataset, get_feature_description
from src.genetic.algorithm import GAConfig, run_genetic_algorithm
from src.genetic.fitness import get_detailed_metrics, calculate_fitness
from src.llm.interpreter import (
    generate_diagnosis_interpretation,
    generate_experiment_analysis,
    answer_natural_language_query,
)
from src.models.classifier import build_model, get_model_display_name
from src.optimization.grid_search import run_grid_search
from src.optimization.random_search import run_random_search
from src.optimization.multiobjective import run_nsga2
from src.optimization.neat_optimizer import run_neat
from src.utils.metrics import compare_models, per_group_metrics

st.set_page_config(
    page_title="Saúde da Mulher — Otimização ML",
    page_icon="🎗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.metric-card { background: #f8f9fa; border-radius: 8px; padding: 12px; text-align: center; }
.positive-delta { color: #28a745; font-weight: bold; }
.negative-delta { color: #dc3545; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ── Labels dos métodos ────────────────────────────────────────────────────────
_METHOD_LABELS = {
    "genetic_algorithm": "Algoritmo Genético (AG)",
    "grid_search": "Grid Search (Força Bruta)",
    "random_search": "Random Search (Estocástico)",
    "nsga2": "NSGA-II (Multi-Objetivo)",
    "neat": "NEAT (Neuroevolução)",
}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🎗️ Saúde da Mulher")
    st.caption("Tech Challenge Fase 2 — FIAP PosTech")
    st.divider()

    model_type = st.selectbox(
        "Tipo de Modelo",
        ["random_forest", "svm", "logistic_regression"],
        format_func=get_model_display_name,
    )

    optim_method = st.selectbox(
        "Método de Otimização",
        list(_METHOD_LABELS.keys()),
        format_func=lambda m: _METHOD_LABELS[m],
    )

    st.divider()

    # Defaults sempre definidos para evitar NameError em outros contextos
    pop_size = 50
    generations = 25
    mutation_rate = 0.15
    crossover_rate = 0.80
    random_state = 42
    cx_method = "uniform"
    mut_method = "random_reset"
    mut_intensity = 1.0
    adaptive_rates = False
    rs_iters = 50
    rs_cv = 3
    gs_cv = 3
    nsga_pop = 40
    nsga_gen = 15
    neat_pop = 30
    neat_gen = 15

    if optim_method == "genetic_algorithm":
        st.subheader("Parâmetros — AG")
        pop_size = st.slider("Tamanho da população", 10, 150, 50, 10)
        generations = st.slider("Gerações", 5, 100, 25, 5)
        mutation_rate = st.slider("Taxa de mutação", 0.01, 0.50, 0.15, 0.01)
        crossover_rate = st.slider("Taxa de crossover", 0.50, 1.00, 0.80, 0.05)
        random_state = st.number_input("Semente aleatória", value=42)
        cx_method = st.selectbox(
            "Método de crossover",
            ["uniform", "arithmetic"],
            format_func=lambda x: "Uniforme" if x == "uniform" else "Aritmético",
            help="Aritmético: combina parâmetros numéricos por interpolação linear (Aula 3)",
        )
        mut_method = st.selectbox(
            "Método de mutação",
            ["random_reset", "gaussian"],
            format_func=lambda x: "Reset aleatório" if x == "random_reset" else "Gaussiana",
            help="Gaussiana: perturbação contínua em parâmetros numéricos (Aula 3)",
        )
        mut_intensity = 1.0
        if mut_method == "gaussian":
            mut_intensity = st.slider("Intensidade da mutação gaussiana", 0.5, 3.0, 1.0, 0.5)
        adaptive_rates = st.toggle(
            "Taxas adaptativas",
            value=False,
            help="Ajusta automaticamente mutação e crossover conforme a entropia genética (Aula 3)",
        )
    elif optim_method == "random_search":
        st.subheader("Parâmetros — Random Search")
        rs_iters = st.slider("Iterações", 20, 200, 50, 10)
        rs_cv = st.slider("Folds (CV)", 2, 5, 3, 1)
        random_state = st.number_input("Semente aleatória", value=42)
    elif optim_method == "grid_search":
        st.subheader("Parâmetros — Grid Search")
        gs_cv = st.slider("Folds (CV)", 2, 5, 3, 1)
    elif optim_method == "nsga2":
        st.subheader("Parâmetros — NSGA-II")
        nsga_pop = st.slider("Tamanho da população", 20, 100, 40, 10)
        nsga_gen = st.slider("Gerações", 5, 50, 15, 5)
        random_state = st.number_input("Semente aleatória", value=42)
    elif optim_method == "neat":
        st.subheader("Parâmetros — NEAT")
        neat_pop = st.slider("Tamanho da população", 10, 100, 30, 10)
        neat_gen = st.slider("Gerações", 5, 50, 15, 5)
        random_state = st.number_input("Semente aleatória", value=42)

    st.divider()
    _btn_label = _METHOD_LABELS[optim_method].split("(")[0].strip()
    run_btn = st.button(f"▶ Executar {_btn_label}", type="primary", use_container_width=True)
    run_all_btn = st.button("⚡ Comparar Todos os Métodos", use_container_width=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_overview, tab_optimize, tab_compare, tab_llm, tab_query = st.tabs([
    "📋 Visão Geral",
    "🔬 Otimização",
    "📊 Comparação",
    "🤖 Interpretação LLM",
    "💬 Consulta",
])

# ── Cache de dados ─────────────────────────────────────────────────────────────
@st.cache_data
def get_data():
    return load_dataset(random_state=42)


@st.cache_data
def get_baseline_metrics(model_type: str):
    data = get_data()
    model = build_model(model_type)
    model.fit(data["X_train"], data["y_train"])
    pred = model.predict(data["X_test"])
    prob = model.predict_proba(data["X_test"])[:, 1] if hasattr(model, "predict_proba") else None
    metrics = get_detailed_metrics(data["y_test"].values, pred)
    return metrics, pred, prob


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — Visão Geral
# ─────────────────────────────────────────────────────────────────────────────
with tab_overview:
    st.title("Otimização de Diagnóstico para Saúde da Mulher")
    st.markdown("""
    Este sistema utiliza **algoritmos de otimização** para ajustar hiperparâmetros de modelos de
    machine learning para diagnóstico de **câncer de mama**, integrando **LLMs** (ChatGPT) para
    interpretação clínica dos resultados.

    **Dataset:** Wisconsin Breast Cancer (569 amostras, 30 features)
    """)

    data = get_data()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de amostras", len(data["X_train"]) + len(data["X_test"]))
    with col2:
        st.metric("Casos malignos", int(data["y_train"].sum() + data["y_test"].sum()))
    with col3:
        st.metric("Features clínicas", len(data["feature_names"]))
    with col4:
        st.metric("Grupos etários", 3)

    st.subheader("Distribuição do Dataset")
    col_a, col_b = st.columns(2)

    with col_a:
        counts = pd.concat([data["y_train"], data["y_test"]]).value_counts()
        fig = go.Figure(go.Pie(
            labels=["Benigno", "Maligno"],
            values=[counts.get(0, 0), counts.get(1, 0)],
            hole=0.4,
            marker_colors=["#27ae60", "#c0392b"],
        ))
        fig.update_layout(title="Classes", height=300, margin=dict(t=40, b=0))
        st.plotly_chart(fig, width="stretch")

    with col_b:
        group_counts = pd.Series(
            np.concatenate([data["age_train"], data["age_test"]])
        ).value_counts()
        fig2 = go.Figure(go.Bar(
            x=group_counts.index,
            y=group_counts.values,
            marker_color=["#3498db", "#9b59b6", "#e67e22"],
        ))
        fig2.update_layout(title="Grupos Etários", height=300, margin=dict(t=40, b=0))
        st.plotly_chart(fig2, width="stretch")

    st.subheader("Principais Features Clínicas")
    st.dataframe(
        pd.DataFrame(list(get_feature_description().items()), columns=["Feature", "Descrição"]),
        width="stretch", hide_index=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — Otimização (método selecionado na sidebar)
# ─────────────────────────────────────────────────────────────────────────────
with tab_optimize:
    st.title(f"{_METHOD_LABELS[optim_method]} — {get_model_display_name(model_type)}")

    def _save_result(method_key, best_params, test_metrics, fitness, extra=None):
        st.session_state["last_optim_result"] = {
            "method_key": method_key,
            "method": _METHOD_LABELS[method_key],
            "model_type": model_type,
            "best_params": best_params,
            "test_metrics": test_metrics,
            "fitness": fitness,
            "extra": extra or {},
        }

    if not run_btn and "last_optim_result" not in st.session_state:
        st.info("Configure os parâmetros na barra lateral e clique em **Executar**.")

    if run_btn:
        data = get_data()
        y_train_arr = data["y_train"].reset_index(drop=True)
        age_train_arr = np.asarray(data["age_train"])
        X_tr, X_val, y_tr, y_val, _, age_val = train_test_split(
            data["X_train"], y_train_arr, age_train_arr,
            test_size=0.2, random_state=42, stratify=y_train_arr,
        )

        # ── Algoritmo Genético ────────────────────────────────────────────────
        if optim_method == "genetic_algorithm":
            config = GAConfig(
                population_size=pop_size,
                generations=generations,
                mutation_rate=mutation_rate,
                crossover_rate=crossover_rate,
                random_state=int(random_state),
                crossover_method=cx_method,
                mutation_method=mut_method,
                mutation_intensity=mut_intensity,
                adaptive=adaptive_rates,
            )
            progress_bar = st.progress(0)
            status = st.empty()
            chart_ph = st.empty()
            best_hist, avg_hist = [], []

            def _update_ga(gen, total, best_fit):
                best_hist.append(best_fit)
                progress_bar.progress(gen / total)
                status.markdown(f"Geração **{gen}/{total}** | Melhor fitness: **{best_fit:.4f}**")
                _fig = go.Figure()
                _fig.add_trace(go.Scatter(y=best_hist, name="Melhor", line=dict(color="#c0392b")))
                _fig.update_layout(title="Convergência do AG", xaxis_title="Geração",
                                   yaxis_title="Fitness", height=300, margin=dict(t=40, b=30))
                chart_ph.plotly_chart(_fig, width="stretch")

            with st.spinner("Executando algoritmo genético..."):
                ga_result = run_genetic_algorithm(
                    model_type=model_type,
                    X_train=X_tr, y_train=y_tr,
                    X_val=X_val, y_val=y_val,
                    age_val=age_val,
                    config=config,
                    progress_callback=lambda g, t, f: (_update_ga(g, t, f), avg_hist.append(0)),
                )

            progress_bar.progress(1.0)
            status.success("Otimização concluída!")

            ga_model = build_model(model_type, ga_result.best_chromosome.genes)
            ga_model.fit(data["X_train"], data["y_train"])
            ga_pred = ga_model.predict(data["X_test"])
            ga_metrics = get_detailed_metrics(data["y_test"].values, ga_pred)
            _save_result("genetic_algorithm", ga_result.best_chromosome.genes, ga_metrics,
                         calculate_fitness(data["y_test"].values, ga_pred),
                         extra={"ga_result": ga_result})

            st.subheader("Melhores Hiperparâmetros")
            st.dataframe(
                pd.DataFrame([(k, str(v)) for k, v in ga_result.best_chromosome.genes.items()],
                             columns=["Hiperparâmetro", "Valor"]),
                width="stretch", hide_index=True,
            )
            fig_conv = go.Figure()
            fig_conv.add_trace(go.Scatter(
                y=ga_result.best_fitness_per_gen, name="Melhor", line=dict(color="#c0392b", width=2)
            ))
            fig_conv.add_trace(go.Scatter(
                y=ga_result.avg_fitness_per_gen, name="Média", line=dict(color="#7f8c8d", dash="dash")
            ))
            if ga_result.std_fitness_per_gen:
                fig_conv.add_trace(go.Scatter(
                    y=ga_result.std_fitness_per_gen, name="Desvio Padrão",
                    line=dict(color="#3498db", dash="dot"),
                ))
            fig_conv.update_layout(title="Curva de Convergência", xaxis_title="Geração",
                                   yaxis_title="Fitness", height=350)
            st.plotly_chart(fig_conv, width="stretch")

            if ga_result.diversity_per_gen:
                fig_div = go.Figure()
                fig_div.add_trace(go.Scatter(
                    y=ga_result.diversity_per_gen,
                    name="Entropia Genética",
                    line=dict(color="#27ae60", width=2),
                    fill="tozeroy",
                    fillcolor="rgba(39,174,96,0.1)",
                ))
                fig_div.update_layout(
                    title="Diversidade Genética (Entropia)",
                    xaxis_title="Geração",
                    yaxis_title="H (bits)",
                    height=280,
                )
                st.plotly_chart(fig_div, width="stretch")
                st.caption(
                    "Entropia alta = população diversificada (exploração). "
                    "Entropia baixa = convergência (aproveitamento)."
                )

        # ── Grid Search ───────────────────────────────────────────────────────
        elif optim_method == "grid_search":
            with st.spinner("Executando Grid Search..."):
                gs = run_grid_search(model_type, data["X_train"], data["y_train"],
                                     data["X_test"], data["y_test"], cv=gs_cv)
            st.success(f"Concluído — {gs['combinations_tested']} combinações testadas")
            _save_result("grid_search", gs["best_params"], gs["test_metrics"], gs["fitness"])

            st.subheader("Melhores Parâmetros")
            st.dataframe(
                pd.DataFrame([(k, str(v)) for k, v in gs["best_params"].items()],
                             columns=["Hiperparâmetro", "Valor"]),
                width="stretch", hide_index=True,
            )
            st.metric("CV Score (F1)", f"{gs['best_cv_score']:.4f}")

        # ── Random Search ─────────────────────────────────────────────────────
        elif optim_method == "random_search":
            with st.spinner(f"Executando Random Search ({rs_iters} iterações)..."):
                rs = run_random_search(model_type, data["X_train"], data["y_train"],
                                       data["X_test"], data["y_test"],
                                       n_iter=rs_iters, cv=rs_cv, random_state=int(random_state))
            st.success(f"Concluído — {rs_iters} amostras aleatórias")
            _save_result("random_search", rs["best_params"], rs["test_metrics"], rs["fitness"])

            st.subheader("Melhores Parâmetros")
            st.dataframe(
                pd.DataFrame([(k, str(v)) for k, v in rs["best_params"].items()],
                             columns=["Hiperparâmetro", "Valor"]),
                width="stretch", hide_index=True,
            )
            st.metric("CV Score (F1)", f"{rs['best_cv_score']:.4f}")

        # ── NSGA-II ───────────────────────────────────────────────────────────
        elif optim_method == "nsga2":
            with st.spinner("Executando NSGA-II..."):
                nsga = run_nsga2(
                    model_type, X_tr, y_tr, X_val, y_val,
                    data["X_test"], data["y_test"],
                    population_size=nsga_pop, generations=nsga_gen,
                    random_state=int(random_state),
                )
            st.success(f"Concluído — {len(nsga.pareto_front)} soluções na Fronteira de Pareto")

            if nsga.best_balanced:
                best = nsga.best_balanced
                best_m = build_model(model_type, best["params"])
                best_m.fit(data["X_train"], data["y_train"])
                best_pred = best_m.predict(data["X_test"])
                _save_result("nsga2", best["params"], best["test_metrics"],
                             calculate_fitness(data["y_test"].values, best_pred),
                             extra={"pareto_front": nsga.pareto_front})

                st.subheader("Melhor Solução (mais balanceada)")
                st.dataframe(
                    pd.DataFrame([(k, str(v)) for k, v in best["params"].items()],
                                 columns=["Hiperparâmetro", "Valor"]),
                    width="stretch", hide_index=True,
                )

                st.subheader("Fronteira de Pareto")
                sens_v = [p["val_sensitivity"] for p in nsga.pareto_front]
                spec_v = [p["val_specificity"] for p in nsga.pareto_front]
                fig_p = go.Figure()
                fig_p.add_trace(go.Scatter(
                    x=sens_v, y=spec_v, mode="markers+text",
                    marker=dict(size=12, color="#9b59b6", symbol="diamond"),
                    text=[f"P{i+1}" for i in range(len(sens_v))],
                    textposition="top center", name="Pareto",
                ))
                fig_p.update_layout(
                    title="Sensibilidade vs Especificidade",
                    xaxis_title="Sensibilidade", yaxis_title="Especificidade",
                    height=420, xaxis=dict(range=[0, 1.05]), yaxis=dict(range=[0, 1.05]),
                )
                st.plotly_chart(fig_p, width="stretch")

        # ── NEAT ──────────────────────────────────────────────────────────────
        elif optim_method == "neat":
            with st.spinner(f"Executando NEAT ({neat_gen} gerações, pop={neat_pop})..."):
                neat_r = run_neat(
                    data["X_train"].values, data["y_train"].values,
                    data["X_test"].values, data["y_test"].values,
                    population_size=neat_pop, generations=neat_gen,
                    random_state=int(random_state),
                )
            st.success(
                f"Concluído — {neat_r.best_n_nodes} nós, "
                f"{neat_r.best_n_connections} conexões, "
                f"{neat_r.n_species_final} espécies"
            )
            _save_result("neat", None, neat_r.test_metrics, neat_r.best_genome_fitness,
                         extra={"neat_result": neat_r})

            c1, c2, c3 = st.columns(3)
            with c1: st.metric("Nós na melhor rede", neat_r.best_n_nodes)
            with c2: st.metric("Conexões ativas", neat_r.best_n_connections)
            with c3: st.metric("Espécies finais", neat_r.n_species_final)

            col_na, col_nb = st.columns(2)
            with col_na:
                if neat_r.fitness_per_generation:
                    fig_fit = go.Figure()
                    fig_fit.add_trace(go.Scatter(
                        y=neat_r.fitness_per_generation, mode="lines+markers",
                        line=dict(color="#e67e22", width=2), name="Melhor fitness",
                    ))
                    fig_fit.update_layout(
                        title="Convergência do Fitness", xaxis_title="Geração",
                        yaxis_title="Fitness", height=300, yaxis=dict(range=[0, 1.05]),
                    )
                    st.plotly_chart(fig_fit, width="stretch")
            with col_nb:
                if neat_r.species_per_generation:
                    fig_sp = go.Figure()
                    fig_sp.add_trace(go.Bar(
                        y=neat_r.species_per_generation,
                        marker_color="#8e44ad", name="Espécies",
                    ))
                    fig_sp.update_layout(
                        title="Evolução das Espécies (Fitness Sharing)",
                        xaxis_title="Geração", yaxis_title="Espécies", height=300,
                    )
                    st.plotly_chart(fig_sp, width="stretch")

            st.markdown("""
            **Conceitos NEAT (PDF Aula 02):**
            - Evolui **topologia + pesos** simultaneamente — começa mínimo
            - `add_node`: divide conexão existente inserindo novo neurônio
            - `add_connection`: adiciona nova aresta entre nós existentes
            - **Especiação** protege inovações estruturais (fitness sharing)
            """)

    # Mostra último resultado se método/modelo coincide
    elif "last_optim_result" in st.session_state:
        lr = st.session_state["last_optim_result"]
        if lr.get("method_key") == optim_method and lr.get("model_type") == model_type:
            st.success(f"Último resultado — {lr['method']}:")
            m = lr["test_metrics"]
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Sensibilidade", f"{m['sensibilidade']:.4f}")
            with c2: st.metric("Especificidade", f"{m['especificidade']:.4f}")
            with c3: st.metric("F1-Score", f"{m['f1_score']:.4f}")
            with c4: st.metric("Fitness", f"{lr['fitness']:.4f}")
            if lr.get("best_params"):
                st.dataframe(
                    pd.DataFrame([(k, str(v)) for k, v in lr["best_params"].items()],
                                 columns=["Hiperparâmetro", "Valor"]),
                    width="stretch", hide_index=True,
                )
        else:
            st.info("Configure os parâmetros na barra lateral e clique em **Executar**.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — Comparação
# ─────────────────────────────────────────────────────────────────────────────
with tab_compare:
    st.title("Comparação de Resultados")
    data = get_data()
    baseline_metrics, _, _ = get_baseline_metrics(model_type)

    # ── Baseline vs último método executado ──────────────────────────────────
    if "last_optim_result" not in st.session_state:
        st.info("Execute um método de otimização na aba **Otimização** para ver a comparação.")
    else:
        lr = st.session_state["last_optim_result"]
        opt_metrics = lr["test_metrics"]

        st.subheader(f"Baseline vs {lr['method']} — {get_model_display_name(lr['model_type'])}")
        cols = st.columns(4)
        for i, k in enumerate(["sensibilidade", "especificidade", "f1_score", "acuracia"]):
            b, o = baseline_metrics.get(k, 0), opt_metrics.get(k, 0)
            with cols[i]:
                st.metric(k.replace("_", " ").title(), f"{o:.3f}", f"{o-b:+.3f}")

        st.subheader("Tabela Comparativa")
        st.dataframe(compare_models(baseline_metrics, opt_metrics),
                     width="stretch", hide_index=True)

        st.subheader("Comparação Visual (Radar)")
        cats = ["Sensibilidade", "Especificidade", "F1-Score", "Precisão", "Acurácia"]
        keys_r = ["sensibilidade", "especificidade", "f1_score", "precisao", "acuracia"]
        b_vals = [baseline_metrics.get(k, 0) for k in keys_r]
        o_vals = [opt_metrics.get(k, 0) for k in keys_r]
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=b_vals + [b_vals[0]], theta=cats + [cats[0]],
            name="Baseline", line_color="#7f8c8d",
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=o_vals + [o_vals[0]], theta=cats + [cats[0]],
            name=lr["method"].split("(")[0].strip(),
            line_color="#c0392b", fill="toself", fillcolor="rgba(192,57,43,0.1)",
        ))
        fig_radar.update_layout(polar=dict(radialaxis=dict(range=[0, 1])), height=400)
        st.plotly_chart(fig_radar, width="stretch")

        if lr.get("best_params"):
            st.subheader("Equidade por Grupo Etário")
            opt_model = build_model(lr["model_type"], lr["best_params"])
            opt_model.fit(data["X_train"], data["y_train"])
            opt_pred = opt_model.predict(data["X_test"])
            group_m = per_group_metrics(
                data["y_test"].values, opt_pred, np.asarray(data["age_test"])
            )
            rows_eq = [{"Grupo": g, "Sensibilidade": f"{m['sensibilidade']:.3f}",
                        "Especificidade": f"{m['especificidade']:.3f}",
                        "F1-Score": f"{m['f1_score']:.3f}"}
                       for g, m in group_m.items()]
            st.dataframe(pd.DataFrame(rows_eq), width="stretch", hide_index=True)

    st.divider()

    # ── Comparação de Todos os 5 Métodos ─────────────────────────────────────
    st.subheader("Comparar Todos os Métodos (PDFs Aulas 01 e 02)")
    st.markdown("""
    | # | Tipo | Método |
    |---|------|--------|
    | 1 | Força Bruta | Grid Search |
    | 2 | Estocástica | Random Search |
    | 3 | Combinatória | Algoritmo Genético |
    | 4 | Multi-Objetivo | NSGA-II |
    | 5 | Neuroevolução | NEAT |
    """)

    if run_all_btn:
        y_tr2 = data["y_train"].reset_index(drop=True)
        X_tr2, X_val2, y_tr2, y_val2, _, age_val2 = train_test_split(
            data["X_train"], y_tr2, np.asarray(data["age_train"]),
            test_size=0.2, random_state=42, stratify=y_tr2,
        )

        all_r: dict = {}

        bl_m = build_model(model_type)
        bl_m.fit(data["X_train"], data["y_train"])
        bl_p = bl_m.predict(data["X_test"])
        all_r["Baseline"] = {
            "test_metrics": get_detailed_metrics(data["y_test"].values, bl_p),
            "fitness": calculate_fitness(data["y_test"].values, bl_p),
        }

        with st.spinner("1/5 — Grid Search..."):
            gs2 = run_grid_search(model_type, data["X_train"], data["y_train"],
                                  data["X_test"], data["y_test"])
            all_r["Grid Search"] = gs2
        st.toast("Grid Search concluído")

        with st.spinner("2/5 — Random Search..."):
            rs2 = run_random_search(model_type, data["X_train"], data["y_train"],
                                    data["X_test"], data["y_test"], n_iter=50)
            all_r["Random Search"] = rs2
        st.toast("Random Search concluído")

        with st.spinner("3/5 — Algoritmo Genético..."):
            cfg2 = GAConfig(population_size=40, generations=20, mutation_rate=0.15, random_state=42)
            ga_r2 = run_genetic_algorithm(model_type, X_tr2, y_tr2, X_val2, y_val2,
                                          age_val=age_val2, config=cfg2)
            ga_m2 = build_model(model_type, ga_r2.best_chromosome.genes)
            ga_m2.fit(data["X_train"], data["y_train"])
            ga_p2 = ga_m2.predict(data["X_test"])
            all_r["Alg. Genético"] = {
                "test_metrics": get_detailed_metrics(data["y_test"].values, ga_p2),
                "fitness": calculate_fitness(data["y_test"].values, ga_p2),
            }
        st.toast("Algoritmo Genético concluído")

        with st.spinner("4/5 — NSGA-II..."):
            nsga2 = run_nsga2(model_type, X_tr2, y_tr2, X_val2, y_val2,
                              data["X_test"], data["y_test"],
                              population_size=40, generations=15, random_state=42)
            if nsga2.best_balanced:
                nsga_m2 = build_model(model_type, nsga2.best_balanced["params"])
                nsga_m2.fit(data["X_train"], data["y_train"])
                nsga_p2 = nsga_m2.predict(data["X_test"])
                all_r["NSGA-II"] = {
                    "test_metrics": get_detailed_metrics(data["y_test"].values, nsga_p2),
                    "fitness": calculate_fitness(data["y_test"].values, nsga_p2),
                    "pareto_size": len(nsga2.pareto_front),
                }
        st.toast("NSGA-II concluído")

        with st.spinner("5/5 — NEAT..."):
            neat_r2 = run_neat(
                data["X_train"].values, data["y_train"].values,
                data["X_test"].values, data["y_test"].values,
                population_size=30, generations=15, random_state=42,
            )
            all_r["NEAT"] = {
                "test_metrics": neat_r2.test_metrics,
                "fitness": neat_r2.best_genome_fitness,
                "nodes": neat_r2.best_n_nodes,
                "connections": neat_r2.best_n_connections,
            }
        st.toast("NEAT concluído")

        st.session_state["all_methods_results"] = all_r
        st.session_state["all_methods_nsga"] = nsga2

    if "all_methods_results" in st.session_state:
        all_r = st.session_state["all_methods_results"]

        st.subheader("Tabela — Todos os Métodos")
        table_rows = []
        for name, r in all_r.items():
            m = r["test_metrics"]
            table_rows.append({
                "Método": name,
                "Sensibilidade": f"{m['sensibilidade']:.4f}",
                "Especificidade": f"{m['especificidade']:.4f}",
                "F1-Score": f"{m['f1_score']:.4f}",
                "Acurácia": f"{m['acuracia']:.4f}",
                "Fitness": f"{r.get('fitness', 0):.4f}",
            })
        st.dataframe(pd.DataFrame(table_rows), width="stretch", hide_index=True)

        methods_names = [r["Método"] for r in table_rows]
        fig_bar = go.Figure()
        for metric, color in [("Sensibilidade", "#c0392b"), ("Especificidade", "#2980b9"),
                               ("F1-Score", "#27ae60")]:
            fig_bar.add_trace(go.Bar(
                name=metric, x=methods_names,
                y=[float(r[metric]) for r in table_rows],
                marker_color=color,
            ))
        fig_bar.update_layout(
            barmode="group", height=400,
            title="Métricas por Método de Otimização",
            xaxis_title="Método", yaxis_title="Score",
            yaxis=dict(range=[0, 1.05]),
        )
        st.plotly_chart(fig_bar, width="stretch")

        nsga_stored = st.session_state.get("all_methods_nsga")
        if nsga_stored and nsga_stored.pareto_front:
            st.subheader("Fronteira de Pareto — NSGA-II")
            sens_v2 = [p["val_sensitivity"] for p in nsga_stored.pareto_front]
            spec_v2 = [p["val_specificity"] for p in nsga_stored.pareto_front]
            fig_p2 = go.Figure()
            fig_p2.add_trace(go.Scatter(
                x=sens_v2, y=spec_v2, mode="markers+text",
                marker=dict(size=12, color="#9b59b6", symbol="diamond"),
                text=[f"P{i+1}" for i in range(len(sens_v2))],
                textposition="top center", name="Pareto",
            ))
            if "Baseline" in all_r:
                bm = all_r["Baseline"]["test_metrics"]
                fig_p2.add_trace(go.Scatter(
                    x=[bm["sensibilidade"]], y=[bm["especificidade"]],
                    mode="markers", marker=dict(size=14, color="#e74c3c", symbol="x"),
                    name="Baseline",
                ))
            fig_p2.update_layout(
                title="Fronteira de Pareto: Sensibilidade vs Especificidade",
                xaxis_title="Sensibilidade", yaxis_title="Especificidade",
                height=420, xaxis=dict(range=[0, 1.05]), yaxis=dict(range=[0, 1.05]),
            )
            st.plotly_chart(fig_p2, width="stretch")

        st.info(
            "**Conclusão:** Grid Search garante o ótimo dentro do grid (lento). "
            "Random Search explora mais espaço com menos avaliações. "
            "O AG equilibra qualidade e custo. "
            "O NSGA-II revela trade-offs entre sensibilidade e especificidade. "
            "O NEAT evolui a topologia da rede neural sem definir arquitetura a priori."
        )
    else:
        st.info("Clique em **⚡ Comparar Todos os Métodos** na barra lateral para executar a comparação completa.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — Interpretação LLM
# ─────────────────────────────────────────────────────────────────────────────
with tab_llm:
    st.title("Interpretação Clínica via ChatGPT")
    st.markdown("Selecione um paciente do conjunto de teste para gerar uma explicação clínica personalizada.")

    data = get_data()

    lr_llm = st.session_state.get("last_optim_result")
    if lr_llm and lr_llm.get("best_params"):
        mt_llm = lr_llm["model_type"]
        opt_model = build_model(mt_llm, lr_llm["best_params"])
        opt_model.fit(data["X_train"], data["y_train"])
        opt_metrics_llm = lr_llm["test_metrics"]
    else:
        mt_llm = model_type
        opt_model = build_model(mt_llm)
        opt_model.fit(data["X_train"], data["y_train"])
        opt_metrics_llm, _, _ = get_baseline_metrics(mt_llm)

    col1, col2 = st.columns([1, 2])
    with col1:
        patient_idx = st.slider("Índice da paciente (teste)", 0, len(data["X_test"]) - 1, 0)
        age_test_list = np.asarray(data["age_test"]).tolist()
        age_group = st.selectbox(
            "Grupo etário", ["jovem", "meia_idade", "senior"],
            index=["jovem", "meia_idade", "senior"].index(age_test_list[patient_idx]),
        )

        patient_features = data["X_test"].iloc[patient_idx]
        true_label = data["y_test"].iloc[patient_idx]
        patient_df = patient_features.to_frame().T
        pred_label = opt_model.predict(patient_df)[0]
        prob = (opt_model.predict_proba(patient_df)[0]
                if hasattr(opt_model, "predict_proba") else [0.5, 0.5])

        diagnosis_label = "MALIGNO" if pred_label == 1 else "BENIGNO"
        st.metric("Predição do modelo", diagnosis_label)
        st.metric("Rótulo real (referência)", "Maligno" if true_label == 1 else "Benigno")
        st.metric("Probabilidade de malignidade", f"{prob[1]:.1%}")

    with col2:
        top_features = sorted(
            zip(data["feature_names"], patient_features.values),
            key=lambda x: abs(x[1]), reverse=True,
        )[:5]
        st.subheader("Top 5 Features")
        st.dataframe(
            pd.DataFrame(top_features, columns=["Feature", "Valor (normalizado)"]),
            width="stretch", hide_index=True,
        )

    if st.button("Gerar Interpretação Clínica", type="primary"):
        with st.spinner("ChatGPT está analisando o diagnóstico..."):
            interpretation = generate_diagnosis_interpretation(
                age_group=age_group,
                diagnosis_label=diagnosis_label,
                prob_malignant=float(prob[1]),
                top_features=top_features,
                metrics=opt_metrics_llm,
            )
        st.markdown("---")
        st.markdown(interpretation)
        st.success("Resposta salva para base de dados Fase 3 (data/results/)")

    if st.button("Analisar Resultados dos Experimentos (LLM)"):
        lr2 = st.session_state.get("last_optim_result")
        if not lr2:
            st.warning("Execute um método de otimização primeiro.")
        else:
            baseline_m, _, _ = get_baseline_metrics(model_type)
            with st.spinner("Gerando análise clínica..."):
                analysis = generate_experiment_analysis(
                    model_type=get_model_display_name(model_type),
                    results_table=f"Método: {lr2['method']} | Fitness: {lr2['fitness']:.4f}",
                    best_params=lr2.get("best_params") or {},
                    baseline_metrics=baseline_m,
                    optimized_metrics=lr2["test_metrics"],
                )
            st.markdown("---")
            st.markdown(analysis)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 — Consulta em Linguagem Natural
# ─────────────────────────────────────────────────────────────────────────────
with tab_query:
    st.title("Consulta em Linguagem Natural")
    st.markdown("Faça perguntas sobre os diagnósticos e resultados do modelo.")

    data = get_data()
    baseline_metrics_q, _, _ = get_baseline_metrics(model_type)

    context = f"""
    Modelo: {get_model_display_name(model_type)}
    Dataset: Wisconsin Breast Cancer
    Sensibilidade: {baseline_metrics_q.get('sensibilidade', 0):.1%}
    Especificidade: {baseline_metrics_q.get('especificidade', 0):.1%}
    F1-Score: {baseline_metrics_q.get('f1_score', 0):.1%}
    Falsos negativos: {baseline_metrics_q.get('falsos_negativos', 0)}
    Falsos positivos: {baseline_metrics_q.get('falsos_positivos', 0)}
    """

    examples = [
        "Qual a taxa de falsos negativos do modelo atual?",
        "Por que a sensibilidade é mais importante que a especificidade nesse contexto?",
        "Como o modelo trata equidade entre diferentes grupos de pacientes?",
        "Quais são os riscos de um falso negativo no diagnóstico de câncer de mama?",
    ]

    st.subheader("Exemplos de perguntas:")
    for ex in examples:
        if st.button(ex, key=ex):
            st.session_state["query_input"] = ex

    query = st.text_input(
        "Sua pergunta:",
        value=st.session_state.get("query_input", ""),
        placeholder="Ex: Qual o impacto dos falsos negativos neste diagnóstico?",
    )

    if st.button("Enviar Consulta", type="primary") and query:
        with st.spinner("Processando consulta..."):
            answer = answer_natural_language_query(question=query, context=context)
        st.markdown("**Resposta:**")
        st.markdown(answer)
