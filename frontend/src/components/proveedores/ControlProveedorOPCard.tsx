import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react';
import {
  consultarControlProveedorOP,
  consultarHabilitacionProveedorOP,
  ejecutarControlProveedorOP,
} from '../../api/controlProveedorOP';
import type {
  ControlProveedorOP,
  EstadoControlProveedorOP,
  EstadoHabilitacionProveedorOP,
  HabilitacionProveedorOP,
} from '../../api/controlProveedorOP';
import {
  RegularizarProveedorOPModal,
} from './RegularizarProveedorOPModal';

type ControlProveedorOPCardProps = {
  expedienteId: string;
  documentoOpId: string;
  nombreArchivo: string;
  seleccionadoPor: string;
  revisionProveedor: number;
  onProveedorRegularizado: () => void;
};

const etiquetasControl: Record<EstadoControlProveedorOP, string> = {
  COINCIDE: 'Coincide',
  CUIT_DIFERENTE: 'Proveedor diferente',
  NO_VERIFICABLE: 'No verificable',
  SIN_PROVEEDOR_SELECCIONADO: 'Sin proveedor seleccionado',
  SIN_SOLICITUD_ASOCIADA: 'Sin Solicitud asociada',
};

const etiquetasHabilitacion:
Record<EstadoHabilitacionProveedorOP, string> = {
  HABILITADO: 'Habilitado',
  REQUIERE_REASIGNACION_PROVEEDOR: 'Requiere regularización',
  REQUIERE_SELECCION_PROVEEDOR: 'Requiere seleccionar proveedor',
  REQUIERE_NUEVO_CONTROL: 'Requiere nuevo control',
  PROVEEDOR_NO_VERIFICABLE: 'Revisión requerida',
  SIN_SOLICITUD_ASOCIADA: 'Sin Solicitud asociada',
};

function claseEstado(
  estado: EstadoHabilitacionProveedorOP,
): string {
  if (estado === 'HABILITADO') return 'green';
  if (
    estado === 'REQUIERE_REASIGNACION_PROVEEDOR'
    || estado === 'PROVEEDOR_NO_VERIFICABLE'
  ) {
    return 'red';
  }
  return 'yellow';
}

function mostrarCuit(cuit: string | null): string {
  if (!cuit) return 'No informado';

  const digitos = cuit.replace(/\D/g, '');
  if (digitos.length !== 11) return cuit;

  return (
    `${digitos.slice(0, 2)}-`
    + `${digitos.slice(2, 10)}-`
    + digitos.slice(10)
  );
}

function mostrarRazonSocial(razonSocial: string | null): string {
  return razonSocial?.trim() || 'Razón social documental no informada';
}

function mensajeError(
  error: unknown,
  fallback: string,
): string {
  return error instanceof Error ? error.message : fallback;
}

function etiquetaMaestro(
  habilitacion: HabilitacionProveedorOP,
): string | null {
  if (
    habilitacion.estado !== 'REQUIERE_REASIGNACION_PROVEEDOR'
    || habilitacion.proveedor_op_en_maestro === null
  ) {
    return null;
  }

  if (!habilitacion.proveedor_op_en_maestro) {
    return 'El proveedor documental no existe en el Maestro.';
  }
  if (habilitacion.proveedor_op_activo === false) {
    return 'El proveedor documental existe, pero está inactivo.';
  }
  return 'El proveedor documental existe y está activo.';
}

