import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API_URL = 'http://localhost:8000';

type Pantalla = 'inicio' | 'nuevo' | 'expedientes' | 'detalle' | 'administracion';
type TabDetalle = 'resumen' | 'documentos' | 'ia' | 'validacion' | 'disposicion' | 'historial';

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
  tamano_bytes?: number | null;
  mime_type?: string | null;
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

type Disposicion = {
  expediente_id: string;
  numero_disposicion: string | null;
  estado: string;
  visto: string;
  considerando: string;
  dispone: string;
  observaciones_ia: string[];
  creado: string;
  actualizado: string;
};

type ChecklistFisico = {
  expediente_id?: string;
  factura: boolean;
  remito_conformidad: boolean;
  cae: boolean;
  arca: boolean;
  arba: boolean;
  observaciones?: string | null;
  usuario?: string;
  fecha?: string;
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

function moneda(valor: number | null | undefined) {
  if (valor === null || valor === undefined) return '-';
  return valor.toLocaleString('es-AR', { style: 'currency', currency: 'ARS' });
}

function bytes(valor?: number | null) {
  if (!valor) return '-';
  if (valor < 1024) return `${valor} B`;
  if (valor < 1024 * 1024) return `${(valor / 1024).toFixed(1)} KB`;
  return `${(valor / 1024 / 1024).toFixed(1)} MB`;
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

function fueValidadoConObservaciones(historial: Historial[]) {
  return historial.some(h => h.accion === 'EXPEDIENTE_VALIDADO_CON_OBSERVACIONES');
}

function estadoAdministrativo(exp: Expediente, historial: Historial[]) {
  if (exp.estado === 'VALIDADO' && fueValidadoConObservaciones(historial)) {
    return { texto: 'Validado con observaciones', clase: 'badge yellow' };
  }
  if (exp.estado === 'VALIDADO') return { texto: 'Validado', clase: 'badge green' };
  if (exp.estado === 'DISPOSICION_EMITIDA') return { texto: 'Disposición emitida', clase: 'badge green' };
  return { texto: etiquetaEstado(exp.estado), clase: claseEstado(exp.estado) };
}

function claseValidacion(estado: string) {
  if (estado === 'OK') return 'badge green';
  if (estado === 'ADVERTENCIA') return 'badge yellow';
  return 'badge red';
}

function diagnosticoIA(analisis: AnalisisOP | null) {
  if (!analisis || !analisis.op_detectada) {
    return { color: 'rojo', etiqueta: 'Sin análisis documental', riesgo: 'ALTO', porcentaje: 0, resumen: 'Todavía no hay datos suficientes para emitir un diagnóstico.', recomendacion: 'Cargar una Orden de Pago y ejecutar el análisis documental.', accion: 'Analizar documentación' };
  }

  const checks = [
    !!analisis.proveedor,
    !!analisis.cuit,
    !!analisis.importe_bruto,
    !!analisis.importe_neto,
    analisis.documentos_comerciales.length > 0,
    analisis.retenciones.length > 0,
    !analisis.faltantes.includes('Remito o conformidad firmada'),
    !analisis.faltantes.includes('Validación CAE'),
    !analisis.faltantes.includes('Certificado Fiscal ARBA'),
    !analisis.faltantes.includes('Constancia ARCA'),
  ];

  const completados = checks.filter(Boolean).length;
  const porcentaje = Math.round((completados / checks.length) * 100);
  const tieneEconomia = analisis.documentos_comerciales.length > 0 && !!analisis.importe_bruto;
  const faltantesCriticos = analisis.faltantes.length;

  if (porcentaje >= 85 && faltantesCriticos <= 1) {
    return { color: 'verde', etiqueta: 'Puede continuar', riesgo: 'BAJO', porcentaje, resumen: `He analizado la OP ${analisis.orden_pago || ''} y no observo inconsistencias económicas relevantes.`, recomendacion: 'Puede avanzar a revisión final si la documentación respaldatoria está completa.', accion: 'Continuar trámite' };
  }

  if (tieneEconomia) {
    return { color: 'amarillo', etiqueta: 'Completar documentación', riesgo: 'MEDIO', porcentaje, resumen: `He interpretado la OP ${analisis.orden_pago || ''}. Las facturas detectadas son consistentes con el monto total, pero todavía hay documentación pendiente.`, recomendacion: 'Solicitar o cargar los faltantes antes de emitir disposición.', accion: 'Completar documentación' };
  }

  return { color: 'rojo', etiqueta: 'Requiere revisión', riesgo: 'ALTO', porcentaje, resumen: 'No cuento con información suficiente para recomendar el avance del expediente.', recomendacion: 'Revisar la documentación cargada antes de continuar.', accion: 'Revisión documental' };
}


function sumarFacturas(analisis: AnalisisOP | null) {
  if (!analisis) return null;
  return analisis.documentos_comerciales.reduce((acc, doc) => acc + doc.importe, 0);
}

function comparacionDocumental(analisis: AnalisisOP | null) {
  if (!analisis || !analisis.op_detectada || !analisis.importe_bruto) {
    return {
      estado: 'Sin datos',
      color: 'rojo',
      totalOp: null as number | null,
      totalFacturas: null as number | null,
      diferencia: null as number | null,
      mensaje: 'No hay información suficiente para comparar OP y facturas.',
    };
  }

  const totalFacturas = sumarFacturas(analisis);

  if (!totalFacturas) {
    return {
      estado: 'Pendiente',
      color: 'amarillo',
      totalOp: analisis.importe_bruto,
      totalFacturas: null as number | null,
      diferencia: null as number | null,
      mensaje: 'No se detectaron facturas liquidadas para comparar.',
    };
  }

  const diferencia = Math.round((totalFacturas - analisis.importe_bruto) * 100) / 100;

  if (Math.abs(diferencia) <= 1) {
    return {
      estado: 'Consistente',
      color: 'verde',
      totalOp: analisis.importe_bruto,
      totalFacturas,
      diferencia: 0,
      mensaje: 'La suma de facturas coincide con el monto total de la OP.',
    };
  }

  return {
    estado: 'Inconsistente',
    color: 'rojo',
    totalOp: analisis.importe_bruto,
    totalFacturas,
    diferencia,
    mensaje: 'La suma de facturas no coincide con el monto total de la OP.',
  };
}

function confiabilidadIA(analisis: AnalisisOP | null) {
  if (!analisis || !analisis.op_detectada) return { valor: 0, prioridad: 'ALTA' };

  let puntaje = 0;
  if (analisis.op_detectada) puntaje += 15;
  if (analisis.proveedor) puntaje += 10;
  if (analisis.cuit) puntaje += 10;
  if (analisis.importe_bruto) puntaje += 10;
  if (analisis.importe_neto) puntaje += 10;
  if (analisis.documentos_comerciales.length > 0) puntaje += 15;

  const comp = comparacionDocumental(analisis);
  if (comp.estado === 'Consistente') puntaje += 20;
  if (analisis.retenciones.length > 0) puntaje += 5;

  puntaje = Math.max(0, Math.min(100, puntaje - Math.min(analisis.faltantes.length * 3, 15)));

  let prioridad = 'BAJA';
  if (comp.estado === 'Inconsistente' || puntaje < 45) prioridad = 'ALTA';
  else if (analisis.faltantes.length >= 3 || puntaje < 80) prioridad = 'MEDIA';

  return { valor: puntaje, prioridad };
}


async function obtenerMensajeError(res: Response) {
  try {
    const data = await res.json();
    if (typeof data.detail === 'string') return data.detail;
    if (data.detail?.mensaje) {
      const errores = data.detail.errores?.length ? ` ${data.detail.errores.join(' ')}` : '';
      const advertencias = data.detail.advertencias?.length ? ` ${data.detail.advertencias.join(' ')}` : '';
      return `${data.detail.mensaje}${errores}${advertencias}`;
    }
    return 'Ocurrió un error.';
  } catch {
    return 'Ocurrió un error.';
  }
}

function App() {
  const [pantalla, setPantalla] = useState<Pantalla>('inicio');
  const [tabDetalle, setTabDetalle] = useState<TabDetalle>('resumen');
  const [expedientes, setExpedientes] = useState<Expediente[]>([]);
  const [seleccionado, setSeleccionado] = useState<Expediente | null>(null);
  const [documentos, setDocumentos] = useState<Documento[]>([]);
  const [historial, setHistorial] = useState<Historial[]>([]);
  const [analisis, setAnalisis] = useState<AnalisisOP | null>(null);
  const [validacion, setValidacion] = useState<Validacion | null>(null);
  const [disposicionBorrador, setDisposicionBorrador] = useState<Disposicion | null>(null);
  const [checklistFisico, setChecklistFisico] = useState<ChecklistFisico>({ factura: false, remito_conformidad: false, cae: false, arca: false, arba: false, observaciones: '' });
  const [mostrarChecklistFisico, setMostrarChecklistFisico] = useState(false);
  const [mensaje, setMensaje] = useState('');
  const [mensajeTipo, setMensajeTipo] = useState<'ok' | 'error' | 'info'>('info');

  const [numeroInterno, setNumeroInterno] = useState('033-188/2025');
  const [establecimiento, setEstablecimiento] = useState('EP N° 2');
  const [objeto, setObjeto] = useState('Recambio total de cañerías de agua fría');
  const [disposicion, setDisposicion] = useState('201/2025');

  const [archivoOP, setArchivoOP] = useState<File | null>(null);
  const [archivoDoc, setArchivoDoc] = useState<File | null>(null);
  const [tipoDoc, setTipoDoc] = useState('FACTURA');
  const [motivoObservacion, setMotivoObservacion] = useState('');

  const metricas = useMemo(() => {
    const pendientes = expedientes.filter(e => ['BORRADOR', 'DOCUMENTACION_EN_CARGA', 'PENDIENTE_VALIDACION'].includes(e.estado));
    const paraFirmar = expedientes.filter(e => e.estado === 'DISPOSICION_EMITIDA');
    const validados = expedientes.filter(e => e.estado === 'VALIDADO');
    return {
      total: expedientes.length,
      pendientes: pendientes.length,
      paraFirmar: paraFirmar.length,
      validados: validados.length,
      recientes: expedientes.slice(-5).reverse(),
      requiereAccion: expedientes.filter(e => ['BORRADOR', 'DOCUMENTACION_EN_CARGA'].includes(e.estado)).slice(0, 6),
    };
  }, [expedientes]);

  function avisar(texto: string, tipo: 'ok' | 'error' | 'info' = 'info') {
    setMensaje(texto);
    setMensajeTipo(tipo);
  }

  async function cargarExpedientes() {
    const res = await fetch(`${API_URL}/expedientes`);
    setExpedientes(await res.json());
  }

  async function cargarDetalle(expediente: Expediente) {
    setSeleccionado(expediente);
    setPantalla('detalle');
    setTabDetalle('resumen');
    setAnalisis(null);
    setMensaje('');

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
    avisar('', 'info');
    const res = await fetch(`${API_URL}/expedientes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ numero_interno: numeroInterno, establecimiento, objeto, numero_disposicion: disposicion }),
    });

    if (!res.ok) {
      avisar(await obtenerMensajeError(res), 'error');
      return;
    }

    const creado = await res.json();
    await cargarExpedientes();
    avisar(`Expediente ${creado.numero_interno} creado correctamente.`, 'ok');
    await cargarDetalle(creado);
  }

  async function subirOP() {
    if (!seleccionado || !archivoOP) {
      avisar('Seleccioná un archivo PDF de Orden de Pago.', 'error');
      return;
    }

    const form = new FormData();
    form.append('file', archivoOP);

    const res = await fetch(`${API_URL}/expedientes/${seleccionado.id}/documentos/op`, { method: 'POST', body: form });

    if (!res.ok) {
      avisar(await obtenerMensajeError(res), 'error');
      return;
    }

    setArchivoOP(null);
    avisar('Orden de Pago cargada correctamente.', 'ok');
    await refrescarDetalleActual();
  }

  async function subirDocumento() {
    if (!seleccionado || !archivoDoc) {
      avisar('Seleccioná un documento.', 'error');
      return;
    }

    const form = new FormData();
    form.append('tipo', tipoDoc);
    form.append('file', archivoDoc);

    const res = await fetch(`${API_URL}/expedientes/${seleccionado.id}/documentos/upload`, { method: 'POST', body: form });

    if (!res.ok) {
      avisar(await obtenerMensajeError(res), 'error');
      return;
    }

    setArchivoDoc(null);
    avisar('Documento cargado correctamente.', 'ok');
    await refrescarDetalleActual();
  }

  async function analizarOP() {
    if (!seleccionado) return;
    const res = await fetch(`${API_URL}/expedientes/${seleccionado.id}/analizar-op`, { method: 'POST' });
    const data = await res.json();
    setAnalisis(data);
    setTabDetalle('ia');
    avisar(data.op_detectada ? 'Orden de Pago analizada correctamente.' : 'No se encontró OP cargada para analizar.', data.op_detectada ? 'ok' : 'error');
  }

  async function consultarValidacion() {
    if (!seleccionado) return;
    const res = await fetch(`${API_URL}/expedientes/${seleccionado.id}/validacion`);
    setValidacion(await res.json());
    setTabDetalle('validacion');
  }

  async function cargarChecklistFisico() {
    if (!seleccionado) return;
    const res = await fetch(`${API_URL}/expedientes/${seleccionado.id}/checklist-fisico`);
    if (res.ok) {
      const data = await res.json();
      if (data) setChecklistFisico(data);
    }
    setMostrarChecklistFisico(true);
  }

  async function guardarChecklistFisico() {
    if (!seleccionado) return;

    const res = await fetch(`${API_URL}/expedientes/${seleccionado.id}/checklist-fisico`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...checklistFisico, usuario: 'Secretario Técnico' }),
    });

    if (!res.ok) {
      avisar(await obtenerMensajeError(res), 'error');
      return;
    }

    const data = await res.json();
    setChecklistFisico(data);
    setMostrarChecklistFisico(false);
    avisar('Checklist físico registrado. La validación fue actualizada.', 'ok');
    await consultarValidacion();
    await cargarExpedientes();
  }

  async function validarExpediente() {
    if (!seleccionado) return;
    const res = await fetch(`${API_URL}/expedientes/${seleccionado.id}/validar`, { method: 'POST' });

    if (!res.ok) {
      avisar(await obtenerMensajeError(res), 'error');
      await consultarValidacion();
      return;
    }

    const actualizado = await res.json();
    avisar('Expediente validado correctamente.', 'ok');
    await cargarExpedientes();
    await cargarDetalle(actualizado);
  }

  async function validarConObservaciones() {
    if (!seleccionado) return;

    if (motivoObservacion.trim().length < 10) {
      avisar('Ingresá un motivo administrativo de al menos 10 caracteres.', 'error');
      return;
    }

    const res = await fetch(`${API_URL}/expedientes/${seleccionado.id}/validar-con-observaciones`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ motivo: motivoObservacion, usuario: 'Secretario Técnico' }),
    });

    if (!res.ok) {
      avisar(await obtenerMensajeError(res), 'error');
      await consultarValidacion();
      return;
    }

    const actualizado = await res.json();
    setMotivoObservacion('');
    avisar('Expediente validado con observaciones. La decisión quedó registrada en historial.', 'ok');
    await cargarExpedientes();
    await cargarDetalle(actualizado);
  }

  async function prepararDisposicion(regenerar = false) {
    if (!seleccionado) return;
    const res = await fetch(`${API_URL}/expedientes/${seleccionado.id}/disposicion/borrador?regenerar=${regenerar}`, { method: 'POST' });

    if (!res.ok) {
      avisar(await obtenerMensajeError(res), 'error');
      return;
    }

    const data = await res.json();
    setDisposicionBorrador(data);
    setTabDetalle('disposicion');
    avisar('Borrador de disposición generado correctamente.', 'ok');
  }

  async function guardarBorradorDisposicion() {
    if (!seleccionado || !disposicionBorrador) return;
    const res = await fetch(`${API_URL}/expedientes/${seleccionado.id}/disposicion/borrador`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        visto: disposicionBorrador.visto,
        considerando: disposicionBorrador.considerando,
        dispone: disposicionBorrador.dispone,
      }),
    });

    if (!res.ok) {
      avisar(await obtenerMensajeError(res), 'error');
      return;
    }

    const data = await res.json();
    setDisposicionBorrador(data);
    avisar('Borrador guardado correctamente.', 'ok');
  }


  async function generarDisposicion() {
    if (!seleccionado) return;
    const res = await fetch(`${API_URL}/expedientes/${seleccionado.id}/generar-disposicion`, { method: 'POST' });

    if (!res.ok) {
      avisar(await obtenerMensajeError(res), 'error');
      await consultarValidacion();
      return;
    }

    const actualizado = await res.json();
    avisar('Disposición emitida correctamente.', 'ok');
    await cargarExpedientes();
    await cargarDetalle(actualizado);
  }

  function abrirVistaPrevia(doc: Documento) {
    if (!seleccionado) return;
    window.open(`${API_URL}/expedientes/${seleccionado.id}/documentos/${doc.id}/vista-previa`, '_blank');
  }

  useEffect(() => {
    cargarExpedientes();
  }, []);

  const diag = diagnosticoIA(analisis);
  const comparacion = comparacionDocumental(analisis);
  const confiabilidad = confiabilidadIA(analisis);

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">▣</div>
          <div><h1>SIGD-ST</h1><p>Consejo Escolar<br />General Alvarado</p></div>
        </div>

        <button className="new-button" onClick={() => setPantalla('nuevo')}>+ Nuevo Expediente</button>

        <nav>
          <button className={pantalla === 'inicio' ? 'active' : ''} onClick={() => setPantalla('inicio')}>Bandeja</button>
          <button className={pantalla === 'expedientes' ? 'active' : ''} onClick={() => setPantalla('expedientes')}>Expedientes</button>
          <button>Fondo Compensador</button>
          <button>SAE</button>
          <button>Infraestructura</button>
          <button>Transporte</button>
          <button className={pantalla === 'administracion' ? 'active' : ''} onClick={() => setPantalla('administracion')}>Administración</button>
        </nav>

        <div className="version">Versión Alfa 0.25</div>
      </aside>

      <section className="content">
        <header className="topbar">
          <div>
            <h2>{pantalla === 'inicio' ? 'Bandeja de trabajo' : pantalla === 'nuevo' ? 'Nuevo Expediente' : pantalla === 'detalle' ? 'Expediente Inteligente' : pantalla === 'administracion' ? 'Administración' : 'Expedientes'}</h2>
            <span>Secretaría Técnica</span>
          </div>
          <div className="user">Gonzalo · Secretario Técnico</div>
        </header>

        {mensaje && <div className={`notice ${mensajeTipo}`}>{mensaje}</div>}

        {pantalla === 'inicio' && (
          <>
            <section className="metrics">
              <div className="metric-card"><span>📁</span><strong>{metricas.total}</strong><p>Expedientes</p></div>
              <div className="metric-card"><span>🕒</span><strong>{metricas.pendientes}</strong><p>Requieren acción</p></div>
              <div className="metric-card"><span>✅</span><strong>{metricas.validados}</strong><p>Validados</p></div>
              <div className="metric-card"><span>✍️</span><strong>{metricas.paraFirmar}</strong><p>Para firma</p></div>
            </section>

            <section className="dashboard-grid">
              <div className="card work-queue">
                <div className="card-title">
                  <h3>Bandeja de pendientes</h3>
                  <button className="link" onClick={() => setPantalla('expedientes')}>Ver todos</button>
                </div>
                {metricas.requiereAccion.length === 0 ? (
                  <p className="empty">No hay expedientes pendientes.</p>
                ) : (
                  metricas.requiereAccion.map(exp => (
                    <button className="queue-item" key={exp.id} onClick={() => cargarDetalle(exp)}>
                      <div>
                        <strong>{exp.numero_interno}</strong>
                        <p>{exp.establecimiento || 'Sin establecimiento'} · {exp.objeto || 'Sin objeto'}</p>
                      </div>
                      <span className={claseEstado(exp.estado)}>{etiquetaEstado(exp.estado)}</span>
                    </button>
                  ))
                )}
              </div>

              <div className="card">
                <h3>Asistente del Secretario Técnico</h3>
                <div className="assistant-box">
                  <p>✓ IA documental con facturas y retenciones.</p>
                  <p>✓ Diagnóstico automático del expediente.</p>
                  <p>✓ Semáforo documental inicial.</p>
                  <p>✓ Recomendaciones administrativas.</p>
                  <p>✓ Comparador documental y confiabilidad.</p>
                  <p>✓ Validación inteligente con bloqueos.</p>
                  <p>✓ Evidencias por archivo, checklist o dato automático.</p>
                  <p>✓ Checklist físico en etapa de validación.</p>
                </div>
                <button className="primary" onClick={() => setPantalla('nuevo')}>Crear expediente</button>
              </div>
            </section>

            <section className="card">
              <h3>Actividad reciente</h3>
              <ExpedientesTabla expedientes={metricas.recientes} abrir={cargarDetalle} />
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
            <h3>Expedientes</h3>
            <ExpedientesTabla expedientes={expedientes} abrir={cargarDetalle} />
          </section>
        )}

        {pantalla === 'detalle' && seleccionado && (
          <section className="expediente-page">
            <div className="expediente-header">
              <div>
                <span className="eyebrow">Expediente</span>
                <h2>{seleccionado.numero_interno}</h2>
                <p>{seleccionado.establecimiento || '-'} · {seleccionado.objeto || '-'}</p>
              </div>
              <span className={estadoAdministrativo(seleccionado, historial).clase}>{estadoAdministrativo(seleccionado, historial).texto}</span>
            </div>

            <div className="expediente-layout">
              <aside className="expediente-side">
                <button className={tabDetalle === 'resumen' ? 'active' : ''} onClick={() => setTabDetalle('resumen')}>Resumen</button>
                <button className={tabDetalle === 'documentos' ? 'active' : ''} onClick={() => setTabDetalle('documentos')}>Documentos</button>
                <button className={tabDetalle === 'ia' ? 'active' : ''} onClick={() => setTabDetalle('ia')}>IA documental</button>
                <button className={tabDetalle === 'validacion' ? 'active' : ''} onClick={consultarValidacion}>Validación</button>
                <button className={tabDetalle === 'disposicion' ? 'active' : ''} onClick={() => setTabDetalle('disposicion')}>Disposición</button>
                <button className={tabDetalle === 'historial' ? 'active' : ''} onClick={() => setTabDetalle('historial')}>Historial</button>
              </aside>

              <section className="expediente-main">
                {tabDetalle === 'resumen' && (
                  <div className="card">
                    <div className="card-title">
                      <h3>Resumen operativo</h3>
                      <span className="badge blue">Fondo Compensador</span>
                    </div>
                    <dl className="data-list">
                      <dt>ID interno</dt><dd>{seleccionado.id}</dd>
                      <dt>Disposición</dt><dd>{seleccionado.numero_disposicion || '-'}</dd>
                      <dt>Documentos</dt><dd>{documentos.length}</dd>
                      <dt>Última acción</dt><dd>{historial[historial.length - 1]?.accion || '-'}</dd>
                    </dl>
                    <div className="actions">
                      <button className="primary" onClick={analizarOP}>Analizar OP</button>
                      <button className="secondary" onClick={consultarValidacion}>Ver validación</button>
                      {!['VALIDADO', 'DISPOSICION_EMITIDA'].includes(seleccionado.estado) && (
                        <button className="primary" onClick={validarExpediente}>Validar expediente</button>
                      )}
                      {seleccionado.estado === 'VALIDADO' && (
                        <button className="primary" onClick={() => prepararDisposicion(false)}>Generar borrador de disposición</button>
                      )}
                      {seleccionado.estado === 'DISPOSICION_EMITIDA' && (
                        <button className="secondary" onClick={() => setTabDetalle('disposicion')}>Ver disposición</button>
                      )}
                    </div>
                    <div className="flow-note">
                      La validación ahora verifica documentación crítica antes de permitir avanzar.
                    </div>
                  </div>
                )}

                {tabDetalle === 'documentos' && (
                  <div className="card">
                    <h3>Documentación del expediente</h3>
                    <div className="upload-grid">
                      <div className="upload-box">
                        <strong>Orden de Pago</strong>
                        <input type="file" accept=".pdf" onChange={(e) => setArchivoOP(e.target.files?.[0] || null)} />
                        <button className="secondary" onClick={subirOP}>Cargar OP</button>
                      </div>
                      <div className="upload-box">
                        <strong>Documento complementario</strong>
                        <select value={tipoDoc} onChange={(e) => setTipoDoc(e.target.value)}>
                          <option value="FACTURA">Factura</option>
                          <option value="REMITO">Remito</option>
                          <option value="CONFORMIDAD">Conformidad</option>
                          <option value="CAE">CAE</option>
                          <option value="ARCA">ARCA</option>
                          <option value="ARBA">ARBA</option>
                          <option value="ACTA_RECEPCION">Acta de Recepción</option>
                          <option value="CHECK_FACTURA">Checklist Facturas verificadas</option>
                          <option value="CHECK_REMITO">Checklist Remito / Conformidad</option>
                          <option value="CHECK_CAE">Checklist CAE</option>
                          <option value="CHECK_ARCA">Checklist ARCA</option>
                          <option value="CHECK_ARBA">Checklist ARBA</option>
                          <option value="OTRO">Otro</option>
                        </select>
                        <input type="file" onChange={(e) => setArchivoDoc(e.target.files?.[0] || null)} />
                        <button className="secondary" onClick={subirDocumento}>Cargar documento</button>
                      </div>
                    </div>

                    {documentos.length === 0 ? <p className="empty">Sin documentos cargados.</p> : (
                      <table>
                        <thead><tr><th>Tipo</th><th>Archivo</th><th>Tamaño</th><th>Fecha</th><th>Acción</th></tr></thead>
                        <tbody>
                          {documentos.map(doc => (
                            <tr key={doc.id}>
                              <td><span className="badge blue">{doc.tipo}</span></td>
                              <td>{doc.nombre_archivo}</td>
                              <td>{bytes(doc.tamano_bytes)}</td>
                              <td>{new Date(doc.fecha_carga).toLocaleString()}</td>
                              <td>
                                <button className="small-button" onClick={() => abrirVistaPrevia(doc)}>Vista previa</button>
                                <a className="small-link" href={`${API_URL}/expedientes/${seleccionado.id}/documentos/${doc.id}/descargar`} target="_blank">Descargar</a>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                )}

                {tabDetalle === 'ia' && (
                  <div className="card">
                    <div className="card-title">
                      <h3>IA documental</h3>
                      <button className="primary" onClick={analizarOP}>Ejecutar análisis</button>
                    </div>
                    {!analisis ? (
                      <p className="empty">Ejecutá el análisis para ver el resumen inteligente del expediente.</p>
                    ) : !analisis.op_detectada ? (
                      <div className="warning-panel">No existe OP cargada para analizar.</div>
                    ) : (
                      <>
                        <div className={`assistant-panel ${diag.color}`}>
                          <div className="assistant-main">
                            <span className="eyebrow">Asistente Administrativo Inteligente</span>
                            <h3>{diag.etiqueta}</h3>
                            <p>{diag.resumen}</p>
                            <div className="assistant-summary">
                              <p>✓ Proveedor: {analisis.proveedor || 'No detectado'}</p>
                              <p>✓ CUIT: {analisis.cuit || 'No detectado'}</p>
                              <p>✓ Facturas detectadas: {analisis.documentos_comerciales.length}</p>
                              <p>✓ Retenciones detectadas: {analisis.retenciones.length}</p>
                              <p>⚠ Faltantes: {analisis.faltantes.length}</p>
                            </div>
                            <strong>Recomendación: {diag.recomendacion}</strong>
                          </div>

                          <div className="assistant-side">
                            <div className={`risk-pill ${diag.color}`}>Riesgo {diag.riesgo}</div>
                            <div className="progress-number">{diag.porcentaje}%</div>
                            <div className="progress-track"><div style={{ width: `${diag.porcentaje}%` }} /></div>
                            <span>avance documental</span>
                            <div className="action-box">{diag.accion}</div>
                          </div>
                        </div>

                        <div className="intelligence-grid">
                          <div className={`intel-card ${comparacion.color}`}>
                            <span className="eyebrow">Comparador documental</span>
                            <h4>{comparacion.estado}</h4>
                            <p>{comparacion.mensaje}</p>
                            <dl>
                              <dt>Total OP</dt><dd>{moneda(comparacion.totalOp)}</dd>
                              <dt>Total facturas</dt><dd>{moneda(comparacion.totalFacturas)}</dd>
                              <dt>Diferencia</dt><dd>{moneda(comparacion.diferencia)}</dd>
                            </dl>
                          </div>

                          <div className="intel-card blue">
                            <span className="eyebrow">Confiabilidad documental</span>
                            <h4>{confiabilidad.valor}%</h4>
                            <div className="progress-track"><div style={{ width: `${confiabilidad.valor}%` }} /></div>
                            <p>Prioridad de revisión: <strong>{confiabilidad.prioridad}</strong></p>
                          </div>
                        </div>

                        <div className="analysis-grid">
                          <div><strong>Proveedor</strong><p>{analisis.proveedor}</p></div>
                          <div><strong>CUIT</strong><p>{analisis.cuit}</p></div>
                          <div><strong>Fondo</strong><p>{analisis.fondo}</p></div>
                          <div><strong>Liquidación</strong><p>{analisis.liquidacion || '-'}</p></div>
                          <div><strong>OP</strong><p>{analisis.orden_pago || '-'}</p></div>
                          <div><strong>Fecha OP</strong><p>{analisis.fecha_op || '-'}</p></div>
                          <div><strong>Importe bruto</strong><p>{moneda(analisis.importe_bruto)}</p></div>
                          <div><strong>Importe neto</strong><p>{moneda(analisis.importe_neto)}</p></div>
                          <div><strong>UC</strong><p>{analisis.cantidad_uc}</p></div>
                          <div><strong>Procedimiento</strong><p>{analisis.procedimiento}</p></div>
                        </div>

                        <div className="subcard">
                          <h4>Checklist inteligente</h4>
                          <div className="checklist-grid">
                            <p className={analisis.op_detectada ? 'ok' : 'warn'}>{analisis.op_detectada ? '✓' : '□'} OP cargada</p>
                            <p className={analisis.proveedor ? 'ok' : 'warn'}>{analisis.proveedor ? '✓' : '□'} Proveedor</p>
                            <p className={analisis.cuit ? 'ok' : 'warn'}>{analisis.cuit ? '✓' : '□'} CUIT</p>
                            <p className={analisis.documentos_comerciales.length ? 'ok' : 'warn'}>{analisis.documentos_comerciales.length ? '✓' : '□'} Facturas liquidadas</p>
                            <p className={!analisis.faltantes.includes('Remito o conformidad firmada') ? 'ok' : 'warn'}>{!analisis.faltantes.includes('Remito o conformidad firmada') ? '✓' : '□'} Remito / conformidad</p>
                            <p className={!analisis.faltantes.includes('Validación CAE') ? 'ok' : 'warn'}>{!analisis.faltantes.includes('Validación CAE') ? '✓' : '□'} CAE</p>
                            <p className={!analisis.faltantes.includes('Certificado Fiscal ARBA') ? 'ok' : 'warn'}>{!analisis.faltantes.includes('Certificado Fiscal ARBA') ? '✓' : '□'} ARBA</p>
                            <p className={!analisis.faltantes.includes('Constancia ARCA') ? 'ok' : 'warn'}>{!analisis.faltantes.includes('Constancia ARCA') ? '✓' : '□'} ARCA</p>
                          </div>
                        </div>


                        <div className="subcard evidence-card">
                          <h4>Evidencias verificadas</h4>
                          <p className="muted">
                            El sistema controla si el requisito está acreditado: archivo, checklist o dato automático de la OP.
                          </p>
                          <div className="evidence-grid">
                            <p className="ok">✓ OP <span>PDF cargado</span></p>
                            <p className={analisis.proveedor ? 'ok' : 'warn'}>{analisis.proveedor ? '✓' : '□'} Proveedor <span>Dato OP</span></p>
                            <p className={analisis.cuit ? 'ok' : 'warn'}>{analisis.cuit ? '✓' : '□'} CUIT <span>Dato OP</span></p>
                            <p className={analisis.documentos_comerciales.length ? 'ok' : 'warn'}>{analisis.documentos_comerciales.length ? '✓' : '□'} Facturas <span>{analisis.documentos_comerciales.length ? 'Detectadas en OP' : 'Archivo o checklist'}</span></p>
                            <p className={!analisis.faltantes.includes('Remito o conformidad firmada') ? 'ok' : 'warn'}>{!analisis.faltantes.includes('Remito o conformidad firmada') ? '✓' : '□'} Remito / conformidad <span>Archivo o checklist</span></p>
                            <p className={!analisis.faltantes.includes('Validación CAE') ? 'ok' : 'warn'}>{!analisis.faltantes.includes('Validación CAE') ? '✓' : '□'} CAE <span>Consulta, archivo o checklist</span></p>
                            <p className={!analisis.faltantes.includes('Certificado Fiscal ARBA') ? 'ok' : 'warn'}>{!analisis.faltantes.includes('Certificado Fiscal ARBA') ? '✓' : '□'} ARBA <span>Archivo o checklist</span></p>
                            <p className={!analisis.faltantes.includes('Constancia ARCA') ? 'ok' : 'warn'}>{!analisis.faltantes.includes('Constancia ARCA') ? '✓' : '□'} ARCA <span>Archivo o checklist</span></p>
                          </div>
                          <div className="info-note">
                            Las retenciones son informativas: las calcula el sistema que emite la OP y no requieren carga documental separada.
                          </div>
                        </div>

                        {analisis.documentos_comerciales.length > 0 && (
                          <div className="subcard">
                            <h4>Facturas liquidadas</h4>
                            <table>
                              <thead><tr><th>Tipo</th><th>Número</th><th>Fecha</th><th>Importe</th></tr></thead>
                              <tbody>
                                {analisis.documentos_comerciales.map((doc, i) => (
                                  <tr key={i}>
                                    <td>{doc.tipo} {doc.letra}</td>
                                    <td>{doc.numero}</td>
                                    <td>{doc.fecha}</td>
                                    <td>{moneda(doc.importe)}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}

                        {analisis.retenciones.length > 0 && (
                          <div className="subcard">
                            <h4>Retenciones detectadas</h4>
                            <table>
                              <thead><tr><th>Concepto</th><th>Importe</th></tr></thead>
                              <tbody>
                                {analisis.retenciones.map((ret, i) => (
                                  <tr key={i}>
                                    <td>{ret.concepto}</td>
                                    <td>{moneda(ret.importe)}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}

                        <div className="validation-columns">
                          <div>
                            <h4>Validaciones</h4>
                            {analisis.validaciones.map((v, i) => <p key={i} className="ok">✓ {v}</p>)}
                          </div>
                          <div>
                            <h4>Faltantes</h4>
                            {analisis.faltantes.map((f, i) => <p key={i} className="warn">⚠ {f}</p>)}
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                )}

                {tabDetalle === 'validacion' && (
                  <div className="card">
                    <div className="card-title">
                      <h3>Validación administrativa</h3>
                      {validacion && <span className={validacion.estado_general === 'VERDE' ? 'badge green' : validacion.estado_general === 'AMARILLO' ? 'badge yellow' : 'badge red'}>{validacion.estado_general}</span>}
                    </div>
                    {!validacion ? (
                      <p className="empty">Presioná “Ver validación” para ejecutar los controles.</p>
                    ) : (
                      <>
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

                        {validacion.estado_general === 'VERDE' && (
                          <div className="validation-action-panel green-panel">
                            <h4>Expediente apto para validar</h4>
                            <p>No se detectan errores ni observaciones relevantes.</p>
                            <button className="primary" onClick={validarExpediente}>Validar expediente</button>
                          </div>
                        )}

                        {validacion.estado_general === 'AMARILLO' && (
                          <div className="validation-action-panel yellow-panel">
                            <h4>Validación con observaciones</h4>
                            <p>Existen evidencias pendientes. Si la documentación existe en el expediente físico, podés acreditarla mediante checklist y volver a consultar la validación.</p>
                            <button className="secondary" onClick={cargarChecklistFisico}>Acreditar documentación física</button>

                            <div className="observation-box">
                              <p>Si aun así corresponde avanzar con observaciones, ingresá el motivo administrativo.</p>
                              <textarea
                                value={motivoObservacion}
                                onChange={(e) => setMotivoObservacion(e.target.value)}
                                placeholder="Ejemplo: Se continúa con observaciones porque la documentación será incorporada posteriormente."
                              />
                              <button className="primary" onClick={validarConObservaciones}>Validar con observaciones</button>
                            </div>
                          </div>
                        )}

                        {validacion.estado_general === 'ROJO' && (
                          <div className="validation-action-panel red-panel">
                            <h4>Validación bloqueada</h4>
                            <p>Existen errores críticos que deben corregirse antes de continuar.</p>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                )}

                {tabDetalle === 'disposicion' && (
                  <div className="card">
                    <div className="card-title">
                      <h3>Editor de disposición</h3>
                      <span className="badge yellow">{disposicionBorrador?.estado || 'BORRADOR IA'}</span>
                    </div>

                    {!disposicionBorrador ? (
                      <div className="empty-disposition">
                        <p className="empty">Todavía no hay borrador generado para este expediente.</p>
                        {seleccionado.estado === 'VALIDADO' ? (
                          <button className="primary" onClick={() => prepararDisposicion(false)}>Generar borrador</button>
                        ) : (
                          <p className="warn">El expediente debe estar validado antes de generar la disposición.</p>
                        )}
                      </div>
                    ) : (
                      <div className="disposition-editor">
                        <div className="disposition-main">
                          <h4>DISPOSICIÓN Nº {disposicionBorrador.numero_disposicion || '____/____'}</h4>

                          <label>VISTO</label>
                          <textarea value={disposicionBorrador.visto} onChange={(e) => setDisposicionBorrador({ ...disposicionBorrador, visto: e.target.value })} />

                          <label>CONSIDERANDO</label>
                          <textarea value={disposicionBorrador.considerando} onChange={(e) => setDisposicionBorrador({ ...disposicionBorrador, considerando: e.target.value })} />

                          <label>EL CUERPO DE CONSEJEROS ESCOLARES DE GRAL. ALVARADO DISPONE</label>
                          <textarea value={disposicionBorrador.dispone} onChange={(e) => setDisposicionBorrador({ ...disposicionBorrador, dispone: e.target.value })} />

                          <div className="actions">
                            <button className="secondary" onClick={() => prepararDisposicion(true)}>Regenerar borrador</button>
                            <button className="primary" onClick={guardarBorradorDisposicion}>Guardar borrador</button>
                            {seleccionado.estado === 'VALIDADO' && <button className="primary" onClick={generarDisposicion}>Emitir disposición</button>}
                          </div>
                        </div>

                        <aside className="disposition-aside">
                          <h4>Observaciones IA</h4>
                          {disposicionBorrador.observaciones_ia.map((obs, i) => <p key={i} className="warn">⚠ {obs}</p>)}
                          {fueValidadoConObservaciones(historial) && (
                            <div className="info-note">Este expediente fue validado con observaciones. Revisá el historial antes de emitir.</div>
                          )}
                          <div className="info-note">La exportación a Word/PDF queda preparada para el próximo sprint.</div>
                        </aside>
                      </div>
                    )}
                  </div>
                )}

                {tabDetalle === 'historial' && (
                  <div className="card">
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
                )}
              </section>
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
      {mostrarChecklistFisico && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <div className="card-title">
              <h3>Checklist de existencia física</h3>
              <button className="small-button" onClick={() => setMostrarChecklistFisico(false)}>Cerrar</button>
            </div>
            <p className="muted">Marcá los documentos que obran físicamente en el expediente papel. Esto acredita la evidencia sin cargar el PDF.</p>

            <label className="check-row">
              <input type="checkbox" checked={checklistFisico.factura} onChange={(e) => setChecklistFisico({ ...checklistFisico, factura: e.target.checked })} />
              Facturas verificadas en expediente físico
            </label>
            <label className="check-row">
              <input type="checkbox" checked={checklistFisico.remito_conformidad} onChange={(e) => setChecklistFisico({ ...checklistFisico, remito_conformidad: e.target.checked })} />
              Remito / conformidad / acta de recepción obrante
            </label>
            <label className="check-row">
              <input type="checkbox" checked={checklistFisico.cae} onChange={(e) => setChecklistFisico({ ...checklistFisico, cae: e.target.checked })} />
              CAE verificado
            </label>
            <label className="check-row">
              <input type="checkbox" checked={checklistFisico.arca} onChange={(e) => setChecklistFisico({ ...checklistFisico, arca: e.target.checked })} />
              Constancia ARCA obrante
            </label>
            <label className="check-row">
              <input type="checkbox" checked={checklistFisico.arba} onChange={(e) => setChecklistFisico({ ...checklistFisico, arba: e.target.checked })} />
              Certificado Fiscal ARBA obrante
            </label>

            <label>Observaciones del operador</label>
            <textarea value={checklistFisico.observaciones || ''} onChange={(e) => setChecklistFisico({ ...checklistFisico, observaciones: e.target.value })} placeholder="Detalle cómo fue verificada la documentación física." />

            <div className="actions">
              <button className="secondary" onClick={() => setMostrarChecklistFisico(false)}>Cancelar</button>
              <button className="primary" onClick={guardarChecklistFisico}>Guardar checklist</button>
            </div>
          </div>
        </div>
      )}
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
