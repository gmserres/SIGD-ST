import {
  useEffect,
  useRef,
  useState,
} from 'react';
import { reemplazarProveedor } from '../../api/seleccionesProveedor';

type RegularizarProveedorOPModalProps = {
  expedienteId: string;
  proveedorId: string;
  seleccionadoPor: string;
  proveedorActualRazonSocial: string;
  proveedorActualCuit: string;
  proveedorDetectadoRazonSocial: string | null;
  proveedorDetectadoCuit: string;
  onClose: () => void;
  onRegularizado: () => Promise<void> | void;
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

function mensajeError(error: unknown): string {
  return error instanceof Error
    ? error.message
    : 'No fue posible regularizar el proveedor.';
}

export function RegularizarProveedorOPModal({
  expedienteId,
  proveedorId,
  seleccionadoPor,
  proveedorActualRazonSocial,
  proveedorActualCuit,
  proveedorDetectadoRazonSocial,
  proveedorDetectadoCuit,
  onClose,
  onRegularizado,
}: RegularizarProveedorOPModalProps) {
  const motivoRef = useRef<HTMLTextAreaElement>(null);
  const [motivo, setMotivo] = useState('');
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    motivoRef.current?.focus();

    function cerrarConEscape(evento: KeyboardEvent) {
      if (evento.key === 'Escape' && !guardando) {
        onClose();
      }
    }

    document.addEventListener('keydown', cerrarConEscape);
    return () => document.removeEventListener(
      'keydown',
      cerrarConEscape,
    );
  }, [guardando, onClose]);

  async function confirmar() {
    const motivoNormalizado = motivo.trim();
    if (!motivoNormalizado) {
      setError('El motivo de la regularización es obligatorio.');
      return;
    }

    setGuardando(true);
    setError('');

    try {
      await reemplazarProveedor(expedienteId, {
        proveedor_id: proveedorId,
        seleccionado_por: seleccionadoPor,
        motivo_reemplazo: motivoNormalizado,
      });
      await onRegularizado();
    } catch (errorDesconocido) {
      setError(mensajeError(errorDesconocido));
    } finally {
      setGuardando(false);
    }
  }

  return (
    <div className="modal-backdrop">
      <section
        className="modal-card regularizar-proveedor-op-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="regularizar-proveedor-op-title"
      >
        <div className="card-title">
          <div>
            <span className="eyebrow">
              Regularización administrativa
            </span>
            <h3 id="regularizar-proveedor-op-title">
              Regularizar proveedor
            </h3>
          </div>
          <button
            className="small-button"
            type="button"
            onClick={onClose}
            disabled={guardando}
          >
            Cerrar
          </button>
        </div>

        <div className="regularizar-proveedor-op-comparison">
          <section>
            <span>Proveedor actual</span>
            <strong>{proveedorActualRazonSocial}</strong>
            <small>CUIT {mostrarCuit(proveedorActualCuit)}</small>
          </section>

          <section>
            <span>Proveedor informado por la OP</span>
            <strong>
              {proveedorDetectadoRazonSocial
                || 'Razón social documental no informada'}
            </strong>
            <small>
              CUIT {mostrarCuit(proveedorDetectadoCuit)}
            </small>
          </section>
        </div>

        <label htmlFor="motivo-regularizacion-proveedor">
          Motivo de la regularización
        </label>
        <textarea
          id="motivo-regularizacion-proveedor"
          ref={motivoRef}
          value={motivo}
          disabled={guardando}
          onChange={(evento) => {
            setMotivo(evento.target.value);
            setError('');
          }}
        />
        <small className="regularizar-proveedor-op-help">
          Ejemplo: Regularización por discrepancia entre el proveedor
          seleccionado y el informado en la Orden de Pago.
        </small>

        <p className="regularizar-proveedor-op-note">
          Después del reemplazo deberá ejecutar un nuevo control contra
          esta OP.
        </p>

        {error && <div className="notice error">{error}</div>}

        <div className="actions regularizar-proveedor-op-actions">
          <button
            className="secondary"
            type="button"
            onClick={onClose}
            disabled={guardando}
          >
            Cancelar
          </button>
          <button
            className="primary"
            type="button"
            onClick={() => void confirmar()}
            disabled={guardando || !motivo.trim()}
          >
            {guardando
              ? 'Regularizando...'
              : 'Confirmar regularización'}
          </button>
        </div>
      </section>
    </div>
  );
}
