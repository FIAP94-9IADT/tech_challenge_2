"""
Executa 3 experimentos com diferentes configurações do algoritmo genético
e salva os resultados para análise comparativa.
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.loader import load_dataset
from src.genetic.algorithm import GAConfig, run_genetic_algorithm
from src.genetic.fitness import get_detailed_metrics
from src.models.classifier import build_model, get_model_display_name
from src.llm.interpreter import generate_experiment_analysis
from src.utils.metrics import compare_models

EXPERIMENTS = [
    {
        "name": "Experimento 1 — Exploração Ampla",
        "description": "População grande, mutação alta: favorece exploração do espaço de busca",
        "config": GAConfig(population_size=30, generations=20, mutation_rate=0.10, crossover_rate=0.85, random_state=42),
    },
    {
        "name": "Experimento 2 — Equilíbrio",
        "description": "Configuração balanceada entre exploração e explotação",
        "config": GAConfig(population_size=60, generations=30, mutation_rate=0.20, crossover_rate=0.75, random_state=42),
    },
    {
        "name": "Experimento 3 — Convergência Refinada",
        "description": "População grande, mutação moderada: maior pressão seletiva",
        "config": GAConfig(population_size=100, generations=50, mutation_rate=0.15, crossover_rate=0.80, random_state=42),
    },
]

MODEL_TYPE = "random_forest"


def run_all_experiments():
    print("=" * 60)
    print("TECH CHALLENGE FASE 2 — Otimização via Algoritmos Genéticos")
    print("Dataset: Wisconsin Breast Cancer")
    print("=" * 60)

    data = load_dataset(random_state=42)
    X_train, X_val, y_train, y_val, age_train, age_val = train_test_split(
        data["X_train"], data["y_train"], data["age_train"],
        test_size=0.2, random_state=42, stratify=data["y_train"]
    )
    X_test = data["X_test"]
    y_test = data["y_test"]
    age_test = data["age_test"]

    # Baseline (sem otimização)
    baseline_model = build_model(MODEL_TYPE)
    baseline_model.fit(data["X_train"], data["y_train"])
    baseline_pred = baseline_model.predict(X_test)
    baseline_metrics = get_detailed_metrics(y_test.values, baseline_pred)

    print(f"\nBaseline {get_model_display_name(MODEL_TYPE)} (sem otimização):")
    for k, v in baseline_metrics.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.4f}")

    all_results = []

    for exp in EXPERIMENTS:
        print(f"\n{'─' * 60}")
        print(f"{exp['name']}")
        print(f"Descrição: {exp['description']}")
        cfg = exp["config"]
        print(f"Config: pop={cfg.population_size}, gen={cfg.generations}, mut={cfg.mutation_rate}, cross={cfg.crossover_rate}")

        start = time.time()

        def progress(gen, total, best):
            if gen % 5 == 0 or gen == total:
                print(f"  Gen {gen:3d}/{total} | Melhor fitness: {best:.4f}")

        ga_result = run_genetic_algorithm(
            model_type=MODEL_TYPE,
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
            age_val=age_val,
            config=exp["config"],
            progress_callback=progress,
        )

        elapsed = time.time() - start

        # Avalia no conjunto de teste
        best_model = build_model(MODEL_TYPE, ga_result.best_chromosome.genes)
        best_model.fit(data["X_train"], data["y_train"])
        best_pred = best_model.predict(X_test)
        test_metrics = get_detailed_metrics(y_test.values, best_pred)

        print(f"\nResultados no teste (tempo: {elapsed:.1f}s):")
        for k, v in test_metrics.items():
            if isinstance(v, float):
                delta = v - baseline_metrics.get(k, 0)
                print(f"  {k}: {v:.4f}  ({delta:+.4f} vs baseline)")

        print(f"\nMelhores hiperparâmetros: {ga_result.best_chromosome.genes}")

        all_results.append({
            "experiment": exp["name"],
            "config": {
                "population_size": cfg.population_size,
                "generations": cfg.generations,
                "mutation_rate": cfg.mutation_rate,
                "crossover_rate": cfg.crossover_rate,
            },
            "best_params": ga_result.best_chromosome.genes,
            "best_fitness": ga_result.best_chromosome.fitness,
            "test_metrics": test_metrics,
            "baseline_metrics": baseline_metrics,
            "convergence": {
                "best": ga_result.best_fitness_per_gen,
                "avg": ga_result.avg_fitness_per_gen,
            },
            "elapsed_seconds": elapsed,
        })

    # Salva resultados
    out_path = Path(__file__).parent.parent / "data" / "results" / "experiments_summary.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\nResultados salvos em: {out_path}")

    # Melhor experimento geral
    best_exp = max(all_results, key=lambda r: r["test_metrics"]["sensibilidade"])
    print(f"\nMelhor experimento por sensibilidade: {best_exp['experiment']}")

    # Gera análise LLM
    print("\nGerando análise clínica via LLM...")
    results_table = "\n".join(
        f"- {r['experiment']}: sens={r['test_metrics']['sensibilidade']:.4f}, "
        f"spec={r['test_metrics']['especificidade']:.4f}, f1={r['test_metrics']['f1_score']:.4f}"
        for r in all_results
    )
    analysis = generate_experiment_analysis(
        model_type=get_model_display_name(MODEL_TYPE),
        results_table=results_table,
        best_params=best_exp["best_params"],
        baseline_metrics=baseline_metrics,
        optimized_metrics=best_exp["test_metrics"],
    )
    print("\n" + "=" * 60)
    print("ANÁLISE CLÍNICA (LLM):")
    print("=" * 60)
    print(analysis)

    return all_results


if __name__ == "__main__":
    run_all_experiments()
