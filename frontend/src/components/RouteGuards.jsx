import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function RequireAuth() {
  const { token, loading } = useAuth();
  if (loading) return <div className="page-loading">Loading…</div>;
  if (!token) return <Navigate to="/login" replace />;
  return <Outlet />;
}

export function RequireManager() {
  const { isManager, loading } = useAuth();
  if (loading) return <div className="page-loading">Loading…</div>;
  if (!isManager) return <Navigate to="/" replace />;
  return <Outlet />;
}
