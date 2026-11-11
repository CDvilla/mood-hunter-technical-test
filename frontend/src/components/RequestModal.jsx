import { useEffect, useState } from "react";
import { createRequest } from "../services/requests.js";

export default function RequestModal({ onClose, onCreated }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    function handleKeyDown(event) {
      if (event.key === "Escape" && !isSubmitting) {
        onClose();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isSubmitting, onClose]);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    const requestTitle = title.trim();
    const requestDescription = description.trim();
    if (!requestTitle || !requestDescription) {
      setError("Completa el título y la descripción.");
      return;
    }

    setIsSubmitting(true);

    try {
      const request = await createRequest({
        title: requestTitle,
        description: requestDescription,
      });
      onCreated(request);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? `No se pudo crear la solicitud: ${requestError.message}`
          : "No se pudo crear la solicitud. Inténtalo nuevamente.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div
      className="modal-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !isSubmitting) {
          onClose();
        }
      }}
    >
      <section
        className="request-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="create-request-title"
      >
        <header className="request-modal-header">
          <div>
            <p className="eyebrow">Nueva solicitud</p>
            <h2 id="create-request-title">Crear solicitud</h2>
          </div>
          <button
            className="modal-close-button"
            type="button"
            aria-label="Cerrar formulario"
            onClick={onClose}
            disabled={isSubmitting}
          >
            ×
          </button>
        </header>

        <p className="modal-description">
          Completa los campos para agregar una solicitud a la bandeja.
        </p>

        {error && (
          <div className="alert-banner modal-error" role="alert">
            {error}
          </div>
        )}

        <form className="request-modal-form" onSubmit={handleSubmit}>
          <label htmlFor="new-request-title">Título</label>
          <input
            id="new-request-title"
            name="title"
            type="text"
            maxLength={200}
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            autoFocus
            required
            disabled={isSubmitting}
          />

          <label htmlFor="new-request-description">Descripción</label>
          <textarea
            id="new-request-description"
            name="description"
            rows={5}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            required
            disabled={isSubmitting}
          />

          <footer className="request-modal-actions">
            <button
              className="filter-reset-button"
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancelar
            </button>
            <button
              className="primary-button"
              type="submit"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Creando..." : "Crear solicitud"}
            </button>
          </footer>
        </form>
      </section>
    </div>
  );
}
