import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../api";

const PAGE_SIZE = 15;

export default function ItemsList() {
  const { token, isManager } = useAuth();
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [categories, setCategories] = useState([]);
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [locationId, setLocationId] = useState("");
  const [archived, setArchived] = useState("");
  const [belowReorder, setBelowReorder] = useState(false);
  const [sortBy, setSortBy] = useState("name");
  const [sortDir, setSortDir] = useState("asc");
  const [page, setPage] = useState(1);

  const [showNewItem, setShowNewItem] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    api
      .listItems(token, {
        search, category_id: categoryId, location_id: locationId, archived,
        at_or_below_reorder: belowReorder || undefined, sort_by: sortBy, sort_dir: sortDir,
        page, page_size: PAGE_SIZE,
      })
      .then((data) => { setItems(data.items); setTotal(data.total); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [token, search, categoryId, locationId, archived, belowReorder, sortBy, sortDir, page]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    api.listCategories(token).then(setCategories).catch(() => {});
    api.listLocations(token).then(setLocations).catch(() => {});
  }, [token]);

  useEffect(() => { setPage(1); }, [search, categoryId, locationId, archived, belowReorder]);

  function toggleSort(field) {
    if (sortBy === field) setSortDir(sortDir === "asc" ? "desc" : "asc");
    else { setSortBy(field); setSortDir("asc"); }
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Items</h1>
          <p className="subtitle">Search, filter, and manage every SKU in the catalog.</p>
        </div>
        {isManager && (
          <button className="btn btn-primary" onClick={() => setShowNewItem(true)}>+ New item</button>
        )}
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="form-inline">
          <div className="form-row" style={{ minWidth: 220 }}>
            <label>Search</label>
            <input placeholder="Name or SKU…" value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <div className="form-row">
            <label>Category</label>
            <select value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
              <option value="">All categories</option>
              {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div className="form-row">
            <label>Location</label>
            <select value={locationId} onChange={(e) => setLocationId(e.target.value)}>
              <option value="">All locations</option>
              {locations.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
            </select>
          </div>
          <div className="form-row">
            <label>Status</label>
            <select value={archived} onChange={(e) => setArchived(e.target.value)}>
              <option value="">Active</option>
              <option value="true">Archived</option>
            </select>
          </div>
          <div className="form-row" style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
            <input type="checkbox" id="belowReorder" checked={belowReorder}
                   onChange={(e) => setBelowReorder(e.target.checked)} style={{ width: "auto" }} />
            <label htmlFor="belowReorder" style={{ marginBottom: 0 }}>At/below reorder</label>
          </div>
        </div>
      </div>

      {error && <div className="alert-banner">{error}</div>}

      <div className="card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th onClick={() => toggleSort("name")}>Name {sortBy === "name" && (sortDir === "asc" ? "▲" : "▼")}</th>
              <th>SKU</th>
              <th>Category</th>
              <th className="num" onClick={() => toggleSort("on_hand")}>
                On hand {sortBy === "on_hand" && (sortDir === "asc" ? "▲" : "▼")}
              </th>
              <th className="num" onClick={() => toggleSort("reorder_level")}>
                Reorder level {sortBy === "reorder_level" && (sortDir === "asc" ? "▲" : "▼")}
              </th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                <td><Link to={`/items/${item.id}`}>{item.name}</Link></td>
                <td className="mono">{item.sku}</td>
                <td>{item.category_name}</td>
                <td className={`num ${item.on_hand_total <= item.reorder_level ? "" : ""}`}
                    style={item.on_hand_total <= item.reorder_level ? { color: "var(--warn)", fontWeight: 600 } : undefined}>
                  {item.on_hand_total}
                </td>
                <td className="num">{item.reorder_level}</td>
                <td>
                  <span className={`badge ${item.is_archived ? "badge-archived" : "badge-active"}`}>
                    {item.is_archived ? "Archived" : "Active"}
                  </span>
                </td>
              </tr>
            ))}
            {!loading && items.length === 0 && (
              <tr><td colSpan={6}><div className="empty-state">No items match these filters.</div></td></tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="pagination">
        <span>{total} item{total === 1 ? "" : "s"} · page {page} of {totalPages}</span>
        <button className="btn btn-sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Previous</button>
        <button className="btn btn-sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>Next</button>
      </div>

      {showNewItem && (
        <NewItemModal
          token={token}
          categories={categories}
          onClose={() => setShowNewItem(false)}
          onCreated={() => { setShowNewItem(false); load(); }}
        />
      )}
    </div>
  );
}

function NewItemModal({ token, categories, onClose, onCreated }) {
  const [form, setForm] = useState({
    sku: "", name: "", description: "", unit_of_measure: "", reorder_level: 0,
    category_id: categories[0]?.id || "",
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await api.createItem(token, { ...form, reorder_level: Number(form.reorder_level), category_id: Number(form.category_id) });
      onCreated();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>New item</h2>
        {error && <div className="alert-banner">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <label>SKU</label>
            <input required value={form.sku} onChange={(e) => setForm({ ...form, sku: e.target.value })} />
          </div>
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
            <input required placeholder="e.g. box, each, bottle" value={form.unit_of_measure}
                   onChange={(e) => setForm({ ...form, unit_of_measure: e.target.value })} />
          </div>
          <div className="form-row">
            <label>Reorder level</label>
            <input required type="number" min="0" value={form.reorder_level}
                   onChange={(e) => setForm({ ...form, reorder_level: e.target.value })} />
          </div>
          <div className="form-row">
            <label>Category</label>
            <select required value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })}>
              {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div className="modal-actions">
            <button type="button" className="btn" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? "Creating…" : "Create item"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
