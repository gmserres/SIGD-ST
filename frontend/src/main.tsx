import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Archive,
  ArrowLeft,
  Building2,
  Bus,
  Check,
  ChevronDown,
  ChevronUp,
  CircleCheck,
  CircleDot,
  Circle,
  CircleX,
  ClipboardList,
  Download,
  ExternalLink,
  FileSignature,
  FileText,
  FolderOpen,
  History,
  Landmark,
  LayoutDashboard,
  PenLine,
  ReceiptText,
  RefreshCw,
  Save,
  ScanSearch,
  Search,
  Settings,
  TriangleAlert,
} from 'lucide-react';
import { API_URL } from './api/config';
import { PanelBusquedaFiltros } from './components/PanelBusquedaFiltros';
import {
  ControlProveedorOPCard,
} from './components/proveedores/ControlProveedorOPCard';
import { DisposicionOPCard } from './components/disposiciones/DisposicionOPCard';
import { ProveedorActualCard } from './components/proveedores/ProveedorActualCard';
import { ProveedoresAdmin } from './components/proveedores/ProveedoresAdmin';
import { CompletitudExpedienteCard } from './components/expedientes/CompletitudExpedienteCard';
import './styles.css';

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
type TabGestionSolicitud = 'tramitacion' | 'historial';

type TrabajoMesa = {
  clave: string;
  tipo: 'Solicitud' | 'Expediente';
  identificador: string;
  establecimiento: string;
  asunto: string;
  estado: string;
  accion: string;
  prioridad?: string;
  fecha: string;
  abrir: () => void;
};

const filtrosRapidosSolicitudes = [
  { value: 'todos', label: 'Todos' },
  {
    value: 'pendientes-de-decision',
    label: 'Pendientes de decisión',
  },
  { value: 'hoy', label: 'Hoy' },
  { value: 'validacion', label: 'Validación' },
  { value: 'disposicion', label: 'Disposición' },
  { value: 'finalizados', label: 'Finalizados' },
] as const;

const SIN_PRIORIDAD = '__SIN_PRIORIDAD__';

const filtrosAvanzadosSolicitudesIniciales = {
  establecimiento: '',
  fondo: '',
  prioridad: '',
  fechaDesde: '',
  fechaHasta: '',
};

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
  fecha_firma?: string | null;
  usuario_registro_firma?: string | null;
  fecha_archivo?: string | null;
  usuario_registro_archivo?: string | null;
  fecha_cierre?: string | null;
  usuario_registro_cierre?: string | null;
  registrado_cierre_en?: string | null;
  fecha_desistimiento?: string | null;
  usuario_registro_desistimiento?: string | null;
  registrado_desistimiento_en?: string | null;
  motivo_desistimiento?: string | null;
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

