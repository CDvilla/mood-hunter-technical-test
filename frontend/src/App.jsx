import { useState } from "react";
import {
  BrowserRouter,
  Navigate,
  Outlet,
  Route,
  Routes,
  useNavigate,
} from "react-router-dom";
import Dashboard from "./components/Dashboard.jsx";
import Home from "./components/Home.jsx";
import Login from "./components/Login.jsx";
import Sidebar from "./components/Sidebar.jsx";
import { isAuthenticated, logout } from "./services/auth.js";

function AppLayout({ onLogout }) {
  return (
    <div className="app-shell">
      <Sidebar onLogout={onLogout} />
      <Outlet />
    </div>
  );
}

function AppRoutes() {
  const navigate = useNavigate();
  const [authenticated, setAuthenticated] = useState(isAuthenticated);
  const [notice, setNotice] = useState("");

  function handleLogin() {
    setNotice("");
    setAuthenticated(true);
    navigate("/home", { replace: true });
  }

  async function handleLogout() {
    setNotice("");

    try {
      await logout();
    } catch {
      setNotice(
        "La sesión local se cerró, pero no fue posible invalidar el token en el servidor.",
      );
    } finally {
      setAuthenticated(false);
      navigate("/", { replace: true });
    }
  }

  if (!authenticated) {
    return <Login onLogin={handleLogin} notice={notice} />;
  }

  return (
    <Routes>
      <Route element={<AppLayout onLogout={handleLogout} />}>
        <Route index element={<Home />} />
        <Route path="home" element={<Home />} />
        <Route path="requests" element={<Dashboard />} />
        <Route path="*" element={<Navigate to="/home" replace />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}
