import { useEffect, useRef, useState } from "react";
import { ApiError } from "../services/api.js";
import RequestModal from "./RequestModal.jsx";
import {
  getRequestSummary,
  getRequests,
  getStatuses,
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

function getPageFromLink(link) {
  if (!link) {
    return null;
  }

  try {
    const url = new URL(link, window.location.origin);
    const page = Number(url.searchParams.get("page"));
    return Number.isInteger(page) && page > 0 ? page : 1;
  } catch {
    return null;
  }
}

function getPageNumbers(currentPage, totalPages) {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, index) => index + 1);
  }

  const pages = new Set([
    1,
    totalPages,
    currentPage - 1,
    currentPage,
    currentPage + 1,
  ]);
  const sortedPages = [...pages]
    .filter((page) => page > 0 && page <= totalPages)
    .sort((a, b) => a - b);
  const items = [];

  sortedPages.forEach((page, index) => {
    if (index > 0 && page - sortedPages[index - 1] > 1) {
      items.push(`ellipsis-${page}`);
    }
    items.push(page);
  });

  return items;
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

export default function Dashboard() {
  const [requestPage, setRequestPage] = useState({
    count: 0,
    next: null,
    previous: null,
    results: [],
  });
  const [requestsLoading, setRequestsLoading] = useState(true);
  const [requestsError, setRequestsError] = useState("");
  const [statuses, setStatuses] = useState([]);
  const [statusesError, setStatusesError] = useState("");
  const [filters, setFilters] = useState({
    search: "",
    status: "",
    start_date: "",
    end_date: "",
  });
  const [filterDraft, setFilterDraft] = useState(filters);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [summaryDateRange, setSummaryDateRange] = useState({
    start_date: "",
    end_date: "",
  });
  const [summary, setSummary] = useState("");
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [summaryError, setSummaryError] = useState("");
  const [summaryDateError, setSummaryDateError] = useState("");
  const [summaryExpanded, setSummaryExpanded] = useState(false);
  const [summaryCanExpand, setSummaryCanExpand] = useState(false);
  const [actionError, setActionError] = useState("");
  const [updatingRequestId, setUpdatingRequestId] = useState(null);
  const [isRequestModalOpen, setIsRequestModalOpen] = useState(false);
  const [requestToEdit, setRequestToEdit] = useState(null);
  const [requestsReloadKey, setRequestsReloadKey] = useState(0);
  const summaryTextRef = useRef(null);

  useEffect(() => {
    const controller = new AbortController();

    async function loadRequests() {
      setRequestsLoading(true);
      setRequestsError("");

      try {
        const data = await getRequests({
          filters,
          page,
          pageSize,
          signal: controller.signal,
        });
        if (!Array.isArray(data?.results) || typeof data?.count !== "number") {
          throw new Error("El servidor devolvió un listado no válido.");
        }

        setRequestPage(data);
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

    loadRequests();
    return () => controller.abort();
  }, [filters, page, pageSize, requestsReloadKey]);

  useEffect(() => {
    const controller = new AbortController();

    async function loadStatuses() {
      try {
        const data = await getStatuses({ signal: controller.signal });
        if (!Array.isArray(data)) {
          throw new Error("El servidor devolvió un catálogo de estados no válido.");
        }
        setStatuses(data);
      } catch {
        if (!controller.signal.aborted) {
          setStatusesError("No se pudieron cargar los estados disponibles.");
        }
      }
    }

    loadStatuses();
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function loadInitialSummary() {
      try {
        const data = await getRequestSummary({
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

    loadInitialSummary();
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const summaryText = summaryTextRef.current;
    setSummaryExpanded(false);
    setSummaryCanExpand(
      Boolean(
        summaryText &&
          summaryText.scrollHeight > summaryText.clientHeight + 1,
      ),
    );
  }, [summary, summaryError, summaryLoading]);

  async function handleGenerateSummary() {
    const { start_date: startDate, end_date: endDate } = summaryDateRange;
    if (Boolean(startDate) !== Boolean(endDate)) {
      setSummaryDateError("Selecciona ambas fechas para definir el período.");
      return;
    }
    if (startDate && startDate > endDate) {
      setSummaryDateError("La fecha inicial debe ser anterior a la fecha final.");
      return;
    }

    setSummaryDateError("");
    setSummaryLoading(true);
    setSummaryError("");

    try {
      const data = await getRequestSummary({
        startDate,
        endDate,
      });

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
      setRequestPage((current) => ({
        ...current,
        results: current.results.map((item) =>
          item.id === request.id ? updatedRequest : item,
        ),
      }));
    } catch (error) {
      setActionError(getTransitionError(error));
    } finally {
      setUpdatingRequestId(null);
    }
  }

  function handleRequestSaved(savedRequest) {
    setIsRequestModalOpen(false);

    if (requestToEdit) {
      setRequestPage((current) => ({
        ...current,
        results: current.results.map((item) =>
          item.id === savedRequest.id ? savedRequest : item,
        ),
      }));
      setRequestToEdit(null);
      setRequestsReloadKey((current) => current + 1);
      return;
    }

    const emptyFilters = {
      search: "",
      status: "",
      start_date: "",
      end_date: "",
    };

    setFilterDraft(emptyFilters);
    setFilters(emptyFilters);
    setPage(1);
    setRequestToEdit(null);
    setRequestsReloadKey((current) => current + 1);
  }

  function openCreateModal() {
    setRequestToEdit(null);
    setIsRequestModalOpen(true);
  }

  function openEditModal(request) {
    setRequestToEdit(request);
    setIsRequestModalOpen(true);
  }

  function applyFilters(event) {
    event.preventDefault();
    setFilters(filterDraft);
    setPage(1);
  }

  function clearFilters() {
    const emptyFilters = {
      search: "",
      status: "",
      start_date: "",
      end_date: "",
    };
    setFilterDraft(emptyFilters);
    setFilters(emptyFilters);
    setPage(1);
  }

  function goToPage(nextPage) {
    if (Number.isInteger(nextPage) && nextPage > 0) {
      setPage(nextPage);
    }
  }

  function goToPageLink(link) {
    const nextPage = getPageFromLink(link);
    if (nextPage !== null) {
      goToPage(nextPage);
    }
  }

  const requests = requestPage.results;
  const totalPages = Math.ceil(requestPage.count / pageSize);
  const pageNumbers = getPageNumbers(page, totalPages);

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
        </header>

        <section className="summary-card" aria-labelledby="summary-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Análisis</p>
              <h2 id="summary-title">Resumen con IA</h2>
            </div>
            <div className="summary-controls">
              <div className="summary-date-field">
                <label htmlFor="summary-start-date">Desde</label>
                <input
                  id="summary-start-date"
                  type="date"
                  value={summaryDateRange.start_date}
                  onChange={(event) => {
                    setSummaryDateRange((current) => ({
                      ...current,
                      start_date: event.target.value,
                    }));
                    setSummaryDateError("");
                  }}
                />
              </div>
              <div className="summary-date-field">
                <label htmlFor="summary-end-date">Hasta</label>
                <input
                  id="summary-end-date"
                  type="date"
                  value={summaryDateRange.end_date}
                  onChange={(event) => {
                    setSummaryDateRange((current) => ({
                      ...current,
                      end_date: event.target.value,
                    }));
                    setSummaryDateError("");
                  }}
                />
              </div>
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
          {summaryDateError && (
            <p className="summary-date-error" role="alert">
              {summaryDateError}
            </p>
          )}

          <div className="summary-content" aria-live="polite">
            {summaryLoading ? (
              <p className="muted-message">Preparando el resumen...</p>
            ) : summaryError ? (
              <p className="summary-warning" role="status">
                {summaryError}
              </p>
            ) : (
              <p
                ref={summaryTextRef}
                className={summaryExpanded ? "summary-expanded" : "summary-clamped"}
              >
                {summary || "No hay resumen disponible para este período."}
              </p>
            )}
          </div>
          {summaryCanExpand && !summaryLoading && !summaryError && (
            <button
              className="summary-toggle"
              type="button"
              aria-expanded={summaryExpanded}
              onClick={() => setSummaryExpanded((expanded) => !expanded)}
            >
              {summaryExpanded ? "Mostrar menos ↑" : "Leer resumen completo ↓"}
            </button>
          )}
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
            <div className="request-heading-actions">
              <span className="request-count">
                {requests.length} de {requestPage.count}{" "}
                {requestPage.count === 1 ? "solicitud" : "solicitudes"}
              </span>
              <button
                className="primary-button"
                type="button"
                onClick={openCreateModal}
              >
                + Crear solicitud
              </button>
            </div>
          </div>

          <form className="request-filters" onSubmit={applyFilters}>
            <div className="filter-field filter-search">
              <label htmlFor="request-search">Buscar</label>
              <input
                id="request-search"
                type="search"
                placeholder="Título o descripción"
                value={filterDraft.search}
                onChange={(event) =>
                  setFilterDraft((current) => ({
                    ...current,
                    search: event.target.value,
                  }))
                }
              />
            </div>

            <div className="filter-field">
              <label htmlFor="request-status">Estado</label>
              <select
                id="request-status"
                value={filterDraft.status}
                onChange={(event) =>
                  setFilterDraft((current) => ({
                    ...current,
                    status: event.target.value,
                  }))
                }
              >
                <option value="">Todos los estados</option>
                {statuses.map((status) => (
                  <option value={status.tag} key={status.tag}>
                    {status.name}
                  </option>
                ))}
              </select>
              {statusesError && (
                <span className="filter-hint">{statusesError}</span>
              )}
            </div>

            <div className="filter-field">
              <label htmlFor="request-start-date">Desde</label>
              <input
                id="request-start-date"
                type="date"
                value={filterDraft.start_date}
                onChange={(event) =>
                  setFilterDraft((current) => ({
                    ...current,
                    start_date: event.target.value,
                  }))
                }
              />
            </div>

            <div className="filter-field">
              <label htmlFor="request-end-date">Hasta</label>
              <input
                id="request-end-date"
                type="date"
                value={filterDraft.end_date}
                onChange={(event) =>
                  setFilterDraft((current) => ({
                    ...current,
                    end_date: event.target.value,
                  }))
                }
              />
            </div>

            <div className="filter-actions">
              <button className="primary-button" type="submit">
                Aplicar filtros
              </button>
              <button
                className="filter-reset-button"
                type="button"
                onClick={clearFilters}
              >
                Limpiar
              </button>
            </div>
          </form>

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
                    <div className="request-leading">
                      <div className="request-main">
                        <h3>{request.title}</h3>
                        <p className="request-date">
                          Creada {formatDate(request.created_at)}
                        </p>
                      </div>
                    </div>

                    <span className={`status-badge status-${statusTag || "unknown"}`}>
                      {statusName}
                    </span>

                    <div className="request-trailing">
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
                      <button
                        className="edit-request-button"
                        type="button"
                        aria-label={`Editar solicitud: ${request.title}`}
                        title="Editar solicitud"
                        onClick={() => openEditModal(request)}
                        disabled={updatingRequestId !== null}
                      >
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                          <path d="M12 20h9" />
                          <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4Z" />
                        </svg>
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
          )}

          {!requestsLoading && !requestsError && totalPages > 0 && (
            <nav className="pagination" aria-label="Paginación de solicitudes">
              <div className="pagination-navigation">
                <button
                  className="page-nav-button"
                  type="button"
                  onClick={() => goToPageLink(requestPage.previous)}
                  disabled={!requestPage.previous}
                >
                  ← Anterior
                </button>
                <div className="page-numbers">
                  {pageNumbers.map((pageNumber) =>
                    typeof pageNumber === "string" ? (
                      <span className="page-ellipsis" key={pageNumber}>
                        …
                      </span>
                    ) : (
                      <button
                        className={`page-number${pageNumber === page ? " is-current" : ""}`}
                        type="button"
                        key={pageNumber}
                        aria-current={pageNumber === page ? "page" : undefined}
                        onClick={() => goToPage(pageNumber)}
                      >
                        {pageNumber}
                      </button>
                    ),
                  )}
                </div>
                <button
                  className="page-nav-button"
                  type="button"
                  onClick={() => goToPageLink(requestPage.next)}
                  disabled={!requestPage.next}
                >
                  Siguiente →
                </button>
              </div>

              <label className="page-size-control">
                Por página
                <select
                  value={pageSize}
                  onChange={(event) => {
                    setPageSize(Number(event.target.value));
                    setPage(1);
                  }}
                >
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                </select>
              </label>
            </nav>
          )}
        </section>
      </div>
      {isRequestModalOpen && (
        <RequestModal
          key={requestToEdit?.id ?? "create"}
          request={requestToEdit}
          onClose={() => {
            setIsRequestModalOpen(false);
            setRequestToEdit(null);
          }}
          onSaved={handleRequestSaved}
        />
      )}
    </main>
  );
}