export function ControlProveedorOPCard({
  expedienteId,
  documentoOpId,
  nombreArchivo,
  seleccionadoPor,
  revisionProveedor,
  onProveedorRegularizado,
}: ControlProveedorOPCardProps) {
  const consultaActual = useRef(0);
  const [control, setControl] =
    useState<ControlProveedorOP | null>(null);
  const [habilitacion, setHabilitacion] =
    useState<HabilitacionProveedorOP | null>(null);
  const [cargando, setCargando] = useState(true);
  const [ejecutando, setEjecutando] = useState(false);
  const [errorControl, setErrorControl] = useState('');
  const [errorHabilitacion, setErrorHabilitacion] = useState('');
  const [errorAccion, setErrorAccion] = useState('');
  const [regularizando, setRegularizando] = useState(false);

  const cargar = useCallback(async () => {
    const numeroConsulta = consultaActual.current + 1;
    consultaActual.current = numeroConsulta;
    setCargando(true);
    setErrorControl('');
    setErrorHabilitacion('');
    setErrorAccion('');

    const [resultadoControl, resultadoHabilitacion] =
      await Promise.allSettled([
        consultarControlProveedorOP(expedienteId, documentoOpId),
        consultarHabilitacionProveedorOP(
          expedienteId,
          documentoOpId,
        ),
      ]);

    if (consultaActual.current !== numeroConsulta) return;

    if (resultadoControl.status === 'fulfilled') {
      setControl(resultadoControl.value);
    } else {
      setControl(null);
      setErrorControl(mensajeError(
        resultadoControl.reason,
        'No fue posible reconstruir el control de proveedor.',
      ));
    }

    if (resultadoHabilitacion.status === 'fulfilled') {
      setHabilitacion(resultadoHabilitacion.value);
    } else {
      setHabilitacion(null);
      setErrorHabilitacion(mensajeError(
        resultadoHabilitacion.reason,
        'No fue posible evaluar la habilitación de esta OP.',
      ));
    }

    setCargando(false);
  }, [documentoOpId, expedienteId, revisionProveedor]);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  async function ejecutarControl() {
    setEjecutando(true);
    setErrorAccion('');

    try {
      const nuevoControl = await ejecutarControlProveedorOP(
        expedienteId,
        documentoOpId,
      );
      setControl(nuevoControl);
      setErrorControl('');

      const nuevaHabilitacion =
        await consultarHabilitacionProveedorOP(
          expedienteId,
          documentoOpId,
        );
      setHabilitacion(nuevaHabilitacion);
      setErrorHabilitacion('');
    } catch (errorDesconocido) {
      setErrorAccion(mensajeError(
        errorDesconocido,
        'No fue posible ejecutar el control de proveedor.',
      ));
    } finally {
      setEjecutando(false);
    }
  }

  async function proveedorRegularizado() {
    setRegularizando(false);
    await cargar();
    onProveedorRegularizado();
  }

  const accionControl = habilitacion?.estado ===
    'REQUIERE_NUEVO_CONTROL'
    ? 'Controlar proveedor'
    : habilitacion?.estado === 'PROVEEDOR_NO_VERIFICABLE'
      ? 'Reintentar control'
      : null;
  const estadoMaestro = habilitacion
    ? etiquetaMaestro(habilitacion)
    : null;
  const puedeRegularizar = (
    control?.estado === 'CUIT_DIFERENTE'
    && habilitacion?.estado === 'REQUIERE_REASIGNACION_PROVEEDOR'
    && habilitacion.proveedor_op_en_maestro === true
    && habilitacion.proveedor_op_activo === true
    && habilitacion.proveedor_definitivo_id !== null
    && control.cuit_seleccionado !== null
    && control.cuit_detectado !== null
    && control.razon_social_seleccionada !== null
  );
  const impedimentoRegularizacion = habilitacion?.estado ===
    'REQUIERE_REASIGNACION_PROVEEDOR'
    ? habilitacion.proveedor_op_en_maestro === false
      ? (
        'El proveedor informado por la OP no existe en el Maestro de '
        + 'Proveedores. Regístrelo desde Administración y vuelva a '
        + 'consultar esta OP.'
      )
      : habilitacion.proveedor_op_activo === false
        ? (
          'El proveedor informado por la OP existe en el Maestro, pero '
          + 'está inactivo. Reactívelo desde Administración antes de '
          + 'regularizar la selección.'
        )
        : null
    : null;

  return (
    <section className="control-proveedor-op-card">
      <div className="control-proveedor-op-heading">
        <div>
          <span className="eyebrow">Proveedor de la OP</span>
          <strong>{nombreArchivo}</strong>
          <small>{documentoOpId}</small>
        </div>
        {habilitacion && (
          <span
            className={`badge ${claseEstado(habilitacion.estado)}`}
          >
            {etiquetasHabilitacion[habilitacion.estado]}
          </span>
        )}
      </div>

      {cargando ? (
        <p className="empty">Consultando control de proveedor...</p>
      ) : (
        <>
          {control && (
            <>
              <p className="control-proveedor-op-evidence">
                {habilitacion?.control_proveedor_op_id
                  ? 'Evidencia administrativa vigente.'
                  : (
                    'Comparación reconstruida. Todavía debe ejecutarse '
                    + 'el control administrativo.'
                  )}
              </p>
              <div className="control-proveedor-op-comparison">
                <div>
                  <span>Seleccionado</span>
                  <strong>
                    {mostrarRazonSocial(
                      control.razon_social_seleccionada,
                    )}
                  </strong>
                  <small>
                    CUIT {mostrarCuit(control.cuit_seleccionado)}
                  </small>
                </div>
                <div>
                  <span>Detectado en OP</span>
                  <strong>
                    {mostrarRazonSocial(
                      control.razon_social_detectada,
                    )}
                  </strong>
                  <small>
                    CUIT {mostrarCuit(control.cuit_detectado)}
                  </small>
                </div>
                <div className="control-proveedor-op-result">
                  <span>Comparación</span>
                  <strong>{etiquetasControl[control.estado]}</strong>
                </div>
              </div>
            </>
          )}

          {habilitacion && (
            <div className="control-proveedor-op-message">
              <p>{habilitacion.mensaje}</p>
              {habilitacion.proxima_accion && (
                <small>
                  Próxima acción: {habilitacion.proxima_accion}
                </small>
              )}
              {estadoMaestro && <small>{estadoMaestro}</small>}
            </div>
          )}

          {control?.advertencias.map((advertencia) => (
            <p
              className="control-proveedor-op-warning"
              key={advertencia}
            >
              {advertencia}
            </p>
          ))}

          {impedimentoRegularizacion && (
            <p className="control-proveedor-op-warning">
              {impedimentoRegularizacion}
            </p>
          )}

          {errorControl && (
            <div className="notice error">{errorControl}</div>
          )}
          {errorHabilitacion && (
            <div className="notice error">{errorHabilitacion}</div>
          )}
          {errorAccion && (
            <div className="notice error">{errorAccion}</div>
          )}

          <div className="control-proveedor-op-actions">
            {(errorControl || errorHabilitacion) && (
              <button
                className="small-button"
                type="button"
                onClick={() => void cargar()}
                disabled={ejecutando}
              >
                Reintentar consulta
              </button>
            )}
            {accionControl && (
              <button
                className="secondary"
                type="button"
                onClick={() => void ejecutarControl()}
                disabled={ejecutando}
              >
                {ejecutando ? 'Controlando...' : accionControl}
              </button>
            )}
            {puedeRegularizar && (
              <button
                className="secondary"
                type="button"
                onClick={() => setRegularizando(true)}
              >
                Regularizar proveedor
              </button>
            )}
          </div>
        </>
      )}

      {regularizando
        && control
        && habilitacion?.proveedor_definitivo_id
        && control.cuit_seleccionado
        && control.cuit_detectado
        && control.razon_social_seleccionada && (
        <RegularizarProveedorOPModal
          expedienteId={expedienteId}
          proveedorId={habilitacion.proveedor_definitivo_id}
          seleccionadoPor={seleccionadoPor}
          proveedorActualRazonSocial={
            control.razon_social_seleccionada
          }
          proveedorActualCuit={control.cuit_seleccionado}
          proveedorDetectadoRazonSocial={
            control.razon_social_detectada
          }
          proveedorDetectadoCuit={control.cuit_detectado}
          onClose={() => setRegularizando(false)}
          onRegularizado={proveedorRegularizado}
        />
      )}
    </section>
  );
}
