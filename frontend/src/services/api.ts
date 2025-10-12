import axios from "axios"

// Resolve API base URL from environment (for Docker) or fallback to localhost (dev)
const resolvedBaseURL =
  (typeof process !== "undefined" && (process as any).env?.REACT_APP_API_URL) ||
  (typeof window !== "undefined" && (window as any).__RUNTIME_CONFIG__?.API_URL) ||
  "http://localhost:8000"

export const api = axios.create({
  baseURL: resolvedBaseURL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token")
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  },
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token")
      localStorage.removeItem("user")
      window.location.href = "/login"
    }
    return Promise.reject(error)
  },
)

// API service functions
export const authService = {
  login: (username: string, password: string) => api.post("/auth/login", { username, password }),

  register: (userData: any) => api.post("/auth/register", userData),

  getCurrentUser: () => api.get("/me"),
}

export const monitoringService = {
  getSensors: () => api.get("/monitoring/sensors"),

  getSensorReadings: (sensorId?: number, limit = 100) =>
    api.get("/monitoring/readings/realtime", { params: { sensor_id: sensorId, limit } }),

  getAnomalies: (status?: string) => api.get("/monitoring/anomalies", { params: { status } }),

  createObservation: (data: any) => api.post("/monitoring/observations", data),

  generateReport: (params: any) => api.post("/monitoring/reports/generate", params),

  reportLeak: (data: any) => api.post("/monitoring/leaks/report", data),
}

export const maintenanceService = {
  getWorkOrders: (status?: string) => api.get("/maintenance/orders", { params: { status } }),

  createWorkOrder: (data: any) => api.post("/maintenance/orders", data),

  updateWorkOrder: (id: number, data: any) => api.put(`/maintenance/orders/${id}`, data),

  assignWorkOrder: (id: number, teamName: string) => api.put(`/maintenance/orders/${id}/assign`, null, { params: { team_name: teamName } }),

  getMaintenanceRecords: () => api.get("/maintenance/maintenances"),

  createMaintenanceRecord: (data: any) => api.post("/maintenance/maintenances", data),

  getComplaints: () => api.get("/maintenance/complaints"),

  createComplaint: (data: any) => api.post("/maintenance/complaints", data),

  getTeams: () => api.get("/maintenance/teams"),

  createTeam: (data: any) => api.post("/maintenance/teams", data),

  generateReport: (params: any) => api.post("/maintenance/reports/interventions", params),
}

export const billingService = {
  getCustomers: () => api.get("/billing/customers"),

  getCustomerBills: (customerId?: number) => api.get("/billing/bills", { params: { customer_id: customerId } }),

  contestBill: (billId: number, data: any) => api.post(`/billing/bills/${billId}/contest`, data),

  getContestations: () => api.get("/billing/contestations"),

  processContestation: (id: number, data: any) => api.put(`/billing/contestations/${id}`, data),

  getNegotiations: () => api.get("/billing/negotiations"),

  createNegotiation: (data: any) => api.post("/billing/negotiations", data),

  getMeterReadings: (meterId?: number) => api.get("/billing/meter-readings", { params: { meter_id: meterId } }),
}

// Crisis service temporarily disabled - endpoints not available in current backend
/*
export const crisisService = {
  getCriticalEvents: (status?: string) => api.get("/crisis/events/critical", { params: { status } }),

  createCriticalEvent: (data: any) => api.post("/crisis/events/critical", data),

  sendCivilDefenseAlert: (eventId: number, data: any) =>
    api.post(`/crisis/events/${eventId}/alert-civil-defense`, data),

  getEvacuationRoutes: (area?: string) => api.get("/crisis/routes/evacuation", { params: { area } }),

  recalculateRoutes: (data: any) => api.post("/crisis/routes/evacuation/recalculate", data),

  getSimulations: () => api.get("/crisis/simulations"),

  createSimulation: (data: any) => api.post("/crisis/simulations", data),

  getSimulationResults: (id: number) => api.get(`/crisis/simulations/${id}/results`),

  getMitigationPlans: (simulationId?: number) =>
    api.get("/crisis/mitigation-plans", { params: { simulation_id: simulationId } }),

  createMitigationPlan: (data: any) => api.post("/crisis/mitigation-plans", data),
}
*/
