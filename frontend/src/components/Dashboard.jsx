import { useEffect, useState } from "react";
import { ApiError } from "../services/api.js";
import {
  getRequestSummary,
  getRequests,
  updateRequestStatus,
} from "../services/requests.js";

const STATUS_LABELS = {
  created: "Nueva",
  in_review: "En revisión",
  in_progress: "En progreso",
  paused: "Pausada",
  done: "Finalizada",
};

const NEXT_STATUSES = {
  created: [{ status: "in_review", label: "Enviar a revisión" }],
  in_review: [
    { status: "in_progress", label: "Iniciar" },
    { status: "paused", label: "Pausar" },
  ],
  in_progress: [
    { status: "done", label: "Completar" },
    { status: "paused", label: "Pausar" },
  ],
  paused: [
    { status: "in_progress", label: "Reanudar" },
    { status: "in_review", label: "Volver a revisión" },
  ],
  done: [],
};

function getDateRange(range) {
  const end = new Date();
  const start = new Date(end);
  start.setDate(start.getDate() - (range === "month" ? 30 : 7));

  return {
    startDate: start.toISOString(),
    endDate: end.toISOString(),
  };
}

function formatDate(value) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Fecha no disponible";
  }

  return new Intl.DateTimeFormat("es", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function getTransitionError(error) {
  if (error instanceof ApiError && error.status === 400) {
    return `El servidor rechazó el cambio: ${error.message}`;
  }

  return error instanceof Error
    ? `No se pudo actualizar la solicitud: ${error.message}`
    : "No se pudo actualizar la solicitud. Inténtalo nuevamente.";
}

function getSummaryUnavailableMessage() {
  return "El servicio de resumen con IA no está disponible temporalmente. Puedes seguir usando el listado de solicitudes.";
}

export default function Dashboard({ onLogout }) {
  const [requests, setRequests] = useState([]);
  const [requestsLoading, setRequestsLoading] = useState(true);
  const [requestsError, setRequestsError] = useState("");
  const [summaryRange, setSummaryRange] = useState("week");
  const [summary, setSummary] = useState("");
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [summaryError, setSummaryError] = useState("");
  const [actionError, setActionError] = useState("");
  const [updatingRequestId, setUpdatingRequestId] = useState(null);

  useEffect(() => {
    const controller = new AbortController();

    async function loadRequests() {
      try {
        const data = await getRequests({ signal: controller.signal });
        if (!Array.isArray(data)) {
          throw new Error("El servidor devolvió un listado no válido.");
        }
        setRequests(data);
      } catch (error) {
        if (!controller.signal.aborted) {
          setRequestsError(
            error instanceof Error
              ? error.message
              : "No se pudieron cargar las solicitudes.",
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setRequestsLoading(false);
        }
      }
    }

    async function loadInitialSummary() {
      try {
        const data = await getRequestSummary({
          ...getDateRange("week"),
          signal: controller.signal,
        });

        if (data?.success === false) {
          throw new Error(data.message || getSummaryUnavailableMessage());
        }

        setSummary(data?.summary || "");
      } catch {
        if (!controller.signal.aborted) {
          setSummaryError(getSummaryUnavailableMessage());
        }
      } finally {
        if (!controller.signal.aborted) {
          setSummaryLoading(false);
        }
      }
    }

    loadRequests();
    loadInitialSummary();

    return () => controller.abort();
  }, []);

  async function handleGenerateSummary() {
    setSummaryLoading(true);
    setSummaryError("");

    try {
      const data = await getRequestSummary(getDateRange(summaryRange));

      if (data?.success === false) {
        throw new Error(data.message || getSummaryUnavailableMessage());
      }

      setSummary(data?.summary || "");
    } catch {
      setSummaryError(getSummaryUnavailableMessage());
    } finally {
      setSummaryLoading(false);
    }
  }

  async function handleStatusChange(request, nextStatus) {
    setActionError("");
    setUpdatingRequestId(request.id);

    try {
      const updatedRequest = await updateRequestStatus(request.id, nextStatus);
      setRequests((current) =>
        current.map((item) =>
          item.id === request.id ? updatedRequest : item,
        ),
      );
    } catch (error) {
      setActionError(getTransitionError(error));
    } finally {
      setUpdatingRequestId(null);
    }
  }

  return (
    <main className="dashboard-page">
      <div className="dashboard-container">
        <header className="dashboard-header">
          <div>
            <p className="eyebrow">Gestión operativa</p>
            <h1 id="dashboard-title">Gestor de Solicitudes</h1>
            <p className="dashboard-subtitle">
              Revisa el resumen reciente y administra el estado de cada solicitud.
            </p>
          </div>
          <button className="logout-button" type="button" onClick={onLogout}>
            Cerrar Sesión
          </button>
        </header>

        <section className="summary-card" aria-labelledby="summary-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Análisis</p>
              <h2 id="summary-title">Resumen con IA</h2>
            </div>
            <div className="summary-controls">
              <label className="visually-hidden" htmlFor="summary-range">
                Rango del resumen
              </label>
              <select
                id="summary-range"
                value={summaryRange}
                onChange={(event) => setSummaryRange(event.target.value)}
              >
                <option value="week">Última semana</option>
                <option value="month">Últimos 30 días</option>
              </select>
              <button
                className="primary-button"
                type="button"
                onClick={handleGenerateSummary}
                disabled={summaryLoading}
              >
                {summaryLoading ? "Generando..." : "Generar resumen"}
              </button>
            </div>
          </div>

          <div className="summary-content" aria-live="polite">
            {summaryLoading ? (
              <p className="muted-message">Preparando el resumen...</p>
            ) : summaryError ? (
              <p className="summary-warning" role="status">
                {summaryError}
              </p>
            ) : (
              <p>{summary || "No hay resumen disponible para este período."}</p>
            )}
          </div>
        </section>

        {actionError && (
          <div className="alert-banner" role="alert">
            <span>{actionError}</span>
            <button
              type="button"
              className="dismiss-button"
              aria-label="Cerrar notificación"
              onClick={() => setActionError("")}
            >
              ×
            </button>
          </div>
        )}

        <section className="requests-card" aria-labelledby="requests-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Bandeja de trabajo</p>
              <h2 id="requests-title">Solicitudes</h2>
            </div>
            <span className="request-count">
              {requests.length}{" "}
              {requests.length === 1 ? "solicitud" : "solicitudes"}
            </span>
          </div>

          {requestsLoading ? (
            <p className="muted-message">Cargando solicitudes...</p>
          ) : requestsError ? (
            <div className="inline-error" role="alert">
              {requestsError}
            </div>
          ) : requests.length === 0 ? (
            <p className="empty-state">Todavía no hay solicitudes para mostrar.</p>
          ) : (
            <div className="request-list">
              {requests.map((request) => {
                const statusTag = request.status?.tag;
                const statusName =
                  request.status?.name || STATUS_LABELS[statusTag] || statusTag;

                return (
                  <article className="request-row" key={request.id}>
                    <div className="request-main">
                      <h3>{request.title}</h3>
                      <p className="request-date">
                        Creada {formatDate(request.created_at)}
                      </p>
                    </div>

                    <span className={`status-badge status-${statusTag || "unknown"}`}>
                      {statusName}
                    </span>

                    <div className="request-actions">
                      {(NEXT_STATUSES[statusTag] || []).map((transition) => (
                        <button
                          className="secondary-button"
                          type="button"
                          key={transition.status}
                          onClick={() =>
                            handleStatusChange(request, transition.status)
                          }
                          disabled={updatingRequestId !== null}
                        >
                          {updatingRequestId === request.id
                            ? "Guardando..."
                            : transition.label}
                        </button>
                      ))}
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
