import { ClipboardList, FileText, Sparkles } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { getInstructions, getReport } from "../services/api";
import Modal from "./Modal";

const ROUTE_COLORS = ["#2b6cb0", "#c05621", "#2f855a", "#6b46c1", "#b83280", "#975a16"];

export default function RoutePanel({ data }) {
  const [modal, setModal] = useState(null); // { title, text, fromCache }
  const [loadingKey, setLoadingKey] = useState(null);
  const [error, setError] = useState(null);

  // cache dos resultados do LLM para a otimização ATUAL; uma nova
  // otimização (novo objeto `data`) limpa tudo, então clicar no mesmo
  // botão duas vezes nunca chama o LLM de novo para as mesmas rotas
  const cacheRef = useRef({});
  useEffect(() => {
    cacheRef.current = {};
  }, [data]);

  if (!data) {
    return (
      <div className="card">
        <div className="card-header">
          <h2><ClipboardList size={16} /> Resultado</h2>
        </div>
        <div className="empty-state">Nenhuma otimização executada ainda.</div>
      </div>
    );
  }

  const { scenario, result, comparison } = data;
  const solution = result.best_solution;
  const vehiclesById = Object.fromEntries(scenario.vehicles.map((v) => [v.id, v]));

  const callLlm = async (cacheKey, title, fetcher) => {
    setError(null);

    const cached = cacheRef.current[cacheKey];
    if (cached) {
      setModal({ title, text: cached, fromCache: true });
      return;
    }

    setLoadingKey(cacheKey);
    try {
      const response = await fetcher();
      const text = response.instructions || response.report;
      cacheRef.current[cacheKey] = text;
      setModal({ title, text, fromCache: false });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingKey(null);
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2><ClipboardList size={16} /> Resultado</h2>
        {solution.feasible ? (
          <span className="badge badge-success">Viável</span>
        ) : (
          <span className="badge badge-danger">Inviável</span>
        )}
      </div>

      <div className="summary-list">
        {comparison && (
          <span className="savings">
            Economia vs Nearest Neighbor: {comparison.economia_km} km ({comparison.economia_pct}%)
          </span>
        )}
        {solution.unassigned.length > 0 && (
          <span className="error">{solution.unassigned.length} entregas não alocadas</span>
        )}
      </div>

      {solution.routes.map((route, i) => {
        const vehicle = vehiclesById[route.vehicle_id];
        const key = `instructions:${route.vehicle_id}`;
        return (
          <div className="vehicle-card" key={route.vehicle_id}>
            <div className="vehicle-header">
              <span className="dot" style={{ background: ROUTE_COLORS[i % ROUTE_COLORS.length] }} />
              <b>{vehicle.name}</b>
              <span className="badge badge-neutral">{route.stops.length} paradas</span>
            </div>
            <div className="vehicle-stats">
              {route.distance_km.toFixed(1)} km / {vehicle.max_range_km} km ·{" "}
              {route.load_kg.toFixed(1)} kg / {vehicle.capacity_kg} kg
            </div>
            <button
              className="btn btn-secondary btn-sm"
              disabled={loadingKey !== null || !route.stops.length}
              onClick={() =>
                callLlm(key, `Instruções de entrega: ${vehicle.name}`, () =>
                  getInstructions(route.vehicle_id)
                )
              }
            >
              <Sparkles size={14} />
              {loadingKey === key ? "Gerando..." : "Gerar instruções"}
            </button>
          </div>
        );
      })}

      <div className="llm-actions">
        <button
          className="btn btn-primary btn-sm"
          disabled={loadingKey !== null}
          onClick={() =>
            callLlm("report:diário", "Relatório diário", () => getReport("diário"))
          }
        >
          <FileText size={14} />
          {loadingKey === "report:diário" ? "Gerando..." : "Relatório diário"}
        </button>
        <button
          className="btn btn-primary btn-sm"
          disabled={loadingKey !== null}
          onClick={() =>
            callLlm("report:semanal", "Relatório semanal", () => getReport("semanal"))
          }
        >
          <FileText size={14} />
          {loadingKey === "report:semanal" ? "Gerando..." : "Relatório semanal"}
        </button>
      </div>

      {error && <div className="alert alert-error" style={{ marginTop: 10 }}>{error}</div>}

      {modal && (
        <Modal
          title={modal.title}
          onClose={() => setModal(null)}
          footer={
            <>
              {modal.fromCache && (
                <span className="cache-hint">
                  <Sparkles size={12} /> resultado em cache desta otimização
                </span>
              )}
              <button className="btn btn-secondary" onClick={() => setModal(null)}>
                Fechar
              </button>
            </>
          }
        >
          <ReactMarkdown>{modal.text}</ReactMarkdown>
        </Modal>
      )}
    </div>
  );
}
