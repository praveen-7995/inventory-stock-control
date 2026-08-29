import { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../api";

export default function ItemDetail() {
  const { id } = useParams();
  const { token, isManager } = useAuth();
  const [item, setItem] = useState(null);
  const [movements, setMovements] = useState([]);
  const [history, setHistory] = useState([]);
  const [locations, setLocations] = useState([]);
  const [myLocations, setMyLocations] = useState([]);
  const [categories, setCategories] = useState([]);
  const [tab, setTab] = useState("ledger");
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(false);

  const loadAll = useCallback(() => {
    api.getItem(token, id).then(setItem).catch((e) => setError(e.message));
    api.listMovementsForItem(token, id).then(setMovements).catch(() => {});
    api.getHistory(token, id).then(setHistory).catch(() => {});
  }, [token, id]);

  useEffect(() => { loadAll(); }, [loadAll]);
  useEffect(() => {
    api.listLocations(token).then(setLocations).catch(() => {});
    api.listMyLocations(token).then(setMyLocations).catch(() => {});
    api.listCategories(token).then(setCategories).catch(() => {});
  }, [token]);

  if (error) return <div className="alert-banner">{error}</div>;
  if (!item) return <div className="page-loading">Loading…</div>;

  async function handleArchiveToggle() {
    try {
      if (item.is_archived) await api.restoreItem(token, id);
      else await api.archiveItem(token, id);
      loadAll();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <p className="subtitle" style={{ marginBottom: 4 }}>
            <Link to="/items">← Items</Link>
          </p>
          <h1>{item.name} <span className="mono" style={{ fontSize: 15, color: "var(--text-faint)", fontWeight: 500 }}>· {item.sku}</span></h1>
          <p className="subtitle">
            {item.category_name} · {item.unit_of_measure} · reorder at {item.reorder_level}
            {" · "}
            <span className={`badge ${item.is_archived ? "badge-archived" : "badge-active"}`}>
              {item.is_archived ? "Archived" : "Active"}
            </span>
          </p>
        </div>
        {isManager && (
          <div style={{ display: "flex", gap: 8 }}>
            {!item.is_archived && <button className="btn" onClick={() => setEditing(true)}>Edit</button>}
            <button className={`btn ${item.is_archived ? "btn-primary" : "btn-danger"}`} onClick={handleArchiveToggle}>
              {item.is_archived ? "Restore item" : "Archive item"}
            </button>
          </div>
        )}
      </div>

      <div className="grid grid-4" style={{ marginBottom: 16 }}>
        <div className="card stat-card">
          <div className="stat-label">On hand (all locations)</div>
          <div className={`stat-value ${item.on_hand_total <= item.reorder_level ? "warn" : ""}`}>
            {item.on_hand_total}
          </div>
        </div>
      </div>

      {item.description && <div className="card" style={{ marginBottom: 16 }}>{item.description}</div>}

      {!item.is_archived && (
        <RecordMovementForm token={token} item={item} locations={locations} myLocations={myLocations} onRecorded={loadAll} />
      )}
      {item.is_archived && (
        <div className="info-banner">This item is archived. Restore it before recording new movements.</div>
      )}

      <div className="tabs" style={{ marginTop: 20 }}>
        <button className={tab === "ledger" ? "active" : ""} onClick={() => setTab("ledger")}>Movement ledger</button>
        <button className={tab === "history" ? "active" : ""} onClick={() => setTab("history")}>Audit history &amp; notes</button>
      </div>

      {tab === "ledger" && <LedgerTable movements={movements} locations={locations} />}
      {tab === "history" && <HistoryTimeline history={history} token={token} itemId={id} onNoteAdded={loadAll} />}

      {editing && (
        <EditItemModal
          token={token} item={item} categories={categories}
          onClose={() => setEditing(false)}
          onSaved={() => { setEditing(false); loadAll(); }}
        />
      )}
    </div>
  );
}

function RecordMovementForm({ token, item, locations, myLocations, onRecorded }) {
  const [kind, setKind] = useState("receipt");
  const [quantity, setQuantity] = useState("");
  const [locationId, setLocationId] = useState("");
  const [fromLocationId, setFromLocationId] = useState("");
  const [toLocationId, setToLocationId] = useState("");
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const payload = { item_id: item.id, kind, quantity: Number(quantity) };
      if (kind === "transfer") {
        payload.from_location_id = Number(fromLocationId);
        payload.to_location_id = Number(toLocationId);
      } else {
        payload.location_id = Number(locationId);
      }
      if (kind === "adjustment") payload.reason = reason;
      await api.createMovement(token, payload);
      setQuantity(""); setReason("");
      onRecorded();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="section-title">Record a movement</div>
      {error && <div className="alert-banner">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-inline">
          <div className="form-row">
            <label>Kind</label>
            <select value={kind} onChange={(e) => setKind(e.target.value)}>
              <option value="receipt">Receipt</option>
              <option value="issue">Issue</option>
              <option value="transfer">Transfer</option>
              <option value="adjustment">Adjustment</option>
            </select>
          </div>
          <div className="form-row">
            <label>Quantity</label>
            <input type="number" required value={quantity} onChange={(e) => setQuantity(e.target.value)}
                   placeholder={kind === "adjustment" ? "e.g. -3 or 5" : "e.g. 10"} />
          </div>
          {kind === "transfer" ? (
            <>
              <div className="form-row">
                <label>From (your locations)</label>
                <select required value={fromLocationId} onChange={(e) => setFromLocationId(e.target.value)}>
                  <option value="">Select…</option>
                  {myLocations.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
                </select>
              </div>
              <div className="form-row">
                <label>To</label>
                <select required value={toLocationId} onChange={(e) => setToLocationId(e.target.value)}>
                  <option value="">Select…</option>
                  {locations.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
                </select>
              </div>
            </>
          ) : (
            <div className="form-row">
              <label>Location</label>
              <select required value={locationId} onChange={(e) => setLocationId(e.target.value)}>
                <option value="">Select…</option>
                {myLocations.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
              </select>
            </div>
          )}
          {kind === "adjustment" && (
            <div className="form-row" style={{ minWidth: 220 }}>
              <label>Reason (required)</label>
              <input required value={reason} onChange={(e) => setReason(e.target.value)} placeholder="e.g. damaged in storage" />
            </div>
          )}
          <div className="form-row">
            <label>&nbsp;</label>
            <button className="btn btn-primary" disabled={submitting}>{submitting ? "Recording…" : "Record"}</button>
          </div>
        </div>
      </form>
    </div>
  );
}

function kindLabel(kind) {
  return kind.charAt(0).toUpperCase() + kind.slice(1);
}

function LedgerTable({ movements, locations }) {
  const nameFor = (id) => locations.find((l) => l.id === id)?.name || `#${id}`;
  if (movements.length === 0) return <div className="card"><div className="empty-state">No movements recorded yet.</div></div>;
  return (
    <div className="card" style={{ padding: 0 }}>
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Kind</th>
            <th className="num">Quantity</th>
            <th>Location(s)</th>
            <th>Reason</th>
            <th>Recorded by</th>
          </tr>
        </thead>
        <tbody>
          {[...movements].reverse().map((m) => (
            <tr key={m.id} className={`ledger-row ${m.kind}`}>
              <td>{new Date(m.created_at).toLocaleString()}</td>
              <td><span className={`badge badge-${m.kind}`}>{kindLabel(m.kind)}</span></td>
              <td className="num">{m.kind === "adjustment" ? (m.quantity > 0 ? "+" : "") + m.quantity : m.quantity}</td>
              <td>
                {m.kind === "transfer"
                  ? `${nameFor(m.from_location_id)} → ${nameFor(m.to_location_id)}`
                  : nameFor(m.location_id)}
              </td>
              <td>{m.reason || "—"}</td>
              <td>{m.recorded_by_name}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function HistoryTimeline({ history, token, itemId, onNoteAdded }) {
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleAddNote(e) {
    e.preventDefault();
    if (!note.trim()) return;
    setSubmitting(true);
    setError("");
    try {
      await api.addNote(token, itemId, note);
      setNote("");
      onNoteAdded();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  function describe(entry) {
    switch (entry.event_type) {
      case "created": return `Item created (${entry.new_value})`;
      case "archived": return "Item archived";
      case "restored": return "Item restored";
      case "note": return entry.note;
      case "field_change": return `Changed ${entry.field_name}: "${entry.old_value}" → "${entry.new_value}"`;
      default: return entry.event_type;
    }
  }

  return (
    <div className="card">
      <div className="section-title">Add a note</div>
      {error && <div className="alert-banner">{error}</div>}
      <form onSubmit={handleAddNote} className="form-inline" style={{ marginBottom: 18 }}>
        <div className="form-row" style={{ flex: 1, minWidth: 260 }}>
          <textarea placeholder="Leave a note for this item…" value={note} onChange={(e) => setNote(e.target.value)} />
        </div>
        <div className="form-row">
          <button className="btn btn-primary" disabled={submitting}>{submitting ? "Saving…" : "Add note"}</button>
        </div>
      </form>

      <div className="section-title">Timeline</div>
      {history.length === 0 && <div className="empty-state">No history yet.</div>}
      {[...history].reverse().map((entry) => (
        <div className="history-entry" key={entry.id}>
          <div>{describe(entry)}</div>
          <div className="meta">{entry.changed_by_name} · {new Date(entry.created_at).toLocaleString()}</div>
        </div>
      ))}
    </div>
  );
}

function EditItemModal({ token, item, categories, onClose, onSaved }) {
  const [form, setForm] = useState({
    name: item.name, description: item.description || "", unit_of_measure: item.unit_of_measure,
    reorder_level: item.reorder_level, category_id: item.category_id,
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await api.updateItem(token, item.id, { ...form, reorder_level: Number(form.reorder_level), category_id: Number(form.category_id) });
      onSaved();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>Edit item</h2>
        {error && <div className="alert-banner">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <label>Name</label>
            <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </div>
          <div className="form-row">
            <label>Description</label>
            <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </div>
          <div className="form-row">
            <label>Unit of measure</label>
            <input required value={form.unit_of_measure} onChange={(e) => setForm({ ...form, unit_of_measure: e.target.value })} />
          </div>
          <div className="form-row">
            <label>Reorder level</label>
            <input required type="number" min="0" value={form.reorder_level} onChange={(e) => setForm({ ...form, reorder_level: e.target.value })} />
          </div>
          <div className="form-row">
            <label>Category</label>
            <select required value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })}>
              {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div className="modal-actions">
            <button type="button" className="btn" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>{submitting ? "Saving…" : "Save changes"}</button>
          </div>
        </form>
      </div>
    </div>
  );
}
