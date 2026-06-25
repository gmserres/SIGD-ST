-- SIGD-ST - Esquema inicial ampliado

CREATE TABLE usuarios (
    id UUID PRIMARY KEY,
    nombre TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    rol TEXT NOT NULL,
    activo BOOLEAN DEFAULT TRUE
);

CREATE TABLE proveedores (
    id UUID PRIMARY KEY,
    cuit TEXT UNIQUE NOT NULL,
    razon_social TEXT NOT NULL,
    condicion_iva TEXT
);

CREATE TABLE establecimientos (
    id UUID PRIMARY KEY,
    tipo TEXT NOT NULL,
    numero TEXT NOT NULL,
    nombre_abreviado TEXT NOT NULL,
    nombre_completo TEXT
);

CREATE TABLE expedientes (
    id UUID PRIMARY KEY,
    numero_interno TEXT NOT NULL,
    tipo_tramite TEXT NOT NULL,
    estado TEXT NOT NULL,
    establecimiento TEXT,
    objeto TEXT,
    numero_disposicion TEXT,
    fecha_creacion TIMESTAMP NOT NULL,
    usuario_creacion UUID REFERENCES usuarios(id)
);

CREATE TABLE documentos (
    id UUID PRIMARY KEY,
    expediente_id UUID REFERENCES expedientes(id),
    tipo TEXT NOT NULL,
    nombre_archivo TEXT NOT NULL,
    ruta TEXT NOT NULL,
    fecha_carga TIMESTAMP NOT NULL,
    observaciones TEXT
);

CREATE TABLE historial_expediente (
    id UUID PRIMARY KEY,
    expediente_id UUID REFERENCES expedientes(id),
    accion TEXT NOT NULL,
    usuario TEXT NOT NULL,
    fecha TIMESTAMP NOT NULL,
    detalle TEXT
);
