import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API_URL = 'http://localhost:8000';

type Pantalla = 'inicio' | 'nuevo' | 'expedientes' | 'detalle' | 'administracion';

type Expediente = {
  id: string;
  numero_interno: string;
  tipo_tramite: string;
  estado: string;
  establecimiento?: string | null;
  objeto?: string | null;
  numero_disposicion?: string | null;
  creado: string;
};

type Documento = {
  id: string;
  expediente_id: string;
  tipo: string;
  nombre_archivo: string;
  ruta: string;
  fecha_carga: string;
  observaciones?: string | null;
};

type Historial = {
  id: string;
  expediente_id: string;
  accion: string;
  usuario: string;
  fecha: string;
  detalle?: string | null;
};

type Validacion = {
  expediente_id: string;
  estado_general: string;
  errores: string[];
  advertencias: string[];
  controles: { control: string; estado: string; observacion?: string | null }[];
};

type AnalisisOP = {
  expediente_id: string;
  modo: string;
  op_detectada: boolean;
  proveedor: string | null;
  cuit: string | null;
  fondo: string | null;
  orden_pago: string | null;
  liquidacion: string | null;
  fecha_op: string | null;
  importe_bruto: number | null;
  importe_neto: number | null;
  valor_uc: number;
  norma_uc: string;
  cantidad_uc: number | null;
  procedimiento: string | null;
  encuadre_legal: string | null;
  documentos_comerciales: { tipo: string; letra: string; numero: string; fecha: string; importe: number }[];
  retenciones: { concepto: string; importe: number }[];
  validaciones: string[];
  advertencias: string[];
  faltantes: string[];
};

function moneda(valor: number | null) {
  if (valor === null || valor === undefined) return '-';
  return valor.toLocaleString('es-AR', { style: 'currency', currency: 'ARS' });
}

function etiquetaEstado(estado: string) {
  const mapa: Record<string, string> = {
    BORRADOR: 'Borrador',
    DOCUMENTACION_EN_CARGA: 'Documentación',
    PENDIENTE_VALIDACION: 'Pendiente',
    VALIDADO: 'Validado',
    DISPOSICION_EMITIDA: 'Disposición emitida',
    FIRMADO: 'Firmado',
    ARCHIVADO: 'Archivado',
  };
  return mapa[estado] || estado;
}

function claseEstado(estado: string) {
  if (['VALIDADO', 'DISPOSICION_EMITIDA', 'FIRMADO', 'ARCHIVADO'].includes(estado)) return 'badge green';
  if (['DOCUMENTACION_EN_CARGA', 'PENDIENTE_VALIDACION', 'BORRADOR'].includes(estado)) return 'badge yellow';
  return 'badge blue';
}

function claseValidacion(estado: string) {
  if (estado === 'OK') return 'badge green';
  if (estado === 'ADVERTENCIA') return 'badge yellow';
  return 'badge red';
}

