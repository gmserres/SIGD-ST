import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react';
import {
  obtenerSeleccionProveedorVigente,
  reemplazarProveedor,
  seleccionarProveedor,
} from '../../api/seleccionesProveedor';
import { ApiError } from '../../api/apiError';
import type {
  SeleccionProveedor,
} from '../../api/seleccionesProveedor';
import type { Proveedor } from '../../api/proveedores';
import { HistorialProveedoresModal } from './HistorialProveedoresModal';
import { ProveedorSelectorModal } from './ProveedorSelectorModal';

type ProveedorActualCardProps = {
  expedienteId: string;
  seleccionadoPor: string;
  revisionProveedor: number;
};

type SelectorModo = 'inicial' | 'reemplazo';

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

function mensajeError(
  error: unknown,
  fallback: string,
): string {
  return error instanceof Error ? error.message : fallback;
}

export function ProveedorActualCard({
  expedienteId,
  seleccionadoPor,
  revisionProveedor,
}: ProveedorActualCardProps) {
  const consultaActual = useRef(0);
  const [seleccion, setSeleccion] =
    useState<SeleccionProveedor | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');
  const [selectorModo, setSelectorModo] =
    useState<SelectorModo | null>(null);
  const [historialAbierto, setHistorialAbierto] = useState(false);

  const cargarSeleccion = useCallback(async () => {
    const numeroConsulta = consultaActual.current + 1;
    consultaActual.current = numeroConsulta;
    setCargando(true);
    setError('');

    try {
      const resultado =
        await obtenerSeleccionProveedorVigente(expedienteId);

      if (consultaActual.current === numeroConsulta) {
        setSeleccion(resultado);
      }
    } catch (errorDesconocido) {
      if (consultaActual.current === numeroConsulta) {
        setError(mensajeError(
          errorDesconocido,
          'No fue posible consultar el proveedor seleccionado.',
        ));
      }
    } finally {
      if (consultaActual.current === numeroConsulta) {
        setCargando(false);
      }
    }
  }, [expedienteId, revisionProveedor]);

  useEffect(() => {
    void cargarSeleccion();
  }, [cargarSeleccion]);

  async function confirmarSeleccion(
    proveedor: Proveedor,
    motivoReemplazo: string | null,
  ) {
    try {
      const nuevaSeleccion = selectorModo === 'reemplazo'
        ? await reemplazarProveedor(expedienteId, {
          proveedor_id: proveedor.id_proveedor,
          seleccionado_por: seleccionadoPor,
          motivo_reemplazo: motivoReemplazo ?? '',
        })
        : await seleccionarProveedor(expedienteId, {
          proveedor_id: proveedor.id_proveedor,
          seleccionado_por: seleccionadoPor,
        });

      setSeleccion(nuevaSeleccion);
      setError('');
      setSelectorModo(null);
    } catch (errorDesconocido) {
      if (
        errorDesconocido instanceof ApiError
        && (errorDesconocido.status === 404
          || errorDesconocido.status === 409)
      ) {
        await cargarSeleccion();
      }

      throw errorDesconocido;
    }
  }

  return (
    <>
      <section className="subcard proveedor-actual-card">
        <div className="proveedor-actual-heading">
          <div>
            <span className="eyebrow">Referencia administrativa</span>
            <h4>Proveedor seleccionado</h4>
          </div>
          {seleccion && (
            <span className="badge green">Vigente</span>
          )}
        </div>

        {cargando ? (
          <p className="empty">Consultando proveedor seleccionado...</p>
        ) : error ? (
          <div className="notice error proveedor-actual-error">
            <span>{error}</span>
            <button
              className="link"
              type="button"
              onClick={() => void cargarSeleccion()}
            >
              Reintentar
            </button>
          </div>
        ) : seleccion ? (
          <>
            <div className="proveedor-actual-data">
              <div>
                <strong>{seleccion.proveedor_razon_social}</strong>
                <span>
                  CUIT {mostrarCuit(seleccion.proveedor_cuit)}
                </span>
              </div>
              <div className="proveedor-actual-metadata">
                <span>
                  Seleccionado el {mostrarFecha(seleccion.fecha_seleccion)}
                </span>
                <span>por {seleccion.seleccionado_por}</span>
              </div>
            </div>

            <div className="proveedor-actual-actions">
              <button
                className="small-button"
                type="button"
                onClick={() => setSelectorModo('reemplazo')}
              >
                Reemplazar proveedor
              </button>
              <button
                className="link"
                type="button"
                onClick={() => setHistorialAbierto(true)}
              >
                Ver historial
              </button>
            </div>
          </>
        ) : (
          <div className="proveedor-actual-empty">
            <div>
              <strong>Sin proveedor seleccionado.</strong>
              <p>Seleccione el proveedor previsto para este expediente.</p>
            </div>
            <button
              className="primary"
              type="button"
              onClick={() => setSelectorModo('inicial')}
            >
              Seleccionar proveedor
            </button>
          </div>
        )}
      </section>

      {selectorModo && (
        <ProveedorSelectorModal
          modo={selectorModo}
          proveedorActual={
            selectorModo === 'reemplazo' ? seleccion : null
          }
          onClose={() => setSelectorModo(null)}
          onConfirmar={confirmarSeleccion}
        />
      )}

      {historialAbierto && (
        <HistorialProveedoresModal
          expedienteId={expedienteId}
          onClose={() => setHistorialAbierto(false)}
        />
      )}
    </>
  );
}
