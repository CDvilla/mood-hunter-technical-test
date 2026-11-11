import { useEffect, useState } from "react";
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
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    function handleKeyDown(event) {
      if (event.key === "Escape") {
        setMenuOpen(false);
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  function closeMenu() {
    setMenuOpen(false);
  }

  return (
    <aside
      className={`sidebar${menuOpen ? " is-menu-open" : ""}`}
      aria-label="Navegación principal"
      onMouseEnter={(event) => {
        if (!window.matchMedia("(max-width: 760px)").matches) {
          event.currentTarget.classList.add("is-expanded");
        }
      }}
      onMouseLeave={(event) => event.currentTarget.classList.remove("is-expanded")}
    >
      <div className="sidebar-topbar">
        <NavLink
          className="sidebar-brand"
          to="/home"
          aria-label="Mood Hunter"
          onClick={closeMenu}
        >
          <span className="brand-mark" aria-hidden="true">
            M
          </span>
          <span className="sidebar-label">Mood Hunter</span>
        </NavLink>
        <button
          className="sidebar-menu-toggle"
          type="button"
          aria-label={menuOpen ? "Cerrar menú" : "Abrir menú"}
          aria-expanded={menuOpen}
          aria-controls="primary-navigation"
          onClick={() => setMenuOpen((isOpen) => !isOpen)}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            {menuOpen ? (
              <path d="m6 6 12 12M18 6 6 18" />
            ) : (
              <path d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      <nav className="sidebar-nav" id="primary-navigation">
        <NavLink
          to="/home"
          end
          onClick={closeMenu}
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
          onClick={closeMenu}
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
        onClick={() => {
          closeMenu();
          onLogout();
        }}
        title="Cerrar sesión"
      >
        <LogoutIcon />
        <span className="sidebar-label">Cerrar sesión</span>
      </button>
    </aside>
  );
}
