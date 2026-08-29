import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";
import { useAuth } from "../context/AuthContext";
import { api } from "../api";

export default function Dashboard() {
  const { token } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getDashboard(token).then(setData).catch((e) => setError(e.message));
  }, [token]);

  if (error) return <div className="alert-banner">{error}</div>;
  if (!data) return <div className="page-loading">Loading…</div>;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p className="subtitle">Live snapshot of stock across every location.</p>
        </div>
      </div>

      <div className="grid grid-4">
        <div className="card stat-card">
          <div className="stat-label">Active items</div>
          <div className="stat-value">{data.active_items}</div>
        </div>
        <div className={`card stat-card ${data.items_at_or_below_reorder > 0 ? "warn" : ""}`}>
          <div className="stat-label">At or below reorder</div>
          <div className="stat-value">{data.items_at_or_below_reorder}</div>
        </div>
        <div className="card stat-card">
          <div className="stat-label">Movements today</div>
          <div className="stat-value">{data.movements_today}</div>
        </div>
        <div className="card stat-card">
          <div className="stat-label">Items moved this week</div>
          <div className="stat-value">{data.distinct_items_moved_this_week}</div>
        </div>
      </div>

      <div className="grid grid-2" style={{ marginTop: 16 }}>
        <div className="card">
          <div className="section-title">On-hand by category</div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={data.on_hand_by_category} margin={{ left: -10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e9ec" vertical={false} />
              <XAxis dataKey="category" fontSize={12} stroke="#8b98a3" />
              <YAxis fontSize={12} stroke="#8b98a3" />
              <Tooltip contentStyle={{ fontSize: 13, borderRadius: 6 }} />
              <Bar dataKey="on_hand" fill="#1f4b4c" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <div className="section-title">On-hand by location</div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={data.on_hand_by_location} margin={{ left: -10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e9ec" vertical={false} />
              <XAxis dataKey="location" fontSize={12} stroke="#8b98a3" />
              <YAxis fontSize={12} stroke="#8b98a3" />
              <Tooltip contentStyle={{ fontSize: 13, borderRadius: 6 }} />
              <Bar dataKey="on_hand" fill="#2a5c8a" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <div className="section-title">Receipts vs. issues — last 8 weeks</div>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={data.weekly_receipt_issue_volume} margin={{ left: -10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e9ec" vertical={false} />
            <XAxis dataKey="week_ending" fontSize={12} stroke="#8b98a3" />
            <YAxis fontSize={12} stroke="#8b98a3" />
            <Tooltip contentStyle={{ fontSize: 13, borderRadius: 6 }} />
            <Legend wrapperStyle={{ fontSize: 12.5 }} />
            <Bar dataKey="receipts" fill="#2f7d5d" radius={[3, 3, 0, 0]} name="Receipts" />
            <Bar dataKey="issues" fill="#b0392b" radius={[3, 3, 0, 0]} name="Issues" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
