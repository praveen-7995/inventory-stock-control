import { useState } from "react";
import { useNavigate, Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login, token, loading } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("praveennaik7995@gmail.com");
  const [password, setPassword] = useState("password123");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (!loading && token) return <Navigate to="/" replace />;

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err.message || "Sign in failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="login-shell">
      <div className="card" style={{ width: 360 }}>
        <h1 style={{ fontSize: 19, marginTop: 0 }}>Stockroom</h1>
        <p className="subtitle" style={{ color: "var(--text-secondary)", marginTop: -8, marginBottom: 18 }}>
          Sign in to manage inventory and stock movements.
        </p>
        {error && <div className="alert-banner">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <label htmlFor="email">Email</label>
            <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div className="form-row">
            <label htmlFor="password">Password</label>
            <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          <button type="submit" className="btn btn-primary" style={{ width: "100%" }} disabled={submitting}>
            {submitting ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <div className="info-banner" style={{ marginTop: 18, marginBottom: 0, fontSize: 12 }}>
          Demo logins — praveennaik7995@gmail.com (manager) / staff1@example.com / staff2@example.com, all with password <code>password123</code>.
        </div>
      </div>
    </div>
  );
}
