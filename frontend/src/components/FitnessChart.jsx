import { TrendingDown } from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export default function FitnessChart({ history }) {
  if (!history?.length) return null;

  const data = history.map((fitness, generation) => ({ generation, fitness }));

  return (
    <div className="card">
      <div className="card-header">
        <h2><TrendingDown size={16} /> Convergência do AG</h2>
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data} margin={{ top: 5, right: 10, bottom: 5, left: -10 }}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.4} />
          <XAxis dataKey="generation" tick={{ fontSize: 11 }} />
          <YAxis domain={["auto", "auto"]} tick={{ fontSize: 11 }}
            tickFormatter={(v) => v.toFixed(0)} />
          <Tooltip formatter={(v) => v.toFixed(1)} labelFormatter={(l) => `Geração ${l}`} />
          <Line type="monotone" dataKey="fitness" stroke="#4a5362" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
