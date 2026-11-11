import { useState } from "react";
import { login } from "../services/auth.js";

export default function Login({ onLogin, notice }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    if (!username.trim() || !password) {
      setError("Completa el usuario y la contraseña.");
      return;
    }

    setIsSubmitting(true);

    try {
      await login(username.trim(), password);
      onLogin();
    } catch {
      setError(
        "No se pudo iniciar sesión. Revisa tus credenciales e inténtalo de nuevo.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="page-shell">
      <section className="login-card" aria-labelledby="login-title">
        <p className="eyebrow">Technical Test</p>
        <h1 id="login-title">Iniciar sesión</h1>
        <p className="login-description">
          Ingresa tus credenciales para continuar.
        </p>

        {notice && (
          <p className="notice-message" role="status">
            {notice}
          </p>
        )}

        {error && (
          <p className="error-message" role="alert">
            {error}
          </p>
        )}

        <form className="login-form" onSubmit={handleSubmit}>
          <label htmlFor="username">Usuario</label>
          <input
            id="username"
            name="username"
            type="text"
            autoComplete="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            disabled={isSubmitting}
          />

          <label htmlFor="password">Contraseña</label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            disabled={isSubmitting}
          />

          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Ingresando..." : "Ingresar"}
          </button>
        </form>
      </section>
    </main>
  );
}
