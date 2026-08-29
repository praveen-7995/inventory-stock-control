import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { RequireAuth, RequireManager } from "./components/RouteGuards";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import ItemsList from "./pages/ItemsList";
import ItemDetail from "./pages/ItemDetail";
import Alerts from "./pages/Alerts";
import ImportExport from "./pages/ImportExport";
import Admin from "./pages/Admin";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<RequireAuth />}>
            <Route element={<Layout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/items" element={<ItemsList />} />
              <Route path="/items/:id" element={<ItemDetail />} />
              <Route path="/alerts" element={<Alerts />} />
              <Route path="/import-export" element={<ImportExport />} />
              <Route element={<RequireManager />}>
                <Route path="/admin" element={<Admin />} />
              </Route>
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
