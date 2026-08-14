import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react';
import {
  listarHistorialProveedores,
} from '../../api/seleccionesProveedor';
import type {
  SeleccionProveedor,
} from '../../api/seleccionesProveedor';

type HistorialProveedoresModalProps = {
  expedienteId: string;
  onClose: () => void;
};

function mostrarCuit(cuit: string): string {
  const digitos = cuit.replace(/\D/g, '');
  if (digitos.length !== 11) return cuit;

  return (
    `${digitos.slice(0, 2)}-`
    + `${digitos.slice(2, 10)}-`
    + digitos.slice(10)
  );
}

function mostrarFecha(fecha: string): string {
  return new Intl.DateTimeFormat('es-AR', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(fecha));
}

function mensajeError(error: unknown): string {
  return error instanceof Error
    ? error.message
    : 'No fue posible consultar el historial de proveedores.';
}

export function HistorialProveedoresModal({
  expedienteId,
  onClose,
}: HistorialProveedoresModalProps) {
  const cerrarRef = useRef<HTMLButtonElement>(null);
  const [historial, setHistorial] =
    useState<SeleccionProveedor[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');

  const cargar = useCallback(async () => {
    setCargando(true);
    setError('');

    try {
      setHistorial(
        await listarHistorialProveedores(expedienteId),
      );
    } catch (errorDesconocido) {
      setError(mensajeError(errorDesconocido));
    } finally {
      setCargando(false);
    }
  }, [expedienteId]);

  useEffect(() => {
    cerrarRef.current?.focus();
    void cargar();
  }, [cargar]);

  useEffect(() => {
    function cerrarConEscape(evento: KeyboardEvent) {
      if (evento.key === 'Escape') onClose();
    }

    document.addEventListener('keydown', cerrarConEscape);
    return () => document.removeEventListener(
      'keydown',
      cerrarConEscape,
    );
  }, [onClose]);

  return (
    <div className="modal-backdrop">
      <section
        className="modal-card historial-proveedores-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="historial-proveedores-title"
      >
        <div className="card-title historial-proveedores-heading">
          <div>
            <span className="eyebrow">Trazabilidad administrativa</span>
            <h3 id="historial-proveedores-title">
              Historial de proveedores
            </h3>
          </div>
          <button
            className="small-button"
            type="button"
            ref={cerrarRef}
            onClick={onClose}
          >
            Cerrar
          </button>
        </div>

        {cargando ? (
          <p className="empty">Cargando historial...</p>
        ) : error ? (
          <div className="notice error historial-proveedores-error">
            <span>{error}</span>
            <button
              className="link"
              type="button"
              onClick={() => void cargar()}
            >
              Reintentar
            </button>
          </div>
        ) : historial.length === 0 ? (
          <p className="empty">
            No existen selecciones de proveedor registradas.
          </p>
        ) : (
          <ol className="historial-proveedores-list">
            {historial.map((seleccion) => (
              <li key={seleccion.id_seleccion}>
                <article className="historial-proveedor-item">
                  <div className="historial-proveedor-title">
                    <div>
                      <strong>
                        {seleccion.proveedor_razon_social}
                      </strong>
                      <span>
                        CUIT {mostrarCuit(seleccion.proveedor_cuit)}
                      </span>
                    </div>
                    <span
                      className={`badge ${
                        seleccion.vigente ? 'green' : 'blue'
                      }`}
                    >
                      {seleccion.vigente ? 'Vigente' : 'Reemplazado'}
                    </span>
                  </div>

                  <div className="historial-proveedor-metadata">
                    <span>{mostrarFecha(seleccion.fecha_seleccion)}</span>
                    <span>Seleccionado por {seleccion.seleccionado_por}</span>
                  </div>

                  <p>
                    {seleccion.motivo_reemplazo
                      ? `Reemplazó al proveedor anterior por: ${seleccion.motivo_reemplazo}`
                      : 'Selección inicial'}
                  </p>
                </article>
              </li>
            ))}
          </ol>
        )}
      </section>
    </div>
  );
}
