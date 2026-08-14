import { ApiError, apiRequest } from './apiError';

export type SeleccionProveedor = {
  id_seleccion: string;
  expediente_id: string;
  solicitud_intervencion_id: string;
  decision_administrativa_id: string;
  proveedor_id: string;
  fecha_seleccion: string;
  seleccionado_por: string;
  proveedor_cuit: string;
  proveedor_razon_social: string;
  motivo_reemplazo: string | null;
  vigente: boolean;
};

export type SeleccionProveedorCrear = {
  proveedor_id: string;
  seleccionado_por: string;
};

export type ReemplazoProveedorCrear = SeleccionProveedorCrear & {
  motivo_reemplazo: string;
};

function rutaExpediente(expedienteId: string): string {
  return `/expedientes/${encodeURIComponent(expedienteId)}`;
}

export async function obtenerSeleccionProveedorVigente(
  expedienteId: string,
): Promise<SeleccionProveedor | null> {
  try {
    return await apiRequest<SeleccionProveedor>(
      `${rutaExpediente(expedienteId)}/seleccion-proveedor`,
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }

    throw error;
  }
}

export function seleccionarProveedor(
  expedienteId: string,
  datos: SeleccionProveedorCrear,
): Promise<SeleccionProveedor> {
  return apiRequest<SeleccionProveedor>(
    `${rutaExpediente(expedienteId)}/seleccion-proveedor`,
    {
      method: 'POST',
      body: JSON.stringify(datos),
    },
  );
}

export function reemplazarProveedor(
  expedienteId: string,
  datos: ReemplazoProveedorCrear,
): Promise<SeleccionProveedor> {
  return apiRequest<SeleccionProveedor>(
    `${rutaExpediente(expedienteId)}/seleccion-proveedor/reemplazos`,
    {
      method: 'POST',
      body: JSON.stringify(datos),
    },
  );
}

export function listarHistorialProveedores(
  expedienteId: string,
): Promise<SeleccionProveedor[]> {
  return apiRequest<SeleccionProveedor[]>(
    `${rutaExpediente(expedienteId)}/seleccion-proveedor/historial`,
  );
}
