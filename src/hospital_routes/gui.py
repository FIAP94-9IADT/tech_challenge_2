"""Interface Pygame para experimentar cenários e observar a convergência."""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

import pygame

from .genetic import GAConfig, GeneticOptimizer
from .io import load_problem, save_solution
from .models import Delivery, Depot, Problem, Solution, Vehicle


WIDTH, HEIGHT = 1280, 760
MAP_RECT = pygame.Rect(25, 105, 780, 610)
PANEL_RECT = pygame.Rect(830, 20, 425, 695)
BEST_GRAPH_RECT = pygame.Rect(850, 420, 385, 100)
MEAN_GRAPH_RECT = pygame.Rect(850, 550, 385, 100)
LAT_RANGE = (-13.06, -12.88)
LON_RANGE = (-38.58, -38.32)
COLORS = [(58, 134, 255), (54, 185, 118), (173, 105, 255), (255, 163, 72), (225, 85, 95)]


@dataclass
class InputField:
    label: str
    value: str
    rect: pygame.Rect
    kind: type = float
    active: bool = False

    def event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.value = self.value[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_TAB):
                self.active = False
            elif event.unicode and event.unicode in "0123456789.-":
                self.value += event.unicode

    def number(self):
        return self.kind(self.value)

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        screen.blit(font.render(self.label, True, (220, 226, 235)), (self.rect.x, self.rect.y - 20))
        pygame.draw.rect(screen, (48, 57, 72) if not self.active else (61, 78, 104), self.rect, border_radius=5)
        pygame.draw.rect(screen, (106, 124, 151), self.rect, 1, border_radius=5)
        screen.blit(font.render(self.value, True, (245, 247, 250)), (self.rect.x + 8, self.rect.y + 7))


