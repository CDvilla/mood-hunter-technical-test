import { useEffect, useState } from "react";
import { createRequest, updateRequest } from "../services/requests.js";

export default function RequestModal({ request, onClose, onSaved }) {
  const isEditing = Boolean(request);
  const [title, setTitle] = useState(request?.title ?? "");
  const [description, setDescription] = useState(request?.description ?? "");
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
      const savedRequest = isEditing
        ? await updateRequest(request.id, {
            title: requestTitle,
            description: requestDescription,
          })
        : await createRequest({
            title: requestTitle,
            description: requestDescription,
          });
      onSaved(savedRequest);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? `No se pudo ${isEditing ? "actualizar" : "crear"} la solicitud: ${requestError.message}`
          : `No se pudo ${isEditing ? "actualizar" : "crear"} la solicitud. Inténtalo nuevamente.`,
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
        aria-labelledby="request-modal-title"
      >
        <header className="request-modal-header">
          <div>
            <p className="eyebrow">
              {isEditing ? "Editar solicitud" : "Nueva solicitud"}
            </p>
            <h2 id="request-modal-title">
              {isEditing ? "Editar solicitud" : "Crear solicitud"}
            </h2>
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
          {isEditing
            ? "Actualiza el título y la descripción de esta solicitud."
            : "Completa los campos para agregar una solicitud a la bandeja."}
        </p>

        {error && (
          <div className="alert-banner modal-error" role="alert">
            {error}
          </div>
        )}

        <form className="request-modal-form" onSubmit={handleSubmit}>
          <label htmlFor="request-title">Título</label>
          <input
            id="request-title"
            name="title"
            type="text"
            maxLength={200}
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            autoFocus
            required
            disabled={isSubmitting}
          />

          <label htmlFor="request-description">Descripción</label>
          <textarea
            id="request-description"
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
              {isSubmitting
                ? isEditing
                  ? "Guardando..."
                  : "Creando..."
                : isEditing
                  ? "Guardar cambios"
                  : "Crear solicitud"}
            </button>
          </footer>
        </form>
      </section>
    </div>
  );
}
