import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../api";

export default function Layout() {
  const { user, token, isManager, logout } = useAuth();
  const [alertCount, setAlertCount] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    let cancelled = false;
    function refresh() {
      api.listAlerts(token).then((alerts) => {
        if (!cancelled) setAlertCount(alerts.length);
      }).catch(() => {});
    }
    refresh();
    const id = setInterval(refresh, 30000);
    return () => { cancelled = true; clearInterval(id); };
  }, [token]);

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          Stockroom
          <small>Inventory Control</small>
        </div>
        <nav>
          <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>Dashboard</NavLink>
          <NavLink to="/items" className={({ isActive }) => (isActive ? "active" : "")}>Items</NavLink>
          <NavLink to="/alerts" className={({ isActive }) => (isActive ? "active" : "")}>
            Low stock alerts
            {alertCount > 0 && <span className="sidebar-badge">{alertCount}</span>}
          </NavLink>
          <NavLink to="/import-export" className={({ isActive }) => (isActive ? "active" : "")}>Import / export</NavLink>
          {isManager && (
            <NavLink to="/admin" className={({ isActive }) => (isActive ? "active" : "")}>Locations &amp; staff</NavLink>
          )}
        </nav>
        <div className="sidebar-footer">
          <div className="sidebar-user">
            <strong>{user?.name}</strong>
            {user?.role} · {user?.email}
          </div>
          <button onClick={handleLogout}>Sign out</button>
        </div>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