class RouteApp:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Planejamento de Rotas Hospitalares")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("segoeui", 16)
        self.small = pygame.font.SysFont("segoeui", 13)
        self.title = pygame.font.SysFont("segoeui", 24, bold=True)
        self.problem = load_problem(Path("data/deliveries.json"))
        self.solution: Solution | None = None
        self.optimizer: GeneticOptimizer | None = None
        self.evolution = None
        self.running_optimization = False
        self.dragged: int | None = None
        self.drag_start = (0, 0)
        self.scenario_number = 0
        self.message = "Ajuste o cenário e selecione Otimizar."
        self.fields = self._fields()
        self.buttons = {
            "scenario": pygame.Rect(850, 350, 90, 40),
            "apply": pygame.Rect(948, 350, 90, 40),
            "optimize": pygame.Rect(1046, 350, 82, 40),
            "save": pygame.Rect(1136, 350, 82, 40),
        }
        self.instructions_rect = pygame.Rect(MAP_RECT.right - 100, 58, 100, 25)

    def _fields(self) -> dict[str, InputField]:
        specifications = [
            ("cities", "Entregas", "10", int), ("vehicles", "Veículos", "3", int),
            ("capacity", "Capacidade (kg)", "55", float), ("autonomy", "Autonomia (km)", "65", float),
            ("population", "População", "120", int), ("generations", "Gerações", "300", int),
            ("crossover", "Crossover", "0.90", float), ("mutation", "Mutação", "0.20", float),
            ("seed", "Semente", "42", int), ("elite", "Elitismo", "4", int),
        ]
        fields = {}
        for index, (key, label, value, kind) in enumerate(specifications):
            column, row = index % 3, index // 3
            rect = pygame.Rect(850 + column * 127, 75 + row * 75, 112, 36)
            fields[key] = InputField(label, value, rect, kind)
        return fields

    def _coordinate_to_screen(self, latitude: float, longitude: float) -> tuple[int, int]:
        x = MAP_RECT.left + (longitude - LON_RANGE[0]) / (LON_RANGE[1] - LON_RANGE[0]) * MAP_RECT.width
        y = MAP_RECT.bottom - (latitude - LAT_RANGE[0]) / (LAT_RANGE[1] - LAT_RANGE[0]) * MAP_RECT.height
        return round(x), round(y)

    def _screen_to_coordinate(self, position: tuple[int, int]) -> tuple[float, float]:
        x, y = position
        longitude = LON_RANGE[0] + (x - MAP_RECT.left) / MAP_RECT.width * (LON_RANGE[1] - LON_RANGE[0])
        latitude = LAT_RANGE[0] + (MAP_RECT.bottom - y) / MAP_RECT.height * (LAT_RANGE[1] - LAT_RANGE[0])
        return latitude, longitude

    def _config(self) -> GAConfig:
        population_size = max(10, self.fields["population"].number())
        elite_size = self.fields["elite"].number()
        if elite_size < 0 or elite_size >= population_size:
            raise ValueError("Elitismo deve estar entre zero e população menos um")
        return GAConfig(
            population_size=population_size,
            generations=max(1, self.fields["generations"].number()),
            crossover_rate=self.fields["crossover"].number(),
            mutation_rate=self.fields["mutation"].number(),
            elite_size=elite_size,
            tournament_size=min(4, population_size),
            stagnation_limit=max(20, self.fields["generations"].number() // 3),
            seed=self.fields["seed"].number(),
        )

    def generate_scenario(self, randomize: bool = True) -> None:
        if randomize:
            source = random.SystemRandom()
            self.scenario_number += 1
            randomized = {
                "cities": source.randint(6, 24),
                "vehicles": source.randint(2, 5),
                "capacity": source.randrange(35, 81, 5),
                "autonomy": source.randrange(50, 121, 5),
                "seed": source.randint(1, 999_999),
            }
            for key, value in randomized.items():
                self.fields[key].value = str(value)
        try:
            count = min(50, max(2, self.fields["cities"].number()))
            vehicle_count = min(8, max(1, self.fields["vehicles"].number()))
            capacity = self.fields["capacity"].number()
            autonomy = self.fields["autonomy"].number()
            if capacity <= 0 or autonomy <= 0:
                raise ValueError("Capacidade e autonomia devem ser positivas")
        except ValueError as exc:
            self.message = f"Valor inválido: {exc}"
            return
        rng = random.Random(self.fields["seed"].number())
        depot = Depot(
            "Hospital Central",
            rng.uniform(-13.005, -12.94),
            rng.uniform(-38.53, -38.45),
        )
        deliveries = tuple(
            Delivery(
                id=f"E{i + 1:02d}", name=f"Ponto {i + 1:02d}",
                latitude=rng.uniform(LAT_RANGE[0] + .01, LAT_RANGE[1] - .01),
                longitude=rng.uniform(LON_RANGE[0] + .01, LON_RANGE[1] - .01),
                demand_kg=round(rng.uniform(4, max(5, capacity * .35)), 1),
                priority=rng.randint(1, 3), service_minutes=10,
            ) for i in range(count)
        )
        vehicles = tuple(Vehicle(f"VEIC-{i + 1:02d}", capacity, autonomy) for i in range(vehicle_count))
        self.problem = Problem(depot, deliveries, vehicles)
        self.solution = None
        self.running_optimization = False
        mode = f"aleatório {self.scenario_number}" if randomize else "com os valores informados"
        self.message = f"Cenário {mode}: {count} entregas e {vehicle_count} veículos."

    def start_optimization(self) -> None:
        try:
            self.optimizer = GeneticOptimizer(self.problem, self._config())
        except ValueError as exc:
            self.message = f"Parâmetro inválido: {exc}"
            return
        self.evolution = self.optimizer.evolve()
        self.solution = None
        self.running_optimization = True
        self.message = "Otimização em andamento..."

    def step_optimization(self) -> None:
        if not self.running_optimization or self.evolution is None:
            return
        try:
            stat, self.solution = next(self.evolution)
            self.message = f"Geração {stat.generation} | melhor fitness {stat.best:.2f}"
        except StopIteration:
            self.running_optimization = False
            assert self.solution is not None
            status = "viável" if self.solution.feasible else "com violações"
            self.message = f"Concluído: {self.solution.total_distance_km:.2f} km | solução {status}."

    def save(self) -> None:
        if self.solution is None:
            self.message = "Execute a otimização antes de salvar."
            return
        output = Path("outputs")
        output.mkdir(exist_ok=True)
        save_solution(output / "interactive_solution.json", self.problem, self.solution)
        self.message = "Resultado salvo em outputs/interactive_solution.json."

    def _city_at(self, position: tuple[int, int]) -> int | None:
        for index, delivery in enumerate(self.problem.deliveries):
            if pygame.Vector2(self._coordinate_to_screen(delivery.latitude, delivery.longitude)).distance_to(position) <= 11:
                return index
        return None

    def _stop_for_editing(self) -> None:
        self.solution = None
        self.optimizer = None
        self.evolution = None
        self.running_optimization = False

    def add_delivery(self, position: tuple[int, int]) -> None:
        """Inclui uma entrega na coordenada indicada pelo usuário."""
        if not MAP_RECT.collidepoint(position):
            return
        depot_point = self._coordinate_to_screen(self.problem.depot.latitude, self.problem.depot.longitude)
        if pygame.Vector2(depot_point).distance_to(position) <= 14:
            self.message = "O hospital ocupa essa posição; escolha outro local."
            return
        used = {delivery.id for delivery in self.problem.deliveries}
        number = 1
        while f"E{number:02d}" in used:
            number += 1
        latitude, longitude = self._screen_to_coordinate(position)
        capacity = min(vehicle.capacity_kg for vehicle in self.problem.vehicles)
        delivery = Delivery(
            id=f"E{number:02d}",
            name=f"Ponto {number:02d}",
            latitude=latitude,
            longitude=longitude,
            demand_kg=round(max(1.0, capacity * 0.15), 1),
            priority=1,
            service_minutes=10,
        )
        self.problem = Problem(
            self.problem.depot,
            self.problem.deliveries + (delivery,),
            self.problem.vehicles,
        )
        self.fields["cities"].value = str(len(self.problem.deliveries))
        self._stop_for_editing()
        self.message = f"{delivery.id} incluído. Arraste para ajustar ou clique para mudar a prioridade."

    def remove_delivery(self, index: int) -> None:
        """Remove uma entrega, preservando ao menos um ponto no cenário."""
        if len(self.problem.deliveries) == 1:
            self.message = "O cenário deve manter pelo menos uma entrega."
            return
        removed = self.problem.deliveries[index]
        deliveries = tuple(item for i, item in enumerate(self.problem.deliveries) if i != index)
        self.problem = Problem(self.problem.depot, deliveries, self.problem.vehicles)
        self.fields["cities"].value = str(len(deliveries))
        self._stop_for_editing()
        self.message = f"{removed.id} removido do cenário."

    def event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.QUIT:
            return False
        for field in self.fields.values():
            field.event(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.dragged = self._city_at(event.pos)
            self.drag_start = event.pos
            if self.buttons["scenario"].collidepoint(event.pos): self.generate_scenario(randomize=True)
            elif self.buttons["apply"].collidepoint(event.pos): self.generate_scenario(randomize=False)
            elif self.buttons["optimize"].collidepoint(event.pos): self.start_optimization()
            elif self.buttons["save"].collidepoint(event.pos): self.save()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and MAP_RECT.collidepoint(event.pos):
            city = self._city_at(event.pos)
            if city is None:
                self.add_delivery(event.pos)
            else:
                self.remove_delivery(city)
        elif event.type == pygame.MOUSEMOTION and self.dragged is not None and MAP_RECT.collidepoint(event.pos):
            lat, lon = self._screen_to_coordinate(event.pos)
            items = list(self.problem.deliveries)
            old = items[self.dragged]
            items[self.dragged] = Delivery(old.id, old.name, lat, lon, old.demand_kg, old.priority, old.service_minutes)
            self.problem = Problem(self.problem.depot, tuple(items), self.problem.vehicles)
            self._stop_for_editing()
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragged is not None:
            if pygame.Vector2(event.pos).distance_to(self.drag_start) < 4:
                items = list(self.problem.deliveries)
                old = items[self.dragged]
                priority = old.priority % 3 + 1
                items[self.dragged] = Delivery(old.id, old.name, old.latitude, old.longitude, old.demand_kg, priority, old.service_minutes)
                self.problem = Problem(self.problem.depot, tuple(items), self.problem.vehicles)
                self._stop_for_editing()
            self.dragged = None
        return True

    def draw_map(self) -> None:
        pygame.draw.rect(self.screen, (236, 240, 244), MAP_RECT, border_radius=7)
        for step in range(1, 10):
            x = MAP_RECT.left + step * MAP_RECT.width // 10
            y = MAP_RECT.top + step * MAP_RECT.height // 10
            pygame.draw.line(self.screen, (215, 222, 229), (x, MAP_RECT.top), (x, MAP_RECT.bottom))
            pygame.draw.line(self.screen, (215, 222, 229), (MAP_RECT.left, y), (MAP_RECT.right, y))
        if self.solution:
            depot_point = self._coordinate_to_screen(self.problem.depot.latitude, self.problem.depot.longitude)
            for i, route in enumerate(self.solution.routes):
                points = [depot_point] + [self._coordinate_to_screen(self.problem.deliveries[j].latitude, self.problem.deliveries[j].longitude) for j in route] + [depot_point]
                if len(points) > 2:
                    pygame.draw.lines(self.screen, COLORS[i % len(COLORS)], False, points, 4)
        depot = self._coordinate_to_screen(self.problem.depot.latitude, self.problem.depot.longitude)
        pygame.draw.circle(self.screen, (205, 55, 65), depot, 12)
        self.screen.blit(self.small.render("H", True, (255, 255, 255)), (depot[0] - 5, depot[1] - 8))
        route_lookup = {gene: i for i, route in enumerate(self.solution.routes) for gene in route} if self.solution else {}
        for i, delivery in enumerate(self.problem.deliveries):
            point = self._coordinate_to_screen(delivery.latitude, delivery.longitude)
            color = COLORS[route_lookup[i] % len(COLORS)] if i in route_lookup else [(109, 154, 212), (242, 164, 65), (220, 72, 72)][delivery.priority - 1]
            pygame.draw.circle(self.screen, color, point, 10)
            label = self.small.render(str(i + 1), True, (255, 255, 255))
            self.screen.blit(label, label.get_rect(center=point))

        legend = pygame.Rect(MAP_RECT.left + 12, MAP_RECT.top + 12, 178, 104)
        pygame.draw.rect(self.screen, (250, 251, 253), legend, border_radius=6)
        pygame.draw.rect(self.screen, (181, 191, 203), legend, 1, border_radius=6)
        self.screen.blit(self.small.render("Prioridade", True, (45, 54, 66)), (legend.x + 10, legend.y + 7))
        priority_colors = [(109, 154, 212), (242, 164, 65), (220, 72, 72)]
        priority_labels = ["1 — Regular", "2 — Alta", "3 — Crítica"]
        for index, (color, text) in enumerate(zip(priority_colors, priority_labels)):
            y = legend.y + 34 + index * 21
            pygame.draw.circle(self.screen, color, (legend.x + 17, y + 6), 6)
            self.screen.blit(self.small.render(text, True, (55, 65, 78)), (legend.x + 30, y - 2))

        if self.solution:
            note = self.small.render("Cores da rota = veículo", True, (75, 86, 101))
            self.screen.blit(note, (MAP_RECT.right - note.get_width() - 12, MAP_RECT.top + 12))
        self._draw_coordinate_tooltip()

    def _draw_coordinate_tooltip(self) -> None:
        """Exibe coordenadas e atributos do ponto sob o cursor."""
        mouse = pygame.mouse.get_pos()
        depot_point = self._coordinate_to_screen(self.problem.depot.latitude, self.problem.depot.longitude)
        lines: list[str] | None = None
        if pygame.Vector2(depot_point).distance_to(mouse) <= 13:
            lines = [
                self.problem.depot.name,
                f"Latitude: {self.problem.depot.latitude:.6f}",
                f"Longitude: {self.problem.depot.longitude:.6f}",
            ]
        else:
            index = self._city_at(mouse)
            if index is not None:
                delivery = self.problem.deliveries[index]
                lines = [
                    f"{delivery.id} — {delivery.name}",
                    f"Latitude: {delivery.latitude:.6f}",
                    f"Longitude: {delivery.longitude:.6f}",
                    f"Prioridade: {delivery.priority} | Carga: {delivery.demand_kg:.1f} kg",
                ]
        if lines is None:
            return
        width = max(self.small.size(line)[0] for line in lines) + 20
        height = len(lines) * 20 + 12
        x = min(mouse[0] + 14, MAP_RECT.right - width - 6)
        y = min(mouse[1] + 14, MAP_RECT.bottom - height - 6)
        tooltip = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, (20, 27, 36), tooltip, border_radius=5)
        pygame.draw.rect(self.screen, (105, 122, 145), tooltip, 1, border_radius=5)
        for index, line in enumerate(lines):
            self.screen.blit(self.small.render(line, True, (240, 244, 249)), (x + 10, y + 7 + index * 20))

    def _draw_instructions_tooltip(self) -> None:
        hovered = self.instructions_rect.collidepoint(pygame.mouse.get_pos())
        label_color = (105, 190, 255) if hovered else (165, 177, 194)
        label = self.small.render("Instruções", True, label_color)
        label_rect = label.get_rect(midleft=self.instructions_rect.midleft)
        self.screen.blit(label, label_rect)
        icon_center = (label_rect.right + 13, self.instructions_rect.centery)
        pygame.draw.circle(self.screen, label_color, icon_center, 8, 1)
        icon = self.small.render("i", True, label_color)
        self.screen.blit(icon, icon.get_rect(center=(icon_center[0], icon_center[1] - 1)))
        if not hovered:
            return
        sections = [
            ("EDIÇÃO DO MAPA", [
                "Botão direito em área vazia: incluir uma entrega",
                "Botão direito em uma entrega: remover a entrega",
                "Arrastar uma entrega: alterar sua posição",
                "Clique curto: alternar prioridade entre 1, 2 e 3",
                "Manter o cursor: consultar coordenadas e dados",
            ]),
            ("CENÁRIO", [
                "Novo cenário: sortear dados e posições",
                "Aplicar dados: usar os valores informados nos campos",
            ]),
            ("EXECUÇÃO", [
                "Otimizar: executar gerações e atualizar gráficos",
                "Salvar: gravar a solução interativa em outputs",
            ]),
        ]
        all_lines = [line for _, lines in sections for line in lines]
        width = max(self.small.size(line)[0] for line in all_lines) + 32
        height = sum(26 + len(lines) * 21 for _, lines in sections) + 14
        tooltip = pygame.Rect(MAP_RECT.right - width, MAP_RECT.top + 8, width, height)
        pygame.draw.rect(self.screen, (20, 27, 36), tooltip, border_radius=7)
        pygame.draw.rect(self.screen, (105, 122, 145), tooltip, 1, border_radius=7)
        y = tooltip.y + 10
        for heading, lines in sections:
            self.screen.blit(self.small.render(heading, True, (105, 190, 255)), (tooltip.x + 14, y))
            y += 23
            for line in lines:
                pygame.draw.circle(self.screen, (112, 132, 161), (tooltip.x + 18, y + 7), 3)
                self.screen.blit(self.small.render(line, True, (232, 237, 244)), (tooltip.x + 28, y))
                y += 21
            y += 3

    def draw_graph(self) -> None:
        self.screen.blit(self.font.render("Convergência em tempo real", True, (230, 235, 242)), (BEST_GRAPH_RECT.x, BEST_GRAPH_RECT.y - 28))
        self._draw_series_graph(BEST_GRAPH_RECT, "best", "Melhor fitness", (60, 205, 139))
        self._draw_series_graph(MEAN_GRAPH_RECT, "mean", "Fitness médio", (112, 132, 161))

    def _draw_series_graph(
        self,
        rect: pygame.Rect,
        attribute: str,
        label: str,
        color: tuple[int, int, int],
    ) -> None:
        """Desenha uma série em escala própria para preservar sua variação."""
        pygame.draw.rect(self.screen, (32, 40, 52), rect, border_radius=6)
        self.screen.blit(self.small.render(label, True, color), (rect.x + 8, rect.y + 6))
        if not self.optimizer or len(self.optimizer.history) < 2:
            message = self.small.render("Aguardando gerações...", True, (150, 164, 183))
            self.screen.blit(message, message.get_rect(center=rect.center))
            return
        history = self.optimizer.history
        values = [getattr(item, attribute) for item in history]
        low, high = min(values), max(values)
        padding = max(1e-9, (high - low) * 0.08)
        low, high = low - padding, high + padding
        span = high - low
        points = [
            (
                rect.x + 8 + i * (rect.width - 16) / max(1, len(history) - 1),
                rect.bottom - 8 - (value - low) / span * (rect.height - 30),
            )
            for i, value in enumerate(values)
        ]
        pygame.draw.lines(self.screen, color, False, points, 2)
        current = self.small.render(f"{values[-1]:.2f}", True, color)
        self.screen.blit(current, (rect.right - current.get_width() - 8, rect.y + 6))

    def draw(self) -> None:
        self.screen.fill((21, 27, 36))
        self.screen.blit(self.title.render("Rotas e pontos de entrega", True, (240, 244, 249)), (25, 28))
        self.screen.blit(self.small.render("Configure o cenário e acompanhe a evolução das rotas.", True, (165, 177, 194)), (25, 62))
        pygame.draw.rect(self.screen, (27, 34, 45), PANEL_RECT, border_radius=9)
        self.screen.blit(self.title.render("Parâmetros", True, (240, 244, 249)), (850, 30))
        self.draw_map()
        self._draw_instructions_tooltip()
        for field in self.fields.values(): field.draw(self.screen, self.small)
        for key, text in (("scenario", "Novo cenário"), ("apply", "Aplicar dados"), ("optimize", "Otimizar"), ("save", "Salvar")):
            color = (41, 142, 98) if key == "optimize" else (55, 74, 102)
            pygame.draw.rect(self.screen, color, self.buttons[key], border_radius=6)
            label = self.small.render(text, True, (255, 255, 255))
            self.screen.blit(label, label.get_rect(center=self.buttons[key].center))
        self.draw_graph()
        self.screen.blit(self.small.render(self.message[:65], True, (215, 222, 232)), (850, 675))
        pygame.display.flip()

    def run(self) -> None:
        active = True
        while active:
            for event in pygame.event.get(): active = self.event(event) and active
            # Uma geração por quadro mantém eventos, mapa e gráfico responsivos.
            self.step_optimization()
            self.draw()
            self.clock.tick(60)
        pygame.quit()


def main() -> None:
    RouteApp().run()


if __name__ == "__main__":
    main()