type EventoHistorialSolicitud =
  | {
      tipo: 'solicitud';
      id: string;
      fecha: string;
      solicitud: SolicitudIntervencion;
    }
  | {
      tipo: 'decision';
      id: string;
      fecha: string;
      decision: DecisionAdministrativa;
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

type DisposicionEmitida = {
  id_disposicion: string;
  expediente_id: string;
  configuracion_uc_id: string;
  numero_disposicion: string;
  fecha_emision: string;
  fondo_interviniente: string;
  numero_op: string;
  numero_liquidacion: string | null;
  proveedor: string;
  cuit: string;
  importe: string | number;
  objeto: string;
  establecimiento: string;
  valor_uc_aplicado: string | number;
  cantidad_uc: string | number;
  procedimiento_contratacion: string;
  norma_uc: string;
  texto_emitido: string;
  ruta_docx: string;
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

function formatearCantidadUC(valor: string | number | null | undefined) {
  if (valor === null || valor === undefined || valor === '') return '-';

  const cantidad = typeof valor === 'number' ? valor : Number(valor);
  if (!Number.isFinite(cantidad)) return String(valor);

  return new Intl.NumberFormat('es-AR', {
    maximumFractionDigits: 20,
    useGrouping: true,
  }).format(cantidad);
}

function formatearFechaHora(valor: string) {
  const fechaSinHora = /^(\d{4})-(\d{2})-(\d{2})$/.exec(valor);
  if (fechaSinHora) {
    const [, anio, mes, dia] = fechaSinHora;
    return new Intl.DateTimeFormat('es-AR').format(
      new Date(Number(anio), Number(mes) - 1, Number(dia)),
    );
  }

  return new Intl.DateTimeFormat('es-AR', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(valor));
}

function formatearFecha(valor: string) {
  const [anio, mes, dia] = valor.split('-');
  return anio && mes && dia ? `${dia}/${mes}/${anio}` : valor;
}

function fechaLocalISO(fecha = new Date()) {
  const anio = fecha.getFullYear();
  const mes = String(fecha.getMonth() + 1).padStart(2, '0');
  const dia = String(fecha.getDate()).padStart(2, '0');
  return `${anio}-${mes}-${dia}`;
}

function normalizarTextoBusqueda(valor: unknown) {
  return String(valor ?? '')
    .trim()
    .toLocaleLowerCase('es')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');
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
    CERRADO: 'Cerrado',
    DESISTIDO: 'Desistido',
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
  if (['VALIDADO', 'DISPOSICION_EMITIDA', 'FIRMADO', 'ARCHIVADO', 'CERRADO'].includes(estado)) return 'badge green';
  if (estado === 'DESISTIDO') return 'badge gray';
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
  if (estado === 'OK') return <CircleCheck aria-hidden="true" />;
  if (estado === 'ADVERTENCIA') return <TriangleAlert aria-hidden="true" />;
  return <CircleX aria-hidden="true" />;
}

function IndicadorBinario({ completo }: { completo: boolean }) {
  return completo
    ? <CircleCheck className="inline-status-icon" aria-hidden="true" />
    : <Circle className="inline-status-icon" aria-hidden="true" />;
}

function IconoEtapaWorkflow({ id, completada }: { id: string; completada: boolean }) {
  if (completada) return <Check aria-hidden="true" />;
  if (id === 'validacion') return <CircleCheck aria-hidden="true" />;
  if (id === 'op') return <ReceiptText aria-hidden="true" />;
  if (id === 'disposicion') return <FileSignature aria-hidden="true" />;
  if (id === 'formalizacion') return <PenLine aria-hidden="true" />;
  return <Archive aria-hidden="true" />;
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
      const mensajes = data.detail
        .map((item: { loc?: unknown[]; msg?: string; type?: string }) => {
          const esFechaIngreso = item.loc?.includes('fecha_ingreso');
          const esErrorFecha = /^(date|datetime)_/.test(item.type || '');
          if (esFechaIngreso && esErrorFecha) return 'La fecha de ingreso no es válida.';
          return item.msg;
        })
        .filter(Boolean);
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
  const solicitudAnalisisActual = useRef(0);
  const [pantalla, setPantalla] = useState<Pantalla>('inicio');
  const [tabDetalle, setTabDetalle] = useState<TabDetalle>('workflow');
  const [expedientes, setExpedientes] = useState<Expediente[]>([]);
  const [cargandoExpedientes, setCargandoExpedientes] = useState(false);
  const [errorExpedientes, setErrorExpedientes] = useState('');
  const [seleccionado, setSeleccionado] = useState<Expediente | null>(null);
  const [revisionProveedor, setRevisionProveedor] = useState(0);
  const [documentos, setDocumentos] = useState<Documento[]>([]);
  const [historial, setHistorial] = useState<Historial[]>([]);
  const [analisis, setAnalisis] = useState<AnalisisOP | null>(null);
  const [cargandoAnalisis, setCargandoAnalisis] = useState(false);
  const [errorAnalisis, setErrorAnalisis] = useState('');
  const [validacion, setValidacion] = useState<Validacion | null>(null);
  const [disposicionBorrador, setDisposicionBorrador] = useState<Disposicion | null>(null);
  const [disposicionEmitidaDetalle, setDisposicionEmitidaDetalle] = useState<DisposicionEmitida | null>(null);
  const [cargandoDisposicionEmitida, setCargandoDisposicionEmitida] = useState(false);
  const [errorDisposicionEmitida, setErrorDisposicionEmitida] = useState('');
  const [mostrarTextoBorrador, setMostrarTextoBorrador] = useState(false);
  const [mostrarTextoDisposicionEmitida, setMostrarTextoDisposicionEmitida] = useState(false);
  const [fechaFirma, setFechaFirma] = useState('');
  const [registrandoFirma, setRegistrandoFirma] = useState(false);
  const [fechaArchivo, setFechaArchivo] = useState('');
  const [registrandoArchivo, setRegistrandoArchivo] = useState(false);
  const [numeroDisposicionEditable, setNumeroDisposicionEditable] = useState('');
  const [guardandoNumeroDisposicion, setGuardandoNumeroDisposicion] = useState(false);
  const [errorNumeroDisposicion, setErrorNumeroDisposicion] = useState('');
  const [checklistFisico, setChecklistFisico] = useState<ChecklistFisico>({ factura: false, remito_conformidad: false, cae: false, arca: false, arba: false, observaciones: '' });
  const [mostrarChecklistFisico, setMostrarChecklistFisico] = useState(false);
  const [mensaje, setMensaje] = useState('');
  const [mensajeTipo, setMensajeTipo] = useState<'ok' | 'error' | 'info'>('info');
  const [solicitudes, setSolicitudes] = useState<SolicitudIntervencion[]>([]);
  const [busquedaSolicitudes, setBusquedaSolicitudes] = useState('');
  const [filtroRapidoSolicitudes, setFiltroRapidoSolicitudes] =
    useState('todos');
  const [
    filtrosAvanzadosSolicitudes,
    setFiltrosAvanzadosSolicitudes,
  ] = useState(filtrosAvanzadosSolicitudesIniciales);

  function limpiarFiltrosSolicitudes() {
    setBusquedaSolicitudes('');
    setFiltroRapidoSolicitudes('todos');
    setFiltrosAvanzadosSolicitudes(filtrosAvanzadosSolicitudesIniciales);
  }

  const [solicitudSeleccionada, setSolicitudSeleccionada] = useState<SolicitudIntervencion | null>(null);
  const [mostrarFormularioSolicitud, setMostrarFormularioSolicitud] = useState(false);
  const [tabGestionSolicitud, setTabGestionSolicitud] = useState<TabGestionSolicitud>('tramitacion');
  const [informacionAdministrativaExpandida, setInformacionAdministrativaExpandida] = useState(true);
  const [solicitudOrigenExpediente, setSolicitudOrigenExpediente] = useState<SolicitudIntervencion | null>(null);
  const [decisionOrigenExpediente, setDecisionOrigenExpediente] = useState<DecisionAdministrativa | null>(null);
  const [cargandoSolicitudes, setCargandoSolicitudes] = useState(false);
  const [guardandoSolicitud, setGuardandoSolicitud] = useState(false);
  const [errorSolicitudes, setErrorSolicitudes] = useState('');
  const [errorCargaSolicitudes, setErrorCargaSolicitudes] = useState('');

  const [decisiones, setDecisiones] = useState<DecisionAdministrativa[]>([]);
  const [decisionesMesa, setDecisionesMesa] = useState<DecisionAdministrativa[]>([]);
  const [cargandoDecisionesMesa, setCargandoDecisionesMesa] = useState(false);
  const [errorDecisionesMesa, setErrorDecisionesMesa] = useState('');
  const [cargandoDecisiones, setCargandoDecisiones] = useState(false);
  const [guardandoDecision, setGuardandoDecision] = useState(false);
  const [errorDecisiones, setErrorDecisiones] = useState('');
  const [decisionAutoridad, setDecisionAutoridad] = useState('');
  const [decisionFecha, setDecisionFecha] = useState('');
  const [decisionResultado, setDecisionResultado] = useState('');
  const [decisionFundamento, setDecisionFundamento] = useState('');
  const [decisionFondoInterviniente, setDecisionFondoInterviniente] = useState('');
  const [decisionDescripcionFondo, setDecisionDescripcionFondo] = useState('');
  const [decisionUsuarioRegistrante] = useState('Secretario Técnico');
  const [decisionRecienCreadaId, setDecisionRecienCreadaId] = useState<string | null>(null);

  const [decisionExpedienteActiva, setDecisionExpedienteActiva] = useState<string | null>(null);
  const [expedienteDecisionNumeroInterno, setExpedienteDecisionNumeroInterno] = useState('');
  const [expedienteDecisionNumeroGdeba, setExpedienteDecisionNumeroGdeba] = useState('');
  const [guardandoExpedienteDecision, setGuardandoExpedienteDecision] = useState(false);
  const [errorExpedienteDecision, setErrorExpedienteDecision] = useState('');

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

  const datosMesa = useMemo(() => {
    const solicitudesConDecision = new Set(
      decisionesMesa.map((decision) => decision.solicitud_intervencion_id),
    );
    const solicitudesPorDecidir = solicitudes.filter(
      (solicitud) => !solicitudesConDecision.has(solicitud.id_solicitud),
    );
    const expedientesEnTramite = expedientes.filter(
      (expediente) => expediente.estado !== 'ARCHIVADO',
    );
    const esperandoValidacion = expedientes.filter(
      (expediente) => expediente.estado === 'PENDIENTE_VALIDACION',
    );
    const disposicionesPorEmitir = expedientes.filter(
      (expediente) => expediente.estado === 'VALIDADO',
    );
    const firmasPendientes = expedientes.filter(
      (expediente) => expediente.estado === 'DISPOSICION_EMITIDA',
    );
    const archivosPendientes = expedientes.filter(
      (expediente) => expediente.estado === 'FIRMADO',
    );

    return {
      solicitudesPorDecidir,
      expedientesEnTramite,
      esperandoValidacion,
      disposicionesPorEmitir,
      firmasPendientes,
      archivosPendientes,
    };
  }, [solicitudes, expedientes, decisionesMesa]);

  const solicitudesRecientesMesa = useMemo(
    () => [...solicitudes]
      .sort((a, b) => b.fecha_ingreso.localeCompare(a.fecha_ingreso))
      .slice(0, 5),
    [solicitudes],
  );

  const opcionesEstablecimientoSolicitudes = useMemo(
    () =>
      Array.from(
        new Set(
          solicitudes
            .map((solicitud) => solicitud.establecimiento.trim())
            .filter(Boolean),
        ),
      )
        .sort((a, b) => a.localeCompare(b, 'es'))
        .map((establecimiento) => ({
          value: establecimiento,
          label: establecimiento,
        })),
    [solicitudes],
  );

  const opcionesFondoSolicitudes = useMemo(
    () =>
      Array.from(
        new Set(
          decisionesMesa
            .map((decision) => decision.fondo_interviniente)
            .filter((fondo): fondo is NonNullable<
              DecisionAdministrativa['fondo_interviniente']
            > => Boolean(fondo)),
        ),
      )
        .sort((a, b) =>
          etiquetaFondoInterviniente(a).localeCompare(
            etiquetaFondoInterviniente(b),
            'es',
          ),
        )
        .map((fondo) => ({
          value: fondo,
          label: etiquetaFondoInterviniente(fondo),
        })),
    [decisionesMesa],
  );

  const opcionesPrioridadSolicitudes = useMemo(() => {
    const prioridades = Array.from(
      new Set(
        solicitudes
          .map((solicitud) => solicitud.prioridad.trim())
          .filter(Boolean),
      ),
    )
      .sort((a, b) => a.localeCompare(b, 'es'))
      .map((prioridad) => ({
        value: prioridad,
        label: prioridad,
      }));

    const existenSolicitudesSinPrioridad = solicitudes.some(
      (solicitud) => !solicitud.prioridad.trim(),
    );

    return existenSolicitudesSinPrioridad
      ? [
          ...prioridades,
          { value: SIN_PRIORIDAD, label: 'Sin prioridad' },
        ]
      : prioridades;
  }, [solicitudes]);

  const configuracionFiltrosAvanzadosSolicitudes = [
    {
      key: 'establecimiento',
      label: 'Establecimiento',
      type: 'select' as const,
      placeholder: 'Todos',
      options: opcionesEstablecimientoSolicitudes,
    },
    {
      key: 'fondo',
      label: 'Fondo',
      type: 'select' as const,
      placeholder: 'Todos',
      options: opcionesFondoSolicitudes,
    },
    {
      key: 'prioridad',
      label: 'Prioridad',
      type: 'select' as const,
      placeholder: 'Todas',
      options: opcionesPrioridadSolicitudes,
    },
    {
      key: 'fechaDesde',
      label: 'Fecha desde',
      type: 'date' as const,
    },
    {
      key: 'fechaHasta',
      label: 'Fecha hasta',
      type: 'date' as const,
    },
  ];

  const busquedaSolicitudesNormalizada =
    normalizarTextoBusqueda(busquedaSolicitudes);

  const filtrosActivosSolicitudes: {
    key: string;
    label: string;
    onRemove: () => void;
  }[] = [];

  if (busquedaSolicitudesNormalizada) {
    filtrosActivosSolicitudes.push({
      key: 'busqueda',
      label: `Búsqueda: ${busquedaSolicitudes}`,
      onRemove: () => setBusquedaSolicitudes(''),
    });
  }

  if (filtroRapidoSolicitudes !== 'todos') {
    const filtroRapidoActivo = filtrosRapidosSolicitudes.find(
      (filtro) => filtro.value === filtroRapidoSolicitudes,
    );

    if (filtroRapidoActivo) {
      filtrosActivosSolicitudes.push({
        key: 'filtro-rapido',
        label: filtroRapidoActivo.label,
        onRemove: () => setFiltroRapidoSolicitudes('todos'),
      });
    }
  }

  if (filtrosAvanzadosSolicitudes.establecimiento) {
    filtrosActivosSolicitudes.push({
      key: 'establecimiento',
      label: `Establecimiento: ${filtrosAvanzadosSolicitudes.establecimiento}`,
      onRemove: () =>
        setFiltrosAvanzadosSolicitudes((filtrosActuales) => ({
          ...filtrosActuales,
          establecimiento: '',
        })),
    });
  }

  if (filtrosAvanzadosSolicitudes.fondo) {
    filtrosActivosSolicitudes.push({
      key: 'fondo',
      label: `Fondo: ${etiquetaFondoInterviniente(
        filtrosAvanzadosSolicitudes.fondo,
      )}`,
      onRemove: () =>
        setFiltrosAvanzadosSolicitudes((filtrosActuales) => ({
          ...filtrosActuales,
          fondo: '',
        })),
    });
  }

  if (filtrosAvanzadosSolicitudes.prioridad) {
    const prioridadActiva =
      filtrosAvanzadosSolicitudes.prioridad === SIN_PRIORIDAD
        ? 'Sin prioridad'
        : filtrosAvanzadosSolicitudes.prioridad;

    filtrosActivosSolicitudes.push({
      key: 'prioridad',
      label: `Prioridad: ${prioridadActiva}`,
      onRemove: () =>
        setFiltrosAvanzadosSolicitudes((filtrosActuales) => ({
          ...filtrosActuales,
          prioridad: '',
        })),
    });
  }

  if (filtrosAvanzadosSolicitudes.fechaDesde) {
    filtrosActivosSolicitudes.push({
      key: 'fecha-desde',
      label: `Desde: ${formatearFecha(
        filtrosAvanzadosSolicitudes.fechaDesde,
      )}`,
      onRemove: () =>
        setFiltrosAvanzadosSolicitudes((filtrosActuales) => ({
          ...filtrosActuales,
          fechaDesde: '',
        })),
    });
  }

  if (filtrosAvanzadosSolicitudes.fechaHasta) {
    filtrosActivosSolicitudes.push({
      key: 'fecha-hasta',
      label: `Hasta: ${formatearFecha(
        filtrosAvanzadosSolicitudes.fechaHasta,
      )}`,
      onRemove: () =>
        setFiltrosAvanzadosSolicitudes((filtrosActuales) => ({
          ...filtrosActuales,
          fechaHasta: '',
        })),
    });
  }

  const filtrosAvanzadosSolicitudesActivos = Object.values(
    filtrosAvanzadosSolicitudes,
  ).some(Boolean);

  const filtrosSolicitudesActivos =
    Boolean(busquedaSolicitudesNormalizada) ||
    filtroRapidoSolicitudes !== 'todos' ||
    filtrosAvanzadosSolicitudesActivos;

  const solicitudesFiltradas = useMemo(() => {
    return solicitudes.filter((solicitud) => {
      const coincideBusqueda =
        !busquedaSolicitudesNormalizada ||
        [
          solicitud.numero_solicitud,
          solicitud.establecimiento,
          solicitud.id_suna,
          solicitud.solicitante,
        ].some((campo) =>
          normalizarTextoBusqueda(campo).includes(
            busquedaSolicitudesNormalizada,
          ),
        );

      if (!coincideBusqueda) {
        return false;
      }

      if (
        filtrosAvanzadosSolicitudes.establecimiento &&
        solicitud.establecimiento !==
          filtrosAvanzadosSolicitudes.establecimiento
      ) {
        return false;
      }

      if (
        filtrosAvanzadosSolicitudes.prioridad === SIN_PRIORIDAD
          ? Boolean(solicitud.prioridad.trim())
          : filtrosAvanzadosSolicitudes.prioridad &&
            solicitud.prioridad !== filtrosAvanzadosSolicitudes.prioridad
      ) {
        return false;
      }

      if (
        filtrosAvanzadosSolicitudes.fechaDesde &&
        solicitud.fecha_ingreso < filtrosAvanzadosSolicitudes.fechaDesde
      ) {
        return false;
      }

      if (
        filtrosAvanzadosSolicitudes.fechaHasta &&
        solicitud.fecha_ingreso > filtrosAvanzadosSolicitudes.fechaHasta
      ) {
        return false;
      }

      const decisionesSolicitud = decisionesMesa.filter(
        (decision) =>
          decision.solicitud_intervencion_id ===
          solicitud.id_solicitud,
      );

      if (
        filtrosAvanzadosSolicitudes.fondo &&
        !decisionesSolicitud.some(
          (decision) =>
            decision.fondo_interviniente ===
            filtrosAvanzadosSolicitudes.fondo,
        )
      ) {
        return false;
      }

      const tieneDecision = decisionesSolicitud.length > 0;

      const expedientesSolicitud = expedientes.filter(
        (expediente) =>
          expediente.solicitud_intervencion_id ===
          solicitud.id_solicitud,
      );

      switch (filtroRapidoSolicitudes) {
        case 'pendientes-de-decision':
          return !tieneDecision;
        case 'hoy':
          return solicitud.fecha_ingreso === fechaLocalISO();
        case 'validacion':
          return expedientesSolicitud.some((expediente) =>
            [
              'PENDIENTE_VALIDACION',
              'PENDIENTE_REVALIDACION',
            ].includes(expediente.estado),
          );
        case 'disposicion':
          return expedientesSolicitud.some(
            (expediente) => expediente.estado === 'VALIDADO',
          );
        case 'finalizados':
          return expedientesSolicitud.some(
            (expediente) => expediente.estado === 'ARCHIVADO',
          );
        default:
          return true;
      }
    });
  }, [
    solicitudes,
    busquedaSolicitudesNormalizada,
    filtroRapidoSolicitudes,
    filtrosAvanzadosSolicitudes,
    decisionesMesa,
    expedientes,
  ]);

  const historialSolicitud = useMemo<EventoHistorialSolicitud[]>(() => {
    if (!solicitudSeleccionada) {
      return [];
    }

    const decisionesSolicitud = decisiones.filter(
      (decision) =>
        decision.solicitud_intervencion_id ===
        solicitudSeleccionada.id_solicitud,
    );
    const eventos: EventoHistorialSolicitud[] = [
      {
        tipo: 'solicitud',
        id: solicitudSeleccionada.id_solicitud,
        fecha: solicitudSeleccionada.fecha_ingreso,
        solicitud: solicitudSeleccionada,
      },
      ...decisionesSolicitud.map(
        (decision): EventoHistorialSolicitud => ({
          tipo: 'decision',
          id: decision.id_decision,
          fecha: decision.fecha_decision,
          decision,
        }),
      ),
    ];

    return eventos.sort((eventoA, eventoB) => {
      if (eventoA.fecha !== eventoB.fecha) {
        return eventoA.fecha < eventoB.fecha ? -1 : 1;
      }

      if (eventoA.tipo !== eventoB.tipo) {
        return eventoA.tipo === 'solicitud' ? -1 : 1;
      }

      if (eventoA.id === eventoB.id) {
        return 0;
      }

      return eventoA.id < eventoB.id ? -1 : 1;
    });
  }, [solicitudSeleccionada, decisiones]);

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
      cargarCatalogo('/catalogos/autoridades-decisoras', setCatalogoAutoridadesDecisoras),
      cargarCatalogo('/catalogos/resultados-decision', setCatalogoResultadosDecision),
    ]);
  }

  async function cargarExpedientes() {
    setCargandoExpedientes(true);
    setErrorExpedientes('');

    try {
      const res = await fetch(`${API_URL}/expedientes`);
      if (!res.ok) {
        setExpedientes([]);
        setErrorExpedientes('No fue posible recuperar los expedientes.');
        return;
      }
      const disponibles = await res.json();
      if (!Array.isArray(disponibles)) {
        throw new Error('Respuesta inesperada al consultar expedientes.');
      }
      setExpedientes(disponibles);
    } catch {
      setExpedientes([]);
      setErrorExpedientes('No fue posible recuperar los expedientes.');
    } finally {
      setCargandoExpedientes(false);
    }
  }

  async function cargarSolicitudes() {
    setCargandoSolicitudes(true);
    setErrorSolicitudes('');
    setErrorCargaSolicitudes('');

    try {
      const res = await fetch(`${API_URL}/solicitudes`);
      if (!res.ok) {
        setSolicitudes([]);
        setErrorCargaSolicitudes('No fue posible recuperar las solicitudes.');
        return;
      }
      const disponibles = await res.json();
      if (!Array.isArray(disponibles)) {
        throw new Error('Respuesta inesperada al consultar solicitudes.');
      }
      setSolicitudes(disponibles);
    } catch {
      setSolicitudes([]);
      setErrorCargaSolicitudes('No fue posible recuperar las solicitudes.');
    } finally {
      setCargandoSolicitudes(false);
    }
  }

  async function cargarDecisionesMesa() {
    setCargandoDecisionesMesa(true);
    setErrorDecisionesMesa('');

    try {
      const res = await fetch(`${API_URL}/decisiones`);
      if (!res.ok) {
        setDecisionesMesa([]);
        setErrorDecisionesMesa('No fue posible recuperar las decisiones administrativas.');
        return;
      }
      const disponibles = await res.json();
      if (!Array.isArray(disponibles)) {
        throw new Error('Respuesta inesperada al consultar decisiones.');
      }
      setDecisionesMesa(disponibles);
    } catch {
      setDecisionesMesa([]);
      setErrorDecisionesMesa('No fue posible recuperar las decisiones administrativas.');
    } finally {
      setCargandoDecisionesMesa(false);
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
    setMostrarFormularioSolicitud(false);
    setSolicitudSeleccionada(null);
    setTabGestionSolicitud('tramitacion');
    setInformacionAdministrativaExpandida(true);
    setMensaje('');
    await cargarSolicitudes();
  }

  async function seleccionarSolicitud(solicitud: SolicitudIntervencion) {
    setPantalla('solicitudes');
    setMostrarFormularioSolicitud(false);
    setTabGestionSolicitud('tramitacion');
    setInformacionAdministrativaExpandida(true);
    setSolicitudSeleccionada(solicitud);
    setMensaje('');
    await cargarDecisiones(solicitud.id_solicitud);
  }

  async function abrirSolicitudDesdeBandeja(
    solicitud: SolicitudIntervencion,
  ) {
    await seleccionarSolicitud(solicitud);
  }

  function volverASolicitudes() {
    setSolicitudSeleccionada(null);
    setDecisiones([]);
    setTabGestionSolicitud('tramitacion');
    setInformacionAdministrativaExpandida(true);
  }

  async function abrirNuevaSolicitud() {
    setPantalla('solicitudes');
    setMostrarFormularioSolicitud(true);
    setSolicitudSeleccionada(null);
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

  function cancelarNuevaSolicitud() {
    setMostrarFormularioSolicitud(false);
    setErrorSolicitudes('');
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
      setMostrarFormularioSolicitud(false);
      await cargarDecisiones(creada.id_solicitud);
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

    if (
      decisionResultado === 'Aprobar intervención'
      && decisionFondoInterviniente === 'OTRO'
      && !decisionDescripcionFondo.trim()
    ) {
      setErrorDecisiones(
        'Debe describir el Fondo Interviniente seleccionado.',
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
          fondo_interviniente:
            decisionResultado === 'Aprobar intervención'
              ? decisionFondoInterviniente || null
              : null,
          descripcion_fondo:
            decisionResultado === 'Aprobar intervención'
              && decisionFondoInterviniente === 'OTRO'
              ? decisionDescripcionFondo || null
              : null,
          usuario_registrante: decisionUsuarioRegistrante,
        }),
      });

      if (!res.ok) {
        setErrorDecisiones(await obtenerMensajeError(res));
        return;
      }

      const creada: DecisionAdministrativa = await res.json();
      await cargarDecisiones(solicitudSeleccionada.id_solicitud);
      setDecisionesMesa((actuales) => [...actuales, creada]);
      setDecisionRecienCreadaId(creada.id_decision);
      setDecisionExpedienteActiva(null);
      setDecisionAutoridad('');
      setDecisionFecha('');
      setDecisionResultado('');
      setDecisionFundamento('');
      setDecisionFondoInterviniente('');
      setDecisionDescripcionFondo('');
      avisar(
        creada.resultado === 'Aprobar intervención'
          && creada.fondo_interviniente === 'FONDO_COMPENSADOR'
          ? 'Decisión registrada correctamente. Próxima etapa disponible: Expediente.'
          : 'Decisión registrada correctamente.',
        'ok',
      );
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

  async function cargarDisposicionEmitida(expediente: Expediente) {
    setDisposicionEmitidaDetalle(null);
    setErrorDisposicionEmitida('');
    setCargandoDisposicionEmitida(false);

    if (!['DISPOSICION_EMITIDA', 'FIRMADO', 'ARCHIVADO'].includes(expediente.estado)) return;

    setDisposicionBorrador(null);
    setCargandoDisposicionEmitida(true);
    try {
      const res = await fetch(`${API_URL}/expedientes/${expediente.id}/disposicion`);
      if (res.status === 404) {
        setErrorDisposicionEmitida('La Disposición emitida no pudo recuperarse.');
        return;
      }
      if (!res.ok) {
        setErrorDisposicionEmitida(await obtenerMensajeError(res));
        return;
      }
      setDisposicionEmitidaDetalle(await res.json());
    } catch {
      setErrorDisposicionEmitida('No se pudo conectar con el backend para recuperar la Disposición emitida.');
    } finally {
      setCargandoDisposicionEmitida(false);
    }
  }

  async function cargarDetalle(expediente: Expediente) {
    const solicitudAnalisis = ++solicitudAnalisisActual.current;
    setSeleccionado(expediente);
    setPantalla('detalle');
    setTabDetalle('workflow');
    setAnalisis(null);
    setCargandoAnalisis(false);
    setErrorAnalisis('');
    setMensaje('');
    setSolicitudOrigenExpediente(null);
    setDecisionOrigenExpediente(null);
    const disposicionEmitidaPromise = cargarDisposicionEmitida(expediente);

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

    const documentosCargados = await docsRes.json();
    setDocumentos(documentosCargados);
    setHistorial(await histRes.json());

    if (
      Array.isArray(documentosCargados)
      && documentosCargados.some((documento: Documento) => documento.tipo === 'OP')
    ) {
      setCargandoAnalisis(true);
      try {
        const analisisRes = await fetch(
          `${API_URL}/expedientes/${expediente.id}/analisis-op`,
        );
        if (analisisRes.ok) {
          const analisisRecuperado = await analisisRes.json();
          if (solicitudAnalisis === solicitudAnalisisActual.current) {
            setAnalisis(analisisRecuperado);
          }
        } else if (analisisRes.status !== 404) {
          const error = await obtenerMensajeError(analisisRes);
          if (solicitudAnalisis === solicitudAnalisisActual.current) {
            setErrorAnalisis(error);
          }
        }
      } catch {
        if (solicitudAnalisis === solicitudAnalisisActual.current) {
          setErrorAnalisis(
            'No fue posible recuperar el análisis vigente de la Orden de Pago.',
          );
        }
      } finally {
        if (solicitudAnalisis === solicitudAnalisisActual.current) {
          setCargandoAnalisis(false);
        }
      }
    }

    if (solicitudOrigenRes?.ok) {
      setSolicitudOrigenExpediente(await solicitudOrigenRes.json());
    }

    if (decisionOrigenRes?.ok) {
      setDecisionOrigenExpediente(await decisionOrigenRes.json());
    }

    await disposicionEmitidaPromise;
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
    setErrorAnalisis('');
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
    if (!seleccionado) return false;
    const res = await fetch(`${API_URL}/expedientes/${seleccionado.id}/disposicion/borrador?regenerar=${regenerar}`, { method: 'POST' });

    if (!res.ok) {
      avisar(await obtenerMensajeError(res), 'error');
      return false;
    }

    const data = await res.json();
    setDisposicionBorrador(data);
    setTabDetalle('disposicion');
    avisar('Borrador de disposición generado correctamente.', 'ok');
    return true;
  }

  async function guardarNumeroDisposicion() {
    if (!seleccionado) return;

    const numeroNormalizado = numeroDisposicionEditable.trim();
    if (!numeroNormalizado) {
      setErrorNumeroDisposicion('Ingresá un número de Disposición antes de guardarlo.');
      return;
    }

    setGuardandoNumeroDisposicion(true);
    setErrorNumeroDisposicion('');

    try {
      const res = await fetch(`${API_URL}/expedientes/${seleccionado.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ numero_disposicion: numeroNormalizado }),
      });

      if (!res.ok) {
        setErrorNumeroDisposicion(await obtenerMensajeError(res));
        return;
      }

      const actualizado: Expediente = await res.json();
      setSeleccionado(actualizado);
      setNumeroDisposicionEditable(actualizado.numero_disposicion || '');
      await cargarExpedientes();

      if (disposicionBorrador) {
        const regenerado = await prepararDisposicion(true);
        if (!regenerado) {
          const mensajeRegeneracion = 'El número de Disposición se guardó, pero no pudo regenerarse el borrador.';
          setErrorNumeroDisposicion(mensajeRegeneracion);
          avisar(mensajeRegeneracion, 'error');
          return;
        }
      }

      avisar('Número de Disposición guardado correctamente.', 'ok');
    } catch {
      setErrorNumeroDisposicion('No se pudo conectar con el backend para guardar el número de Disposición.');
    } finally {
      setGuardandoNumeroDisposicion(false);
    }
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
    if (!seleccionado.numero_disposicion?.trim()) {
      const mensajeNumero = 'Ingresá y guardá el número de Disposición antes de emitir.';
      setErrorNumeroDisposicion(mensajeNumero);
      avisar(mensajeNumero, 'error');
      return;
    }
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

  function descargarDisposicionEmitida() {
    if (!disposicionEmitidaDetalle?.ruta_docx?.trim()) {
      setErrorDisposicionEmitida('La Disposición emitida no posee un archivo disponible para descargar.');
      return;
    }
    const ruta = disposicionEmitidaDetalle.ruta_docx.replace(/^\/+/, '');
    window.open(`${API_URL}/storage/${ruta}`, '_blank');
  }

  async function registrarFirma() {
    if (!seleccionado || !fechaFirma) {
      avisar('Debe indicar la fecha de firma.', 'error');
      return;
    }
    if (!window.confirm('¿Confirma el registro de la firma ológrafa?')) return;

    setRegistrandoFirma(true);
    try {
      const res = await fetch(
        `${API_URL}/expedientes/${seleccionado.id}/registrar-firma`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ fecha_firma: fechaFirma }),
        },
      );
      if (!res.ok) {
        avisar(await obtenerMensajeError(res), 'error');
        return;
      }
      const actualizado: Expediente = await res.json();
      await cargarExpedientes();
      await cargarDetalle(actualizado);
      setFechaFirma('');
      avisar('Firma ológrafa registrada correctamente.', 'ok');
    } catch {
      avisar('No se pudo conectar con el backend para registrar la firma.', 'error');
    } finally {
      setRegistrandoFirma(false);
    }
  }

  async function registrarArchivo() {
    if (!seleccionado || !fechaArchivo) {
      avisar('Debe indicar la fecha de archivo.', 'error');
      return;
    }
    if (!window.confirm('¿Confirma que el expediente pasó al archivo institucional?')) return;

    setRegistrandoArchivo(true);
    try {
      const res = await fetch(
        `${API_URL}/expedientes/${seleccionado.id}/registrar-archivo`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ fecha_archivo: fechaArchivo }),
        },
      );
      if (!res.ok) {
        avisar(await obtenerMensajeError(res), 'error');
        return;
      }
      const actualizado: Expediente = await res.json();
      await cargarExpedientes();
      await cargarDetalle(actualizado);
      setFechaArchivo('');
      avisar('Expediente archivado correctamente.', 'ok');
    } catch {
      avisar('No se pudo conectar con el backend para archivar el expediente.', 'error');
    } finally {
      setRegistrandoArchivo(false);
    }
  }

  function abrirVistaPrevia(doc: Documento) {
    if (!seleccionado) return;
    window.open(`${API_URL}/expedientes/${seleccionado.id}/documentos/${doc.id}/vista-previa`, '_blank');
  }

  useEffect(() => {
    cargarExpedientes();
    cargarSolicitudes();
    cargarDecisionesMesa();
    cargarCatalogosIntervencion();
  }, []);

  useEffect(() => {
    setNumeroDisposicionEditable(seleccionado?.numero_disposicion || '');
    setErrorNumeroDisposicion('');
    setMostrarTextoBorrador(false);
    setMostrarTextoDisposicionEmitida(false);
  }, [seleccionado?.id, seleccionado?.numero_disposicion]);

  const diag = diagnosticoIA(analisis);
  const comparacion = comparacionDocumental(analisis);
  const confiabilidad = confiabilidadIA(analisis);
  const tieneOP = documentos.some((documento) => documento.tipo === 'OP');
  const opConExtraccionFallida = analisis?.modo === 'EXTRACCION_FALLIDA';
  const opAnalizadaCorrectamente = Boolean(
    analisis?.op_detectada && analisis.modo !== 'EXTRACCION_FALLIDA',
  );
  const expedienteArchivadoLegacy = Boolean(
    seleccionado?.estado === 'ARCHIVADO'
      && !seleccionado.fecha_cierre
      && !seleccionado.fecha_desistimiento,
  );
  const disposicionEmitida = Boolean(
    seleccionado
      && (
        ['DISPOSICION_EMITIDA', 'FIRMADO'].includes(seleccionado.estado)
        || expedienteArchivadoLegacy
      ),
  );
  const expedienteFirmado = seleccionado?.estado === 'FIRMADO';
  const expedienteArchivado = seleccionado?.estado === 'ARCHIVADO';
  const expedienteTerminal = ['CERRADO', 'DESISTIDO', 'ARCHIVADO'].includes(
    seleccionado?.estado || '',
  );
  const firmaPendiente = seleccionado?.estado === 'DISPOSICION_EMITIDA';
  const validacionAdministrativaCompleta = Boolean(
    seleccionado
      && (
        ['VALIDADO', 'DISPOSICION_EMITIDA', 'FIRMADO', 'ARCHIVADO'].includes(seleccionado.estado)
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
      texto: 'Decisión sobre la Intervención registrada.',
      accion: 'Registrar Decisión sobre la Intervención.',
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

  const etapaWorkflow = expedienteFirmado || expedienteArchivado
    ? 'archivo'
    : disposicionEmitida
      ? 'formalizacion'
      : seleccionado?.estado === 'VALIDADO'
        ? 'disposicion'
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
      estado: seleccionado?.estado === 'VALIDADO' || disposicionEmitida
        ? 'completed'
        : opConExtraccionFallida
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
      estado: disposicionEmitida
        ? 'completed'
        : etapaWorkflow === 'disposicion'
          ? 'current'
          : 'blocked',
    },
    {
      id: 'formalizacion',
      texto: 'Formalización',
      estado: expedienteFirmado || expedienteArchivado
        ? 'completed'
        : seleccionado?.estado === 'DISPOSICION_EMITIDA'
          ? 'current'
          : 'blocked',
    },
    {
      id: 'archivo',
      texto: 'Archivo',
      estado: expedienteArchivado
        ? 'completed'
        : expedienteFirmado
          ? 'current'
          : 'future',
    },
  ];

  const accionPrincipal = (() => {
    if (expedienteTerminal) {
      return {
        descripcion: 'El Expediente está finalizado. Sus actuaciones permanecen disponibles para consulta histórica.',
        etiqueta: 'Consultar historial',
        ejecutar: () => setTabDetalle('historial'),
      };
    }

    if (disposicionEmitida) {
      return {
        descripcion: 'La disposición fue emitida y se encuentra disponible para su descarga.',
        etiqueta: 'Descargar disposición',
        ejecutar: descargarDisposicionEmitida,
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
        descripcion: 'Administre el control y la Disposición desde cada Orden de Pago.',
        etiqueta: 'Ver Órdenes de Pago',
        ejecutar: () => setTabDetalle('documentos'),
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

    if (validacion?.estado_general === 'VERDE' && seleccionado?.estado !== 'VALIDADO') {
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

  const mesaCargando = cargandoSolicitudes || cargandoExpedientes || cargandoDecisionesMesa;
  const mesaConError = Boolean(errorCargaSolicitudes || errorExpedientes || errorDecisionesMesa);
  const indicadoresMesa = [
    {
      clave: 'solicitudes',
      etiqueta: 'Solicitudes por decidir',
      valor: datosMesa.solicitudesPorDecidir.length,
      icono: <ClipboardList aria-hidden="true" />,
    },
    {
      clave: 'tramite',
      etiqueta: 'Expedientes en trámite',
      valor: datosMesa.expedientesEnTramite.length,
      icono: <FolderOpen aria-hidden="true" />,
    },
    {
      clave: 'validacion',
      etiqueta: 'Esperando validación',
      valor: datosMesa.esperandoValidacion.length,
      icono: <CircleCheck aria-hidden="true" />,
    },
    {
      clave: 'disposicion',
      etiqueta: 'Disposiciones por emitir',
      valor: datosMesa.disposicionesPorEmitir.length,
      icono: <FileSignature aria-hidden="true" />,
    },
    {
      clave: 'firma',
      etiqueta: 'Firmas pendientes',
      valor: datosMesa.firmasPendientes.length,
      icono: <PenLine aria-hidden="true" />,
    },
    {
      clave: 'archivo',
      etiqueta: 'Archivos pendientes',
      valor: datosMesa.archivosPendientes.length,
      icono: <Archive aria-hidden="true" />,
    },
  ];
  const accionPorEstadoExpediente: Record<string, string> = {
    BORRADOR: 'Completar preparación',
    DOCUMENTACION_EN_CARGA: 'Completar documentación',
    PENDIENTE_VALIDACION: 'Continuar validación',
    VALIDADO: 'Preparar Disposición',
    DISPOSICION_EMITIDA: 'Registrar firma',
    FIRMADO: 'Registrar archivo',
  };
  const prioridadOrden: Record<string, number> = {
    ALTA: 0,
    MEDIA: 1,
    NORMAL: 2,
    BAJA: 3,
  };
  const trabajoPendiente: TrabajoMesa[] = [
    ...datosMesa.solicitudesPorDecidir.map((solicitud): TrabajoMesa => ({
      clave: `solicitud-${solicitud.id_solicitud}`,
      tipo: 'Solicitud',
      identificador: solicitud.numero_solicitud || 'Sin número',
      establecimiento: solicitud.establecimiento || 'No disponible',
      asunto: solicitud.motivo || 'Sin motivo informado',
      estado: 'Sin decisión registrada',
      accion: 'Registrar decisión',
      prioridad: solicitud.prioridad || undefined,
      fecha: solicitud.fecha_ingreso,
      abrir: () => abrirSolicitudDesdeBandeja(solicitud),
    })),
    ...datosMesa.expedientesEnTramite.map((expediente): TrabajoMesa => ({
      clave: `expediente-${expediente.id}`,
      tipo: 'Expediente',
      identificador: expediente.numero_interno,
      establecimiento: expediente.establecimiento || 'No disponible',
      asunto: expediente.objeto || expediente.tipo_tramite,
      estado: etiquetaEstado(expediente.estado),
      accion: accionPorEstadoExpediente[expediente.estado] || 'Continuar trámite',
      fecha: expediente.creado,
      abrir: () => cargarDetalle(expediente),
    })),
  ].sort((a, b) => {
    const prioridadA = prioridadOrden[a.prioridad || ''] ?? 4;
    const prioridadB = prioridadOrden[b.prioridad || ''] ?? 4;
    if (prioridadA !== prioridadB) return prioridadA - prioridadB;
    if (a.fecha !== b.fecha) return a.fecha.localeCompare(b.fecha);
    return a.identificador.localeCompare(b.identificador);
  });
  const gruposTrabajoPendiente = [
    {
      clave: 'solicitudes',
      titulo: 'Solicitudes',
      items: trabajoPendiente.filter((trabajo) => trabajo.tipo === 'Solicitud'),
    },
    {
      clave: 'expedientes',
      titulo: 'Expedientes',
      items: trabajoPendiente.filter((trabajo) => trabajo.tipo === 'Expediente'),
    },
  ].filter((grupo) => grupo.items.length > 0);

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <img
            className="brand-product-logo"
            src="/branding/logo-sigd-st-sidebar.png"
            alt="SIGD-ST, Sistema Inteligente de Gestión Documental"
          />
          <div className="brand-institution">
            <img
              src="/branding/logo-consejo-escolar-general-alvarado.png"
              alt="Consejo Escolar General Alvarado"
            />
            <span>Secretaría Técnica</span>
          </div>
        </div>

        <nav className="sidebar-nav" aria-label="Navegación principal">
          <button className={pantalla === 'inicio' ? 'active' : ''} onClick={() => setPantalla('inicio')}><LayoutDashboard aria-hidden="true" />Mesa de Control</button>
          <button className={pantalla === 'expedientes' ? 'active' : ''} onClick={() => setPantalla('expedientes')}><FolderOpen aria-hidden="true" />Expedientes</button>
          <button className={pantalla === 'solicitudes' ? 'active' : ''} onClick={abrirSolicitudes}><ClipboardList aria-hidden="true" />Solicitudes de Intervención</button>
          <button><Landmark aria-hidden="true" />Fondo Compensador</button>
          <button><Building2 aria-hidden="true" />SAE</button>
          <button><Building2 aria-hidden="true" />Infraestructura</button>
          <button><Bus aria-hidden="true" />Transporte</button>
          <button className={pantalla === 'administracion' ? 'active' : ''} onClick={() => setPantalla('administracion')}><Settings aria-hidden="true" />Administración</button>
        </nav>

        <div className="version">Versión Alfa 0.29B</div>
      </aside>

      <section className="content">
        {!(pantalla === 'solicitudes' && solicitudSeleccionada) && (
        <header className="topbar">
          <div>
            <h2>{pantalla === 'inicio' ? 'Mesa de Control' : pantalla === 'nuevo' ? 'Nuevo Expediente' : pantalla === 'detalle' ? 'Expediente Inteligente' : pantalla === 'solicitudes' ? solicitudSeleccionada ? 'Gestión de la Solicitud' : 'Solicitudes de Intervención' : pantalla === 'administracion' ? 'Administración' : 'Expedientes'}</h2>
            <span>
              {pantalla === 'inicio'
                ? 'Trabajo operativo de SIGD-ST'
                : pantalla === 'solicitudes'
                ? cargandoSolicitudes
                  ? 'Cargando solicitudes...'
                  : errorCargaSolicitudes
                    ? 'Solicitudes no disponibles'
                    : filtrosSolicitudesActivos
                      ? `${solicitudesFiltradas.length} de ${solicitudes.length} solicitudes`
                      : `${solicitudes.length} solicitudes registradas`
                : 'Secretaría Técnica'}
            </span>
          </div>
          <div className="institutional-context">
            <strong>Secretaría Técnica</strong>
            <span>Consejo Escolar General Alvarado</span>
          </div>
        </header>
        )}

        {mensaje && <div className={`notice ${mensajeTipo}`}>{mensaje}</div>}

        {pantalla === 'inicio' && (
          <div className="control-desk">
            {mesaCargando && <div className="notice info">Cargando trabajo operativo...</div>}
            {!mesaCargando && mesaConError && (
              <div className="notice error">No fue posible recuperar toda la información de la Mesa de Control.</div>
            )}

            <section className="control-indicators" aria-label="Indicadores operativos">
              {indicadoresMesa.map((indicador) => (
                <article className="control-indicator" key={indicador.clave}>
                  <span className="control-indicator-icon">{indicador.icono}</span>
                  <div>
                    <strong>{mesaCargando ? 'Cargando' : mesaConError ? 'No disponible' : indicador.valor}</strong>
                    <p>{indicador.etiqueta}</p>
                  </div>
                </article>
              ))}
            </section>

            <section className="control-main-grid">
              <div className="card control-work-card">
                <div className="card-title">
                  <div><span className="eyebrow">Operación diaria</span><h3>Trabajo pendiente</h3></div>
                  {!mesaCargando && !mesaConError && <span className="badge blue">{trabajoPendiente.length} tareas</span>}
                </div>
                {mesaCargando ? (
                  <p className="empty">Recuperando tareas pendientes...</p>
                ) : mesaConError ? (
                  <p className="empty">El trabajo pendiente no está disponible hasta completar la carga.</p>
                ) : trabajoPendiente.length === 0 ? (
                  <p className="empty">No existen actuaciones pendientes con los estados disponibles.</p>
                ) : (
                  <div className="control-work-groups">
                    {gruposTrabajoPendiente.map((grupo) => (
                      <section className="control-work-group" key={grupo.clave} aria-labelledby={`trabajo-${grupo.clave}`}>
                        <div className="control-work-group-title">
                          <h4 id={`trabajo-${grupo.clave}`}>{grupo.titulo}</h4>
                          <span>{grupo.items.length}</span>
                        </div>
                        <div className="control-work-list">
                          {grupo.items.map((trabajo) => (
                            <article className="control-work-item" key={trabajo.clave}>
                              <div className="control-work-kind">
                                {trabajo.tipo === 'Solicitud' ? <ClipboardList aria-hidden="true" /> : <FolderOpen aria-hidden="true" />}
                                <span>{trabajo.tipo}</span>
                              </div>
                              <div className="control-work-body">
                                <strong>{trabajo.identificador}</strong>
                                <p>{trabajo.establecimiento}</p>
                                <small>{trabajo.asunto}</small>
                              </div>
                              <div className="control-work-status">
                                <span>{trabajo.estado}</span>
                                <strong>{trabajo.accion}</strong>
                                {trabajo.prioridad && <small>Prioridad {trabajo.prioridad}</small>}
                              </div>
                              <button className="small-button" type="button" onClick={trabajo.abrir}>Abrir</button>
                            </article>
                          ))}
                        </div>
                      </section>
                    ))}
                  </div>
                )}
              </div>

              <aside className="card control-quick-access">
                <span className="eyebrow">Navegación</span>
                <h3>Accesos rápidos</h3>
                <button type="button" onClick={abrirNuevaSolicitud}><ClipboardList aria-hidden="true" />Nueva Solicitud</button>
                <button type="button" onClick={abrirSolicitudes}><Search aria-hidden="true" />Buscar Solicitud</button>
                <button type="button" onClick={() => setPantalla('expedientes')}><Search aria-hidden="true" />Buscar Expediente</button>
                <button type="button" onClick={() => setPantalla('administracion')}><Landmark aria-hidden="true" />Configuración UC</button>
                <button type="button" onClick={() => setPantalla('administracion')}><Settings aria-hidden="true" />Administración</button>
              </aside>
            </section>

            <section className="control-secondary-grid">
              <div className="card control-recent-card">
                <div className="card-title">
                  <div><span className="eyebrow">Información disponible</span><h3>Solicitudes recientes</h3></div>
                  <button className="link" type="button" onClick={abrirSolicitudes}>Ver Solicitudes</button>
                </div>
                {cargandoSolicitudes ? (
                  <p className="empty">Cargando Solicitudes...</p>
                ) : errorCargaSolicitudes ? (
                  <p className="empty">Las Solicitudes recientes no están disponibles.</p>
                ) : solicitudesRecientesMesa.length === 0 ? (
                  <p className="empty">No existen Solicitudes registradas.</p>
                ) : (
                  <div className="control-recent-list">
                    {solicitudesRecientesMesa.map((solicitud) => (
                      <button type="button" key={solicitud.id_solicitud} onClick={() => abrirSolicitudDesdeBandeja(solicitud)}>
                        <span><strong>{solicitud.numero_solicitud || 'Sin número'}</strong>{solicitud.establecimiento}</span>
                        <time dateTime={solicitud.fecha_ingreso}>{new Date(`${solicitud.fecha_ingreso}T00:00:00`).toLocaleDateString('es-AR')}</time>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <aside className="card control-system-status">
                <span className="eyebrow">Contexto institucional</span>
                <h3>Estado del sistema</h3>
                <dl>
                  <div><dt>Sistema</dt><dd>SIGD-ST</dd></div>
                  <div><dt>Fondo activo</dt><dd>Fondo Compensador</dd></div>
                  <div><dt>Versión</dt><dd>Alfa 0.29B</dd></div>
                </dl>
              </aside>
            </section>
          </div>
        )}

        {pantalla === 'nuevo' && (
          <section className="card form-card">
            <button className="secondary" type="button" onClick={abrirSolicitudes}>
              <ArrowLeft aria-hidden="true" /> Volver a Solicitudes
            </button>
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
            <div className="card-title expedientes-list-header">
              <h3>Expedientes</h3>
              <div className="actions">
                <button className="secondary" type="button" onClick={cargarExpedientes} disabled={cargandoExpedientes}>
                  {cargandoExpedientes ? 'Actualizando...' : 'Actualizar'}
                </button>
                <button className="primary" type="button" onClick={() => setPantalla('nuevo')}>
                  + Nuevo Expediente Manual
                </button>
              </div>
            </div>
            {cargandoExpedientes ? (
              <p className="empty">Cargando expedientes...</p>
            ) : errorExpedientes ? (
              <div className="notice error">{errorExpedientes}</div>
            ) : (
              <ExpedientesTabla expedientes={expedientes} abrir={cargarDetalle} />
            )}
          </section>
        )}

        {pantalla === 'solicitudes' && (
          <section className="solicitudes-page">
            {!solicitudSeleccionada ? (
              <>
            <div className="solicitudes-toolbar">
              <button
                className="secondary"
                type="button"
                onClick={cargarSolicitudes}
                disabled={cargandoSolicitudes}
              >
                {cargandoSolicitudes ? 'Actualizando...' : 'Actualizar'}
              </button>
              {!mostrarFormularioSolicitud && (
                <button className="primary" type="button" onClick={abrirNuevaSolicitud}>
                  + Nueva Solicitud
                </button>
              )}
            </div>

            <PanelBusquedaFiltros
              placeholder="Buscar solicitud, establecimiento, SUNA o solicitante..."
              value={busquedaSolicitudes}
              onSearchChange={setBusquedaSolicitudes}
              quickFilters={filtrosRapidosSolicitudes}
              activeQuickFilter={filtroRapidoSolicitudes}
              onQuickFilterChange={setFiltroRapidoSolicitudes}
              advancedFilters={configuracionFiltrosAvanzadosSolicitudes}
              advancedFilterValues={filtrosAvanzadosSolicitudes}
              onAdvancedFilterChange={(key, value) =>
                setFiltrosAvanzadosSolicitudes((filtrosActuales) => ({
                  ...filtrosActuales,
                  [key]: value,
                }))
              }
              activeFilters={filtrosActivosSolicitudes}
              canClearFilters={filtrosSolicitudesActivos}
              onClearFilters={limpiarFiltrosSolicitudes}
            />

            {errorSolicitudes && <div className="notice error">{errorSolicitudes}</div>}

            <div
              className={`solicitud-create-region ${
                mostrarFormularioSolicitud ? 'open' : ''
              }`}
              aria-hidden={!mostrarFormularioSolicitud}
            >
              <div>
              <form className="card solicitud-create-panel" onSubmit={crearSolicitud}>
                <div className="card-title">
                  <h3>Nueva Solicitud</h3>
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

                <div className="actions">
                  <button
                    className="secondary"
                    type="button"
                    onClick={cancelarNuevaSolicitud}
                    disabled={guardandoSolicitud}
                  >
                    Cancelar
                  </button>
                  <button className="primary" type="submit" disabled={guardandoSolicitud}>
                    {guardandoSolicitud ? 'Registrando...' : 'Registrar solicitud'}
                  </button>
                </div>
              </form>
              </div>
            </div>

            <div
              className={`solicitudes-management ${
                solicitudSeleccionada ? 'has-selection' : 'without-selection'
              }`}
            >
                <section className="card solicitudes-table">
                  <div className="card-title">
                    <h3>Solicitudes registradas</h3>
                  </div>

                  {errorCargaSolicitudes ? (
                    <div className="notice error">{errorCargaSolicitudes}</div>
                  ) : cargandoSolicitudes ? (
                    <p className="empty">Cargando solicitudes...</p>
                  ) : solicitudes.length === 0 ? (
                    <p className="empty">No existen solicitudes registradas.</p>
                  ) : solicitudesFiltradas.length === 0 ? (
                    <p className="empty">
                      No se encontraron solicitudes que coincidan con los filtros aplicados.
                    </p>
                  ) : (
                    <table>
                      <thead>
                        <tr>
                          <th>Número</th>
                          <th>Establecimiento</th>
                          <th>Motivo</th>
                          <th>Prioridad</th>
                          <th>Estado</th>
                          <th></th>
                        </tr>
                      </thead>
                      <tbody>
                        {solicitudesFiltradas.map((solicitud) => (
                          <tr key={solicitud.id_solicitud}>
                            <td>
                              <strong className="solicitud-number">
                                {solicitud.numero_solicitud}
                              </strong>
                            </td>
                            <td>{solicitud.establecimiento}</td>
                            <td>
                              <span className="solicitud-reason" title={solicitud.motivo}>
                                {solicitud.motivo}
                              </span>
                            </td>
                            <td>{solicitud.prioridad}</td>
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
              </div>
              </>
            ) : (
              <div className="solicitud-case-page">
                <div className="solicitud-case-topbar">
                  <button className="secondary" type="button" onClick={volverASolicitudes}>
                    <ArrowLeft aria-hidden="true" /> Volver a Solicitudes
                  </button>
                  <h3>Gestión de la Solicitud</h3>
                  <button className="secondary" type="button" disabled>
                    Acciones
                  </button>
                </div>

                <section className="card solicitud-case-header">
                  <div className="solicitud-case-title">
                    <span className="eyebrow">Número de Solicitud</span>
                    <h3>{solicitudSeleccionada.numero_solicitud}</h3>
                  </div>
                  <div className="solicitud-case-id-suna">
                    <span>ID SUNA</span>
                    <strong>{solicitudSeleccionada.id_suna || 'No disponible'}</strong>
                  </div>
                </section>

                <section
                  className={`card solicitud-administrative-info ${
                    informacionAdministrativaExpandida ? 'expanded' : 'collapsed'
                  }`}
                >
                  <button
                    className="solicitud-administrative-info-toggle"
                    type="button"
                    aria-expanded={informacionAdministrativaExpandida}
                    aria-controls="solicitud-informacion-administrativa"
                    onClick={() => setInformacionAdministrativaExpandida(
                      (expandida) => !expandida,
                    )}
                  >
                    <span>
                      <strong>Información administrativa</strong>
                    </span>
                    <span aria-hidden="true">
                      {informacionAdministrativaExpandida ? '−' : '+'}
                    </span>
                  </button>

                  {informacionAdministrativaExpandida && (
                    <div
                      className="solicitud-administrative-info-grid"
                      id="solicitud-informacion-administrativa"
                    >
                      <article>
                        <span>Motivo</span>
                        <strong>{solicitudSeleccionada.motivo}</strong>
                      </article>
                      <article>
                        <span>Establecimiento</span>
                        <strong>{solicitudSeleccionada.establecimiento}</strong>
                      </article>
                      <article>
                        <span>Procedencia</span>
                        <strong>{solicitudSeleccionada.procedencia}</strong>
                      </article>
                      <article>
                        <span>Solicitante</span>
                        <strong>{solicitudSeleccionada.solicitante}</strong>
                      </article>
                      <article>
                        <span>Estado</span>
                        <strong>
                          <span className="badge blue">{solicitudSeleccionada.estado}</span>
                        </strong>
                      </article>
                      <article>
                        <span>Prioridad</span>
                        <strong>{solicitudSeleccionada.prioridad}</strong>
                      </article>
                      <article>
                        <span>Fondo Interviniente</span>
                        <strong>
                          {decisiones.find((decision) => decision.resultado === 'Aprobar intervención')?.fondo_interviniente
                            ? etiquetaFondoInterviniente(
                              decisiones.find((decision) => decision.resultado === 'Aprobar intervención')!.fondo_interviniente!,
                            )
                            : 'No determinado'}
                        </strong>
                      </article>
                      <article>
                        <span>Fecha de ingreso</span>
                        <strong>{solicitudSeleccionada.fecha_ingreso}</strong>
                      </article>
                    </div>
                  )}
                </section>

                <div className="solicitud-case-workflow" aria-label="Etapas de la gestión">
                  {[
                    'Solicitud',
                    'Decisión',
                    'Expediente',
                    'Preparación',
                    'Validación',
                    'Orden de Pago',
                    'Disposición',
                    'Finalizada',
                  ].map((etapa, indice) => (
                    <div
                      className={`solicitud-case-step ${
                        indice === 0 ? 'completed' : indice === 1 ? 'current' : 'future'
                      }`}
                      key={etapa}
                    >
                      <span>{indice === 0 ? <Check aria-hidden="true" /> : indice + 1}</span>
                      <strong>{etapa}</strong>
                    </div>
                  ))}
                </div>

                <section className="solicitud-executive-grid" aria-label="Panel ejecutivo">
                  <article className="card solicitud-executive-primary">
                    <span>Próxima acción</span>
                    <strong>Continuar gestión administrativa</strong>
                    <small>Revise la información disponible para avanzar con el trámite.</small>
                  </article>
                  <article className="card">
                    <span>Responsable</span>
                    <strong>Secretaría Técnica</strong>
                  </article>
                  <article className="card">
                    <span>Bloqueos</span>
                    <strong>Sin bloqueos informados</strong>
                  </article>
                  <article className="card">
                    <span>Pendientes</span>
                    <strong>Revisar documentación</strong>
                  </article>
                </section>

                <nav className="solicitud-case-tabs" aria-label="Secciones de la solicitud">
                  {[
                    ['tramitacion', 'Tramitación'],
                    ['historial', 'Historial'],
                  ].map(([id, texto]) => (
                    <button
                      className={tabGestionSolicitud === id ? 'active' : ''}
                      type="button"
                      key={id}
                      onClick={() => setTabGestionSolicitud(id as TabGestionSolicitud)}
                    >
                      {texto}
                    </button>
                  ))}
                </nav>

                <section className="card solicitud-detail">
                  {tabGestionSolicitud === 'tramitacion' && (
                      <>
                      <section className="subcard solicitud-analysis-block">
                        <div className="card-title">
                          <div>
                            <span className="eyebrow">Tramitación</span>
                            <h3>Decisión sobre la Intervención</h3>
                            <p className="solicitud-analysis-intro">
                              Registre la decisión adoptada por la autoridad competente.
                            </p>
                          </div>
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
                          <form
                            className="decision-intervention-form"
                            onSubmit={crearDecision}
                          >
                            <h4>Nueva decisión</h4>

                            <div className="decision-brief-fields">
                              <div className="decision-field">
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
                              </div>

                              <div className="decision-field">
                                <label>Fecha de decisión</label>
                                <input
                                  type="date"
                                  value={decisionFecha}
                                  onChange={(e) => setDecisionFecha(e.target.value)}
                                />
                              </div>

                              <div className="decision-field">
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
                              </div>

                              <div className="decision-field">
                                <label>Fondo Interviniente</label>
                                <select
                                  value={decisionFondoInterviniente}
                                  onChange={(e) => {
                                    const fondo = e.target.value;
                                    setDecisionFondoInterviniente(fondo);
                                    if (fondo !== 'OTRO') {
                                      setDecisionDescripcionFondo('');
                                    }
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
                              </div>
                            </div>

                            {decisionFondoInterviniente === 'OTRO' && (
                              <div className="decision-field decision-field-wide">
                                <label>Descripción del Fondo</label>
                                <input
                                  value={decisionDescripcionFondo}
                                  onChange={(e) => setDecisionDescripcionFondo(e.target.value)}
                                />
                              </div>
                            )}

                            <div className="decision-field decision-field-wide decision-foundation">
                              <label>Fundamento</label>
                              <textarea
                                rows={3}
                                value={decisionFundamento}
                                onChange={(e) => setDecisionFundamento(e.target.value)}
                              />
                            </div>

                            <div className="decision-submit-row">
                              <button
                                className="primary"
                                type="submit"
                                disabled={guardandoDecision}
                              >
                                {guardandoDecision
                                  ? 'Guardando...'
                                  : 'Guardar decisión'}
                              </button>
                            </div>
                          </form>

                          <div>
                            <h4>Decisiones sobre la intervención</h4>
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

                      <section className="solicitud-future-stages" aria-label="Etapas posteriores de la tramitación">
                        {[
                          'Expediente',
                          'Contratación',
                          'Ejecución',
                          'Orden de Pago',
                          'Disposición',
                        ].map((etapa) => (
                          <article key={etapa}>
                            <Circle aria-hidden="true" />
                            <strong>{etapa}</strong>
                            <small>Etapa futura</small>
                          </article>
                        ))}
                      </section>
                      </>
                  )}

                  {tabGestionSolicitud === 'historial' && (
                    <section
                      className="solicitud-history"
                      aria-live="polite"
                    >
                      <div className="solicitud-history-heading">
                        <h3>Historial</h3>
                        <p>
                          Cronología de la Solicitud y sus Decisiones registradas.
                        </p>
                      </div>

                      {cargandoDecisiones ? (
                        <p className="empty">Cargando historial...</p>
                      ) : errorDecisiones ? (
                        <div className="notice error">{errorDecisiones}</div>
                      ) : historialSolicitud.length === 0 ? (
                        <p className="empty">No existen eventos registrados.</p>
                      ) : (
                        <ol className="solicitud-history-list">
                          {historialSolicitud.map((evento) => (
                            <li
                              className="solicitud-history-event"
                              key={`${evento.tipo}-${evento.id}`}
                            >
                              <div
                                className={`solicitud-history-marker ${evento.tipo}`}
                                aria-hidden="true"
                              />

                              <article>
                                <time dateTime={evento.fecha}>
                                  {formatearFechaHora(evento.fecha)}
                                </time>

                                {evento.tipo === 'solicitud' ? (
                                  <>
                                    <h4>Solicitud registrada</h4>
                                    <p>
                                      Número de Solicitud:{' '}
                                      <strong>
                                        {evento.solicitud.numero_solicitud}
                                      </strong>
                                    </p>
                                    <p>
                                      Procedencia: {evento.solicitud.procedencia}
                                    </p>
                                    {evento.solicitud.solicitante && (
                                      <p>
                                        Solicitante:{' '}
                                        {evento.solicitud.solicitante}
                                      </p>
                                    )}
                                  </>
                                ) : (
                                  <>
                                    <h4>Decisión registrada</h4>
                                    <p>
                                      Resultado: {evento.decision.resultado}
                                    </p>
                                    <p>
                                      Autoridad decisora:{' '}
                                      {evento.decision.autoridad_decisora}
                                    </p>
                                    {evento.decision.fondo_interviniente && (
                                      <p>
                                        Fondo Interviniente:{' '}
                                        {etiquetaFondoInterviniente(
                                          evento.decision.fondo_interviniente,
                                        )}
                                      </p>
                                    )}
                                    {evento.decision.descripcion_fondo && (
                                      <p>
                                        Descripción del Fondo:{' '}
                                        {evento.decision.descripcion_fondo}
                                      </p>
                                    )}
                                    <p>
                                      Fundamento: {evento.decision.fundamento}
                                    </p>
                                    {evento.decision.usuario_registrante && (
                                      <p>
                                        Registrada por:{' '}
                                        {evento.decision.usuario_registrante}
                                      </p>
                                    )}
                                  </>
                                )}
                              </article>
                            </li>
                          ))}
                        </ol>
                      )}
                    </section>
                  )}
                </section>

                <div className="solicitud-case-actions">
                  <button className="secondary" type="button" disabled>Imprimir Resumen</button>
                  <button className="secondary" type="button" disabled>Más acciones</button>
                  <button className="primary" type="button" disabled>Guardar y continuar</button>
                </div>
              </div>
            )}
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

            <CompletitudExpedienteCard
              expediente={seleccionado}
              onFinalizado={(actualizado) => {
                setSeleccionado(actualizado);
                void cargarDetalle(actualizado);
              }}
            />

            <ProveedorActualCard
              expedienteId={seleccionado.id}
              seleccionadoPor={decisionUsuarioRegistrante}
              revisionProveedor={revisionProveedor}
              soloLectura={expedienteTerminal}
            />

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
                    <span aria-hidden="true">{control.completo ? <CircleCheck /> : <Circle />}</span>
                    <span>{control.texto.replace(/\.$/, '')}</span>
                  </div>
                ))}
              </div>
              <div className="administrative-preparation-legend" aria-label="Referencia de estados">
                <span><Circle aria-hidden="true" /> Pendiente</span>
                <span><CircleCheck aria-hidden="true" /> Completo</span>
              </div>
            </section>

            <div className="workflow-steps" aria-label="Etapas del trámite">
              {workflowSteps.map((etapa) => (
                <div className={`workflow-step ${etapa.estado}`} key={etapa.id}>
                  <span className="workflow-step-number">
                    <IconoEtapaWorkflow id={etapa.id} completada={etapa.estado === 'completed'} />
                  </span>
                  <span>{etapa.texto}</span>
                </div>
              ))}
            </div>

            {disposicionEmitida && (
              <nav className="workflow-final-navigation" aria-label="Consultas del expediente">
                <button className={tabDetalle === 'workflow' ? 'active' : ''} type="button" onClick={() => setTabDetalle('workflow')}>
                  <CircleDot aria-hidden="true" /> Estado del trámite
                </button>
                <button className={tabDetalle === 'documentos' ? 'active' : ''} type="button" onClick={() => setTabDetalle('documentos')}>
                  <FileText aria-hidden="true" /> Documentos
                </button>
                <button className={tabDetalle === 'ia' ? 'active' : ''} type="button" onClick={() => setTabDetalle('ia')}>
                  <ScanSearch aria-hidden="true" /> Análisis
                </button>
                <button className={tabDetalle === 'historial' ? 'active' : ''} type="button" onClick={() => setTabDetalle('historial')}>
                  <History aria-hidden="true" /> Historial
                </button>
                <button className={tabDetalle === 'validacion' ? 'active' : ''} type="button" onClick={consultarValidacion}>
                  <CircleCheck aria-hidden="true" /> Validación
                </button>
                {solicitudOrigenExpediente && (
                  <button type="button" onClick={abrirSolicitudOrigen}>
                    <ExternalLink aria-hidden="true" /> Abrir Solicitud
                  </button>
                )}
              </nav>
            )}

            <div className={`workflow-layout ${disposicionEmitida ? 'final-state' : ''}`}>
              <section className="expediente-main">
                {tabDetalle === 'workflow' && (
                  <>
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
                                : etapaWorkflow === 'archivo'
                                  ? 'Archivo'
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
                  {disposicionEmitida && (
                    <div className="card">
                      <div className="card-title">
                        <div>
                          <span className="eyebrow">Acto administrativo emitido</span>
                          <h3>Disposición</h3>
                        </div>
                        <div className="disposition-issued-actions">
                          <span className="badge green">Emitida</span>
                          <button className="secondary" type="button" onClick={descargarDisposicionEmitida}>
                            <Download aria-hidden="true" /> Descargar Word
                          </button>
                        </div>
                      </div>

                      {cargandoDisposicionEmitida && <p className="muted">Cargando Disposición emitida...</p>}
                      {errorDisposicionEmitida && <div className="notice error">{errorDisposicionEmitida}</div>}

                      {disposicionEmitidaDetalle && (
                        <>
                          <div className="expediente-summary-grid">
                            <div><span>Número de Disposición</span><strong>{disposicionEmitidaDetalle.numero_disposicion}</strong></div>
                            <div><span>Estado</span><strong>{estadoAdministrativo(seleccionado, historial).texto}</strong></div>
                            <div><span>Expediente</span><strong>{seleccionado.numero_interno}</strong></div>
                            <div><span>OP</span><strong>{disposicionEmitidaDetalle.numero_op}</strong></div>
                            <div><span>Proveedor</span><strong>{disposicionEmitidaDetalle.proveedor}</strong></div>
                            <div><span>Importe</span><strong>{moneda(Number(disposicionEmitidaDetalle.importe))}</strong></div>
                            <div><span>Procedimiento</span><strong>{disposicionEmitidaDetalle.procedimiento_contratacion}</strong></div>
                            <div><span>Norma</span><strong>{disposicionEmitidaDetalle.norma_uc}</strong></div>
                            <div><span>Fecha</span><strong>{formatearFechaHora(disposicionEmitidaDetalle.fecha_emision)}</strong></div>
                          </div>

                          <button
                            className="disposition-collapse-toggle"
                            type="button"
                            aria-expanded={mostrarTextoDisposicionEmitida}
                            onClick={() => setMostrarTextoDisposicionEmitida((visible) => !visible)}
                          >
                            {mostrarTextoDisposicionEmitida ? <ChevronUp aria-hidden="true" /> : <ChevronDown aria-hidden="true" />}
                            {mostrarTextoDisposicionEmitida ? 'Ocultar texto completo de la Disposición' : 'Ver texto completo de la Disposición'}
                          </button>

                          {mostrarTextoDisposicionEmitida && (
                            <div className="observation-box disposition-collapsible-content">
                              <h4>Texto emitido</h4>
                              {disposicionEmitidaDetalle.texto_emitido.split('\n').map((linea, indice) => (
                                <p key={`${indice}-${linea}`}>{linea || '\u00a0'}</p>
                              ))}
                            </div>
                          )}

                          {firmaPendiente && (
                            <div className="form-grid">
                              <label>
                                Fecha de firma
                                <input
                                  type="date"
                                  value={fechaFirma}
                                  max={new Date().toISOString().slice(0, 10)}
                                  onChange={(evento) => setFechaFirma(evento.target.value)}
                                />
                              </label>
                              <div className="actions-row">
                                <button
                                  onClick={registrarFirma}
                                  disabled={registrandoFirma || !fechaFirma}
                                >
                                  <PenLine aria-hidden="true" />
                                  {registrandoFirma ? 'Registrando...' : 'Registrar firma'}
                                </button>
                              </div>
                            </div>
                          )}

                          {['FIRMADO', 'ARCHIVADO'].includes(seleccionado?.estado || '') && (
                            <div className="expediente-summary-grid">
                              <div><span>Fecha de firma</span><strong>{seleccionado.fecha_firma ? formatearFecha(seleccionado.fecha_firma) : 'No informada'}</strong></div>
                              <div><span>Usuario de firma</span><strong>{seleccionado.usuario_registro_firma || 'No informado'}</strong></div>
                              {seleccionado.estado === 'ARCHIVADO' && (
                                <>
                                  <div><span>Fecha de archivo</span><strong>{seleccionado.fecha_archivo ? formatearFecha(seleccionado.fecha_archivo) : 'No informada'}</strong></div>
                                  <div><span>Usuario de archivo</span><strong>{seleccionado.usuario_registro_archivo || 'No informado'}</strong></div>
                                </>
                              )}
                            </div>
                          )}

                          {seleccionado?.estado === 'FIRMADO' && (
                            <div className="form-grid">
                              <label>
                                Fecha de archivo
                                <input
                                  type="date"
                                  value={fechaArchivo}
                                  min={seleccionado.fecha_firma || undefined}
                                  max={fechaLocalISO()}
                                  onChange={(evento) => setFechaArchivo(evento.target.value)}
                                />
                              </label>
                              <label>
                                Usuario registrante
                                <input value="Secretario Técnico" readOnly />
                              </label>
                              <div className="actions-row">
                                <button
                                  onClick={registrarArchivo}
                                  disabled={registrandoArchivo || !fechaArchivo}
                                >
                                  <Archive aria-hidden="true" />
                                  {registrandoArchivo ? 'Archivando...' : 'Archivar expediente'}
                                </button>
                              </div>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  )}
                  </>
                )}

                {tabDetalle === 'documentos' && (
                  <div className="card">
                    <h3>Documentación del expediente</h3>
                    <div className="upload-grid">
                      <div className="upload-box">
                        <strong>Orden de Pago</strong>
                        {validacionAdministrativaCompleta ? (
                          <>
                            <input type="file" accept=".pdf" disabled={expedienteTerminal} onChange={(e) => setArchivoOP(e.target.files?.[0] || null)} />
                            <button className="secondary" disabled={expedienteTerminal} onClick={subirOP}>Cargar OP</button>
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
                        <input type="file" disabled={expedienteTerminal} onChange={(e) => setArchivoDoc(e.target.files?.[0] || null)} />
                        <button className="secondary" disabled={expedienteTerminal} onClick={subirDocumento}>Cargar documento</button>
                      </div>
                    </div>

                    {documentos.length === 0 ? <p className="empty">Sin documentos cargados.</p> : (
                      <table>
                        <thead><tr><th>Tipo</th><th>Archivo</th><th>Tamaño</th><th>Fecha</th><th>Acción</th></tr></thead>
                        <tbody>
                          {documentos.map(doc => (
                            <React.Fragment key={doc.id}>
                              <tr>
                                <td><span className="badge blue">{doc.tipo}</span></td>
                                <td>{doc.nombre_archivo}</td>
                                <td>{bytes(doc.tamano_bytes)}</td>
                                <td>{new Date(doc.fecha_carga).toLocaleString()}</td>
                                <td>
                                  <button className="small-button" onClick={() => abrirVistaPrevia(doc)}>Vista previa</button>
                                  <a className="small-link icon-link" href={`${API_URL}/expedientes/${seleccionado.id}/documentos/${doc.id}/descargar`} target="_blank"><Download aria-hidden="true" />Descargar</a>
                                </td>
                              </tr>
                              {doc.tipo === 'OP' && (
                                <tr className="control-proveedor-op-row">
                                  <td colSpan={5}>
                                    <ControlProveedorOPCard
                                      expedienteId={seleccionado.id}
                                      documentoOpId={doc.id}
                                      nombreArchivo={doc.nombre_archivo}
                                      seleccionadoPor={
                                        decisionUsuarioRegistrante
                                      }
                                      revisionProveedor={revisionProveedor}
                                      soloLectura={expedienteTerminal}
                                      onProveedorRegularizado={() => {
                                        setRevisionProveedor(
                                          (revision) => revision + 1,
                                        );
                                      }}
                                    />
                                    <DisposicionOPCard
                                      expedienteId={seleccionado.id}
                                      documentoOpId={doc.id}
                                      nombreArchivo={doc.nombre_archivo}
                                      revisionProveedor={revisionProveedor}
                                      soloLectura={expedienteTerminal}
                                    />
                                  </td>
                                </tr>
                              )}
                            </React.Fragment>
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
                    {cargandoAnalisis ? (
                      <p className="empty">Recuperando análisis de la Orden de Pago...</p>
                    ) : errorAnalisis ? (
                      <div className="warning-panel">{errorAnalisis}</div>
                    ) : !analisis ? (
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
                              <p><CircleCheck className="inline-status-icon" aria-hidden="true" /> Proveedor: {analisis.proveedor || 'No detectado'}</p>
                              <p><CircleCheck className="inline-status-icon" aria-hidden="true" /> CUIT: {analisis.cuit || 'No detectado'}</p>
                              <p><CircleCheck className="inline-status-icon" aria-hidden="true" /> Facturas detectadas: {analisis.documentos_comerciales.length}</p>
                              <p><CircleCheck className="inline-status-icon" aria-hidden="true" /> Retenciones detectadas: {analisis.retenciones.length}</p>
                              <p><TriangleAlert className="inline-status-icon" aria-hidden="true" /> Faltantes: {analisis.faltantes.length}</p>
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
                          <div><strong>UC</strong><p>{formatearCantidadUC(analisis.cantidad_uc)}</p></div>
                          <div><strong>Procedimiento</strong><p>{analisis.procedimiento}</p></div>
                          <div><strong>Norma</strong><p>{analisis.norma_uc}</p></div>
                        </div>

                        <div className="subcard">
                          <h4>Checklist inteligente</h4>
                          <div className="checklist-grid">
                            <p className={analisis.op_detectada ? 'ok' : 'warn'}><IndicadorBinario completo={analisis.op_detectada} /> OP cargada</p>
                            <p className={analisis.proveedor ? 'ok' : 'warn'}><IndicadorBinario completo={Boolean(analisis.proveedor)} /> Proveedor</p>
                            <p className={analisis.cuit ? 'ok' : 'warn'}><IndicadorBinario completo={Boolean(analisis.cuit)} /> CUIT</p>
                            <p className={analisis.documentos_comerciales.length ? 'ok' : 'warn'}><IndicadorBinario completo={Boolean(analisis.documentos_comerciales.length)} /> Facturas liquidadas</p>
                            <p className={!analisis.faltantes.includes('Remito o conformidad firmada') ? 'ok' : 'warn'}><IndicadorBinario completo={!analisis.faltantes.includes('Remito o conformidad firmada')} /> Remito / conformidad</p>
                            <p className={!analisis.faltantes.includes('Validación CAE') ? 'ok' : 'warn'}><IndicadorBinario completo={!analisis.faltantes.includes('Validación CAE')} /> CAE</p>
                            <p className={!analisis.faltantes.includes('Certificado Fiscal ARBA') ? 'ok' : 'warn'}><IndicadorBinario completo={!analisis.faltantes.includes('Certificado Fiscal ARBA')} /> ARBA</p>
                            <p className={!analisis.faltantes.includes('Constancia ARCA') ? 'ok' : 'warn'}><IndicadorBinario completo={!analisis.faltantes.includes('Constancia ARCA')} /> ARCA</p>
                          </div>
                        </div>


                        <div className="subcard evidence-card">
                          <h4>Evidencias verificadas</h4>
                          <p className="muted">
                            El sistema controla si el requisito está acreditado: archivo, checklist o dato automático de la OP.
                          </p>
                          <div className="evidence-grid">
                            <p className="ok"><CircleCheck className="inline-status-icon" aria-hidden="true" /> OP <span>PDF cargado</span></p>
                            <p className={analisis.proveedor ? 'ok' : 'warn'}><IndicadorBinario completo={Boolean(analisis.proveedor)} /> Proveedor <span>Dato OP</span></p>
                            <p className={analisis.cuit ? 'ok' : 'warn'}><IndicadorBinario completo={Boolean(analisis.cuit)} /> CUIT <span>Dato OP</span></p>
                            <p className={analisis.documentos_comerciales.length ? 'ok' : 'warn'}><IndicadorBinario completo={Boolean(analisis.documentos_comerciales.length)} /> Facturas <span>{analisis.documentos_comerciales.length ? 'Detectadas en OP' : 'Archivo o checklist'}</span></p>
                            <p className={!analisis.faltantes.includes('Remito o conformidad firmada') ? 'ok' : 'warn'}><IndicadorBinario completo={!analisis.faltantes.includes('Remito o conformidad firmada')} /> Remito / conformidad <span>Archivo o checklist</span></p>
                            <p className={!analisis.faltantes.includes('Validación CAE') ? 'ok' : 'warn'}><IndicadorBinario completo={!analisis.faltantes.includes('Validación CAE')} /> CAE <span>Consulta, archivo o checklist</span></p>
                            <p className={!analisis.faltantes.includes('Certificado Fiscal ARBA') ? 'ok' : 'warn'}><IndicadorBinario completo={!analisis.faltantes.includes('Certificado Fiscal ARBA')} /> ARBA <span>Archivo o checklist</span></p>
                            <p className={!analisis.faltantes.includes('Constancia ARCA') ? 'ok' : 'warn'}><IndicadorBinario completo={!analisis.faltantes.includes('Constancia ARCA')} /> ARCA <span>Archivo o checklist</span></p>
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
                            {analisis.validaciones.map((v, i) => <p key={i} className="ok"><CircleCheck className="inline-status-icon" aria-hidden="true" /> {v}</p>)}
                          </div>
                          <div>
                            <h4>Faltantes</h4>
                            {analisis.faltantes.map((f, i) => <p key={i} className="warn"><TriangleAlert className="inline-status-icon" aria-hidden="true" /> {f}</p>)}
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
                            <span><CircleCheck aria-hidden="true" /> Cumplido</span>
                            <span><TriangleAlert aria-hidden="true" /> Advertencia</span>
                            <span><CircleX aria-hidden="true" /> Error bloqueante</span>
                          </div>
                        </div>

                        {validacion.estado_general === 'VERDE' && seleccionado.estado !== 'VALIDADO' && (
                          <div className="validation-action-panel green-panel">
                            <h4>Validación documental completa</h4>
                            <p>Todas las evidencias requeridas fueron acreditadas. El expediente puede ser validado para continuar con la generación de la Disposición.</p>
                            <button className="primary" disabled={expedienteTerminal} onClick={validarExpediente}>Validar expediente</button>
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
                              <button className="primary" disabled={expedienteTerminal} onClick={validarConObservaciones}>Validar con observaciones</button>
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

                    {!disposicionBorrador && <div className="observation-box">
                      <h4>Número de Disposición</h4>
                      {disposicionEmitida ? (
                        <p><strong>{seleccionado.numero_disposicion || 'No informado'}</strong></p>
                      ) : (
                        <>
                          <label htmlFor="numero-disposicion-expediente">Número asignado</label>
                          <input
                            id="numero-disposicion-expediente"
                            value={numeroDisposicionEditable}
                            onChange={(e) => {
                              setNumeroDisposicionEditable(e.target.value);
                              setErrorNumeroDisposicion('');
                            }}
                            placeholder="Ejemplo: 75/2026"
                          />
                          <div className="actions">
                            <button
                              className="secondary"
                              type="button"
                              onClick={guardarNumeroDisposicion}
                              disabled={guardandoNumeroDisposicion}
                            >
                              {guardandoNumeroDisposicion ? 'Guardando...' : 'Guardar número'}
                            </button>
                          </div>
                          {errorNumeroDisposicion && (
                            <div className="notice error">{errorNumeroDisposicion}</div>
                          )}
                        </>
                      )}
                    </div>}

                    {!disposicionBorrador ? (
                      <div className="empty-disposition">
                        <p className="empty">Todavía no hay borrador generado para este expediente.</p>
                        {seleccionado.estado === 'VALIDADO' ? (
                          <button className="secondary" disabled={expedienteTerminal} onClick={() => prepararDisposicion(false)}>Generar borrador de Disposición</button>
                        ) : (
                          <p className="warn">El expediente debe estar validado antes de generar la disposición.</p>
                        )}
                      </div>
                    ) : (
                      <>
                        <div className="expediente-summary-grid disposition-summary-grid">
                          <div>
                            <span>Número de Disposición</span>
                            <input
                              aria-label="Número de Disposición"
                              value={numeroDisposicionEditable}
                              onChange={(e) => {
                                setNumeroDisposicionEditable(e.target.value);
                                setErrorNumeroDisposicion('');
                              }}
                              placeholder="Ejemplo: 75/2026"
                            />
                            <button
                              className="secondary small-button"
                              type="button"
                              onClick={guardarNumeroDisposicion}
                              disabled={guardandoNumeroDisposicion}
                            >
                              {guardandoNumeroDisposicion ? 'Guardando...' : 'Guardar número'}
                            </button>
                            {errorNumeroDisposicion && <span className="warn">{errorNumeroDisposicion}</span>}
                          </div>
                          <div><span>Estado</span><strong>{disposicionBorrador.estado}</strong></div>
                          <div><span>Expediente</span><strong>{seleccionado.numero_interno}</strong></div>
                          <div><span>OP</span><strong>{analisis?.orden_pago || 'No informada'}</strong></div>
                          <div><span>Proveedor</span><strong>{analisis?.proveedor || 'No informado'}</strong></div>
                          <div><span>Importe</span><strong>{analisis?.importe_bruto != null ? moneda(analisis.importe_bruto) : 'No informado'}</strong></div>
                          <div><span>Procedimiento</span><strong>{analisis?.procedimiento || 'No informado'}</strong></div>
                          <div><span>Norma</span><strong>{analisis?.norma_uc || 'No informada'}</strong></div>
                          <div><span>Fecha</span><strong>{formatearFechaHora(disposicionBorrador.actualizado || disposicionBorrador.creado)}</strong></div>
                        </div>

                        <div className="actions disposition-primary-actions">
                          <button className="secondary" disabled={expedienteTerminal} onClick={() => prepararDisposicion(true)}><RefreshCw aria-hidden="true" />Regenerar borrador</button>
                          <button className="primary" disabled={expedienteTerminal} onClick={guardarBorradorDisposicion}><Save aria-hidden="true" />Guardar borrador</button>
                          <button className="secondary" onClick={descargarBorradorTexto}><FileText aria-hidden="true" />Exportar texto</button>
                          <button className="primary" onClick={descargarBorradorWord}><Download aria-hidden="true" />Descargar Word</button>
                          {seleccionado.estado === 'VALIDADO' && <button className="primary" onClick={generarDisposicion}><FileSignature aria-hidden="true" />Emitir disposición</button>}
                        </div>

                        <button
                          className="disposition-collapse-toggle"
                          type="button"
                          aria-expanded={mostrarTextoBorrador}
                          onClick={() => setMostrarTextoBorrador((visible) => !visible)}
                        >
                          {mostrarTextoBorrador ? <ChevronUp aria-hidden="true" /> : <ChevronDown aria-hidden="true" />}
                          {mostrarTextoBorrador ? 'Ocultar borrador de Disposición' : 'Ver borrador de Disposición'}
                        </button>

                        {mostrarTextoBorrador && (
                          <div className="disposition-editor disposition-collapsible-content">
                            <div className="disposition-main">
                              <h4>DISPOSICIÓN Nº {disposicionBorrador.numero_disposicion || '____/____'}</h4>

                              <label>VISTO</label>
                              <textarea value={disposicionBorrador.visto} onChange={(e) => setDisposicionBorrador({ ...disposicionBorrador, visto: e.target.value })} />

                              <label>CONSIDERANDO</label>
                              <textarea value={disposicionBorrador.considerando} onChange={(e) => setDisposicionBorrador({ ...disposicionBorrador, considerando: e.target.value })} />

                              <label>POR ELLO / DISPONE</label>
                              <textarea value={disposicionBorrador.dispone} onChange={(e) => setDisposicionBorrador({ ...disposicionBorrador, dispone: e.target.value })} />
                            </div>

                            <aside className="disposition-aside">
                              <h4>Observaciones IA</h4>
                              {disposicionBorrador.observaciones_ia.map((obs, i) => <p key={i} className="warn"><TriangleAlert className="inline-status-icon" aria-hidden="true" /> {obs}</p>)}
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
                      </>
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

              {!disposicionEmitida && <aside className="next-action-panel">
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
              </aside>}
            </div>
          </section>
        )}

        {pantalla === 'administracion' && (
          <div className="administracion-page">
            <section className="card administracion-summary">
              <div className="card-title administracion-summary-heading">
                <div>
                  <h3>Administración</h3>
                  <p className="muted">
                    Configuración institucional y catálogos del sistema.
                  </p>
                </div>
                <span className="badge blue">Configuración</span>
              </div>

              <div className="admin-grid">
                <div>
                  <strong>Parámetros institucionales</strong>
                  <span>Datos del organismo, distrito y localidad.</span>
                </div>
                <div>
                  <strong>Catálogos administrativos</strong>
                  <span>Autoridades, resultados y datos auxiliares.</span>
                </div>
                <div>
                  <strong>Fondos y Unidad de Contratación</strong>
                  <span>Configuración institucional de fondos y UC.</span>
                </div>
                <div>
                  <strong>Usuarios y plantillas</strong>
                  <span>Permisos y plantillas documentales.</span>
                </div>
              </div>
            </section>

            <ProveedoresAdmin />
          </div>
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
              <button className="primary" disabled={expedienteTerminal} onClick={guardarChecklistFisico}>Guardar checklist</button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

function ExpedientesTabla({ expedientes, abrir }: { expedientes: Expediente[], abrir: (exp: Expediente) => void }) {
  if (expedientes.length === 0) return <p className="empty">No existen expedientes registrados.</p>;
  const proximasAcciones: Record<string, string> = {
    BORRADOR: 'Completar preparación',
    DOCUMENTACION_EN_CARGA: 'Completar documentación',
    PENDIENTE_VALIDACION: 'Continuar validación',
    VALIDADO: 'Emitir disposición',
    DISPOSICION_EMITIDA: 'Registrar firma',
    FIRMADO: 'Archivar',
    PENDIENTE_REVALIDACION: 'Continuar trámite',
    ARCHIVADO: 'Finalizado',
  };
  return (
    <div className="expedientes-table-wrap">
    <table>
      <thead><tr><th>Expediente</th><th>Expediente GDEBA</th><th>ID SUNA</th><th>Área</th><th>Estado</th><th>Establecimiento</th><th>Próxima acción</th><th></th></tr></thead>
      <tbody>
        {expedientes.map((exp) => (
          <tr key={exp.id}>
            <td>{exp.numero_interno}</td>
            <td>{exp.numero_gdeba || '-'}</td>
            <td>{exp.id_suna || '-'}</td>
            <td>Fondo Comp.</td>
            <td><span className={claseEstado(exp.estado)}>{etiquetaEstado(exp.estado)}</span></td>
            <td>{exp.establecimiento || '-'}</td>
            <td className="next-action-cell">{proximasAcciones[exp.estado] || 'Continuar trámite'}</td>
            <td><button className="small-button" onClick={() => abrir(exp)}>Abrir</button></td>
          </tr>
        ))}
      </tbody>
    </table>
    </div>
  );
}

createRoot(document.getElementById('root')!).render(<App />);
