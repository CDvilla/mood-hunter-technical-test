import { useState } from "react";
import Dashboard from "./components/Dashboard.jsx";
import Login from "./components/Login.jsx";
import { isAuthenticated, logout } from "./services/auth.js";

export default function App() {
  const [authenticated, setAuthenticated] = useState(isAuthenticated);
  const [notice, setNotice] = useState("");

  function handleLogin() {
    setNotice("");
    setAuthenticated(true);
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
    }
  }

  return authenticated ? (
    <Dashboard onLogout={handleLogout} />
  ) : (
    <Login onLogin={handleLogin} notice={notice} />
  );
}
