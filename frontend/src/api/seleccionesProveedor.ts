import { ApiError, apiRequest } from './apiError';

export type SeleccionProveedor = {
  id_seleccion: string;
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

function rutaSolicitud(solicitudId: string): string {
  return `/solicitudes/${encodeURIComponent(solicitudId)}`;
}

export async function obtenerSeleccionProveedorVigente(
  solicitudId: string,
): Promise<SeleccionProveedor | null> {
  try {
    return await apiRequest<SeleccionProveedor>(
      `${rutaSolicitud(solicitudId)}/seleccion-proveedor`,
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }

    throw error;
  }
}

export function seleccionarProveedor(
  solicitudId: string,
  datos: SeleccionProveedorCrear,
): Promise<SeleccionProveedor> {
  return apiRequest<SeleccionProveedor>(
    `${rutaSolicitud(solicitudId)}/seleccion-proveedor`,
    {
      method: 'POST',
      body: JSON.stringify(datos),
    },
  );
}

export function reemplazarProveedor(
  solicitudId: string,
  datos: ReemplazoProveedorCrear,
): Promise<SeleccionProveedor> {
  return apiRequest<SeleccionProveedor>(
    `${rutaSolicitud(solicitudId)}/seleccion-proveedor/reemplazos`,
    {
      method: 'POST',
      body: JSON.stringify(datos),
    },
  );
}

export function listarHistorialProveedores(
  solicitudId: string,
): Promise<SeleccionProveedor[]> {
  return apiRequest<SeleccionProveedor[]>(
    `${rutaSolicitud(solicitudId)}/selecciones-proveedor`,
  );
}
