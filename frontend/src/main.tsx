import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API_URL = 'http://localhost:8000';
const procedenciasDisponibles = [
  'SUNA',
  'MESA DE ENTRADA',
  'CORREO ELECTRÓNICO',
  'OTRA',
];
const fondosIntervinientesDisponibles = [
  'FONDO_COMPENSADOR',
  'CUFP',
  'OTRO',
];

type Pantalla = 'inicio' | 'nuevo' | 'expedientes' | 'detalle' | 'solicitudes' | 'administracion';
type TabDetalle = 'workflow' | 'documentos' | 'ia' | 'validacion' | 'disposicion' | 'historial';

const CONTROLES_OBLIGATORIOS_VALIDACION = new Set([
  'Expediente interno',
  'Establecimiento',
  'Objeto',
]);

type Expediente = {
  id: string;
  numero_interno: string;
  numero_gdeba?: string | null;
  id_suna?: string | null;
  tipo_tramite: string;
  estado: string;
  establecimiento?: string | null;
  objeto?: string | null;
  numero_disposicion?: string | null;
  solicitud_intervencion_id?: string | null;
  decision_administrativa_id?: string | null;
  creado: string;
};

type SolicitudIntervencion = {
  id_solicitud: string;
  numero_solicitud: string;
  procedencia: string;
  id_suna: string | null;
  fecha_ingreso: string;
  establecimiento: string;
  solicitante: string;
  motivo: string;
  prioridad: string;
  estado: string;
};

type EvaluacionAdministrativa = {
  id_evaluacion: string;
  solicitud_intervencion_id: string;
  fecha_inicio: string;
  evaluador: string;
  observaciones: string;
};

