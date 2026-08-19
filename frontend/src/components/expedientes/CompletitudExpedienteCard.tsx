import { useCallback, useEffect, useState } from 'react';
import {
  archivarExpediente,
  cerrarExpediente,
  consultarHabilitacionCierre,
  consultarHabilitacionDesistimiento,
  desistirExpediente,
} from '../../api/finalizacionExpediente';
import type {
  HabilitacionCierre,
  HabilitacionDesistimiento,
} from '../../api/finalizacionExpediente';

type Props<T> = {
  expediente: T & {
    id: string;
    estado: string;
    fecha_cierre?: string | null;
    usuario_registro_cierre?: string | null;
    registrado_cierre_en?: string | null;
    fecha_desistimiento?: string | null;
    usuario_registro_desistimiento?: string | null;
    registrado_desistimiento_en?: string | null;
    motivo_desistimiento?: string | null;
    fecha_archivo?: string | null;
    usuario_registro_archivo?: string | null;
  };
  onFinalizado: (expediente: T) => void;
};

const hoy = () => {
  const fecha = new Date();
  const offset = fecha.getTimezoneOffset() * 60_000;
  return new Date(fecha.getTime() - offset).toISOString().slice(0, 10);
};

const mensajeError = (error: unknown) => error instanceof Error
  ? error.message : 'No fue posible completar la operación.';

