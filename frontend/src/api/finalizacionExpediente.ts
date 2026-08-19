import { apiRequest } from './apiError';

export type OPPendienteCierre = {
  documento_op_id: string;
  nombre_archivo: string;
  causa: 'SIN_DISPOSICION' | 'DISPOSICION_SIN_FORMALIZAR';
};

export type HabilitacionCierre = {
  estado: 'HABILITADO' | 'YA_CERRADO' | 'YA_DESISTIDO' | 'ARCHIVADO' | 'ESTADO_NO_APTO' | 'SIN_OP' | 'OP_SIN_DISPOSICION' | 'DISPOSICION_SIN_FORMALIZAR';
  habilitado: boolean;
  cantidad_op: number;
  disposiciones_emitidas: number;
  disposiciones_formalizadas: number;
  op_pendientes: OPPendienteCierre[];
  mensaje: string;
  proxima_accion: string;
};

export type HabilitacionDesistimiento = {
  estado: 'HABILITADO' | 'YA_DESISTIDO' | 'YA_CERRADO' | 'ARCHIVADO' | 'ESTADO_NO_APTO' | 'TIENE_OP';
  habilitado: boolean;
  cantidad_op: number;
  mensaje: string;
  proxima_accion: string;
};

export const consultarHabilitacionCierre = (expedienteId: string) =>
  apiRequest<HabilitacionCierre>(`/expedientes/${expedienteId}/habilitacion-cierre`);

export const consultarHabilitacionDesistimiento = (expedienteId: string) =>
  apiRequest<HabilitacionDesistimiento>(`/expedientes/${expedienteId}/habilitacion-desistimiento`);

export const cerrarExpediente = <T>(expedienteId: string, fecha_cierre: string) =>
  apiRequest<T>(`/expedientes/${expedienteId}/cierre`, {
    method: 'POST',
    body: JSON.stringify({ fecha_cierre, confirmacion_completitud: true }),
  });

export const desistirExpediente = <T>(expedienteId: string, fecha_desistimiento: string, motivo_desistimiento: string) =>
  apiRequest<T>(`/expedientes/${expedienteId}/desistimiento`, {
    method: 'POST',
    body: JSON.stringify({ fecha_desistimiento, motivo_desistimiento }),
  });
