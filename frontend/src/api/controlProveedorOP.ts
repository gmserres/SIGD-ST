import { apiRequest } from './apiError';

export type EstadoControlProveedorOP =
  | 'COINCIDE'
  | 'CUIT_DIFERENTE'
  | 'NO_VERIFICABLE'
  | 'SIN_PROVEEDOR_SELECCIONADO'
  | 'SIN_SOLICITUD_ASOCIADA';

export type ControlProveedorOP = {
  expediente_id: string;
  documento_op_id: string;
  solicitud_intervencion_id: string | null;
  seleccion_proveedor_id: string | null;
  estado: EstadoControlProveedorOP;
  cuit_seleccionado: string | null;
  cuit_detectado: string | null;
  razon_social_seleccionada: string | null;
  razon_social_detectada: string | null;
  advertencias: string[];
  modo_analisis: string | null;
};

export type ControlProveedorOPRegistro = ControlProveedorOP & {
  id_control: string | null;
  fecha_control: string | null;
};

export type EstadoHabilitacionProveedorOP =
  | 'HABILITADO'
  | 'REQUIERE_REASIGNACION_PROVEEDOR'
  | 'REQUIERE_SELECCION_PROVEEDOR'
  | 'REQUIERE_NUEVO_CONTROL'
  | 'PROVEEDOR_NO_VERIFICABLE'
  | 'SIN_SOLICITUD_ASOCIADA';

export type HabilitacionProveedorOP = {
  expediente_id: string;
  documento_op_id: string;
  estado: EstadoHabilitacionProveedorOP;
  solicitud_intervencion_id: string | null;
  seleccion_proveedor_id: string | null;
  control_proveedor_op_id: string | null;
  proveedor_definitivo_id: string | null;
  proveedor_definitivo_cuit: string | null;
  proveedor_definitivo_razon_social: string | null;
  proveedor_op_en_maestro: boolean | null;
  proveedor_op_activo: boolean | null;
  mensaje: string;
  proxima_accion: string | null;
};

function rutaControlProveedorOP(
  expedienteId: string,
  documentoOpId: string,
): string {
  return (
    `/expedientes/${encodeURIComponent(expedienteId)}`
    + `/documentos/${encodeURIComponent(documentoOpId)}`
  );
}

export function consultarControlProveedorOP(
  expedienteId: string,
  documentoOpId: string,
): Promise<ControlProveedorOP> {
  return apiRequest<ControlProveedorOP>(
    `${rutaControlProveedorOP(expedienteId, documentoOpId)}`
    + '/control-proveedor',
  );
}

export function ejecutarControlProveedorOP(
  expedienteId: string,
  documentoOpId: string,
): Promise<ControlProveedorOPRegistro> {
  return apiRequest<ControlProveedorOPRegistro>(
    `${rutaControlProveedorOP(expedienteId, documentoOpId)}`
    + '/control-proveedor',
    {
      method: 'POST',
    },
  );
}

export function consultarHabilitacionProveedorOP(
  expedienteId: string,
  documentoOpId: string,
): Promise<HabilitacionProveedorOP> {
  return apiRequest<HabilitacionProveedorOP>(
    `${rutaControlProveedorOP(expedienteId, documentoOpId)}`
    + '/habilitacion-proveedor',
  );
}
