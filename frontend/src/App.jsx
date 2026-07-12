import { Moon, Route, Sun, Truck, MapPin, TrendingDown, Timer } from "lucide-react";
import { useEffect, useState } from "react";
import ChatBox from "./components/ChatBox";
import ConfigForm from "./components/ConfigForm";
import FitnessChart from "./components/FitnessChart";
import MapView from "./components/MapView";
import RoutePanel from "./components/RoutePanel";
import { optimize } from "./services/api";
import "./App.css";

export default function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "dark");

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  const handleOptimize = async (params) => {
    setLoading(true);
    setError(null);
    try {
      const response = await optimize(params);
      setData(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const solution = data?.result?.best_solution;

  return (
    <div className="layout">
      <nav className="top-navbar">
        <div className="navbar-left">
          <div className="navbar-brand">
            <div className="brand-icon">
              <Route size={20} />
            </div>
            <div>
              <strong>Rotas Médicas</strong>
              <span>Tech Challenge Fase 2 · FIAP/POSTECH - GRUPO 4</span>
            </div>
          </div>
        </div>
        <div className="navbar-actions">
          <button
            className="theme-toggle"
            onClick={() => setTheme(theme === "light" ? "dark" : "light")}
            aria-label="Alternar tema"
          >
            {theme === "light" ? <Moon size={18} /> : <Sun size={18} />}
          </button>
        </div>
      </nav>

      <aside className="sidebar">
        <ConfigForm onSubmit={handleOptimize} loading={loading} />
        {error && <div className="alert alert-error sidebar-alert">{error}</div>}
      </aside>

      <main className="page">
        <div className="main-grid">
          <div className="center-col">
            <section className="map-section">
              <MapView scenario={data?.scenario} solution={solution} />
            </section>
          </div>

          <aside className="right-panel">
            {solution && (
              <div className="stats-grid stats-compact">
                <div className="stat-card stat-card--blue">
                  <div className="stat-top">
                    <span className="stat-icon"><MapPin size={14} /></span>
                    <span className="stat-value">{solution.total_distance_km.toFixed(1)} km</span>
                  </div>
                  <div className="stat-label">Distância total</div>
                </div>
                <div className="stat-card stat-card--indigo">
                  <div className="stat-top">
                    <span className="stat-icon"><Truck size={14} /></span>
                    <span className="stat-value">
                      {solution.routes.filter((r) => r.stops.length).length}
                    </span>
                  </div>
                  <div className="stat-label">Veículos em rota</div>
                </div>
                <div className="stat-card stat-card--green">
                  <div className="stat-top">
                    <span className="stat-icon"><TrendingDown size={14} /></span>
                    <span className="stat-value">
                      {data.comparison ? `${data.comparison.economia_pct}%` : "-"}
                    </span>
                  </div>
                  <div className="stat-label">Economia vs NN</div>
                </div>
                <div className="stat-card stat-card--amber">
                  <div className="stat-top">
                    <span className="stat-icon"><Timer size={14} /></span>
                    <span className="stat-value">{data.elapsed_s}s</span>
                  </div>
                  <div className="stat-label">{data.result.generations_run} gerações</div>
                </div>
              </div>
            )}
            <RoutePanel data={data} />
            <FitnessChart history={data?.result?.history} />
            <div className="card participants-card">
              <div className="card-header">
                <h2>Integrantes</h2>
              </div>
              <ul className="participants-list">
                <li>Lucas Bastos Garcia</li>
                <li>Guilherme Diniz Raposo Pimentel</li>
                <li>Felipe Diniz Sampaio</li>
                <li>Luan Francisco Amâncio da Silva</li>
                <li>Vinicius Santos Nogueira de Sousa</li>
              </ul>
            </div>
          </aside>
        </div>
      </main>

      <ChatBox enabled={Boolean(data)} optimizationKey={data?.elapsed_s ?? null} />
    </div>
  );
}
