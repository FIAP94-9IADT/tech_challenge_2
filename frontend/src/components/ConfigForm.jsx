import { Play } from "lucide-react";
import { useState } from "react";

const DEFAULTS = {
  n_points: 20,
  n_vehicles: 3,
  seed: 42,
  population_size: 150,
  generations: 400,
  mutation_probability: 0.3,
  selection: "tournament",
};

export default function ConfigForm({ onSubmit, loading }) {
  const [form, setForm] = useState(DEFAULTS);

  const update = (key, value) => setForm((f) => ({ ...f, [key]: value }));

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      ...form,
      n_points: Number(form.n_points),
      n_vehicles: Number(form.n_vehicles),
      seed: Number(form.seed),
      population_size: Number(form.population_size),
      generations: Number(form.generations),
      mutation_probability: Number(form.mutation_probability),
    });
  };

  return (
    <form className="sidebar-form" onSubmit={handleSubmit}>
      <div className="nav-section-label">Cenário</div>
      <div className="sidebar-section">
        <div className="form-row">
          <div className="form-group">
            <label className="form-label">Entregas</label>
            <input className="form-control" type="number" min="3" max="100"
              value={form.n_points} onChange={(e) => update("n_points", e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Veículos</label>
            <input className="form-control" type="number" min="1" max="10"
              value={form.n_vehicles} onChange={(e) => update("n_vehicles", e.target.value)} />
          </div>
        </div>
        <div className="form-group">
          <label className="form-label">Seed</label>
          <input className="form-control" type="number" min="0"
            value={form.seed} onChange={(e) => update("seed", e.target.value)} />
        </div>
      </div>

      <div className="nav-section-label">Algoritmo Genético</div>
      <div className="sidebar-section">
        <div className="form-row">
          <div className="form-group">
            <label className="form-label">População</label>
            <input className="form-control" type="number" min="10" max="1000"
              value={form.population_size} onChange={(e) => update("population_size", e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Gerações</label>
            <input className="form-control" type="number" min="10" max="5000"
              value={form.generations} onChange={(e) => update("generations", e.target.value)} />
          </div>
        </div>
        <div className="form-row">
          <div className="form-group">
            <label className="form-label">Mutação</label>
            <input className="form-control" type="number" min="0" max="1" step="0.05"
              value={form.mutation_probability}
              onChange={(e) => update("mutation_probability", e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Seleção</label>
            <select className="form-control" value={form.selection}
              onChange={(e) => update("selection", e.target.value)}>
              <option value="tournament">Torneio</option>
              <option value="roulette">Roleta</option>
            </select>
          </div>
        </div>
      </div>

      <div className="sidebar-footer">
        <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
          <Play size={15} />
          {loading ? "Otimizando..." : "Otimizar rotas"}
        </button>
      </div>
    </form>
  );
}
