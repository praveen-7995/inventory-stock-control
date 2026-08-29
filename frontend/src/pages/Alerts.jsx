import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../api";

export default function Alerts() {
  const { token, isManager } = useAuth();
  const [alerts, setAlerts] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    api.listAlerts(token).then(setAlerts).catch((e) => setError(e.message));
  }, [token]);

  useEffect(() => { load(); }, [load]);

  async function handleDismiss(itemId) {
    try {
      await api.dismissAlert(token, itemId);
      load();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Low stock alerts</h1>
          <p className="subtitle">Items at or below their reorder level, across all locations.</p>
        </div>
      </div>

      {error && <div className="alert-banner">{error}</div>}

      {!alerts && <div className="page-loading" style={{ minHeight: 200 }}>Loading…</div>}

      {alerts && alerts.length === 0 && (
        <div className="card"><div className="empty-state">Nothing below reorder level right now.</div></div>
      )}

      {alerts && alerts.length > 0 && (
        <div className="card" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th>Item</th>
                <th>SKU</th>
                <th className="num">On hand</th>
                <th className="num">Reorder level</th>
                {isManager && <th></th>}
              </tr>
            </thead>
            <tbody>
              {alerts.map((a) => (
                <tr key={a.item_id}>
                  <td><Link to={`/items/${a.item_id}`}>{a.name}</Link></td>
                  <td className="mono">{a.sku}</td>
                  <td className="num" style={{ color: "var(--warn)", fontWeight: 600 }}>{a.on_hand_total}</td>
                  <td className="num">{a.reorder_level}</td>
                  {isManager && (
                    <td>
                      <button className="btn btn-sm" onClick={() => handleDismiss(a.item_id)}>Dismiss</button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <p className="subtitle" style={{ marginTop: 12 }}>
        Dismissing an alert hides it until stock rises back above the reorder level and then drops again.
      </p>
    </div>
  );
}
