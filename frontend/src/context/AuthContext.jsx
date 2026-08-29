import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api } from "../api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .me(token)
      .then(setUser)
      .catch(() => {
        localStorage.removeItem("token");
        setToken(null);
      })
      .finally(() => setLoading(false));
  }, [token]);

  const login = useCallback(async (email, password) => {
    const data = await api.login(email, password);
    localStorage.setItem("token", data.access_token);
    setToken(data.access_token);
    setUser(data.user);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ token, user, loading, login, logout, isManager: user?.role === "manager" }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
