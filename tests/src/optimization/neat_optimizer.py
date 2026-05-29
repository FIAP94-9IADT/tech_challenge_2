"""
Otimização via NEAT (NeuroEvolution of Augmenting Topologies).
Implementa o conceito do PDF Aula 2 — evolui a TOPOLOGIA da rede neural,
não apenas os pesos. Começa com conexões mínimas e adiciona neurônios/
conexões ao longo das gerações via mutações estruturais.

Conceitos do PDF implementados:
- Crossover estrutural (alinha genes por número de inovação)
- Mutação add_connection (adiciona nova conexão)
- Mutação add_node (divide conexão existente em dois)
- Fitness sharing via especiação (evita convergência prematura)
- Innovation tracking (cada gene tem número único de inovação)
"""

import os
import io
import textwrap
import tempfile
from dataclasses import dataclass, field

import neat
import numpy as np

from src.genetic.fitness import sensitivity, specificity, get_detailed_metrics


# ── Config ────────────────────────────────────────────────────────────────────

def _build_neat_config_text(n_inputs: int, population_size: int) -> str:
    """Gera o texto de configuração do neat-python para classificação binária."""
    return textwrap.dedent(f"""\
        [NEAT]
        fitness_criterion        = max
        fitness_threshold        = 0.95
        no_fitness_termination   = False
        pop_size                 = {population_size}
        reset_on_extinction      = True

        [DefaultGenome]
        # Tipo de neurônio
        activation_default      = sigmoid
        activation_mutate_rate  = 0.05
        activation_options      = sigmoid tanh relu

        # Agregação
        aggregation_default     = sum
        aggregation_mutate_rate = 0.0
        aggregation_options     = sum

        # Viés
        bias_init_mean          = 0.0
        bias_init_stdev         = 1.0
        bias_max_value          = 30.0
        bias_min_value          = -30.0
        bias_mutate_power       = 0.5
        bias_mutate_rate        = 0.7
        bias_replace_rate       = 0.1

        # Resposta do neurônio (escala de saída da ativação)
        response_init_mean      = 1.0
        response_init_stdev     = 0.0
        response_max_value      = 30.0
        response_min_value      = -30.0
        response_mutate_power   = 0.0
        response_mutate_rate    = 0.0
        response_replace_rate   = 0.0

        # Compatibilidade (especiação)
        compatibility_disjoint_coefficient = 1.0
        compatibility_weight_coefficient   = 0.5

        # Conexões
        conn_add_prob           = 0.5
        conn_delete_prob        = 0.2
        enabled_default         = True
        enabled_mutate_rate     = 0.01

        # Topologia: começa mínimo, cresce por mutação
        feed_forward            = True
        initial_connection      = full_direct

        # Nós
        node_add_prob           = 0.3
        node_delete_prob        = 0.1
        num_hidden              = 0
        num_inputs              = {n_inputs}
        num_outputs             = 1

        # Pesos
        weight_init_mean        = 0.0
        weight_init_stdev       = 1.0
        weight_max_value        = 30.0
        weight_min_value        = -30.0
        weight_mutate_power     = 0.5
        weight_mutate_rate      = 0.8
        weight_replace_rate     = 0.1

        [DefaultSpeciesSet]
        compatibility_threshold = 3.0

        [DefaultStagnation]
        species_fitness_func = max
        max_stagnation       = 10
        species_elitism      = 2

        [DefaultReproduction]
        elitism            = 2
        survival_threshold = 0.2
    """)


def _load_neat_config(n_inputs: int, population_size: int) -> neat.Config:
    """Cria um objeto neat.Config a partir do texto gerado em memória."""
    config_text = _build_neat_config_text(n_inputs, population_size)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
        f.write(config_text)
        config_path = f.name
    try:
        config = neat.Config(
            neat.DefaultGenome,
            neat.DefaultReproduction,
            neat.DefaultSpeciesSet,
            neat.DefaultStagnation,
            config_path,
        )
    finally:
        os.unlink(config_path)
    return config


# ── Rede neural → predição ────────────────────────────────────────────────────

def _predict_with_net(net: neat.nn.FeedForwardNetwork, X: np.ndarray) -> np.ndarray:
    """Executa a rede NEAT em cada amostra e retorna labels binárias (threshold 0.5)."""
    preds = np.array([net.activate(row)[0] for row in X])
    return (preds >= 0.5).astype(int)


# ── Resultado ─────────────────────────────────────────────────────────────────

@dataclass
class NEATResult:
    best_genome_fitness: float
    test_metrics: dict
    generations_run: int
    n_species_final: int
    best_n_nodes: int
    best_n_connections: int
    fitness_per_generation: list[float] = field(default_factory=list)
    species_per_generation: list[int] = field(default_factory=list)


# ── Runner principal ──────────────────────────────────────────────────────────

def run_neat(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    population_size: int = 50,
    generations: int = 30,
    random_state: int = 42,
) -> NEATResult:
    """
    Executa NEAT para classificação binária (diagnóstico de câncer).

    A rede evolui sua própria topologia — começa sem neurônios ocultos
    e adiciona nós/conexões ao longo das gerações por mutação estrutural.
    O fitness usa sensibilidade + especificidade ponderados, alinhado ao
    objetivo médico do projeto.
    """
    np.random.seed(random_state)

    X_tr = np.asarray(X_train)
    y_tr = np.asarray(y_train)
    X_te = np.asarray(X_test)
    y_te = np.asarray(y_test)

    n_inputs = X_tr.shape[1]
    config = _load_neat_config(n_inputs, population_size)

    fitness_history: list[float] = []
    species_history: list[int] = []

    def eval_genomes(genomes, cfg):
        for _, genome in genomes:
            net = neat.nn.FeedForwardNetwork.create(genome, cfg)
            y_pred = _predict_with_net(net, X_tr)
            s = sensitivity(y_tr, y_pred)
            sp = specificity(y_tr, y_pred)
            # Fitness médico: prioriza sensibilidade (não perder diagnósticos)
            genome.fitness = 0.6 * s + 0.4 * sp

    population = neat.Population(config)

    # Estatísticas a cada geração
    class _GenStats(neat.reporting.BaseReporter):
        def post_evaluate(self, cfg, pop, species_set, best_genome):
            fitness_history.append(best_genome.fitness)
            species_history.append(len(species_set.species))

    population.add_reporter(_GenStats())

    winner = population.run(eval_genomes, generations)

    # Avalia vencedor no conjunto de teste
    best_net = neat.nn.FeedForwardNetwork.create(winner, config)
    y_pred_test = _predict_with_net(best_net, X_te)
    metrics = get_detailed_metrics(y_te, y_pred_test)

    n_nodes = len(winner.nodes)
    n_connections = sum(1 for cg in winner.connections.values() if cg.enabled)

    return NEATResult(
        best_genome_fitness=winner.fitness,
        test_metrics=metrics,
        generations_run=len(fitness_history),
        n_species_final=len(population.species.species),
        best_n_nodes=n_nodes,
        best_n_connections=n_connections,
        fitness_per_generation=fitness_history,
        species_per_generation=species_history,
    )
