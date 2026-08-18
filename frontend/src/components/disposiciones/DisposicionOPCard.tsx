import { Download, FileSignature, RefreshCw, Save } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { API_URL } from '../../api/config';
import { consultarHabilitacionProveedorOP } from '../../api/controlProveedorOP';
import type { HabilitacionProveedorOP } from '../../api/controlProveedorOP';
import {
  emitirDisposicionOP,
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
};

const errorMensaje = (error: unknown) => (
  error instanceof Error ? error.message : 'No fue posible completar la operación.'
);

export function DisposicionOPCard({
  expedienteId,
  documentoOpId,
  nombreArchivo,
  revisionProveedor,
}: Props) {
  const consulta = useRef(0);
  const [habilitacion, setHabilitacion] = useState<HabilitacionProveedorOP | null>(null);
  const [borrador, setBorrador] = useState<DisposicionBorrador | null>(null);
  const [emitida, setEmitida] = useState<DisposicionEmitida | null>(null);
  const [numero, setNumero] = useState('');
  const [cargando, setCargando] = useState(true);
  const [procesando, setProcesando] = useState(false);
  const [error, setError] = useState('');

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

  const descargar = () => {
    if (!emitida) return;
    window.open(`${API_URL}/storage/${emitida.ruta_docx.replace(/^\/+/, '')}`, '_blank');
  };

  return (
    <section className="disposicion-op-card">
      <div className="disposicion-op-heading">
        <div><span className="eyebrow">Disposición de esta OP</span><strong>{nombreArchivo}</strong></div>
        {emitida && <span className="badge green">Emitida</span>}
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
          <button className="secondary" type="button" onClick={descargar}><Download />Descargar DOCX definitivo</button>
        </>
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
