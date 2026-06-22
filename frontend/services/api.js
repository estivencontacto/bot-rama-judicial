// Cliente API usado por la version React del frontend.
// El dashboard estatico en index.html tiene su propio cliente embebido para ejecucion local simple.
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Wrapper minimo de fetch con error textual para mostrar fallos del backend.
async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, options);
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

// Encabezado de autenticacion JWT para endpoints protegidos.
function authHeaders(token) {
  return { Authorization: `Bearer ${token}` };
}

export const apiClient = {
  // Autenticacion.
  login(email, password) {
    return request("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
  },
  // Lecturas principales del dashboard.
  dashboard(token) {
    return request("/dashboard/resumen", { headers: authHeaders(token) });
  },
  procesos(token) {
    return request("/procesos", { headers: authHeaders(token) });
  },
  procesoDetalle(token, radicado) {
    return request(`/procesos/${encodeURIComponent(radicado)}`, { headers: authHeaders(token) });
  },
  reportes(token) {
    return request("/reportes", { headers: authHeaders(token) });
  },
  notificaciones(token) {
    return request("/notificaciones", { headers: authHeaders(token) });
  },
  // Configuracion de notificaciones.
  guardarNotificacion(token, payload) {
    return request("/notificaciones", {
      method: "PUT",
      headers: { ...authHeaders(token), "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  },
  reporteDownloadUrl(id) {
    return `${API_URL}/reportes/${id}/download`;
  },
  // Cargas y ejecuciones del scraper.
  uploadRadicados(token, file) {
    const form = new FormData();
    form.append("file", file);
    return request("/radicados/upload", {
      method: "POST",
      headers: authHeaders(token),
      body: form,
    });
  },
  ejecutarConsulta(token) {
    return request("/consultas/ejecutar", {
      method: "POST",
      headers: { ...authHeaders(token), "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
  },
};
