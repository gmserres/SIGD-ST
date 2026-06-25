-- SIGD-ST - Esquema inicial

CREATE TABLE usuarios (
    id UUID PRIMARY KEY,
    nombre TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    rol TEXT NOT NULL,
    activo BOOLEAN DEFAULT TRUE
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
    fecha_carga TIMESTAMP NOT NULL
);

CREATE TABLE auditoria (
    id UUID PRIMARY KEY,
    expediente_id UUID REFERENCES expedientes(id),
    usuario_id UUID REFERENCES usuarios(id),
    accion TEXT NOT NULL,
    fecha TIMESTAMP NOT NULL,
    detalle TEXT
);
