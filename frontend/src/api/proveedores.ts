import { apiRequest } from './apiError';

export type Proveedor = {
  id_proveedor: string;
  cuit: string;
  razon_social: string;
  activo: boolean;
};

export type FiltrosProveedores = {
  buscar?: string;
  activo?: boolean;
};

export type ProveedorCrear = {
  cuit: string;
  razon_social: string;
};

export type ProveedorModificar = {
  razon_social: string;
};

function rutaProveedor(proveedorId: string): string {
  return `/proveedores/${encodeURIComponent(proveedorId)}`;
}

export function listarProveedores(
  filtros: FiltrosProveedores = {},
): Promise<Proveedor[]> {
  const parametros = new URLSearchParams();

  if (filtros.buscar !== undefined && filtros.buscar.trim()) {
    parametros.set('buscar', filtros.buscar.trim());
  }

  if (filtros.activo !== undefined) {
    parametros.set('activo', String(filtros.activo));
  }

  const consulta = parametros.toString();

  return apiRequest<Proveedor[]>(
    `/proveedores${consulta ? `?${consulta}` : ''}`,
  );
}

export function obtenerProveedor(
  proveedorId: string,
): Promise<Proveedor> {
  return apiRequest<Proveedor>(rutaProveedor(proveedorId));
}

export function crearProveedor(
  datos: ProveedorCrear,
): Promise<Proveedor> {
  return apiRequest<Proveedor>('/proveedores', {
    method: 'POST',
    body: JSON.stringify(datos),
  });
}

export function modificarRazonSocialProveedor(
  proveedorId: string,
  datos: ProveedorModificar,
): Promise<Proveedor> {
  return apiRequest<Proveedor>(rutaProveedor(proveedorId), {
    method: 'PATCH',
    body: JSON.stringify(datos),
  });
}

export function cambiarEstadoProveedor(
  proveedorId: string,
  activo: boolean,
): Promise<Proveedor> {
  return apiRequest<Proveedor>(
    `${rutaProveedor(proveedorId)}/estado`,
    {
      method: 'PATCH',
      body: JSON.stringify({ activo }),
    },
  );
}
