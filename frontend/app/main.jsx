import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { Bell, Download, Filter, LogOut, Play, Search, Upload } from "lucide-react";

import { apiClient } from "../services/api.js";
import "../app/styles.css";

// Pantalla de login para la version React del dashboard.
function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    setError("");
    try {
      const data = await apiClient.login(email, password);
      onLogin(data.access_token);
    } catch {
      setError("Credenciales invalidas o servicio no disponible.");
    }
  }

  return (
    <main className="loginShell">
      <form className="loginPanel" onSubmit={submit}>
        <div>
          <p className="eyebrow">Monitoreo judicial</p>
          <h1>Bot Rama Judicial</h1>
        </div>
        <label>
          Email
          <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" required />
        </label>
        <label>
          Password
          <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" required />
        </label>
        {error && <p className="error">{error}</p>}
        <button className="primaryButton" type="submit">Ingresar</button>
      </form>
    </main>
  );
}

// Dashboard React experimental. La version operativa actual se sirve desde frontend/index.html.
function Dashboard({ token, onLogout }) {
  const [resumen, setResumen] = useState(null);
  const [procesos, setProcesos] = useState([]);
  const [reportes, setReportes] = useState([]);
  const [notificaciones, setNotificaciones] = useState([]);
  const [selected, setSelected] = useState(null);
  const [filters, setFilters] = useState({ radicado: "", juzgado: "", estado: "", fecha: "" });
  const [busy, setBusy] = useState(false);

  // Carga los datos principales que alimentan metricas, tablas y reportes.
  async function refresh() {
    const [resumenData, procesosData, reportesData, notificacionesData] = await Promise.all([
      apiClient.dashboard(token),
      apiClient.procesos(token),
      apiClient.reportes(token),
      apiClient.notificaciones(token),
    ]);
    setResumen(resumenData);
    setProcesos(procesosData);
    setReportes(reportesData);
    setNotificaciones(notificacionesData);
  }

  useEffect(() => {
    refresh().catch(() => undefined);
  }, []);

  // Filtrado local para que la tabla responda sin llamar al backend en cada tecla.
  const filtered = useMemo(() => {
    return procesos.filter((item) => {
      const fecha = item.fecha_ultima_actuacion || item.fecha_radicacion || "";
      return (
        item.radicado.toLowerCase().includes(filters.radicado.toLowerCase()) &&
        (item.juzgado || "").toLowerCase().includes(filters.juzgado.toLowerCase()) &&
        (filters.estado ? item.estado === filters.estado : true) &&
        (filters.fecha ? fecha.startsWith(filters.fecha) : true)
      );
    });
  }, [procesos, filters]);

  // Carga masiva de radicados desde Excel.
  async function uploadExcel(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setBusy(true);
    try {
      await apiClient.uploadRadicados(token, file);
      await refresh();
    } finally {
      setBusy(false);
      event.target.value = "";
    }
  }

  // Inicia una consulta del scraper desde la interfaz.
  async function ejecutarConsulta() {
    setBusy(true);
    try {
      await apiClient.ejecutarConsulta(token);
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  async function openDetail(radicado) {
    setSelected(await apiClient.procesoDetalle(token, radicado));
  }

  async function toggleTelegram(event) {
    const current = notificaciones.find((item) => item.canal === "telegram");
    const destino = current?.destino || "";
    await apiClient.guardarNotificacion(token, {
      canal: "telegram",
      destino,
      habilitada: event.target.checked,
    });
    await refresh();
  }

  return (
    <main className="appShell">
      <aside className="sidebar">
        <h1>Rama Judicial</h1>
        <button title="Cerrar sesion" className="iconButton" onClick={onLogout}><LogOut size={18} /></button>
      </aside>

      <section className="content">
        <header className="toolbar">
          <div>
            <p className="eyebrow">Dashboard</p>
            <h2>Procesos monitoreados</h2>
          </div>
          <div className="actions">
            <label className="toolButton" title="Cargar Excel">
              <Upload size={18} />
              <input type="file" accept=".xlsx,.xls" onChange={uploadExcel} hidden />
            </label>
            <button className="toolButton" title="Ejecutar consulta" disabled={busy} onClick={ejecutarConsulta}><Play size={18} /></button>
          </div>
        </header>

        <section className="summaryGrid">
          {["total_radicados", "total_procesos", "total_consultas", "total_errores", "notificaciones_activas"].map((key) => (
            <article className="metric" key={key}>
              <span>{key.replaceAll("_", " ")}</span>
              <strong>{resumen?.[key] ?? 0}</strong>
            </article>
          ))}
        </section>

        <section className="filters">
          <Filter size={18} />
          <input placeholder="Radicado" value={filters.radicado} onChange={(e) => setFilters({ ...filters, radicado: e.target.value })} />
          <input placeholder="Juzgado" value={filters.juzgado} onChange={(e) => setFilters({ ...filters, juzgado: e.target.value })} />
          <input type="date" value={filters.fecha} onChange={(e) => setFilters({ ...filters, fecha: e.target.value })} />
          <select value={filters.estado} onChange={(e) => setFilters({ ...filters, estado: e.target.value })}>
            <option value="">Todos</option>
            <option value="monitoreado">Monitoreado</option>
          </select>
        </section>

        <section className="workArea">
          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>Radicado</th>
                  <th>Juzgado</th>
                  <th>Partes</th>
                  <th>Ultima actuacion</th>
                  <th>Estado</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((item) => (
                  <tr key={item.radicado}>
                    <td>{item.radicado}</td>
                    <td>{item.juzgado || "Sin dato"}</td>
                    <td>{item.partes || "Sin dato"}</td>
                    <td>{item.fecha_ultima_actuacion || "Sin fecha"}</td>
                    <td><span className="status">{item.estado}</span></td>
                    <td><button title="Ver detalle" className="iconButton" onClick={() => openDetail(item.radicado)}><Search size={16} /></button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <aside className="detailPanel">
            {selected ? (
              <>
                <h3>{selected.radicado}</h3>
                <p>{selected.juzgado || "Juzgado no identificado"}</p>
                <dl>
                  <dt>Demandante</dt><dd>{selected.demandante || "Sin dato"}</dd>
                  <dt>Demandado</dt><dd>{selected.demandado || "Sin dato"}</dd>
                  <dt>Radicacion</dt><dd>{selected.fecha_radicacion || "Sin fecha"}</dd>
                </dl>
                <h4>Historial</h4>
                <ul className="history">
                  {selected.historial.map((item) => <li key={item.id}>{item.fecha || ""} {item.titulo}</li>)}
                  {!selected.historial.length && <li>Sin actuaciones registradas.</li>}
                </ul>
              </>
            ) : (
              <p>Selecciona un proceso para ver su detalle.</p>
            )}
          </aside>
        </section>

        <section className="bottomGrid">
          <div>
            <h3>Reportes</h3>
            {reportes.map((reporte) => (
              <div className="reportRow" key={reporte.id}>
                <span>{reporte.nombre_archivo}</span>
                <a title="Descargar reporte" href={apiClient.reporteDownloadUrl(reporte.id)}><Download size={16} /></a>
              </div>
            ))}
          </div>
          <div>
            <h3>Notificaciones</h3>
            <label className="toggle">
              <input
                type="checkbox"
                checked={notificaciones.find((item) => item.canal === "telegram")?.habilitada ?? false}
                onChange={toggleTelegram}
              />
              <Bell size={16} /> Telegram
            </label>
          </div>
        </section>
      </section>
    </main>
  );
}

function App() {
  const [token, setToken] = useState(localStorage.getItem("access_token"));
  function onLogin(nextToken) {
    localStorage.setItem("access_token", nextToken);
    setToken(nextToken);
  }
  function onLogout() {
    localStorage.removeItem("access_token");
    setToken(null);
  }
  return token ? <Dashboard token={token} onLogout={onLogout} /> : <Login onLogin={onLogin} />;
}

createRoot(document.getElementById("root")).render(<App />);
