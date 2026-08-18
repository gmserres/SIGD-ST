import { ApiError, apiRequest } from './apiError';

export type DisposicionBorrador = {
  expediente_id: string;
  documento_op_id: string;
  control_proveedor_op_id: string;
  seleccion_proveedor_id: string;
  proveedor_definitivo_id: string;
  proveedor_definitivo_cuit: string;
  proveedor_definitivo_razon_social: string | null;
  estado_habilitacion_actual: string;
  obsoleto: boolean;
  numero_disposicion: string | null;
  estado: string;
  visto: string;
  considerando: string;
  dispone: string;
  observaciones_ia: string[];
  creado: string;
  actualizado: string;
};

export type DisposicionEmitida = {
  id_disposicion: string;
  expediente_id: string;
  documento_op_id: string;
  control_proveedor_op_id: string;
  seleccion_proveedor_id: string;
  proveedor_definitivo_id: string;
  proveedor_definitivo_cuit: string;
  proveedor_definitivo_razon_social: string | null;
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
  estado_formalizacion: 'PENDIENTE' | 'FORMALIZADA';
  fecha_formalizacion: string | null;
  usuario_registro_formalizacion: string | null;
  registrado_formalizacion_en: string | null;
};

const ruta = (expedienteId: string, documentoOpId: string) => (
  `/expedientes/${expedienteId}/documentos/${documentoOpId}/disposicion`
);

export async function obtenerDisposicionOP(
  expedienteId: string,
  documentoOpId: string,
): Promise<DisposicionEmitida | null> {
  try {
    return await apiRequest(ruta(expedienteId, documentoOpId));
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export function generarBorradorDisposicionOP(
  expedienteId: string,
  documentoOpId: string,
  regenerar = false,
): Promise<DisposicionBorrador> {
  return apiRequest(
    `${ruta(expedienteId, documentoOpId)}/borrador?regenerar=${regenerar}`,
    { method: 'POST' },
  );
}

export function guardarBorradorDisposicionOP(
  expedienteId: string,
  documentoOpId: string,
  borrador: Pick<DisposicionBorrador, 'visto' | 'considerando' | 'dispone'>,
): Promise<DisposicionBorrador> {
  return apiRequest(`${ruta(expedienteId, documentoOpId)}/borrador`, {
    method: 'PUT',
    body: JSON.stringify(borrador),
  });
}

export function emitirDisposicionOP(
  expedienteId: string,
  documentoOpId: string,
  numeroDisposicion: string,
): Promise<DisposicionEmitida> {
  return apiRequest(ruta(expedienteId, documentoOpId), {
    method: 'POST',
    body: JSON.stringify({ numero_disposicion: numeroDisposicion }),
  });
}

export function formalizarDisposicion(
  idDisposicion: string,
  fechaFormalizacion: string,
): Promise<DisposicionEmitida> {
  return apiRequest(`/disposiciones/${idDisposicion}/formalizacion`, {
    method: 'POST',
    body: JSON.stringify({ fecha_formalizacion: fechaFormalizacion }),
  });
}
