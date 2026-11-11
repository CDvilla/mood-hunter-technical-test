import { Link } from "react-router-dom";

export default function Home() {
  return (
    <main className="home-page">
      <section className="home-hero" aria-labelledby="home-title">
        <p className="eyebrow">Mood Hunter · Gestión operativa</p>
        <h1 id="home-title">
          Claridad para cada
          <span> solicitud.</span>
        </h1>
        <p className="home-description">
          Centraliza el seguimiento de solicitudes, identifica prioridades y
          convierte la actividad reciente en información útil para tu equipo.
        </p>
        <Link className="primary-button home-cta" to="/requests">
          Ir a solicitudes <span aria-hidden="true">→</span>
        </Link>
        <div className="home-feature-grid" aria-label="Funciones principales">
          <article className="home-feature">
            <span className="home-feature-icon" aria-hidden="true">
              01
            </span>
            <h2>Seguimiento simple</h2>
            <p>Consulta estados y avanza cada solicitud desde una sola vista.</p>
          </article>
          <article className="home-feature">
            <span className="home-feature-icon" aria-hidden="true">
              02
            </span>
            <h2>Información enfocada</h2>
            <p>Filtra y encuentra rápidamente lo que necesita atención.</p>
          </article>
          <article className="home-feature">
            <span className="home-feature-icon" aria-hidden="true">
              03
            </span>
            <h2>Resumen inteligente</h2>
            <p>Obtén una lectura ejecutiva de la actividad seleccionada.</p>
          </article>
        </div>
      </section>
    </main>
  );
}
