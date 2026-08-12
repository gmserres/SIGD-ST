import {
  useCallback,
  useEffect,
  useState,
} from 'react';
import {
  obtenerSeleccionProveedorVigente,
  seleccionarProveedor,
} from '../../api/seleccionesProveedor';
import type {
  SeleccionProveedor,
} from '../../api/seleccionesProveedor';
import type { Proveedor } from '../../api/proveedores';
import { ProveedorSelectorModal } from './ProveedorSelectorModal';

type ProveedorActualCardProps = {
  solicitudId: string;
  seleccionadoPor: string;
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

function mensajeError(
  error: unknown,
  fallback: string,
): string {
  return error instanceof Error ? error.message : fallback;
}

export function ProveedorActualCard({
  solicitudId,
  seleccionadoPor,
}: ProveedorActualCardProps) {
  const [seleccion, setSeleccion] =
    useState<SeleccionProveedor | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');
  const [selectorAbierto, setSelectorAbierto] = useState(false);

  const cargarSeleccion = useCallback(async () => {
    setCargando(true);
    setError('');

    try {
      setSeleccion(
        await obtenerSeleccionProveedorVigente(solicitudId),
      );
    } catch (errorDesconocido) {
      setError(mensajeError(
        errorDesconocido,
        'No fue posible consultar el proveedor seleccionado.',
      ));
    } finally {
      setCargando(false);
    }
  }, [solicitudId]);

  useEffect(() => {
    void cargarSeleccion();
  }, [cargarSeleccion]);

  async function confirmarSeleccion(proveedor: Proveedor) {
    try {
      const nuevaSeleccion = await seleccionarProveedor(
        solicitudId,
        {
          proveedor_id: proveedor.id_proveedor,
          seleccionado_por: seleccionadoPor,
        },
      );
      setSeleccion(nuevaSeleccion);
      setError('');
      setSelectorAbierto(false);
    } catch (errorDesconocido) {
      if (
        errorDesconocido instanceof Error
        && errorDesconocido.message
          === 'La Solicitud ya posee una selección vigente.'
      ) {
        setSelectorAbierto(false);
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
        ) : (
          <div className="proveedor-actual-empty">
            <div>
              <strong>Sin proveedor seleccionado.</strong>
              <p>Seleccione el proveedor previsto para la intervención.</p>
            </div>
            <button
              className="primary"
              type="button"
              onClick={() => setSelectorAbierto(true)}
            >
              Seleccionar proveedor
            </button>
          </div>
        )}
      </section>

      {selectorAbierto && (
        <ProveedorSelectorModal
          onClose={() => setSelectorAbierto(false)}
          onConfirmar={confirmarSeleccion}
        />
      )}
    </>
  );
}
