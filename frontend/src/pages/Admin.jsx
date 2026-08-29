import { useEffect, useState, useCallback } from "react";
import { useAuth } from "../context/AuthContext";
import { api } from "../api";

export default function Admin() {
  const { token } = useAuth();
  const [tab, setTab] = useState("locations");

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Locations &amp; staff</h1>
          <p className="subtitle">Manager-only: locations, categories, staff assignments, and accounts.</p>
        </div>
      </div>

      <div className="tabs">
        <button className={tab === "locations" ? "active" : ""} onClick={() => setTab("locations")}>Locations</button>
        <button className={tab === "categories" ? "active" : ""} onClick={() => setTab("categories")}>Categories</button>
        <button className={tab === "assignments" ? "active" : ""} onClick={() => setTab("assignments")}>Staff assignments</button>
        <button className={tab === "users" ? "active" : ""} onClick={() => setTab("users")}>Accounts</button>
      </div>

      {tab === "locations" && <LocationsPanel token={token} />}
      {tab === "categories" && <CategoriesPanel token={token} />}
      {tab === "assignments" && <AssignmentsPanel token={token} />}
      {tab === "users" && <UsersPanel token={token} />}
    </div>
  );
}

function LocationsPanel({ token }) {
  const [locations, setLocations] = useState([]);
  const [name, setName] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(() => api.listLocations(token).then(setLocations), [token]);
  useEffect(() => { load(); }, [load]);

  async function handleAdd(e) {
    e.preventDefault();
    setError("");
    try {
      await api.createLocation(token, name);
      setName("");
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="card">
      {error && <div className="alert-banner">{error}</div>}
      <form onSubmit={handleAdd} className="form-inline" style={{ marginBottom: 18 }}>
        <div className="form-row">
          <label>New location name</label>
          <input required value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Retail Store C" />
        </div>
        <div className="form-row"><button className="btn btn-primary">Add location</button></div>
      </form>
      <table>
        <thead><tr><th>Location</th></tr></thead>
        <tbody>
          {locations.map((l) => <tr key={l.id}><td>{l.name}</td></tr>)}
        </tbody>
      </table>
    </div>
  );
}

function CategoriesPanel({ token }) {
  const [categories, setCategories] = useState([]);
  const [name, setName] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(() => api.listCategories(token).then(setCategories), [token]);
  useEffect(() => { load(); }, [load]);

  async function handleAdd(e) {
    e.preventDefault();
    setError("");
    try {
      await api.createCategory(token, name);
      setName("");
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="card">
      {error && <div className="alert-banner">{error}</div>}
      <form onSubmit={handleAdd} className="form-inline" style={{ marginBottom: 18 }}>
        <div className="form-row">
          <label>New category name</label>
          <input required value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Frozen Foods" />
        </div>
        <div className="form-row"><button className="btn btn-primary">Add category</button></div>
      </form>
      <table>
        <thead><tr><th>Category</th></tr></thead>
        <tbody>
          {categories.map((c) => <tr key={c.id}><td>{c.name}</td></tr>)}
        </tbody>
      </table>
    </div>
  );
}

function AssignmentsPanel({ token }) {
  const [assignments, setAssignments] = useState([]);
  const [staff, setStaff] = useState([]);
  const [locations, setLocations] = useState([]);
  const [userId, setUserId] = useState("");
  const [locationId, setLocationId] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(() => {
    api.listAssignments(token).then(setAssignments);
    api.listStaff(token).then(setStaff);
    api.listLocations(token).then(setLocations);
  }, [token]);
  useEffect(() => { load(); }, [load]);

  async function handleAdd(e) {
    e.preventDefault();
    setError("");
    try {
      await api.createAssignment(token, Number(userId), Number(locationId));
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleRemove(id) {
    try {
      await api.deleteAssignment(token, id);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="card">
      {error && <div className="alert-banner">{error}</div>}
      <form onSubmit={handleAdd} className="form-inline" style={{ marginBottom: 18 }}>
        <div className="form-row">
          <label>Staff member</label>
          <select required value={userId} onChange={(e) => setUserId(e.target.value)}>
            <option value="">Select…</option>
            {staff.map((s) => <option key={s.id} value={s.id}>{s.name} ({s.email})</option>)}
          </select>
        </div>
        <div className="form-row">
          <label>Location</label>
          <select required value={locationId} onChange={(e) => setLocationId(e.target.value)}>
            <option value="">Select…</option>
            {locations.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
          </select>
        </div>
        <div className="form-row"><button className="btn btn-primary">Assign</button></div>
      </form>
      <table>
        <thead><tr><th>Staff</th><th>Location</th><th></th></tr></thead>
        <tbody>
          {assignments.map((a) => (
            <tr key={a.id}>
              <td>{a.user_name}</td>
              <td>{a.location_name}</td>
              <td><button className="btn btn-sm" onClick={() => handleRemove(a.id)}>Remove</button></td>
            </tr>
          ))}
          {assignments.length === 0 && <tr><td colSpan={3}><div className="empty-state">No assignments yet.</div></td></tr>}
        </tbody>
      </table>
    </div>
  );
}

function UsersPanel({ token }) {
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "staff" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(() => api.listUsers(token).then(setUsers), [token]);
  useEffect(() => { load(); }, [load]);

  async function handleAdd(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await api.createUser(token, form);
      setForm({ name: "", email: "", password: "", role: "staff" });
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="card">
      {error && <div className="alert-banner">{error}</div>}
      <form onSubmit={handleAdd} className="form-inline" style={{ marginBottom: 18 }}>
        <div className="form-row">
          <label>Name</label>
          <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </div>
        <div className="form-row">
          <label>Email</label>
          <input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        </div>
        <div className="form-row">
          <label>Password</label>
          <input required type="password" minLength={8} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        </div>
        <div className="form-row">
          <label>Role</label>
          <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
            <option value="staff">Staff</option>
            <option value="manager">Manager</option>
          </select>
        </div>
        <div className="form-row"><button className="btn btn-primary" disabled={submitting}>Create account</button></div>
      </form>
      <table>
        <thead><tr><th>Name</th><th>Email</th><th>Role</th></tr></thead>
        <tbody>
          {users.map((u) => <tr key={u.id}><td>{u.name}</td><td className="mono">{u.email}</td><td>{u.role}</td></tr>)}
        </tbody>
      </table>
    </div>
  );
}
