export default function Dashboard({ onLogout }) {
  return (
    <main className="page-shell">
      <section className="dashboard" aria-labelledby="dashboard-title">
        <header className="dashboard-header">
          <div>
            <p className="eyebrow">Technical Test</p>
            <h1 id="dashboard-title">Panel principal</h1>
          </div>
          <button className="logout-button" type="button" onClick={onLogout}>
            Cerrar Sesión
          </button>
        </header>
      </section>
    </main>
  );
}
