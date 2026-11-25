import { FormEvent, ReactNode, useEffect, useState } from 'react';
import {
  cerrarSesion,
  iniciarSesion,
  obtenerSesion,
  UsuarioSesion,
} from '../api/auth';


export function AuthGate({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<UsuarioSesion | null>(null);
  const [cargando, setCargando] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    obtenerSesion().then(setUsuario).finally(() => setCargando(false));
    const expirada = () => setUsuario(null);
    window.addEventListener('sigd-st-auth-expired', expirada);
    return () => window.removeEventListener('sigd-st-auth-expired', expirada);
  }, []);

  async function ingresar(event: FormEvent) {
    event.preventDefault();
    setEnviando(true);
    setError('');
    try {
      setUsuario(await iniciarSesion(email, password));
      setPassword('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No fue posible iniciar sesión.');
    } finally {
      setEnviando(false);
    }
  }

  if (cargando) return <main className="auth-screen"><p>Verificando sesión…</p></main>;
  if (!usuario) {
    return (
      <main className="auth-screen">
        <form className="auth-card" onSubmit={ingresar}>
          <img src="/branding/logo-sigd-st-sidebar.png" alt="SIGD-ST" />
          <div><span>Acceso institucional</span><h1>Iniciar sesión</h1></div>
          {error && <div className="notice error" role="alert">{error}</div>}
          <label>Correo electrónico<input type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus /></label>
          <label>Contraseña<input type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required /></label>
          <button className="primary" disabled={enviando}>{enviando ? 'Ingresando…' : 'Ingresar'}</button>
        </form>
      </main>
    );
  }
  return (
    <div className="authenticated-shell">
      <div className="session-indicator">
        <span><strong>{usuario.nombre}</strong> · {usuario.rol.replaceAll('_', ' ')}</span>
        <button onClick={async () => { await cerrarSesion(); setUsuario(null); }}>Cerrar sesión</button>
      </div>
      {children}
    </div>
  );
}
