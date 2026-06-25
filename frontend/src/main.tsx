import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

type Expediente = {
  id: string;
  numero_interno: string;
  tipo_tramite: string;
  estado: string;
  establecimiento?: string;
  objeto?: string;
  numero_disposicion?: string;
  creado: string;
};

function App() {
  const [expedientes, setExpedientes] = useState<Expediente[]>([]);
  const [numeroInterno, setNumeroInterno] = useState('033-188/2025');
  const [establecimiento, setEstablecimiento] = useState('EP N° 2');
  const [objeto, setObjeto] = useState('Recambio total de cañerías de agua fría');
  const [disposicion, setDisposicion] = useState('201/2025');

  async function cargarExpedientes() {
    const res = await fetch('http://localhost:8000/expedientes');
    setExpedientes(await res.json());
  }

  async function crearExpediente() {
    await fetch('http://localhost:8000/expedientes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        numero_interno: numeroInterno,
        establecimiento,
        objeto,
        numero_disposicion: disposicion,
      }),
    });
    await cargarExpedientes();
  }

  useEffect(() => {
    cargarExpedientes();
  }, []);

  return (
    <main className="layout">
      <aside className="sidebar">
        <h1>SIGD-ST</h1>
        <p>Sistema Inteligente de Gestión Documental</p>
        <button>Panel principal</button>
        <button>Nuevo Expediente</button>
        <button>Expedientes</button>
        <button>Administración</button>
      </aside>

      <section className="content">
        <header>
          <h2>Nuevo Expediente</h2>
          <span>Alfa 0.1.0</span>
        </header>

        <div className="card">
          <label>Expediente interno</label>
          <input value={numeroInterno} onChange={(e) => setNumeroInterno(e.target.value)} />

          <label>Número de disposición</label>
          <input value={disposicion} onChange={(e) => setDisposicion(e.target.value)} />

          <label>Establecimiento</label>
          <input value={establecimiento} onChange={(e) => setEstablecimiento(e.target.value)} />

          <label>Objeto</label>
          <textarea value={objeto} onChange={(e) => setObjeto(e.target.value)} />

          <button className="primary" onClick={crearExpediente}>
            Crear expediente
          </button>
        </div>

        <div className="card">
          <h3>Expedientes</h3>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Expediente</th>
                <th>Estado</th>
                <th>Establecimiento</th>
              </tr>
            </thead>
            <tbody>
              {expedientes.map((exp) => (
                <tr key={exp.id}>
                  <td>{exp.id}</td>
                  <td>{exp.numero_interno}</td>
                  <td>{exp.estado}</td>
                  <td>{exp.establecimiento}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}

createRoot(document.getElementById('root')!).render(<App />);