function App() {
  const [pantalla, setPantalla] = useState<Pantalla>('inicio');
  const [expedientes, setExpedientes] = useState<Expediente[]>([]);
  const [seleccionado, setSeleccionado] = useState<Expediente | null>(null);
  const [documentos, setDocumentos] = useState<Documento[]>([]);
  const [historial, setHistorial] = useState<Historial[]>([]);
  const [analisis, setAnalisis] = useState<AnalisisOP | null>(null);
  const [validacion, setValidacion] = useState<Validacion | null>(null);
  const [mensaje, setMensaje] = useState('');

  const [numeroInterno, setNumeroInterno] = useState('033-188/2025');
  const [establecimiento, setEstablecimiento] = useState('EP N° 2');
  const [objeto, setObjeto] = useState('Recambio total de cañerías de agua fría');
  const [disposicion, setDisposicion] = useState('201/2025');

  const [archivoOP, setArchivoOP] = useState<File | null>(null);
  const [archivoDoc, setArchivoDoc] = useState<File | null>(null);
  const [tipoDoc, setTipoDoc] = useState('FACTURA');

  const metricas = useMemo(() => ({
    total: expedientes.length,
    pendientes: expedientes.filter(e => ['BORRADOR', 'DOCUMENTACION_EN_CARGA', 'PENDIENTE_VALIDACION'].includes(e.estado)).length,
    paraFirmar: expedientes.filter(e => e.estado === 'DISPOSICION_EMITIDA').length,
    emitidos: expedientes.filter(e => ['DISPOSICION_EMITIDA', 'FIRMADO', 'ARCHIVADO'].includes(e.estado)).length,
  }), [expedientes]);

  async function cargarExpedientes() {
    const res = await fetch(`${API_URL}/expedientes`);
    setExpedientes(await res.json());
  }

  async function cargarDetalle(expediente: Expediente) {
    setSeleccionado(expediente);
    setPantalla('detalle');

    const [docsRes, histRes] = await Promise.all([
      fetch(`${API_URL}/expedientes/${expediente.id}/documentos`),
      fetch(`${API_URL}/expedientes/${expediente.id}/historial`),
    ]);

    setDocumentos(await docsRes.json());
    setHistorial(await histRes.json());
  }

  async function refrescarDetalleActual() {
    if (!seleccionado) return;
    const res = await fetch(`${API_URL}/expedientes/${seleccionado.id}`);
    const exp = await res.json();
    await cargarExpedientes();
    await cargarDetalle(exp);
  }

  async function crearExpediente() {
    setMensaje('');
    const res = await fetch(`${API_URL}/expedientes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ numero_interno: numeroInterno, establecimiento, objeto, numero_disposicion: disposicion }),
    });

    const creado = await res.json();
    await cargarExpedientes();
    setMensaje(`Expediente ${creado.numero_interno} creado correctamente.`);
    await cargarDetalle(creado);
  }

  async function subirOP() {
    if (!seleccionado || !archivoOP) {
      setMensaje('Seleccioná un archivo PDF de Orden de Pago.');
      return;
    }

    const form = new FormData();
    form.append('file', archivoOP);

    const res = await fetch(`${API_URL}/expedientes/${seleccionado.id}/documentos/op`, { method: 'POST', body: form });

    if (!res.ok) {
      setMensaje('No se pudo cargar la OP.');
      return;
    }

    setArchivoOP(null);
    setMensaje('Orden de Pago cargada correctamente.');
    await refrescarDetalleActual();
  }

  async function subirDocumento() {
    if (!seleccionado || !archivoDoc) {
      setMensaje('Seleccioná un documento.');
      return;
    }

    const form = new FormData();
    form.append('tipo', tipoDoc);
    form.append('file', archivoDoc);

    const res = await fetch(`${API_URL}/expedientes/${seleccionado.id}/documentos/upload`, { method: 'POST', body: form });

    if (!res.ok) {
      setMensaje('No se pudo cargar el documento.');
      return;
    }

    setArchivoDoc(null);
    setMensaje('Documento cargado correctamente.');
    await refrescarDetalleActual();
  }

  async function analizarOP() {
    if (!seleccionado) return;
    const res = await fetch(`${API_URL}/expedientes/${seleccionado.id}/analizar-op`, { method: 'POST' });
    const data = await res.json();
    setAnalisis(data);
    setMensaje(data.op_detectada ? 'Orden de Pago analizada correctamente.' : 'No se encontró OP cargada para analizar.');
    await refrescarDetalleActual();
  }

  async function consultarValidacion() {
    if (!seleccionado) return;
    const res = await fetch(`${API_URL}/expedientes/${seleccionado.id}/validacion`);
    setValidacion(await res.json());
    await refrescarDetalleActual();
  }

  async function validarExpediente() {
    if (!seleccionado) return;
    const res = await fetch(`${API_URL}/expedientes/${seleccionado.id}/validar`, { method: 'POST' });
    const actualizado = await res.json();
    await cargarExpedientes();
    await cargarDetalle(actualizado);
  }

  async function generarDisposicion() {
    if (!seleccionado) return;
    const res = await fetch(`${API_URL}/expedientes/${seleccionado.id}/generar-disposicion`, { method: 'POST' });

    if (!res.ok) {
      const error = await res.json();
      setMensaje(error.detail || 'No se pudo generar la disposición.');
      return;
    }

    const actualizado = await res.json();
    await cargarExpedientes();
    await cargarDetalle(actualizado);
  }

  useEffect(() => {
    cargarExpedientes();
  }, []);

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">▣</div>
          <div><h1>SIGD-ST</h1><p>Consejo Escolar<br />General Alvarado</p></div>
        </div>

        <button className="new-button" onClick={() => setPantalla('nuevo')}>+ Nuevo Expediente</button>

        <nav>
          <button className={pantalla === 'inicio' ? 'active' : ''} onClick={() => setPantalla('inicio')}>Inicio</button>
          <button className={pantalla === 'expedientes' ? 'active' : ''} onClick={() => setPantalla('expedientes')}>Mis Expedientes</button>
          <button>Fondo Compensador</button>
          <button>SAE</button>
          <button>Infraestructura</button>
          <button>Transporte</button>
          <button className={pantalla === 'administracion' ? 'active' : ''} onClick={() => setPantalla('administracion')}>Administración</button>
        </nav>

        <div className="version">Versión Alfa 0.6.0</div>
      </aside>

      <section className="content">
        <header className="topbar">
          <div>
            <h2>{pantalla === 'inicio' ? 'Inicio' : pantalla === 'nuevo' ? 'Nuevo Expediente' : pantalla === 'detalle' ? 'Ficha del Expediente' : pantalla === 'administracion' ? 'Administración' : 'Mis Expedientes'}</h2>
            <span>Secretaría Técnica</span>
          </div>
          <div className="user">Gonzalo · Secretario Técnico</div>
        </header>

        {mensaje && <div className="notice">{mensaje}</div>}

        {pantalla === 'inicio' && (
          <>
            <section className="metrics">
              <div className="metric-card"><span>📁</span><strong>{metricas.total}</strong><p>Expedientes en trámite</p></div>
              <div className="metric-card"><span>🕒</span><strong>{metricas.pendientes}</strong><p>Pendientes</p></div>
              <div className="metric-card"><span>✍️</span><strong>{metricas.paraFirmar}</strong><p>Actos para firmar</p></div>
              <div className="metric-card"><span>✅</span><strong>{metricas.emitidos}</strong><p>Actos emitidos</p></div>
            </section>

            <section className="grid-two">
              <div className="card">
                <div className="card-title"><h3>Mis expedientes recientes</h3><button className="link" onClick={() => setPantalla('expedientes')}>Ver todos</button></div>
                <ExpedientesTabla expedientes={expedientes.slice(0, 5)} abrir={cargarDetalle} />
              </div>

              <div className="card">
                <h3>Asistente del Expediente</h3>
                <div className="assistant-box">
                  <p>✓ Gestión documental habilitada.</p>
                  <p>✓ Análisis IA Alfa disponible.</p>
                  <p>✓ Validaciones mínimas disponibles.</p>
                  <p>⚠ Generación documental completa pendiente.</p>
                </div>
                <button className="primary" onClick={() => setPantalla('nuevo')}>Crear expediente</button>
              </div>
            </section>
          </>
        )}

        {pantalla === 'nuevo' && (
          <section className="card form-card">
            <h3>Datos iniciales del expediente</h3>

            <label>Tipo de trámite</label>
            <select defaultValue="FONDO_COMPENSADOR">
              <option value="FONDO_COMPENSADOR">Fondo Compensador</option>
              <option value="SAE" disabled>SAE - Próximamente</option>
              <option value="INFRAESTRUCTURA" disabled>Infraestructura - Próximamente</option>
            </select>

            <label>Expediente interno</label>
            <input value={numeroInterno} onChange={(e) => setNumeroInterno(e.target.value)} />

            <label>Número de disposición</label>
            <input value={disposicion} onChange={(e) => setDisposicion(e.target.value)} />

            <label>Establecimiento</label>
            <input value={establecimiento} onChange={(e) => setEstablecimiento(e.target.value)} />

            <label>Objeto</label>
            <textarea value={objeto} onChange={(e) => setObjeto(e.target.value)} />

            <button className="primary" onClick={crearExpediente}>Crear expediente</button>
          </section>
        )}

        {pantalla === 'expedientes' && (
          <section className="card">
            <h3>Mis Expedientes</h3>
            <ExpedientesTabla expedientes={expedientes} abrir={cargarDetalle} />
          </section>
        )}

        {pantalla === 'detalle' && seleccionado && (
          <section className="detail-layout">
            <div className="card">
              <div className="card-title">
                <h3>Expediente {seleccionado.numero_interno}</h3>
                <span className={claseEstado(seleccionado.estado)}>{etiquetaEstado(seleccionado.estado)}</span>
              </div>

              <dl className="data-list">
                <dt>ID interno</dt><dd>{seleccionado.id}</dd>
                <dt>Tipo</dt><dd>{seleccionado.tipo_tramite}</dd>
                <dt>Disposición</dt><dd>{seleccionado.numero_disposicion || '-'}</dd>
                <dt>Establecimiento</dt><dd>{seleccionado.establecimiento || '-'}</dd>
                <dt>Objeto</dt><dd>{seleccionado.objeto || '-'}</dd>
              </dl>

              <div className="actions">
                <button className="primary" onClick={analizarOP}>Analizar OP</button>
                <button className="secondary" onClick={consultarValidacion}>Ver validación</button>
                <button className="primary" onClick={validarExpediente}>Validar expediente</button>
                <button className="primary" onClick={generarDisposicion}>Generar disposición</button>
              </div>
            </div>

            <div className="card">
              <h3>Cargar documentación</h3>
              <div className="upload-box">
                <strong>Orden de Pago</strong>
                <input type="file" accept=".pdf" onChange={(e) => setArchivoOP(e.target.files?.[0] || null)} />
                <button className="secondary" onClick={subirOP}>Cargar OP</button>
              </div>

              <div className="upload-box">
                <strong>Otro documento</strong>
                <select value={tipoDoc} onChange={(e) => setTipoDoc(e.target.value)}>
                  <option value="FACTURA">Factura</option>
                  <option value="REMITO">Remito</option>
                  <option value="CONFORMIDAD">Conformidad</option>
                  <option value="ARCA">ARCA</option>
                  <option value="ARBA">ARBA</option>
                  <option value="ACTA_RECEPCION">Acta de Recepción</option>
                  <option value="OTRO">Otro</option>
                </select>
                <input type="file" onChange={(e) => setArchivoDoc(e.target.files?.[0] || null)} />
                <button className="secondary" onClick={subirDocumento}>Cargar documento</button>
              </div>
            </div>

            {validacion && (
              <div className="card full">
                <div className="card-title">
                  <h3>Validación del expediente</h3>
                  <span className={validacion.estado_general === 'VERDE' ? 'badge green' : validacion.estado_general === 'AMARILLO' ? 'badge yellow' : 'badge red'}>{validacion.estado_general}</span>
                </div>
                <table>
                  <thead><tr><th>Control</th><th>Estado</th><th>Observación</th></tr></thead>
                  <tbody>
                    {validacion.controles.map((c, i) => (
                      <tr key={i}>
                        <td>{c.control}</td>
                        <td><span className={claseValidacion(c.estado)}>{c.estado}</span></td>
                        <td>{c.observacion || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {analisis && (
              <div className="card full">
                <div className="card-title">
                  <h3>Análisis IA de Orden de Pago</h3>
                  <span className={analisis.op_detectada ? 'badge green' : 'badge yellow'}>{analisis.modo}</span>
                </div>

                {!analisis.op_detectada ? (
                  <p className="empty">No existe OP cargada para analizar.</p>
                ) : (
                  <>
                    <div className="analysis-grid">
                      <div><strong>Proveedor</strong><p>{analisis.proveedor}</p></div>
                      <div><strong>CUIT</strong><p>{analisis.cuit}</p></div>
                      <div><strong>Fondo</strong><p>{analisis.fondo}</p></div>
                      <div><strong>Liquidación</strong><p>{analisis.liquidacion}</p></div>
                      <div><strong>Importe bruto</strong><p>{moneda(analisis.importe_bruto)}</p></div>
                      <div><strong>Importe neto</strong><p>{moneda(analisis.importe_neto)}</p></div>
                      <div><strong>UC</strong><p>{analisis.cantidad_uc}</p></div>
                      <div><strong>Procedimiento</strong><p>{analisis.procedimiento}</p></div>
                    </div>
                  </>
                )}
              </div>
            )}

            <div className="card full">
              <h3>Documentos asociados</h3>
              {documentos.length === 0 ? <p className="empty">Sin documentos cargados.</p> : (
                <table>
                  <thead><tr><th>Tipo</th><th>Archivo</th><th>Fecha</th><th>Acción</th></tr></thead>
                  <tbody>
                    {documentos.map(doc => (
                      <tr key={doc.id}>
                        <td>{doc.tipo}</td>
                        <td>{doc.nombre_archivo}</td>
                        <td>{new Date(doc.fecha_carga).toLocaleString()}</td>
                        <td><a className="small-link" href={`${API_URL}/expedientes/${seleccionado.id}/documentos/${doc.id}/descargar`} target="_blank">Abrir / descargar</a></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <div className="card full">
              <h3>Historial</h3>
              {historial.length === 0 ? <p className="empty">Sin actividad registrada.</p> : (
                <table>
                  <thead><tr><th>Fecha</th><th>Usuario</th><th>Acción</th><th>Detalle</th></tr></thead>
                  <tbody>
                    {historial.map(h => (
                      <tr key={h.id}><td>{new Date(h.fecha).toLocaleString()}</td><td>{h.usuario}</td><td>{h.accion}</td><td>{h.detalle || '-'}</td></tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </section>
        )}

        {pantalla === 'administracion' && (
          <section className="card">
            <h3>Administración</h3>
            <div className="admin-grid">
              <div><strong>Usuarios</strong><p>Administrador, Secretario Técnico, Operador, Consulta.</p></div>
              <div><strong>Unidad de Contratación</strong><p>$1.677 · Resolución OPC Nº 54/2025.</p></div>
              <div><strong>Plantillas</strong><p>Disposición FC, Checklist, Actas.</p></div>
              <div><strong>Catálogos</strong><p>Proveedores y establecimientos.</p></div>
            </div>
          </section>
        )}
      </section>
    </main>
  );
}

function ExpedientesTabla({ expedientes, abrir }: { expedientes: Expediente[], abrir: (exp: Expediente) => void }) {
  if (expedientes.length === 0) return <p className="empty">Todavía no hay expedientes cargados.</p>;

  return (
    <table>
      <thead><tr><th>Expediente</th><th>Área</th><th>Estado</th><th>Establecimiento</th><th></th></tr></thead>
      <tbody>
        {expedientes.map((exp) => (
          <tr key={exp.id}>
            <td>{exp.numero_interno}</td>
            <td>Fondo Comp.</td>
            <td><span className={claseEstado(exp.estado)}>{etiquetaEstado(exp.estado)}</span></td>
            <td>{exp.establecimiento || '-'}</td>
            <td><button className="small-button" onClick={() => abrir(exp)}>Abrir</button></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

createRoot(document.getElementById('root')!).render(<App />);
