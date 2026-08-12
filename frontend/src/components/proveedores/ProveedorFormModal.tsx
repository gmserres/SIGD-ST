import {
  FormEvent,
  useEffect,
  useRef,
  useState,
} from 'react';
import type {
  Proveedor,
  ProveedorCrear,
  ProveedorModificar,
} from '../../api/proveedores';

type ProveedorFormModalProps = {
  proveedor: Proveedor | null;
  onClose: () => void;
  onCrear: (datos: ProveedorCrear) => Promise<void>;
  onModificar: (
    proveedorId: string,
    datos: ProveedorModificar,
  ) => Promise<void>;
};

export function ProveedorFormModal({
  proveedor,
  onClose,
  onCrear,
  onModificar,
}: ProveedorFormModalProps) {
  const esEdicion = proveedor !== null;
  const primerCampoRef = useRef<HTMLInputElement>(null);
  const [cuit, setCuit] = useState(proveedor?.cuit ?? '');
  const [razonSocial, setRazonSocial] = useState(
    proveedor?.razon_social ?? '',
  );
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    primerCampoRef.current?.focus();

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

  async function guardar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setError('');

    const razonSocialNormalizada = razonSocial.trim();
    if (!razonSocialNormalizada) {
      setError('La razón social es obligatoria.');
      return;
    }

    const cuitNormalizado = cuit.trim();
    if (!esEdicion && !cuitNormalizado) {
      setError('El CUIT es obligatorio.');
      return;
    }

    setGuardando(true);

    try {
      if (proveedor) {
        await onModificar(proveedor.id_proveedor, {
          razon_social: razonSocialNormalizada,
        });
      } else {
        await onCrear({
          cuit: cuitNormalizado,
          razon_social: razonSocialNormalizada,
        });
      }
    } catch (errorDesconocido) {
      setError(
        errorDesconocido instanceof Error
          ? errorDesconocido.message
          : 'No fue posible guardar el proveedor.',
      );
    } finally {
      setGuardando(false);
    }
  }

  return (
    <div className="modal-backdrop">
      <section
        className="modal-card proveedor-form-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="proveedor-form-title"
      >
        <div className="card-title">
          <div>
            <span className="eyebrow">Maestro de Proveedores</span>
            <h3 id="proveedor-form-title">
              {esEdicion ? 'Editar proveedor' : 'Nuevo proveedor'}
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

        <form onSubmit={guardar}>
          <label htmlFor="proveedor-cuit">CUIT</label>
          <input
            id="proveedor-cuit"
            ref={!esEdicion ? primerCampoRef : undefined}
            value={cuit}
            readOnly={esEdicion}
            aria-readonly={esEdicion}
            autoComplete="off"
            onChange={(evento) => setCuit(evento.target.value)}
            placeholder="30-12345678-9"
          />
          {esEdicion && (
            <p className="muted proveedor-field-help">
              El CUIT identifica fiscalmente al proveedor y no puede
              modificarse.
            </p>
          )}

          <label htmlFor="proveedor-razon-social">
            Razón social
          </label>
          <input
            id="proveedor-razon-social"
            ref={esEdicion ? primerCampoRef : undefined}
            value={razonSocial}
            autoComplete="organization"
            onChange={(evento) => setRazonSocial(evento.target.value)}
          />

          {error && (
            <div className="notice error proveedor-form-error">
              {error}
            </div>
          )}

          <div className="actions proveedor-form-actions">
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
              type="submit"
              disabled={guardando}
            >
              {guardando ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
