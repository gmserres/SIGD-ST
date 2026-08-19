import { CheckCircle2, Download, FileSignature, RefreshCw, Save } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { API_URL } from '../../api/config';
import { consultarHabilitacionProveedorOP } from '../../api/controlProveedorOP';
import type { HabilitacionProveedorOP } from '../../api/controlProveedorOP';
import {
  emitirDisposicionOP,
  formalizarDisposicion,
  generarBorradorDisposicionOP,
  guardarBorradorDisposicionOP,
  obtenerDisposicionOP,
} from '../../api/disposiciones';
import type {
  DisposicionBorrador,
  DisposicionEmitida,
} from '../../api/disposiciones';

type Props = {
  expedienteId: string;
  documentoOpId: string;
  nombreArchivo: string;
  revisionProveedor: number;
  soloLectura?: boolean;
};

const errorMensaje = (error: unknown) => (
  error instanceof Error ? error.message : 'No fue posible completar la operación.'
);

const fechaLocalISO = () => {
  const hoy = new Date();
  const offset = hoy.getTimezoneOffset() * 60_000;
  return new Date(hoy.getTime() - offset).toISOString().slice(0, 10);
};

export function DisposicionOPCard({
  expedienteId,
  documentoOpId,
  nombreArchivo,
  revisionProveedor,
  soloLectura = false,
}: Props) {
  const consulta = useRef(0);
  const [habilitacion, setHabilitacion] = useState<HabilitacionProveedorOP | null>(null);
  const [borrador, setBorrador] = useState<DisposicionBorrador | null>(null);
  const [emitida, setEmitida] = useState<DisposicionEmitida | null>(null);
  const [numero, setNumero] = useState('');
  const [cargando, setCargando] = useState(true);
  const [procesando, setProcesando] = useState(false);
  const [error, setError] = useState('');
  const [confirmandoFormalizacion, setConfirmandoFormalizacion] = useState(false);
  const [fechaFormalizacion, setFechaFormalizacion] = useState(fechaLocalISO());

  const cargar = useCallback(async () => {
    const actual = ++consulta.current;
    setCargando(true);
    setError('');
    try {
      const [disposicion, estado] = await Promise.all([
        obtenerDisposicionOP(expedienteId, documentoOpId),
        consultarHabilitacionProveedorOP(expedienteId, documentoOpId),
      ]);
      if (actual !== consulta.current) return;
      setEmitida(disposicion);
      setHabilitacion(estado);
      if (disposicion) setNumero(disposicion.numero_disposicion);
    } catch (errorDesconocido) {
      if (actual === consulta.current) setError(errorMensaje(errorDesconocido));
    } finally {
      if (actual === consulta.current) setCargando(false);
    }
  }, [documentoOpId, expedienteId, revisionProveedor]);

  useEffect(() => { void cargar(); }, [cargar]);

  async function generar(regenerar = false) {
    setProcesando(true);
    setError('');
    try {
      setBorrador(await generarBorradorDisposicionOP(
        expedienteId, documentoOpId, regenerar,
      ));
    } catch (errorDesconocido) {
      setError(errorMensaje(errorDesconocido));
    } finally {
      setProcesando(false);
    }
  }

  async function guardar() {
    if (!borrador) return;
    setProcesando(true);
    try {
      setBorrador(await guardarBorradorDisposicionOP(
        expedienteId, documentoOpId, borrador,
      ));
    } catch (errorDesconocido) {
      setError(errorMensaje(errorDesconocido));
    } finally {
      setProcesando(false);
    }
  }

  async function emitir() {
    const normalizado = numero.trim();
    if (!normalizado) {
      setError('Ingresá el número institucional de la Disposición.');
      return;
    }
    setProcesando(true);
    setError('');
    try {
      setEmitida(await emitirDisposicionOP(
        expedienteId, documentoOpId, normalizado,
      ));
      setBorrador(null);
    } catch (errorDesconocido) {
      setError(errorMensaje(errorDesconocido));
      await cargar();
    } finally {
      setProcesando(false);
    }
  }

  async function formalizar() {
    if (!emitida || !fechaFormalizacion) return;
    setProcesando(true);
    setError('');
    try {
      setEmitida(await formalizarDisposicion(
        emitida.id_disposicion,
        fechaFormalizacion,
      ));
      setConfirmandoFormalizacion(false);
    } catch (errorDesconocido) {
      setError(errorMensaje(errorDesconocido));
      await cargar();
    } finally {
      setProcesando(false);
    }
  }

  const descargar = () => {
    if (!emitida) return;
    window.open(`${API_URL}/storage/${emitida.ruta_docx.replace(/^\/+/, '')}`, '_blank');
  };

  return (
    <section className="disposicion-op-card">
      <div className="disposicion-op-heading">
        <div><span className="eyebrow">Disposición de esta OP</span><strong>{nombreArchivo}</strong></div>
        {emitida && <span className="badge green">
          {emitida.estado_formalizacion === 'FORMALIZADA' ? 'Formalizada' : 'Emitida'}
        </span>}
      </div>
      {cargando ? <p className="empty">Consultando Disposición...</p> : emitida ? (
        <>
          <div className="disposicion-op-summary">
            <div><span>Número</span><strong>{emitida.numero_disposicion}</strong></div>
            <div><span>Fecha</span><strong>{new Date(emitida.fecha_emision).toLocaleString()}</strong></div>
            <div><span>OP</span><strong>{emitida.numero_op}</strong></div>
            <div><span>Proveedor</span><strong>{emitida.proveedor}</strong></div>
            <div><span>CUIT</span><strong>{emitida.cuit}</strong></div>
          </div>
          <div className="disposicion-op-formalizacion">
            {emitida.estado_formalizacion === 'FORMALIZADA' ? (
              <div className="notice success">
                <strong><CheckCircle2 />Disposición formalizada</strong>
                <span>Fecha: {emitida.fecha_formalizacion}</span>
                <span>Registrado por: {emitida.usuario_registro_formalizacion}</span>
                <span>Registrado en SIGD-ST: {emitida.registrado_formalizacion_en ? new Date(emitida.registrado_formalizacion_en).toLocaleString() : '—'}</span>
              </div>
            ) : (
              <>
                <p className="muted"><strong>Disposición emitida</strong> · Pendiente de formalización</p>
                {soloLectura ? null : !confirmandoFormalizacion ? (
                  <button className="primary" type="button" onClick={() => {
                    setFechaFormalizacion(fechaLocalISO());
                    setConfirmandoFormalizacion(true);
                  }}><FileSignature />Registrar formalización</button>
                ) : (
                  <div className="disposicion-op-confirmacion">
                    <p>Confirme que la Disposición N.º {emitida.numero_disposicion} fue incorporada al expediente papel y firmada. SIGD-ST registrará esta constancia administrativa; no realiza ni valida la firma.</p>
                    <label>Fecha de formalización<input type="date" min={emitida.fecha_emision.slice(0, 10)} max={fechaLocalISO()} value={fechaFormalizacion} onChange={(e) => setFechaFormalizacion(e.target.value)} /></label>
                    <div className="disposicion-op-actions">
                      <button className="secondary" type="button" disabled={procesando} onClick={() => setConfirmandoFormalizacion(false)}>Cancelar</button>
                      <button className="primary" type="button" disabled={procesando || !fechaFormalizacion} onClick={() => void formalizar()}>{procesando ? 'Registrando...' : 'Confirmar formalización'}</button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
          <button className="secondary" type="button" onClick={descargar}><Download />Descargar DOCX definitivo</button>
        </>
      ) : soloLectura ? (
        <p className="muted">El Expediente está finalizado. No admite nuevas actuaciones.</p>
      ) : habilitacion?.estado !== 'HABILITADO' ? (
        <div className="control-proveedor-op-message"><p>{habilitacion?.mensaje || 'La OP no está habilitada.'}</p><small>{habilitacion?.proxima_accion}</small></div>
      ) : !borrador ? (
        <button className="secondary" type="button" disabled={procesando} onClick={() => void generar()}>
          <FileSignature />{procesando ? 'Generando...' : 'Generar borrador de Disposición'}
        </button>
      ) : (
        <>
          <label>Número de Disposición<input value={numero} onChange={(e) => setNumero(e.target.value)} placeholder="Ejemplo: 148/2026" /></label>
          <label>VISTO<textarea value={borrador.visto} onChange={(e) => setBorrador({ ...borrador, visto: e.target.value })} /></label>
          <label>CONSIDERANDO<textarea value={borrador.considerando} onChange={(e) => setBorrador({ ...borrador, considerando: e.target.value })} /></label>
          <label>DISPONE<textarea value={borrador.dispone} onChange={(e) => setBorrador({ ...borrador, dispone: e.target.value })} /></label>
          <div className="disposicion-op-actions">
            <button className="secondary" type="button" disabled={procesando} onClick={() => void generar(true)}><RefreshCw />Regenerar</button>
            <button className="secondary" type="button" disabled={procesando} onClick={() => void guardar()}><Save />Guardar</button>
            <button className="primary" type="button" disabled={procesando || !numero.trim()} onClick={() => void emitir()}><FileSignature />{procesando ? 'Emitiendo...' : 'Emitir Disposición'}</button>
          </div>
        </>
      )}
      {error && <div className="notice error">{error}</div>}
    </section>
  );
}
