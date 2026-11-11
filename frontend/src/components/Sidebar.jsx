import { NavLink, useLocation } from "react-router-dom";

function HomeIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="m3.5 10 8.5-7 8.5 7v10a1 1 0 0 1-1 1h-5.2v-7h-4.6v7H4.5a1 1 0 0 1-1-1z" />
    </svg>
  );
}

function RequestsIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <rect x="4" y="3.5" width="16" height="17" rx="2" />
      <path d="M8 8h8M8 12h8M8 16h5" />
    </svg>
  );
}

function LogoutIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M10 4H5.5a1.5 1.5 0 0 0-1.5 1.5v13A1.5 1.5 0 0 0 5.5 20H10" />
      <path d="M14 16l4-4-4-4M18 12H9" />
    </svg>
  );
}

export default function Sidebar({ onLogout }) {
  const { pathname } = useLocation();
  const homeIsActive = pathname === "/" || pathname === "/home";

  return (
    <aside
      className="sidebar"
      aria-label="Navegación principal"
      onMouseEnter={(event) => event.currentTarget.classList.add("is-expanded")}
      onMouseLeave={(event) =>
        event.currentTarget.classList.remove("is-expanded")
      }
    >
      <NavLink className="sidebar-brand" to="/home" aria-label="Mood Hunter">
        <span className="brand-mark" aria-hidden="true">
          M
        </span>
        <span className="sidebar-label">Mood Hunter</span>
      </NavLink>

      <nav className="sidebar-nav">
        <NavLink
          to="/home"
          end
          className={({ isActive }) =>
            `sidebar-link${isActive || homeIsActive ? " is-active" : ""}`
          }
          title="Home"
        >
          <HomeIcon />
          <span className="sidebar-label">Home</span>
        </NavLink>
        <NavLink
          to="/requests"
          className={({ isActive }) =>
            `sidebar-link${isActive ? " is-active" : ""}`
          }
          title="Solicitudes"
        >
          <RequestsIcon />
          <span className="sidebar-label">Solicitudes</span>
        </NavLink>
      </nav>

      <button
        className="sidebar-link sidebar-logout"
        type="button"
        onClick={onLogout}
        title="Cerrar sesión"
      >
        <LogoutIcon />
        <span className="sidebar-label">Cerrar sesión</span>
      </button>
    </aside>
  );
}
