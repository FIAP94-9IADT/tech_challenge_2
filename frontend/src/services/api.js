const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || `Erro ${response.status}`);
  }
  return data;
}

export function optimize(params) {
  return request("/api/optimize", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export function getInstructions(vehicleId = null) {
  return request("/api/llm/instructions", {
    method: "POST",
    body: JSON.stringify({ vehicle_id: vehicleId }),
  });
}

export function getReport(period = "diário") {
  return request("/api/llm/report", {
    method: "POST",
    body: JSON.stringify({ period }),
  });
}

export function askQuestion(question) {
  return request("/api/llm/ask", {
    method: "POST",
    body: JSON.stringify({ question }),
  });
}
