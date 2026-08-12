import {
  FormEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react';
import {
  cambiarEstadoProveedor,
  crearProveedor,
  listarProveedores,
  modificarRazonSocialProveedor,
} from '../../api/proveedores';
import type {
  FiltrosProveedores,
  Proveedor,
  ProveedorCrear,
  ProveedorModificar,
} from '../../api/proveedores';
import { ProveedorFormModal } from './ProveedorFormModal';

type FiltroEstado = 'todos' | 'activos' | 'inactivos';

type ModalProveedor =
  | { tipo: 'crear' }
  | { tipo: 'editar'; proveedor: Proveedor }
  | null;

function filtrosApi(
  buscar: string,
  estado: FiltroEstado,
): FiltrosProveedores {
  return {
    buscar: buscar || undefined,
    activo: estado === 'todos'
      ? undefined
      : estado === 'activos',
  };
}

function mensajeError(
  error: unknown,
  fallback: string,
): string {
  return error instanceof Error ? error.message : fallback;
}

function mostrarCuit(cuit: string): string {
  const digitos = cuit.replace(/\D/g, '');
  if (digitos.length !== 11) return cuit;
  return `${digitos.slice(0, 2)}-${digitos.slice(2, 10)}-${digitos.slice(10)}`;
}

export function ProveedoresAdmin() {
  const consultaActual = useRef(0);
  const [proveedores, setProveedores] = useState<Proveedor[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');
  const [mensajeExito, setMensajeExito] = useState('');
  const [busqueda, setBusqueda] = useState('');
  const [busquedaAplicada, setBusquedaAplicada] = useState('');
  const [filtroEstado, setFiltroEstado] =
    useState<FiltroEstado>('todos');
  const [modal, setModal] = useState<ModalProveedor>(null);
  const [cambiandoEstadoId, setCambiandoEstadoId] =
    useState<string | null>(null);

  const cargar = useCallback(async () => {
    const numeroConsulta = consultaActual.current + 1;
    consultaActual.current = numeroConsulta;
    setCargando(true);
    setError('');

    try {
      const resultado = await listarProveedores(
        filtrosApi(busquedaAplicada, filtroEstado),
      );

      if (consultaActual.current === numeroConsulta) {
        setProveedores(resultado);
      }
    } catch (errorDesconocido) {
      if (consultaActual.current === numeroConsulta) {
        setError(mensajeError(
          errorDesconocido,
          'No fue posible consultar los proveedores.',
        ));
      }
    } finally {
      if (consultaActual.current === numeroConsulta) {
        setCargando(false);
      }
    }
  }, [busquedaAplicada, filtroEstado]);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  function buscar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setMensajeExito('');
    const nuevaBusqueda = busqueda.trim();

    if (nuevaBusqueda === busquedaAplicada) {
      void cargar();
    } else {
      setBusquedaAplicada(nuevaBusqueda);
    }
  }

  function cambiarFiltro(nuevoFiltro: FiltroEstado) {
    setMensajeExito('');
    setFiltroEstado(nuevoFiltro);
  }

  async function registrar(datos: ProveedorCrear) {
    await crearProveedor(datos);
    setModal(null);
    setMensajeExito('Proveedor registrado correctamente.');
    await cargar();
  }

  async function modificar(
    proveedorId: string,
    datos: ProveedorModificar,
  ) {
    await modificarRazonSocialProveedor(proveedorId, datos);
    setModal(null);
    setMensajeExito('Razón social actualizada correctamente.');
    await cargar();
  }

  async function cambiarEstado(proveedor: Proveedor) {
    if (
      proveedor.activo
      && !window.confirm(
        `¿Inactivar a ${proveedor.razon_social}? `
        + 'El proveedor conservará su información histórica.',
      )
    ) {
      return;
    }

    setCambiandoEstadoId(proveedor.id_proveedor);
    setError('');
    setMensajeExito('');

    try {
      await cambiarEstadoProveedor(
        proveedor.id_proveedor,
        !proveedor.activo,
      );
      setMensajeExito(
        proveedor.activo
          ? 'Proveedor inactivado correctamente.'
          : 'Proveedor reactivado correctamente.',
      );
      await cargar();
    } catch (errorDesconocido) {
      const mensaje = mensajeError(
        errorDesconocido,
        'No fue posible actualizar el estado del proveedor.',
      );
      await cargar();
      setError(mensaje);
    } finally {
      setCambiandoEstadoId(null);
    }
  }

  const hayCriterios = Boolean(busquedaAplicada)
    || filtroEstado !== 'todos';

  return (
    <>
      <section className="card proveedores-admin">
        <div className="card-title proveedores-admin-heading">
          <div>
            <span className="eyebrow">Maestro persistente</span>
            <h3>Proveedores</h3>
            <p className="muted">
              Consulte y administre los proveedores habilitados para
              los circuitos administrativos.
            </p>
          </div>
          <button
            className="primary"
            type="button"
            onClick={() => setModal({ tipo: 'crear' })}
          >
            + Nuevo proveedor
          </button>
        </div>

        <form
          className="proveedores-search"
          role="search"
          onSubmit={buscar}
        >
          <label htmlFor="buscar-proveedor">
            Buscar por CUIT o razón social
          </label>
          <div>
            <input
              id="buscar-proveedor"
              type="search"
              value={busqueda}
              onChange={(evento) => setBusqueda(evento.target.value)}
              placeholder="CUIT o razón social..."
            />
            <button
              className="secondary"
              type="submit"
              disabled={cargando}
            >
              Buscar
            </button>
          </div>
        </form>

        <div
          className="proveedores-filtros"
          aria-label="Filtrar proveedores por estado"
        >
          {([
            ['todos', 'Todos'],
            ['activos', 'Activos'],
            ['inactivos', 'Inactivos'],
          ] as const).map(([valor, etiqueta]) => (
            <button
              className={filtroEstado === valor ? 'active' : ''}
              type="button"
              key={valor}
              aria-pressed={filtroEstado === valor}
              onClick={() => cambiarFiltro(valor)}
            >
              {etiqueta}
            </button>
          ))}
        </div>

        {mensajeExito && (
          <div className="notice ok">{mensajeExito}</div>
        )}

        {error && (
          <div className="notice error">
            <span>{error}</span>
            <button
              className="link"
              type="button"
              onClick={() => void cargar()}
            >
              Reintentar
            </button>
          </div>
        )}

        {cargando ? (
          <p className="empty">Cargando proveedores...</p>
        ) : proveedores.length === 0 ? (
          <p className="empty">
            {hayCriterios
              ? 'No se encontraron proveedores para la búsqueda o filtro aplicado.'
              : 'No hay proveedores registrados.'}
          </p>
        ) : (
          <div className="proveedores-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Razón social</th>
                  <th>CUIT</th>
                  <th>Estado</th>
                  <th><span className="sr-only">Acciones</span></th>
                </tr>
              </thead>
              <tbody>
                {proveedores.map((proveedor) => {
                  const cambiando = cambiandoEstadoId
                    === proveedor.id_proveedor;

                  return (
                    <tr key={proveedor.id_proveedor}>
                      <td><strong>{proveedor.razon_social}</strong></td>
                      <td>{mostrarCuit(proveedor.cuit)}</td>
                      <td>
                        <span
                          className={`badge ${
                            proveedor.activo ? 'green' : 'yellow'
                          }`}
                        >
                          {proveedor.activo ? 'Activo' : 'Inactivo'}
                        </span>
                      </td>
                      <td>
                        <div className="proveedores-row-actions">
                          <button
                            className="link"
                            type="button"
                            onClick={() => setModal({
                              tipo: 'editar',
                              proveedor,
                            })}
                            disabled={cambiando}
                          >
                            Editar
                          </button>
                          <button
                            className="link"
                            type="button"
                            onClick={() => void cambiarEstado(proveedor)}
                            disabled={cambiando}
                          >
                            {cambiando
                              ? 'Actualizando...'
                              : proveedor.activo
                                ? 'Inactivar'
                                : 'Reactivar'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {modal && (
        <ProveedorFormModal
          proveedor={modal.tipo === 'editar' ? modal.proveedor : null}
          onClose={() => setModal(null)}
          onCrear={registrar}
          onModificar={modificar}
        />
      )}
    </>
  );
}
