import {
  FormEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react';
import {
  listarProveedores,
} from '../../api/proveedores';
import type { Proveedor } from '../../api/proveedores';

type ProveedorSelectorModalProps = {
  onClose: () => void;
  onConfirmar: (proveedor: Proveedor) => Promise<void>;
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

function mensajeError(
  error: unknown,
  fallback: string,
): string {
  return error instanceof Error ? error.message : fallback;
}

export function ProveedorSelectorModal({
  onClose,
  onConfirmar,
}: ProveedorSelectorModalProps) {
  const consultaActual = useRef(0);
  const busquedaRef = useRef<HTMLInputElement>(null);
  const [proveedores, setProveedores] = useState<Proveedor[]>([]);
  const [busqueda, setBusqueda] = useState('');
  const [busquedaAplicada, setBusquedaAplicada] = useState('');
  const [proveedorSeleccionadoId, setProveedorSeleccionadoId] =
    useState<string | null>(null);
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState('');

  const cargar = useCallback(async () => {
    const numeroConsulta = consultaActual.current + 1;
    consultaActual.current = numeroConsulta;
    setCargando(true);
    setError('');

    try {
      const resultado = await listarProveedores({
        buscar: busquedaAplicada || undefined,
        activo: true,
      });

      if (consultaActual.current === numeroConsulta) {
        setProveedores(resultado);
        setProveedorSeleccionadoId((seleccionado) => (
          resultado.some(
            (proveedor) =>
              proveedor.id_proveedor === seleccionado,
          )
            ? seleccionado
            : null
        ));
      }
    } catch (errorDesconocido) {
      if (consultaActual.current === numeroConsulta) {
        setError(mensajeError(
          errorDesconocido,
          'No fue posible consultar los proveedores activos.',
        ));
      }
    } finally {
      if (consultaActual.current === numeroConsulta) {
        setCargando(false);
      }
    }
  }, [busquedaAplicada]);

  useEffect(() => {
    busquedaRef.current?.focus();
    void cargar();
  }, [cargar]);

  useEffect(() => {
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

  function buscar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const nuevaBusqueda = busqueda.trim();

    if (nuevaBusqueda === busquedaAplicada) {
      void cargar();
    } else {
      setBusquedaAplicada(nuevaBusqueda);
    }
  }

  async function confirmar() {
    const proveedor = proveedores.find(
      (item) => item.id_proveedor === proveedorSeleccionadoId,
    );
    if (!proveedor) return;

    setGuardando(true);
    setError('');

    try {
      await onConfirmar(proveedor);
    } catch (errorDesconocido) {
      setError(mensajeError(
        errorDesconocido,
        'No fue posible seleccionar el proveedor.',
      ));
      await cargar();
    } finally {
      setGuardando(false);
    }
  }

  const busquedaSinResultados = Boolean(busquedaAplicada)
    && proveedores.length === 0;

  return (
    <div className="modal-backdrop">
      <section
        className="modal-card proveedor-selector-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="proveedor-selector-title"
      >
        <div className="card-title proveedor-selector-heading">
          <div>
            <span className="eyebrow">Maestro de Proveedores</span>
            <h3 id="proveedor-selector-title">
              Seleccionar proveedor
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

        <form
          className="proveedores-search"
          role="search"
          onSubmit={buscar}
        >
          <label htmlFor="buscar-proveedor-seleccion">
            Buscar por CUIT o razón social
          </label>
          <div>
            <input
              id="buscar-proveedor-seleccion"
              ref={busquedaRef}
              type="search"
              value={busqueda}
              onChange={(evento) => setBusqueda(evento.target.value)}
              placeholder="CUIT o razón social..."
            />
            <button
              className="secondary"
              type="submit"
              disabled={cargando || guardando}
            >
              Buscar
            </button>
          </div>
        </form>

        {error && (
          <div className="notice error proveedor-selector-error">
            {error}
          </div>
        )}

        <div className="proveedor-selector-results">
          {cargando ? (
            <p className="empty">Cargando proveedores activos...</p>
          ) : proveedores.length === 0 ? (
            <div className="proveedor-selector-empty">
              <strong>
                {busquedaSinResultados
                  ? 'No se encontraron proveedores activos.'
                  : 'No hay proveedores activos disponibles.'}
              </strong>
              <p>
                Administre proveedores desde Administración.
              </p>
            </div>
          ) : (
            <div
              className="proveedor-selector-list"
              role="radiogroup"
              aria-label="Proveedores activos"
            >
              {proveedores.map((proveedor) => (
                <label
                  className={`proveedor-selector-option ${
                    proveedorSeleccionadoId
                      === proveedor.id_proveedor
                      ? 'selected'
                      : ''
                  }`}
                  key={proveedor.id_proveedor}
                >
                  <input
                    type="radio"
                    name="proveedor-seleccionado"
                    value={proveedor.id_proveedor}
                    checked={
                      proveedorSeleccionadoId
                      === proveedor.id_proveedor
                    }
                    disabled={guardando}
                    onChange={() => setProveedorSeleccionadoId(
                      proveedor.id_proveedor,
                    )}
                  />
                  <span>
                    <strong>{proveedor.razon_social}</strong>
                    <small>
                      CUIT {mostrarCuit(proveedor.cuit)}
                    </small>
                  </span>
                </label>
              ))}
            </div>
          )}
        </div>

        <div className="actions proveedor-selector-actions">
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
            disabled={!proveedorSeleccionadoId || guardando}
          >
            {guardando ? 'Guardando...' : 'Confirmar selección'}
          </button>
        </div>
      </section>
    </div>
  );
}