type DecisionAdministrativa = {
  id_decision: string;
  solicitud_intervencion_id: string;
  autoridad_decisora: string;
  fecha_decision: string;
  resultado: string;
  fundamento: string;
  fondo_interviniente: 'FONDO_COMPENSADOR' | 'CUFP' | 'OTRO' | null;
  descripcion_fondo: string | null;
  usuario_registrante: string;
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

function etiquetaFondoInterviniente(fondo: string | null) {
  const etiquetas: Record<string, string> = {
    FONDO_COMPENSADOR: 'Fondo Compensador',
    CUFP: 'CUFP',
    OTRO: 'Otro',
  };
  return fondo ? etiquetas[fondo] || fondo : 'No determinado';
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

function iconoValidacion(estado: string) {
  if (estado === 'OK') return '✓';
  if (estado === 'ADVERTENCIA') return '!';
  return '×';
}

function etiquetaValidacion(estado: string) {
  if (estado === 'OK') return 'Cumplido';
  if (estado === 'ADVERTENCIA') return 'Advertencia';
  return 'Error bloqueante';
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
    if (Array.isArray(data.detail)) {
      const mensajes = data.detail.map((item: { msg?: string }) => item.msg).filter(Boolean);
      if (mensajes.length) return mensajes.join(' ');
    }
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
  const [tabDetalle, setTabDetalle] = useState<TabDetalle>('workflow');
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
  const [solicitudes, setSolicitudes] = useState<SolicitudIntervencion[]>([]);
  const [solicitudSeleccionada, setSolicitudSeleccionada] = useState<SolicitudIntervencion | null>(null);
  const [solicitudOrigenExpediente, setSolicitudOrigenExpediente] = useState<SolicitudIntervencion | null>(null);
  const [decisionOrigenExpediente, setDecisionOrigenExpediente] = useState<DecisionAdministrativa | null>(null);
  const [cargandoSolicitudes, setCargandoSolicitudes] = useState(false);
  const [guardandoSolicitud, setGuardandoSolicitud] = useState(false);
  const [errorSolicitudes, setErrorSolicitudes] = useState('');

  const [evaluaciones, setEvaluaciones] = useState<EvaluacionAdministrativa[]>([]);
  const [cargandoEvaluaciones, setCargandoEvaluaciones] = useState(false);
  const [guardandoEvaluacion, setGuardandoEvaluacion] = useState(false);
  const [errorEvaluaciones, setErrorEvaluaciones] = useState('');
  const [evaluacionFechaInicio, setEvaluacionFechaInicio] = useState('');
  const [evaluacionEvaluador, setEvaluacionEvaluador] = useState('');
  const [evaluacionObservaciones, setEvaluacionObservaciones] = useState('');

  const [decisiones, setDecisiones] = useState<DecisionAdministrativa[]>([]);
  const [cargandoDecisiones, setCargandoDecisiones] = useState(false);
  const [guardandoDecision, setGuardandoDecision] = useState(false);
  const [errorDecisiones, setErrorDecisiones] = useState('');
  const [decisionAutoridad, setDecisionAutoridad] = useState('');
  const [decisionFecha, setDecisionFecha] = useState('');
  const [decisionResultado, setDecisionResultado] = useState('');
  const [decisionFundamento, setDecisionFundamento] = useState('');
  const [decisionFondoInterviniente, setDecisionFondoInterviniente] = useState('');
  const [decisionDescripcionFondo, setDecisionDescripcionFondo] = useState('');
  const [decisionUsuarioRegistrante, setDecisionUsuarioRegistrante] = useState('');
  const [decisionRecienCreadaId, setDecisionRecienCreadaId] = useState<string | null>(null);

  const [decisionExpedienteActiva, setDecisionExpedienteActiva] = useState<string | null>(null);
  const [expedienteDecisionNumeroInterno, setExpedienteDecisionNumeroInterno] = useState('');
  const [expedienteDecisionNumeroGdeba, setExpedienteDecisionNumeroGdeba] = useState('');
  const [guardandoExpedienteDecision, setGuardandoExpedienteDecision] = useState(false);
  const [errorExpedienteDecision, setErrorExpedienteDecision] = useState('');

  const [catalogoEvaluadores, setCatalogoEvaluadores] = useState<string[]>([]);
  const [catalogoAutoridadesDecisoras, setCatalogoAutoridadesDecisoras] = useState<string[]>([]);
  const [catalogoResultadosDecision, setCatalogoResultadosDecision] = useState<string[]>([]);

  const [solicitudProcedencia, setSolicitudProcedencia] = useState('');
  const [solicitudIdSuna, setSolicitudIdSuna] = useState('');
  const [solicitudFechaIngreso, setSolicitudFechaIngreso] = useState('');
  const [solicitudEstablecimiento, setSolicitudEstablecimiento] = useState('');
  const [solicitudSolicitante, setSolicitudSolicitante] = useState('');
  const [solicitudMotivo, setSolicitudMotivo] = useState('');
  const [solicitudPrioridad, setSolicitudPrioridad] = useState('');

  const [numeroInterno, setNumeroInterno] = useState('033-188/2025');
  const [numeroGdeba, setNumeroGdeba] = useState('');
  const [idSuna, setIdSuna] = useState('45872');
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

  const metricasSolicitudes = useMemo(() => {
    const solicitudesConExpediente = new Set(
      expedientes
        .map((expediente) => expediente.solicitud_intervencion_id)
        .filter((solicitudId): solicitudId is string => Boolean(solicitudId)),
    );
    const pendientes = solicitudes.filter(
      (solicitud) => !solicitudesConExpediente.has(solicitud.id_solicitud),
    );

    return {
      total: solicitudes.length,
      pendientes,
      conIdSuna: solicitudes.filter((solicitud) => Boolean(solicitud.id_suna)).length,
      conExpediente: solicitudesConExpediente.size,
      recientes: solicitudes.slice(-5).reverse(),
    };
  }, [solicitudes, expedientes]);

  function avisar(texto: string, tipo: 'ok' | 'error' | 'info' = 'info') {
    setMensaje(texto);
    setMensajeTipo(tipo);
  }

  async function cargarCatalogosIntervencion() {
    async function cargarCatalogo(
      ruta: string,
      asignar: (valores: string[]) => void,
    ) {
      try {
        const res = await fetch(`${API_URL}${ruta}`);
        if (!res.ok) return;
        asignar(await res.json());
      } catch {
        asignar([]);
      }
    }

    await Promise.all([
      cargarCatalogo('/catalogos/evaluadores', setCatalogoEvaluadores),
      cargarCatalogo('/catalogos/autoridades-decisoras', setCatalogoAutoridadesDecisoras),
      cargarCatalogo('/catalogos/resultados-decision', setCatalogoResultadosDecision),
    ]);
  }

  async function cargarExpedientes() {
    const res = await fetch(`${API_URL}/expedientes`);
    setExpedientes(await res.json());
  }

  async function cargarSolicitudes() {
    setCargandoSolicitudes(true);
    setErrorSolicitudes('');

    try {
      const res = await fetch(`${API_URL}/solicitudes`);
      if (!res.ok) {
        setErrorSolicitudes(await obtenerMensajeError(res));
        return;
      }
      setSolicitudes(await res.json());
    } catch {
      setErrorSolicitudes('No se pudo conectar con el backend para consultar las solicitudes.');
    } finally {
      setCargandoSolicitudes(false);
    }
  }

  async function cargarEvaluaciones(solicitudId: string) {
    setCargandoEvaluaciones(true);
    setErrorEvaluaciones('');

    try {
      const res = await fetch(`${API_URL}/evaluaciones`);
      if (!res.ok) {
        setErrorEvaluaciones(await obtenerMensajeError(res));
        return;
      }

      const disponibles: EvaluacionAdministrativa[] = await res.json();
      setEvaluaciones(
        disponibles.filter(
          (evaluacion) => evaluacion.solicitud_intervencion_id === solicitudId,
        ),
      );
    } catch {
      setErrorEvaluaciones(
        'No se pudo conectar con el backend para consultar las evaluaciones.',
      );
    } finally {
      setCargandoEvaluaciones(false);
    }
  }

  async function cargarDecisiones(solicitudId: string) {
    setCargandoDecisiones(true);
    setErrorDecisiones('');

    try {
      const res = await fetch(`${API_URL}/decisiones`);
      if (!res.ok) {
        setErrorDecisiones(await obtenerMensajeError(res));
        return;
      }

      const disponibles: DecisionAdministrativa[] = await res.json();
      setDecisiones(
        disponibles.filter(
          (decision) => decision.solicitud_intervencion_id === solicitudId,
        ),
      );
    } catch {
      setErrorDecisiones(
        'No se pudo conectar con el backend para consultar las decisiones.',
      );
    } finally {
      setCargandoDecisiones(false);
    }
  }

  async function abrirSolicitudes() {
    setPantalla('solicitudes');
    setMensaje('');
    await Promise.all([
      cargarSolicitudes(),
      solicitudSeleccionada
        ? cargarEvaluaciones(solicitudSeleccionada.id_solicitud)
        : Promise.resolve(),
      solicitudSeleccionada
        ? cargarDecisiones(solicitudSeleccionada.id_solicitud)
        : Promise.resolve(),
    ]);
  }

  async function seleccionarSolicitud(solicitud: SolicitudIntervencion) {
    setPantalla('solicitudes');
    setSolicitudSeleccionada(solicitud);
    setMensaje('');
    await Promise.all([
      cargarEvaluaciones(solicitud.id_solicitud),
      cargarDecisiones(solicitud.id_solicitud),
    ]);
  }

  async function abrirSolicitudDesdeBandeja(
    solicitud: SolicitudIntervencion,
  ) {
    await seleccionarSolicitud(solicitud);
  }

  async function abrirNuevaSolicitud() {
    setPantalla('solicitudes');
    setSolicitudSeleccionada(null);
    setEvaluaciones([]);
    setDecisiones([]);
    setSolicitudProcedencia('');
    setSolicitudIdSuna('');
    setSolicitudFechaIngreso('');
    setSolicitudEstablecimiento('');
    setSolicitudSolicitante('');
    setSolicitudMotivo('');
    setSolicitudPrioridad('');
    setErrorSolicitudes('');
    setMensaje('');
    await cargarSolicitudes();
  }

  async function crearSolicitud(evento: React.FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setGuardandoSolicitud(true);
    setErrorSolicitudes('');
    setMensaje('');

    try {
      const ejercicio = new Date().getFullYear();
      const patronNumeroSolicitud = new RegExp(`^SOL-${ejercicio}-(\\d{6})$`);
      const mayorCorrelativo = solicitudes.reduce((mayor, solicitud) => {
        const coincidencia = solicitud.numero_solicitud.match(patronNumeroSolicitud);
        return coincidencia
          ? Math.max(mayor, Number(coincidencia[1]))
          : mayor;
      }, 0);
      const numeroSolicitud = `SOL-${ejercicio}-${String(
        mayorCorrelativo + 1,
      ).padStart(6, '0')}`;
      const res = await fetch(`${API_URL}/solicitudes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          numero_solicitud: numeroSolicitud,
          procedencia: solicitudProcedencia,
          id_suna: solicitudIdSuna || null,
          fecha_ingreso: solicitudFechaIngreso,
          establecimiento: solicitudEstablecimiento,
          solicitante: solicitudSolicitante,
          motivo: solicitudMotivo,
          prioridad: solicitudPrioridad,
        }),
      });

      if (!res.ok) {
        setErrorSolicitudes(await obtenerMensajeError(res));
        return;
      }

      const creada: SolicitudIntervencion = await res.json();
      setSolicitudes((actuales) => [...actuales, creada]);
      setSolicitudSeleccionada(creada);
      await Promise.all([
        cargarEvaluaciones(creada.id_solicitud),
        cargarDecisiones(creada.id_solicitud),
      ]);
      setSolicitudProcedencia('');
      setSolicitudIdSuna('');
      setSolicitudFechaIngreso('');
      setSolicitudEstablecimiento('');
      setSolicitudSolicitante('');
      setSolicitudMotivo('');
      setSolicitudPrioridad('');
      avisar(`Solicitud ${creada.numero_solicitud} registrada correctamente.`, 'ok');
    } catch {
      setErrorSolicitudes('No se pudo conectar con el backend para registrar la solicitud.');
    } finally {
      setGuardandoSolicitud(false);
    }
  }

  async function crearEvaluacion(evento: React.FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    if (!solicitudSeleccionada) return;

    setGuardandoEvaluacion(true);
    setErrorEvaluaciones('');
    setMensaje('');

    try {
      const res = await fetch(`${API_URL}/evaluaciones`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          solicitud_intervencion_id: solicitudSeleccionada.id_solicitud,
          fecha_inicio: evaluacionFechaInicio,
          evaluador: evaluacionEvaluador,
          observaciones: evaluacionObservaciones,
        }),
      });

      if (!res.ok) {
        setErrorEvaluaciones(await obtenerMensajeError(res));
        return;
      }

      await cargarEvaluaciones(solicitudSeleccionada.id_solicitud);
      setEvaluacionFechaInicio('');
      setEvaluacionEvaluador('');
      setEvaluacionObservaciones('');
      avisar('Evaluación administrativa registrada correctamente.', 'ok');
    } catch {
      setErrorEvaluaciones(
        'No se pudo conectar con el backend para registrar la evaluación.',
      );
    } finally {
      setGuardandoEvaluacion(false);
    }
  }

  async function crearDecision(evento: React.FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    if (!solicitudSeleccionada) return;

    if (
      decisionResultado === 'Aprobar intervención'
      && solicitudYaAprobada
    ) {
      setErrorDecisiones('La intervención ya fue aprobada.');
      return;
    }

    if (
      decisionResultado === 'Aprobar intervención'
      && !decisionFondoInterviniente
    ) {
      setErrorDecisiones(
        'Debe seleccionar el Fondo Interviniente antes de registrar una decisión aprobatoria.',
      );
      return;
    }

    setGuardandoDecision(true);
    setErrorDecisiones('');
    setMensaje('');

    try {
      const res = await fetch(`${API_URL}/decisiones`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          solicitud_intervencion_id: solicitudSeleccionada.id_solicitud,
          autoridad_decisora: decisionAutoridad,
          fecha_decision: decisionFecha,
          resultado: decisionResultado,
          fundamento: decisionFundamento,
          fondo_interviniente: decisionFondoInterviniente || null,
          descripcion_fondo: decisionDescripcionFondo || null,
          usuario_registrante: decisionUsuarioRegistrante,
        }),
      });

      if (!res.ok) {
        setErrorDecisiones(await obtenerMensajeError(res));
        return;
      }

      const creada: DecisionAdministrativa = await res.json();
      await cargarDecisiones(solicitudSeleccionada.id_solicitud);
      setDecisionRecienCreadaId(creada.id_decision);
      setDecisionExpedienteActiva(
        creada.resultado === 'Aprobar intervención'
          && creada.fondo_interviniente === 'FONDO_COMPENSADOR'
          ? creada.id_decision
          : null,
      );
      setDecisionAutoridad('');
      setDecisionFecha('');
      setDecisionResultado('');
      setDecisionFundamento('');
      setDecisionFondoInterviniente('');
      setDecisionDescripcionFondo('');
      setDecisionUsuarioRegistrante('');
      avisar('Decisión administrativa registrada correctamente.', 'ok');
    } catch {
      setErrorDecisiones(
        'No se pudo conectar con el backend para registrar la decisión.',
      );
    } finally {
      setGuardandoDecision(false);
    }
  }

  function mostrarFormularioExpediente(decisionId: string) {
    setDecisionExpedienteActiva(decisionId);
    setExpedienteDecisionNumeroInterno('');
    setExpedienteDecisionNumeroGdeba('');
    setErrorExpedienteDecision('');
  }

  function ocultarFormularioExpediente() {
    setDecisionExpedienteActiva(null);
    setErrorExpedienteDecision('');
  }

  async function crearExpedienteDesdeDecision(
    evento: React.FormEvent<HTMLFormElement>,
    decisionId: string,
  ) {
    evento.preventDefault();
    setGuardandoExpedienteDecision(true);
    setErrorExpedienteDecision('');
    setMensaje('');

    try {
      const res = await fetch(`${API_URL}/decisiones/${decisionId}/expedientes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          numero_interno: expedienteDecisionNumeroInterno,
          numero_gdeba: expedienteDecisionNumeroGdeba || null,
        }),
      });

      if (!res.ok) {
        setErrorExpedienteDecision(await obtenerMensajeError(res));
        return;
      }

      const creado: Expediente = await res.json();
      setDecisionExpedienteActiva(null);
      setExpedienteDecisionNumeroInterno('');
      setExpedienteDecisionNumeroGdeba('');
      await cargarExpedientes();
      await cargarDetalle(creado);
      avisar(`Expediente ${creado.numero_interno} creado correctamente.`, 'ok');
    } catch {
      setErrorExpedienteDecision(
        'No se pudo conectar con el backend para crear el expediente.',
      );
    } finally {
      setGuardandoExpedienteDecision(false);
    }
  }

  async function cargarDetalle(expediente: Expediente) {
    setSeleccionado(expediente);
    setPantalla('detalle');
    setTabDetalle('workflow');
    setAnalisis(null);
    setMensaje('');
    setSolicitudOrigenExpediente(null);
    setDecisionOrigenExpediente(null);

    const [
      docsRes,
      histRes,
      solicitudOrigenRes,
      decisionOrigenRes,
    ] = await Promise.all([
      fetch(`${API_URL}/expedientes/${expediente.id}/documentos`),
      fetch(`${API_URL}/expedientes/${expediente.id}/historial`),
      expediente.solicitud_intervencion_id
        ? fetch(`${API_URL}/solicitudes/${expediente.solicitud_intervencion_id}`)
        : Promise.resolve(null),
      expediente.decision_administrativa_id
        ? fetch(`${API_URL}/decisiones/${expediente.decision_administrativa_id}`)
        : Promise.resolve(null),
    ]);

    setDocumentos(await docsRes.json());
    setHistorial(await histRes.json());

    if (solicitudOrigenRes?.ok) {
      setSolicitudOrigenExpediente(await solicitudOrigenRes.json());
    }

    if (decisionOrigenRes?.ok) {
      setDecisionOrigenExpediente(await decisionOrigenRes.json());
    }
  }

  async function abrirSolicitudOrigen() {
    if (!solicitudOrigenExpediente) return;

    setPantalla('solicitudes');
    setMensaje('');
    await cargarSolicitudes();
    await seleccionarSolicitud(solicitudOrigenExpediente);
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
      body: JSON.stringify({ numero_interno: numeroInterno, numero_gdeba: numeroGdeba || null, id_suna: idSuna, establecimiento, objeto, numero_disposicion: disposicion }),
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

    if (!res.ok) {
      avisar(await obtenerMensajeError(res), 'error');
      return;
    }

    const data = await res.json();
    setAnalisis(data);
    setTabDetalle('ia');

    if (data.modo === 'EXTRACCION_FALLIDA') {
      avisar(
        'La Orden de Pago fue incorporada al expediente, pero no fue posible '
          + 'extraer la información necesaria para generar la disposición.',
        'error',
      );
      return;
    }

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

  function descargarBorradorTexto() {
    if (!seleccionado) return;
    window.open(`${API_URL}/expedientes/${seleccionado.id}/disposicion/borrador/texto`, '_blank');
  }

  function descargarBorradorWord() {
    if (!seleccionado) return;
    window.open(`${API_URL}/expedientes/${seleccionado.id}/disposicion/borrador/docx`, '_blank');
  }

  function abrirVistaPrevia(doc: Documento) {
    if (!seleccionado) return;
    window.open(`${API_URL}/expedientes/${seleccionado.id}/documentos/${doc.id}/vista-previa`, '_blank');
  }

  useEffect(() => {
    cargarExpedientes();
    cargarSolicitudes();
    cargarCatalogosIntervencion();
  }, []);

  const diag = diagnosticoIA(analisis);
  const comparacion = comparacionDocumental(analisis);
  const confiabilidad = confiabilidadIA(analisis);
  const tieneOP = documentos.some((documento) => documento.tipo === 'OP');
  const opConExtraccionFallida = analisis?.modo === 'EXTRACCION_FALLIDA';
  const opAnalizadaCorrectamente = Boolean(
    analisis?.op_detectada && analisis.modo !== 'EXTRACCION_FALLIDA',
  );
  const disposicionEmitida = seleccionado?.estado === 'DISPOSICION_EMITIDA';
  const validacionAdministrativaCompleta = Boolean(
    seleccionado
      && (
        ['VALIDADO', 'DISPOSICION_EMITIDA'].includes(seleccionado.estado)
        || historial.some((evento) =>
          [
            'EXPEDIENTE_VALIDADO',
            'EXPEDIENTE_VALIDADO_CON_OBSERVACIONES',
          ].includes(evento.accion),
        )
      ),
  );

  const controlesPreparacionAdministrativa = [
    {
      texto: 'Número GDEBA informado.',
      accion: 'Informar Número GDEBA.',
      completo: Boolean(seleccionado?.numero_gdeba),
    },
    {
      texto: 'Objeto del Expediente informado.',
      accion: 'Completar Objeto del Expediente.',
      completo: Boolean(seleccionado?.objeto),
    },
    {
      texto: 'Establecimiento informado.',
      accion: 'Informar Establecimiento.',
      completo: Boolean(seleccionado?.establecimiento),
    },
    {
      texto: 'Solicitud de Intervención asociada.',
      accion: 'Asociar Solicitud de Intervención.',
      completo: Boolean(solicitudOrigenExpediente),
    },
    {
      texto: 'Decisión Administrativa registrada.',
      accion: 'Registrar Decisión Administrativa.',
      completo: Boolean(decisionOrigenExpediente),
    },
    {
      texto: 'Fondo Interviniente determinado.',
      accion: 'Determinar Fondo Interviniente.',
      completo: Boolean(decisionOrigenExpediente?.fondo_interviniente),
    },
  ];
  const preparacionAdministrativaCompleta = controlesPreparacionAdministrativa.every(
    (control) => control.completo,
  );
  const controlesPreparacionPendientes = controlesPreparacionAdministrativa.filter(
    (control) => !control.completo,
  );
  const solicitudYaAprobada = decisiones.some(
    (decision) => decision.resultado === 'Aprobar intervención',
  );

  const etapaWorkflow = seleccionado?.estado === 'ARCHIVADO'
    ? 'archivo'
    : disposicionEmitida
      ? 'formalizacion'
      : disposicionBorrador
        ? 'disposicion'
        : opConExtraccionFallida || tieneOP
          ? 'op'
          : validacionAdministrativaCompleta
            ? 'op'
            : 'validacion';

  const estadoOP = opConExtraccionFallida
    ? 'Requiere atención'
    : opAnalizadaCorrectamente
      ? 'Analizada'
      : tieneOP
        ? 'Pendiente de análisis'
        : 'No incorporada';

  const workflowSteps = [
    {
      id: 'validacion',
      texto: 'Validación',
      estado: validacionAdministrativaCompleta
        ? 'completed'
        : etapaWorkflow === 'validacion'
          ? 'current'
          : 'blocked',
    },
    {
      id: 'op',
      texto: 'Orden de Pago',
      estado: opConExtraccionFallida
        ? 'attention'
        : opAnalizadaCorrectamente
          ? 'completed'
          : etapaWorkflow === 'op'
            ? 'current'
            : validacionAdministrativaCompleta
              ? 'current'
              : 'blocked',
    },
    {
      id: 'disposicion',
      texto: 'Disposición',
      estado: etapaWorkflow === 'archivo' || disposicionEmitida
        ? 'completed'
        : etapaWorkflow === 'disposicion'
          ? 'current'
          : 'blocked',
    },
    {
      id: 'formalizacion',
      texto: 'Formalización',
      estado: etapaWorkflow === 'archivo'
        ? 'completed'
        : disposicionEmitida
          ? 'current'
          : 'blocked',
    },
    {
      id: 'archivo',
      texto: 'Archivo',
      estado: etapaWorkflow === 'archivo' ? 'current' : 'future',
    },
  ];

  const accionPrincipal = (() => {
    if (disposicionEmitida) {
      return {
        descripcion: 'La disposición fue emitida y se encuentra disponible para su descarga.',
        etiqueta: 'Descargar disposición',
        ejecutar: descargarBorradorWord,
      };
    }

    if (disposicionBorrador) {
      return {
        descripcion: 'Existe un borrador de disposición pendiente de revisión.',
        etiqueta: 'Trabajar en la disposición',
        ejecutar: () => setTabDetalle('disposicion'),
      };
    }

    if (opConExtraccionFallida) {
      return {
        descripcion: 'La Orden de Pago fue incorporada, pero requiere revisión antes de continuar.',
        etiqueta: 'Revisar documentación',
        ejecutar: () => setTabDetalle('documentos'),
      };
    }

    if (opAnalizadaCorrectamente) {
      return {
        descripcion: 'La Orden de Pago fue analizada y puede prepararse la disposición.',
        etiqueta: 'Preparar disposición',
        ejecutar: () => prepararDisposicion(false),
      };
    }

    if (tieneOP) {
      return {
        descripcion: 'La Orden de Pago fue incorporada y está pendiente de análisis.',
        etiqueta: 'Analizar Orden de Pago',
        ejecutar: analizarOP,
      };
    }

    if (validacionAdministrativaCompleta) {
      return {
        descripcion: 'La validación administrativa está completa. Corresponde incorporar la Orden de Pago.',
        etiqueta: 'Incorporar Orden de Pago',
        ejecutar: () => setTabDetalle('documentos'),
      };
    }

    if (validacion?.estado_general === 'VERDE') {
      return {
        descripcion: 'Los controles están completos. Corresponde validar administrativamente el expediente.',
        etiqueta: 'Validar expediente',
        ejecutar: validarExpediente,
      };
    }

    if (validacion?.estado_general === 'AMARILLO') {
      return {
        descripcion: 'La validación presenta observaciones que deben resolverse o acreditarse.',
        etiqueta: 'Completar checklist físico',
        ejecutar: cargarChecklistFisico,
      };
    }

    return {
      descripcion: 'El expediente requiere completar su validación administrativa.',
      etiqueta: 'Completar validación',
      ejecutar: cargarChecklistFisico,
    };
  })();

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">▣</div>
          <div><h1>SIGD-ST</h1><p>Consejo Escolar<br />General Alvarado</p></div>
        </div>

        <button className="new-button" onClick={abrirNuevaSolicitud}>+ Nueva Solicitud</button>

        <nav>
          <button className={pantalla === 'inicio' ? 'active' : ''} onClick={() => setPantalla('inicio')}>Bandeja</button>
          <button className={pantalla === 'expedientes' ? 'active' : ''} onClick={() => setPantalla('expedientes')}>Expedientes</button>
          <button className={pantalla === 'solicitudes' ? 'active' : ''} onClick={abrirSolicitudes}>Solicitudes de Intervención</button>
          <button>Fondo Compensador</button>
          <button>SAE</button>
          <button>Infraestructura</button>
          <button>Transporte</button>
          <button className={pantalla === 'administracion' ? 'active' : ''} onClick={() => setPantalla('administracion')}>Administración</button>
        </nav>

        <div className="version">Versión Alfa 0.29B</div>
      </aside>

      <section className="content">
        <header className="topbar">
          <div>
            <h2>{pantalla === 'inicio' ? 'Dashboard de Solicitudes de Intervención' : pantalla === 'nuevo' ? 'Nuevo Expediente' : pantalla === 'detalle' ? 'Expediente Inteligente' : pantalla === 'solicitudes' ? 'Solicitudes de Intervención' : pantalla === 'administracion' ? 'Administración' : 'Expedientes'}</h2>
            <span>Secretaría Técnica</span>
          </div>
          <div className="user">Gonzalo · Secretario Técnico</div>
        </header>

        {mensaje && <div className={`notice ${mensajeTipo}`}>{mensaje}</div>}

        {pantalla === 'inicio' && (
          <>
            <section className="metrics">
              <div className="metric-card"><span>📨</span><strong>{metricasSolicitudes.total}</strong><p>Solicitudes ingresadas</p></div>
              <div className="metric-card"><span>🕒</span><strong>{metricasSolicitudes.pendientes.length}</strong><p>Pendientes de tramitación</p></div>
              <div className="metric-card"><span>🔗</span><strong>{metricasSolicitudes.conIdSuna}</strong><p>Con ID SUNA</p></div>
              <div className="metric-card"><span>📁</span><strong>{metricasSolicitudes.conExpediente}</strong><p>Con Expediente generado</p></div>
            </section>

            <section className="dashboard-grid">
              <div className="card work-queue">
                <div className="card-title">
                  <h3>Solicitudes pendientes</h3>
                  <button className="link" onClick={abrirSolicitudes}>Ver todas</button>
                </div>
                {metricasSolicitudes.pendientes.length === 0 ? (
                  <p className="empty">No hay Solicitudes pendientes.</p>
                ) : (
                  metricasSolicitudes.pendientes.slice(0, 6).map((solicitud) => (
                    <button
                      className="queue-item"
                      key={solicitud.id_solicitud}
                      onClick={() => abrirSolicitudDesdeBandeja(solicitud)}
                    >
                      <div>
                        <strong>{solicitud.numero_solicitud}</strong>
                        <p>{solicitud.establecimiento} · {solicitud.motivo}</p>
                      </div>
                      <span className="badge blue">{solicitud.estado}</span>
                    </button>
                  ))
                )}
              </div>

              <div className="card">
                <div className="card-title">
                  <h3>Solicitudes recientes</h3>
                  <button className="link" onClick={abrirSolicitudes}>Abrir registro</button>
                </div>
                {metricasSolicitudes.recientes.length === 0 ? (
                  <p className="empty">Todavía no hay Solicitudes registradas.</p>
                ) : (
                  metricasSolicitudes.recientes.map((solicitud) => (
                    <button
                      className="queue-item"
                      key={solicitud.id_solicitud}
                      onClick={() => abrirSolicitudDesdeBandeja(solicitud)}
                    >
                      <div>
                        <strong>{solicitud.numero_solicitud}</strong>
                        <p>{solicitud.procedencia} · {solicitud.establecimiento}</p>
                      </div>
                      <span className="badge blue">{solicitud.estado}</span>
                    </button>
                  ))
                )}
              </div>
            </section>

            <section className="card">
              <div className="card-title">
                <h3>Expedientes derivados recientes</h3>
                <button className="link" onClick={() => setPantalla('expedientes')}>Ver Expedientes</button>
              </div>
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

            <label>Expediente GDEBA</label>
            <input value={numeroGdeba} onChange={(e) => setNumeroGdeba(e.target.value)} />

            <label>ID SUNA</label>
            <input value={idSuna} onChange={(e) => setIdSuna(e.target.value)} />

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

        {pantalla === 'solicitudes' && (
          <section>
            {errorSolicitudes && <div className="notice error">{errorSolicitudes}</div>}

            <div className={`solicitudes-layout ${solicitudSeleccionada ? 'detail-only' : ''}`}>
              {!solicitudSeleccionada && (
              <form className="card" onSubmit={crearSolicitud}>
                <div className="card-title">
                  <h3>Registrar Solicitud</h3>
                  <span className="badge blue">Nueva intervención</span>
                </div>

                <label>Número de solicitud</label>
                <p className="muted">
                  Se asignará automáticamente al registrar la Solicitud
                </p>

                <label>Procedencia</label>
                <select
                  value={solicitudProcedencia}
                  onChange={(e) => setSolicitudProcedencia(e.target.value)}
                >
                  <option value="">Seleccionar procedencia</option>
                  {procedenciasDisponibles.map((procedencia) => (
                    <option key={procedencia} value={procedencia}>
                      {procedencia}
                    </option>
                  ))}
                </select>

                <label>ID SUNA</label>
                <input
                  value={solicitudIdSuna}
                  onChange={(e) => setSolicitudIdSuna(e.target.value)}
                  placeholder="Obligatorio cuando la procedencia es SUNA"
                />

                <label>Fecha de ingreso</label>
                <input
                  type="date"
                  value={solicitudFechaIngreso}
                  onChange={(e) => setSolicitudFechaIngreso(e.target.value)}
                />

                <label>Establecimiento</label>
                <input
                  value={solicitudEstablecimiento}
                  onChange={(e) => setSolicitudEstablecimiento(e.target.value)}
                />

                <label>Solicitante</label>
                <input
                  value={solicitudSolicitante}
                  onChange={(e) => setSolicitudSolicitante(e.target.value)}
                />

                <label>Motivo</label>
                <textarea
                  value={solicitudMotivo}
                  onChange={(e) => setSolicitudMotivo(e.target.value)}
                />

                <label>Prioridad</label>
                <input
                  value={solicitudPrioridad}
                  onChange={(e) => setSolicitudPrioridad(e.target.value)}
                />

                <button className="primary" type="submit" disabled={guardandoSolicitud}>
                  {guardandoSolicitud ? 'Registrando...' : 'Registrar solicitud'}
                </button>
              </form>
              )}

              <div>
                <section className="card solicitudes-table">
                  <div className="card-title">
                    <h3>Solicitudes registradas</h3>
                    <button className="small-button" onClick={cargarSolicitudes} disabled={cargandoSolicitudes}>
                      Actualizar
                    </button>
                  </div>

                  {cargandoSolicitudes ? (
                    <p className="empty">Cargando solicitudes...</p>
                  ) : solicitudes.length === 0 ? (
                    <p className="empty">Todavía no hay solicitudes registradas.</p>
                  ) : (
                    <table>
                      <thead>
                        <tr><th>Número</th><th>Procedencia</th><th>Estado</th><th></th></tr>
                      </thead>
                      <tbody>
                        {solicitudes.map((solicitud) => (
                          <tr key={solicitud.id_solicitud}>
                            <td>{solicitud.numero_solicitud}</td>
                            <td>{solicitud.procedencia}</td>
                            <td><span className="badge blue">{solicitud.estado}</span></td>
                            <td>
                              <button className="small-button" onClick={() => seleccionarSolicitud(solicitud)}>
                                Ver
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </section>

                <section className="card">
                  <h3>Detalle de la solicitud</h3>
                  {solicitudSeleccionada ? (
                    <>
                      <dl className="data-list">
                        <dt>Número</dt><dd>{solicitudSeleccionada.numero_solicitud}</dd>
                        <dt>Estado</dt><dd><span className="badge blue">{solicitudSeleccionada.estado}</span></dd>
                        <dt>Procedencia</dt><dd>{solicitudSeleccionada.procedencia}</dd>
                        <dt>ID SUNA</dt><dd>{solicitudSeleccionada.id_suna || '-'}</dd>
                        <dt>Fecha de ingreso</dt><dd>{solicitudSeleccionada.fecha_ingreso}</dd>
                        <dt>Establecimiento</dt><dd>{solicitudSeleccionada.establecimiento}</dd>
                        <dt>Solicitante</dt><dd>{solicitudSeleccionada.solicitante}</dd>
                        <dt>Prioridad</dt><dd>{solicitudSeleccionada.prioridad}</dd>
                        <dt>Motivo</dt><dd>{solicitudSeleccionada.motivo}</dd>
                      </dl>

                      <section className="subcard">
                        <div className="card-title">
                          <h4>Evaluaciones Administrativas</h4>
                          <button
                            className="small-button"
                            onClick={() => cargarEvaluaciones(solicitudSeleccionada.id_solicitud)}
                            disabled={cargandoEvaluaciones}
                          >
                            Actualizar
                          </button>
                        </div>

                        {errorEvaluaciones && (
                          <div className="notice error">{errorEvaluaciones}</div>
                        )}

                        <div className="evaluaciones-grid">
                          <form onSubmit={crearEvaluacion}>
                            <h4>Registrar evaluación</h4>

                            <label>Fecha de inicio</label>
                            <input
                              type="date"
                              value={evaluacionFechaInicio}
                              onChange={(e) => setEvaluacionFechaInicio(e.target.value)}
                            />

                            <label>Evaluador</label>
                            <select
                              value={evaluacionEvaluador}
                              onChange={(e) => setEvaluacionEvaluador(e.target.value)}
                              disabled={catalogoEvaluadores.length === 0}
                            >
                              <option value="">
                                {catalogoEvaluadores.length === 0 ? 'No disponible' : 'Seleccionar evaluador'}
                              </option>
                              {catalogoEvaluadores.map((evaluador) => (
                                <option key={evaluador} value={evaluador}>{evaluador}</option>
                              ))}
                            </select>

                            <label>Observaciones</label>
                            <textarea
                              value={evaluacionObservaciones}
                              onChange={(e) => setEvaluacionObservaciones(e.target.value)}
                            />

                            <button
                              className="primary"
                              type="submit"
                              disabled={guardandoEvaluacion}
                            >
                              {guardandoEvaluacion
                                ? 'Registrando...'
                                : 'Registrar evaluación'}
                            </button>
                          </form>

                          <div>
                            <h4>Evaluaciones registradas</h4>
                            {cargandoEvaluaciones ? (
                              <p className="empty">Cargando evaluaciones...</p>
                            ) : evaluaciones.length === 0 ? (
                              <p className="empty">
                                Todavía no hay evaluaciones para esta solicitud.
                              </p>
                            ) : (
                              <div className="evaluaciones-list">
                                {evaluaciones.map((evaluacion) => (
                                  <article key={evaluacion.id_evaluacion}>
                                    <strong>{evaluacion.fecha_inicio}</strong>
                                    <p>Evaluador: {evaluacion.evaluador}</p>
                                    <p>{evaluacion.observaciones}</p>
                                    <small>ID técnico: {evaluacion.id_evaluacion}</small>
                                  </article>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      </section>

                      <section className="subcard">
                        <div className="card-title">
                          <h4>Decisiones Administrativas</h4>
                          <button
                            className="small-button"
                            onClick={() => cargarDecisiones(solicitudSeleccionada.id_solicitud)}
                            disabled={cargandoDecisiones}
                          >
                            Actualizar
                          </button>
                        </div>

                        {errorDecisiones && (
                          <div className="notice error">{errorDecisiones}</div>
                        )}

                        <div className="decisiones-grid">
                          <form onSubmit={crearDecision}>
                            <h4>Registrar decisión</h4>

                            <label>Autoridad decisora</label>
                            <select
                              value={decisionAutoridad}
                              onChange={(e) => setDecisionAutoridad(e.target.value)}
                              disabled={catalogoAutoridadesDecisoras.length === 0}
                            >
                              <option value="">
                                {catalogoAutoridadesDecisoras.length === 0 ? 'No disponible' : 'Seleccionar autoridad'}
                              </option>
                              {catalogoAutoridadesDecisoras.map((autoridad) => (
                                <option key={autoridad} value={autoridad}>{autoridad}</option>
                              ))}
                            </select>

                            <label>Fecha de decisión</label>
                            <input
                              type="date"
                              value={decisionFecha}
                              onChange={(e) => setDecisionFecha(e.target.value)}
                            />

                            <label>Resultado</label>
                            <select
                              value={decisionResultado}
                              onChange={(e) => {
                                const resultado = e.target.value;
                                setDecisionResultado(resultado);
                                if (resultado !== 'Aprobar intervención') {
                                  setDecisionFondoInterviniente('');
                                  setDecisionDescripcionFondo('');
                                  setErrorDecisiones('');
                                }
                              }}
                              disabled={catalogoResultadosDecision.length === 0}
                            >
                              <option value="">
                                {catalogoResultadosDecision.length === 0 ? 'No disponible' : 'Seleccionar resultado'}
                              </option>
                              {catalogoResultadosDecision.map((resultado) => (
                                <option
                                  disabled={
                                    resultado === 'Aprobar intervención'
                                    && solicitudYaAprobada
                                  }
                                  key={resultado}
                                  value={resultado}
                                >
                                  {resultado}
                                </option>
                              ))}
                            </select>
                            {solicitudYaAprobada && (
                              <div className="notice info">
                                La intervención ya fue aprobada.
                              </div>
                            )}

                            <label>Fundamento</label>
                            <textarea
                              value={decisionFundamento}
                              onChange={(e) => setDecisionFundamento(e.target.value)}
                            />

                            <label>Fondo Interviniente</label>
                            <select
                              value={decisionFondoInterviniente}
                              onChange={(e) => {
                                setDecisionFondoInterviniente(e.target.value);
                                setErrorDecisiones('');
                              }}
                              disabled={decisionResultado !== 'Aprobar intervención'}
                            >
                              <option value="">
                                {decisionResultado !== 'Aprobar intervención'
                                  ? 'Disponible para decisiones aprobatorias'
                                  : 'Seleccionar fondo'}
                              </option>
                              {fondosIntervinientesDisponibles.map((fondo) => (
                                <option key={fondo} value={fondo}>
                                  {etiquetaFondoInterviniente(fondo)}
                                </option>
                              ))}
                            </select>

                            {decisionFondoInterviniente === 'OTRO' && (
                              <>
                                <label>Descripción del Fondo</label>
                                <input
                                  value={decisionDescripcionFondo}
                                  onChange={(e) => setDecisionDescripcionFondo(e.target.value)}
                                />
                              </>
                            )}

                            <label>Usuario registrante</label>
                            <input
                              value={decisionUsuarioRegistrante}
                              onChange={(e) => setDecisionUsuarioRegistrante(e.target.value)}
                            />

                            <button
                              className="primary"
                              type="submit"
                              disabled={guardandoDecision}
                            >
                              {guardandoDecision
                                ? 'Registrando...'
                                : 'Registrar decisión'}
                            </button>
                          </form>

                          <div>
                            <h4>Decisiones registradas</h4>
                            {cargandoDecisiones ? (
                              <p className="empty">Cargando decisiones...</p>
                            ) : decisiones.length === 0 ? (
                              <p className="empty">
                                Todavía no hay decisiones para esta solicitud.
                              </p>
                            ) : (
                              <div className="decisiones-list">
                                {decisiones.map((decision) => {
                                  const expedientesDecision = expedientes.filter(
                                    (expediente) => (
                                      expediente.decision_administrativa_id
                                      === decision.id_decision
                                    ),
                                  );

                                  return (
                                    <article
                                      className={
                                        decisionRecienCreadaId === decision.id_decision
                                          ? 'decision-newly-created'
                                          : ''
                                      }
                                      key={decision.id_decision}
                                    >
                                      {decisionRecienCreadaId === decision.id_decision && (
                                        <span className="badge green">Decisión recién registrada</span>
                                      )}
                                      <strong>{decision.fecha_decision}</strong>
                                      <p>Autoridad: {decision.autoridad_decisora}</p>
                                      <p>Resultado: {decision.resultado}</p>
                                      <p>
                                        Fondo Interviniente:{' '}
                                        {etiquetaFondoInterviniente(decision.fondo_interviniente)}
                                      </p>
                                      {decision.descripcion_fondo && (
                                        <p>Descripción del Fondo: {decision.descripcion_fondo}</p>
                                      )}
                                      <p>Registrada por: {decision.usuario_registrante}</p>
                                      <p>{decision.fundamento}</p>

                                      {decision.resultado === 'Aprobar intervención'
                                        && decision.fondo_interviniente === 'FONDO_COMPENSADOR' && (
                                        <>
                                          {expedientesDecision.length > 0 && (
                                            <div className="subcard">
                                              <h4>Expedientes generados</h4>
                                              <table>
                                                <thead>
                                                  <tr>
                                                    <th>Número interno</th>
                                                    <th>Número GDEBA</th>
                                                    <th>Estado</th>
                                                    <th></th>
                                                  </tr>
                                                </thead>
                                                <tbody>
                                                  {expedientesDecision.map((expediente) => (
                                                    <tr key={expediente.id}>
                                                      <td>{expediente.numero_interno}</td>
                                                      <td>
                                                        {expediente.numero_gdeba
                                                          || 'Sin número GDEBA'}
                                                      </td>
                                                      <td>
                                                        <span className={claseEstado(expediente.estado)}>
                                                          {etiquetaEstado(expediente.estado)}
                                                        </span>
                                                      </td>
                                                      <td>
                                                        <button
                                                          className="small-button"
                                                          type="button"
                                                          onClick={() => cargarDetalle(expediente)}
                                                        >
                                                          Abrir expediente
                                                        </button>
                                                      </td>
                                                    </tr>
                                                  ))}
                                                </tbody>
                                              </table>
                                            </div>
                                          )}

                                        <button
                                          className="secondary"
                                          type="button"
                                          onClick={() => mostrarFormularioExpediente(decision.id_decision)}
                                        >
                                          {expedientesDecision.length > 0
                                            ? 'Crear otro expediente'
                                            : 'Crear expediente'}
                                        </button>

                                        {decisionExpedienteActiva === decision.id_decision && (
                                          <form
                                            className="subcard"
                                            onSubmit={(evento) => crearExpedienteDesdeDecision(
                                              evento,
                                              decision.id_decision,
                                            )}
                                          >
                                            <h4>Crear Expediente derivado</h4>

                                            {errorExpedienteDecision && (
                                              <div className="notice error">
                                                {errorExpedienteDecision}
                                              </div>
                                            )}

                                            <label>Número de expediente interno</label>
                                            <input
                                              value={expedienteDecisionNumeroInterno}
                                              onChange={(e) => setExpedienteDecisionNumeroInterno(e.target.value)}
                                            />

                                            <label>Número de expediente GDEBA (opcional)</label>
                                            <input
                                              value={expedienteDecisionNumeroGdeba}
                                              onChange={(e) => setExpedienteDecisionNumeroGdeba(e.target.value)}
                                            />

                                            <div className="actions">
                                              <button
                                                className="secondary"
                                                type="button"
                                                onClick={ocultarFormularioExpediente}
                                              >
                                                Cancelar
                                              </button>
                                              <button
                                                className="primary"
                                                type="submit"
                                                disabled={guardandoExpedienteDecision}
                                              >
                                                {guardandoExpedienteDecision
                                                  ? 'Creando...'
                                                  : 'Confirmar creación'}
                                              </button>
                                            </div>
                                          </form>
                                        )}
                                        </>
                                      )}

                                      {decision.resultado === 'Aprobar intervención'
                                        && !decision.fondo_interviniente && (
                                        <div className="notice info">
                                          La decisión no tiene un Fondo Interviniente determinado.
                                        </div>
                                      )}

                                      {decision.resultado === 'Aprobar intervención'
                                        && decision.fondo_interviniente
                                        && decision.fondo_interviniente !== 'FONDO_COMPENSADOR' && (
                                        <div className="notice info">
                                          El circuito del Fondo Interviniente seleccionado todavía no está implementado.
                                        </div>
                                      )}
                                    </article>
                                  );
                                })}
                              </div>
                            )}
                          </div>
                        </div>
                      </section>
                    </>
                  ) : (
                    <p className="empty">Seleccioná una solicitud para ver su detalle.</p>
                  )}
                </section>
              </div>
            </div>
          </section>
        )}

        {pantalla === 'detalle' && seleccionado && (
          <section className="expediente-page">
            <div className="expediente-header">
              <div className="expediente-identity">
                <span className="eyebrow">Expediente</span>
                <h2>{seleccionado.numero_interno}</h2>
              </div>

              <div className="expediente-header-status">
                <span className={estadoAdministrativo(seleccionado, historial).clase}>
                  {estadoAdministrativo(seleccionado, historial).texto}
                </span>
                <div>
                  <span>Fondo Interviniente</span>
                  <strong>
                    {decisionOrigenExpediente?.fondo_interviniente
                      ? etiquetaFondoInterviniente(decisionOrigenExpediente.fondo_interviniente)
                      : 'No disponible'}
                  </strong>
                </div>
              </div>
            </div>

            <section className="card expediente-origin-section">
              <div className="card-title">
                <h3>Resumen del Expediente</h3>
              </div>
              <div className="expediente-summary-grid">
                <div className="expediente-summary-group">
                  <h4>Origen</h4>
                  <div className="expediente-summary-primary">
                    <span>Solicitud</span>
                    <strong>{solicitudOrigenExpediente?.numero_solicitud || 'No disponible'}</strong>
                  </div>
                  <div>
                    <span>ID SUNA</span>
                    <strong>{solicitudOrigenExpediente?.id_suna || 'No disponible'}</strong>
                  </div>
                </div>

                <div className="expediente-summary-group">
                  <h4>Intervención</h4>
                  <div className="expediente-summary-primary">
                    <span>Escuela o establecimiento</span>
                    <strong>
                      {solicitudOrigenExpediente?.establecimiento
                        || seleccionado.establecimiento
                        || 'No disponible'}
                    </strong>
                  </div>
                  <div>
                    <span>Objeto</span>
                    <strong>{seleccionado.objeto || 'No disponible'}</strong>
                  </div>
                </div>

                <div className="expediente-summary-group">
                  <h4>Decisión</h4>
                  <div className="expediente-summary-primary">
                    <span>Resultado</span>
                    <strong>{decisionOrigenExpediente?.resultado || 'No disponible'}</strong>
                  </div>
                  <div>
                    <span>Autoridad</span>
                    <strong>{decisionOrigenExpediente?.autoridad_decisora || 'No disponible'}</strong>
                  </div>
                  <div>
                    <span>Fecha</span>
                    <strong>{decisionOrigenExpediente?.fecha_decision || 'No disponible'}</strong>
                  </div>
                </div>

                <div className="expediente-summary-group">
                  <h4>Administración</h4>
                  <div>
                    <span>Fondo Interviniente</span>
                    <strong>
                      {decisionOrigenExpediente?.fondo_interviniente
                        ? etiquetaFondoInterviniente(decisionOrigenExpediente.fondo_interviniente)
                        : 'No disponible'}
                    </strong>
                  </div>
                  <div>
                    <span>Tipo de trámite</span>
                    <strong>
                      {seleccionado.tipo_tramite === 'FONDO_COMPENSADOR'
                        ? 'Fondo Compensador'
                        : seleccionado.tipo_tramite || 'No disponible'}
                    </strong>
                  </div>
                  <div>
                    <span>Número GDEBA</span>
                    <strong>{seleccionado.numero_gdeba || 'No disponible'}</strong>
                  </div>
                </div>
              </div>
            </section>

            <section
              className={`card administrative-preparation ${
                preparacionAdministrativaCompleta ? 'complete' : ''
              }`}
            >
              <div className="card-title">
                <h3>Preparación Administrativa</h3>
                <span className="muted">
                  {controlesPreparacionPendientes.length === 0
                    ? 'Completa'
                    : `${controlesPreparacionPendientes.length} pendiente${
                      controlesPreparacionPendientes.length === 1 ? '' : 's'
                    }`}
                </span>
              </div>
              <div className="administrative-preparation-grid">
                {controlesPreparacionAdministrativa.map((control) => (
                  <div className="administrative-preparation-item" key={control.texto}>
                    <span aria-hidden="true">{control.completo ? '✓' : '○'}</span>
                    <span>{control.texto.replace(/\.$/, '')}</span>
                    <strong>{control.completo ? 'Completo' : 'Pendiente'}</strong>
                  </div>
                ))}
              </div>
            </section>

            <div className="workflow-steps" aria-label="Etapas del trámite">
              {workflowSteps.map((etapa, indice) => (
                <div className={`workflow-step ${etapa.estado}`} key={etapa.id}>
                  <span className="workflow-step-number">
                    {etapa.estado === 'completed' ? '✓' : indice + 1}
                  </span>
                  <span>{etapa.texto}</span>
                </div>
              ))}
            </div>

            <div className="workflow-layout">
              <section className="expediente-main">
                {tabDetalle === 'workflow' && (
                  <div className="card">
                    <div className="card-title">
                      <div>
                        <span className="eyebrow">Etapa actual</span>
                        <h3>
                          {etapaWorkflow === 'validacion'
                            ? 'Validación administrativa'
                            : etapaWorkflow === 'op'
                              ? 'Orden de Pago'
                              : etapaWorkflow === 'disposicion'
                                ? 'Disposición'
                                : 'Formalización'}
                        </h3>
                      </div>
                      {opConExtraccionFallida && <span className="badge red">Requiere atención</span>}
                    </div>

                    <div className="workflow-active-status">
                      {etapaWorkflow === 'validacion' && (
                        <article>
                        <span>Validación administrativa</span>
                        <strong>
                          {validacionAdministrativaCompleta ? 'Completa' : validacion?.estado_general || 'Pendiente'}
                        </strong>
                        </article>
                      )}
                      {etapaWorkflow === 'op' && (
                        <article className={opConExtraccionFallida ? 'attention' : ''}>
                          <span>Orden de Pago</span>
                          <strong>{estadoOP}</strong>
                        </article>
                      )}
                      {etapaWorkflow === 'disposicion' && (
                        <article>
                          <span>Disposición</span>
                          <strong>{disposicionBorrador ? 'Borrador' : 'Pendiente'}</strong>
                        </article>
                      )}
                      {etapaWorkflow === 'formalizacion' && (
                        <article>
                          <span>Formalización</span>
                          <strong>{seleccionado.numero_disposicion || 'Disposición emitida'}</strong>
                        </article>
                      )}
                      {etapaWorkflow === 'archivo' && (
                        <article>
                          <span>Archivo</span>
                          <strong>{estadoAdministrativo(seleccionado, historial).texto}</strong>
                        </article>
                      )}
                    </div>
                  </div>
                )}

                {tabDetalle === 'documentos' && (
                  <div className="card">
                    <h3>Documentación del expediente</h3>
                    <div className="upload-grid">
                      <div className="upload-box">
                        <strong>Orden de Pago</strong>
                        {validacionAdministrativaCompleta ? (
                          <>
                            <input type="file" accept=".pdf" onChange={(e) => setArchivoOP(e.target.files?.[0] || null)} />
                            <button className="secondary" onClick={subirOP}>Cargar OP</button>
                          </>
                        ) : (
                          <p className="blocked-note">
                            La Orden de Pago podrá incorporarse una vez completada la validación administrativa.
                          </p>
                        )}
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
                    ) : analisis.modo === 'EXTRACCION_FALLIDA' ? (
                      <div className="warning-panel">
                        <strong>
                          La Orden de Pago fue incorporada al expediente, pero no fue
                          posible extraer la información necesaria para generar la
                          disposición.
                        </strong>
                        <p>
                          No fue posible leer correctamente el contenido de la Orden de Pago.
                        </p>
                      </div>
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
                        <div className="administrative-controls">
                          <section>
                            <h4>Controles obligatorios</h4>
                            <div className="administrative-controls-list">
                              {validacion.controles
                                .filter((control) => CONTROLES_OBLIGATORIOS_VALIDACION.has(control.control))
                                .map((control) => (
                                  <div
                                    className="administrative-control"
                                    key={control.control}
                                    title={control.observacion || undefined}
                                  >
                                    <span
                                      className={`validation-control-icon ${claseValidacion(control.estado)}`}
                                      aria-label={etiquetaValidacion(control.estado)}
                                    >
                                      {iconoValidacion(control.estado)}
                                    </span>
                                    <span>{control.control}</span>
                                  </div>
                                ))}
                            </div>
                          </section>

                          <section>
                            <h4>Documentación y controles complementarios</h4>
                            <div className="administrative-controls-list">
                              {validacion.controles
                                .filter((control) => !CONTROLES_OBLIGATORIOS_VALIDACION.has(control.control))
                                .map((control) => (
                                  <div
                                    className="administrative-control"
                                    key={control.control}
                                    title={control.observacion || undefined}
                                  >
                                    <span
                                      className={`validation-control-icon ${claseValidacion(control.estado)}`}
                                      aria-label={etiquetaValidacion(control.estado)}
                                    >
                                      {iconoValidacion(control.estado)}
                                    </span>
                                    <span>{control.control}</span>
                                  </div>
                                ))}
                            </div>
                          </section>

                          <div className="administrative-controls-legend" aria-label="Referencia de estados">
                            <span><strong>✓</strong> Cumplido</span>
                            <span><strong>!</strong> Advertencia</span>
                            <span><strong>×</strong> Error bloqueante</span>
                          </div>
                        </div>

                        {validacion.estado_general === 'VERDE' && (
                          <div className="validation-action-panel green-panel">
                            <h4>Validación documental completa</h4>
                            <p>Todas las evidencias requeridas fueron acreditadas. El expediente puede ser validado para continuar con la generación de la Disposición.</p>
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
                      <span className="badge yellow">{disposicionBorrador?.estado || 'BORRADOR PLANTILLA'}</span>
                    </div>

                    {!disposicionBorrador ? (
                      <div className="empty-disposition">
                        <p className="empty">Todavía no hay borrador generado para este expediente.</p>
                        {seleccionado.estado === 'VALIDADO' ? (
                          <button className="secondary" onClick={() => prepararDisposicion(false)}>Preparar disposición</button>
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

                          <label>POR ELLO / DISPONE</label>
                          <textarea value={disposicionBorrador.dispone} onChange={(e) => setDisposicionBorrador({ ...disposicionBorrador, dispone: e.target.value })} />

                          <div className="actions">
                            <button className="secondary" onClick={() => prepararDisposicion(true)}>Regenerar borrador</button>
                            <button className="primary" onClick={guardarBorradorDisposicion}>Guardar borrador</button>
                            <button className="secondary" onClick={descargarBorradorTexto}>Exportar texto</button>
                            <button className="primary" onClick={descargarBorradorWord}>Descargar Word</button>
                            {seleccionado.estado === 'VALIDADO' && <button className="primary" onClick={generarDisposicion}>Emitir disposición</button>}
                          </div>
                        </div>

                        <aside className="disposition-aside">
                          <h4>Observaciones IA</h4>
                          {disposicionBorrador.observaciones_ia.map((obs, i) => <p key={i} className="warn">⚠ {obs}</p>)}
                          {fueValidadoConObservaciones(historial) && (
                            <div className="info-note">Este expediente fue validado con observaciones. Revisá el historial antes de emitir.</div>
                          )}
                          <div className="info-note">Plantilla institucional 2026.2 aplicada. La exportación Word está disponible. La exportación PDF queda preparada para el próximo sprint.</div>
                          <div className="template-status">
                            <strong>Vista documento institucional</strong>
                            <span>Tablas dinámicas · Negritas controladas · Variables oficiales</span>
                          </div>
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

              <aside className="next-action-panel">
                <section>
                  <span className="eyebrow">Próxima acción recomendada</span>
                  <p>{accionPrincipal.descripcion}</p>
                  <button
                    className="primary next-action-button"
                    type="button"
                    onClick={accionPrincipal.ejecutar}
                  >
                    {accionPrincipal.etiqueta}
                  </button>
                </section>

                <section>
                  <span className="eyebrow">Acciones disponibles</span>
                  <nav className="workflow-consultations">
                    <button
                      className={tabDetalle === 'workflow' ? 'active' : ''}
                      type="button"
                      onClick={() => setTabDetalle('workflow')}
                    >
                      Estado del trámite
                    </button>
                    <button
                      className={tabDetalle === 'documentos' ? 'active' : ''}
                      type="button"
                      onClick={() => setTabDetalle('documentos')}
                    >
                      Documentos
                    </button>
                    <button
                      className={tabDetalle === 'ia' ? 'active' : ''}
                      type="button"
                      onClick={() => setTabDetalle('ia')}
                    >
                      Análisis
                    </button>
                    <button
                      className={tabDetalle === 'historial' ? 'active' : ''}
                      type="button"
                      onClick={() => setTabDetalle('historial')}
                    >
                      Historial
                    </button>
                    <button
                      className={tabDetalle === 'validacion' ? 'active' : ''}
                      type="button"
                      onClick={consultarValidacion}
                    >
                      Validación
                    </button>
                    {solicitudOrigenExpediente && (
                      <button type="button" onClick={abrirSolicitudOrigen}>
                        Abrir Solicitud
                      </button>
                    )}
                  </nav>
                </section>
              </aside>
            </div>
          </section>
        )}

        {pantalla === 'administracion' && (
          <section className="card">
            <div className="card-title">
              <h3>Administración institucional</h3>
              <span className="badge blue">Parámetros del sistema</span>
            </div>

            {parametrosInstitucionales ? (
              <>
                <div className="admin-grid">
                  <div>
                    <strong>Unidad de Contratación</strong>
                    <label>Valor UC</label>
                    <input type="number" value={parametrosInstitucionales.valor_uc} onChange={(e) => setParametrosInstitucionales({ ...parametrosInstitucionales, valor_uc: Number(e.target.value) })} />
                    <label>Norma UC vigente</label>
                    <input value={parametrosInstitucionales.norma_uc} onChange={(e) => setParametrosInstitucionales({ ...parametrosInstitucionales, norma_uc: e.target.value })} />
                    <label>Fecha de vigencia</label>
                    <input value={parametrosInstitucionales.fecha_vigencia_uc} onChange={(e) => setParametrosInstitucionales({ ...parametrosInstitucionales, fecha_vigencia_uc: e.target.value })} />
                  </div>

                  <div>
                    <strong>Ejercicio y numeración</strong>
                    <label>Ejercicio</label>
                    <input type="number" value={parametrosInstitucionales.ejercicio} onChange={(e) => setParametrosInstitucionales({ ...parametrosInstitucionales, ejercicio: Number(e.target.value) })} />
                    <label>Próxima disposición</label>
                    <input type="number" value={parametrosInstitucionales.proxima_disposicion} onChange={(e) => setParametrosInstitucionales({ ...parametrosInstitucionales, proxima_disposicion: Number(e.target.value) })} />
                  </div>

                  <div>
                    <strong>Datos institucionales</strong>
                    <label>Organismo</label>
                    <input value={parametrosInstitucionales.organismo} onChange={(e) => setParametrosInstitucionales({ ...parametrosInstitucionales, organismo: e.target.value })} />
                    <label>Distrito</label>
                    <input value={parametrosInstitucionales.distrito} onChange={(e) => setParametrosInstitucionales({ ...parametrosInstitucionales, distrito: e.target.value })} />
                    <label>Localidad</label>
                    <input value={parametrosInstitucionales.localidad} onChange={(e) => setParametrosInstitucionales({ ...parametrosInstitucionales, localidad: e.target.value })} />
                  </div>

                  <div>
                    <strong>Plantillas</strong>
                    <p>Disposición FC 2026.2 activa.</p>
                    <p className="muted">El versionado y la carga de nuevas plantillas quedan preparados para próximos sprints.</p>
                  </div>
                </div>

                <div className="actions">
                  <button className="primary" onClick={guardarParametrosInstitucionales}>Guardar parámetros</button>
                </div>
              </>
            ) : (
              <p className="empty">Cargando parámetros institucionales...</p>
            )}
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
      <thead><tr><th>Expediente</th><th>Expediente GDEBA</th><th>ID SUNA</th><th>Área</th><th>Estado</th><th>Establecimiento</th><th></th></tr></thead>
      <tbody>
        {expedientes.map((exp) => (
          <tr key={exp.id}>
            <td>{exp.numero_interno}</td>
            <td>{exp.numero_gdeba || '-'}</td>
            <td>{exp.id_suna || '-'}</td>
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