export function CompletitudExpedienteCard<T>({ expediente, onFinalizado }: Props<T>) {
  const [cierre, setCierre] = useState<HabilitacionCierre | null>(null);
  const [desistimiento, setDesistimiento] = useState<HabilitacionDesistimiento | null>(null);
  const [cargando, setCargando] = useState(true);
  const [procesando, setProcesando] = useState(false);
  const [error, setError] = useState('');
  const [modo, setModo] = useState<'cierre' | 'desistimiento' | 'archivo' | null>(null);
  const [fecha, setFecha] = useState(hoy());
  const [motivo, setMotivo] = useState('');
  const [confirmado, setConfirmado] = useState(false);

  const cargar = useCallback(async () => {
    if (['CERRADO', 'DESISTIDO', 'ARCHIVADO'].includes(expediente.estado)) {
      setCargando(false);
      return;
    }
    setCargando(true);
    setError('');
    try {
      const estadoCierre = await consultarHabilitacionCierre(expediente.id);
      setCierre(estadoCierre);
      if (estadoCierre.cantidad_op === 0) {
        setDesistimiento(await consultarHabilitacionDesistimiento(expediente.id));
      } else {
        setDesistimiento(null);
      }
    } catch (err) {
      setError(mensajeError(err));
    } finally {
      setCargando(false);
    }
  }, [expediente.id, expediente.estado]);

  useEffect(() => { void cargar(); }, [cargar]);

  async function confirmar() {
    setProcesando(true);
    setError('');
    try {
      if (modo === 'cierre') {
        onFinalizado(await cerrarExpediente<T>(expediente.id, fecha));
      } else if (modo === 'desistimiento') {
        onFinalizado(await desistirExpediente<T>(expediente.id, fecha, motivo.trim()));
      } else if (modo === 'archivo') {
        onFinalizado(await archivarExpediente<T>(expediente.id, fecha));
      }
      setModo(null);
    } catch (err) {
      setError(mensajeError(err));
    } finally {
      setProcesando(false);
    }
  }

  if (expediente.estado === 'ARCHIVADO') {
    const procedencia = expediente.fecha_cierre
      ? 'Cerrado'
      : expediente.fecha_desistimiento
        ? 'Desistido'
        : 'Registro histórico / legacy';
    return <section className="card completitud-expediente terminal">
      <h3>Expediente archivado</h3>
      <p>Finalización: <strong>{procedencia}</strong></p>
      {expediente.fecha_cierre && <p>Fecha de cierre: <strong>{expediente.fecha_cierre}</strong></p>}
      {expediente.fecha_desistimiento && <p>Fecha de desistimiento: <strong>{expediente.fecha_desistimiento}</strong></p>}
      {expediente.motivo_desistimiento && <p>Motivo: <strong>{expediente.motivo_desistimiento}</strong></p>}
      <p>Fecha de archivo: <strong>{expediente.fecha_archivo || '—'}</strong></p>
      <p>Registrado por: <strong>{expediente.usuario_registro_archivo || '—'}</strong></p>
    </section>;
  }
  if (['CERRADO', 'DESISTIDO'].includes(expediente.estado)) {
    const cerrado = expediente.estado === 'CERRADO';
    return <section className="card completitud-expediente terminal">
      <h3>{cerrado ? 'Expediente cerrado' : 'Expediente desistido'}</h3>
      <p>Fecha: <strong>{cerrado ? expediente.fecha_cierre : expediente.fecha_desistimiento}</strong></p>
      {!cerrado && <p>Motivo: <strong>{expediente.motivo_desistimiento}</strong></p>}
      <p>Registrado por: <strong>{cerrado ? expediente.usuario_registro_cierre : expediente.usuario_registro_desistimiento}</strong></p>
      <p>Registrado en SIGD-ST: <strong>{(() => {
        const valor = cerrado ? expediente.registrado_cierre_en : expediente.registrado_desistimiento_en;
        return valor ? new Date(valor).toLocaleString() : '—';
      })()}</strong></p>
      {error && <div className="notice error">{error}</div>}
      {modo !== 'archivo' && <button className="primary" type="button" onClick={() => setModo('archivo')}>Archivar expediente</button>}
      {modo === 'archivo' && <div className="completitud-confirmacion">
        <p>Confirme que este Expediente fue incorporado al archivo. Esta acción no modifica ni elimina las actuaciones registradas y no puede deshacerse desde el circuito ordinario.</p>
        <label>Fecha de archivo<input type="date" min={(cerrado ? expediente.fecha_cierre : expediente.fecha_desistimiento) || undefined} max={hoy()} value={fecha} onChange={(e) => setFecha(e.target.value)} /></label>
        <div className="actions"><button className="secondary" type="button" onClick={() => setModo(null)}>Cancelar</button><button className="primary" type="button" disabled={procesando || !fecha} onClick={() => void confirmar()}>{procesando ? 'Archivando...' : 'Confirmar archivo'}</button></div>
      </div>}
    </section>;
  }

  return <section className="card completitud-expediente">
    <div className="card-title"><div><span className="eyebrow">Completitud</span><h3>Completitud del Expediente</h3></div></div>
    {cargando && <p className="muted">Consultando completitud...</p>}
    {error && <div className="notice error">{error}</div>}
    {!cargando && cierre && cierre.cantidad_op > 0 && <>
      <div className="completitud-metricas"><span><strong>{cierre.cantidad_op}</strong> Órdenes de Pago</span><span><strong>{cierre.disposiciones_emitidas}</strong> Disposiciones emitidas</span><span><strong>{cierre.disposiciones_formalizadas}</strong> Formalizadas</span></div>
      {cierre.op_pendientes.length > 0 && <ul>{cierre.op_pendientes.map((op) => <li key={op.documento_op_id}>{op.nombre_archivo}: {op.causa === 'SIN_DISPOSICION' ? 'emitir Disposición' : 'formalizar Disposición'}</li>)}</ul>}
      <p>{cierre.mensaje}</p><small>{cierre.proxima_accion}</small>
      {cierre.habilitado && <button className="primary" type="button" onClick={() => setModo('cierre')}>Cerrar expediente</button>}
    </>}
    {!cargando && cierre?.cantidad_op === 0 && desistimiento && <>
      <p><strong>Sin Órdenes de Pago registradas.</strong></p><p>{desistimiento.mensaje}</p>
      {desistimiento.habilitado && <button className="secondary" type="button" onClick={() => setModo('desistimiento')}>Desistir expediente</button>}
    </>}
    {modo && <div className="completitud-confirmacion">
      <p>{modo === 'cierre' ? 'Confirmo que la contratación o intervención correspondiente a este Expediente se encuentra completa y que no se esperan nuevas Órdenes de Pago. Al cerrar el Expediente se bloquearán nuevas actuaciones administrativas.' : 'Confirme que la intervención no será ejecutada y que este Expediente no posee Órdenes de Pago. El Expediente quedará desistido y no admitirá nuevas actuaciones administrativas.'}</p>
      <label>Fecha<input type="date" max={hoy()} value={fecha} onChange={(e) => setFecha(e.target.value)} /></label>
      {modo === 'desistimiento' && <label>Motivo<textarea value={motivo} onChange={(e) => setMotivo(e.target.value)} required /></label>}
      {modo === 'cierre' && <label className="checkbox-row"><input type="checkbox" checked={confirmado} onChange={(e) => setConfirmado(e.target.checked)} /> Confirmo la completitud y que no se esperan nuevas OP.</label>}
      <div className="actions"><button className="secondary" type="button" onClick={() => setModo(null)}>Cancelar</button><button className="primary" type="button" disabled={procesando || !fecha || (modo === 'cierre' ? !confirmado : !motivo.trim())} onClick={() => void confirmar()}>{procesando ? 'Registrando...' : 'Confirmar'}</button></div>
    </div>}
  </section>;
}
