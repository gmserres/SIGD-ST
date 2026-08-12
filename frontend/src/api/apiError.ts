import { API_URL } from './config';

type DetalleValidacion = {
  msg?: unknown;
};

type DetalleAdministrativo = {
  mensaje?: unknown;
};

function esRegistro(valor: unknown): valor is Record<string, unknown> {
  return typeof valor === 'object' && valor !== null;
}

function mensajeDesdeDetalle(detalle: unknown): string | null {
  if (typeof detalle === 'string' && detalle.trim()) {
    return detalle;
  }

  if (Array.isArray(detalle)) {
    const mensajes = detalle
      .map((item: DetalleValidacion) => (
        typeof item?.msg === 'string' ? item.msg : null
      ))
      .filter((mensaje): mensaje is string => Boolean(mensaje));

    return mensajes.length > 0 ? mensajes.join(' ') : null;
  }

  if (esRegistro(detalle)) {
    const detalleAdministrativo = detalle as DetalleAdministrativo;

    if (
      typeof detalleAdministrativo.mensaje === 'string'
      && detalleAdministrativo.mensaje.trim()
    ) {
      return detalleAdministrativo.mensaje;
    }
  }

  return null;
}

function mensajeHttp(status: number): string {
  if (status === 404) return 'El recurso solicitado no existe.';
  if (status === 409) {
    return 'La operación entra en conflicto con el estado actual.';
  }
  if (status === 422) return 'Los datos ingresados no son válidos.';
  return 'No fue posible completar la operación.';
}

export class ApiError extends Error {
  readonly status: number;
  readonly detail: unknown;

  constructor(status: number, detail: unknown) {
    super(mensajeDesdeDetalle(detail) ?? mensajeHttp(status));
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

async function leerRespuesta(response: Response): Promise<unknown> {
  if (response.status === 204) return undefined;

  try {
    return await response.json();
  } catch {
    return undefined;
  }
}

export async function apiRequest<T>(
  ruta: string,
  opciones: RequestInit = {},
): Promise<T> {
  const headers = new Headers(opciones.headers);

  if (opciones.body !== undefined && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${API_URL}${ruta}`, {
    ...opciones,
    headers,
  });
  const contenido = await leerRespuesta(response);

  if (!response.ok) {
    const detail = esRegistro(contenido) && 'detail' in contenido
      ? contenido.detail
      : contenido;

    throw new ApiError(response.status, detail);
  }

  return contenido as T;
}
