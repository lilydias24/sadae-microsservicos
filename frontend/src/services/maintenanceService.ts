import type { AxiosResponse } from "axios"
import axios from "axios"
import { api } from "./api"

// Tipos para o módulo de Manutenção
export interface WorkOrder {
  id: number
  protocol_number: string
  title: string
  description: string
  priority: "low" | "medium" | "high" | "critical"
  location: string
  status: "open" | "assigned" | "in_progress" | "completed"
  assigned_team?: string
  created_by: number
  created_by_name?: string
  created_at: string
  updated_at: string
}

export interface Team {
  id: number
  name: string
  description?: string
  specialization?: string
  members_count: number
  max_concurrent_orders: number
  is_active: boolean
  status?: "available" | "busy"
  members?: TeamMember[]
  created_at: string
  updated_at: string
}

export interface TeamMember {
  id: number
  team_id: number
  name: string
  role?: string
  contact?: string
  is_active: boolean
}

export interface Complaint {
  id: number
  protocol_number: string
  title: string
  description: string
  category: string
  location: string
  citizen_name: string
  citizen_contact: string
  status: "pending" | "in_progress" | "resolved"
  created_at: string
  updated_at: string
}

// Serviço de Manutenção (via API Gateway - pode ter problemas de auth)
export const maintenanceService = {
  getWorkOrders(params: { status?: string } = {}): Promise<AxiosResponse<WorkOrder[]>> {
    return api.get("/maintenance/orders", { params })
  },

  getWorkOrder(id: number): Promise<AxiosResponse<WorkOrder>> {
    return api.get(`/maintenance/orders/${id}`)
  },

  createWorkOrder(data: any): Promise<AxiosResponse<WorkOrder>> {
    return api.post("/maintenance/orders", data)
  },

  updateWorkOrder(id: number, data: any): Promise<AxiosResponse<WorkOrder>> {
    return api.put(`/maintenance/orders/${id}`, data)
  },

  assignWorkOrder(id: number, teamName: string): Promise<AxiosResponse<WorkOrder>> {
    return api.put(`/maintenance/orders/${id}/assign`, null, { params: { team_name: teamName } })
  },

  getOrderProgress(id: number): Promise<AxiosResponse<any[]>> {
    return api.get(`/maintenance/orders/${id}/progress`)
  },

  addOrderProgress(id: number, data: any): Promise<AxiosResponse<any>> {
    return api.post(`/maintenance/orders/${id}/progress`, data)
  },

  getTeams(params: { active_only?: boolean } = {}): Promise<AxiosResponse<Team[]>> {
    return api.get("/maintenance/teams", { params })
  },

  createTeam(data: any): Promise<AxiosResponse<Team>> {
    return api.post("/maintenance/teams", data)
  },

  updateTeam(id: number, data: any): Promise<AxiosResponse<Team>> {
    return api.put(`/maintenance/teams/${id}`, data)
  },

  deleteTeam(id: number): Promise<AxiosResponse<void>> {
    return api.delete(`/maintenance/teams/${id}`)
  },

  getTeamMembers(teamId: number): Promise<AxiosResponse<TeamMember[]>> {
    return api.get(`/maintenance/teams/${teamId}/members`)
  },

  addTeamMember(teamId: number, data: any): Promise<AxiosResponse<TeamMember>> {
    return api.post(`/maintenance/teams/${teamId}/members`, data)
  },

  updateTeamMember(teamId: number, memberId: number, data: any): Promise<AxiosResponse<TeamMember>> {
    return api.put(`/maintenance/teams/${teamId}/members/${memberId}`, data)
  },

  deleteTeamMember(teamId: number, memberId: number): Promise<AxiosResponse<void>> {
    return api.delete(`/maintenance/teams/${teamId}/members/${memberId}`)
  },

  getComplaints(params: { status?: string; category?: string } = {}): Promise<AxiosResponse<Complaint[]>> {
    return api.get("/maintenance/complaints", { params })
  },

  createComplaint(data: any): Promise<AxiosResponse<Complaint>> {
    return api.post("/maintenance/public/complaints", data)
  },
}

// Acesso DIRETO ao core-service (bypass gateway) para desenvolvimento
// ✅ Igual ao monitoringDev - acessa localhost:8002 diretamente
const maintenanceDirect = axios.create({ 
  baseURL: "http://localhost:8002", 
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// Interceptor para adicionar token nas requisições diretas
maintenanceDirect.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token")
    console.log("🔐 maintenanceDev: Enviando requisição", {
      url: config.url,
      method: config.method,
      hasToken: !!token,
      token: token ? `${token.substring(0, 20)}...` : null
    })
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    console.error("❌ maintenanceDev: Erro no interceptor de request", error)
    return Promise.reject(error)
  }
)

// Interceptor de resposta para debug
maintenanceDirect.interceptors.response.use(
  (response) => {
    console.log("✅ maintenanceDev: Resposta recebida", {
      url: response.config.url,
      status: response.status,
      data: response.data
    })
    return response
  },
  (error) => {
    console.error("❌ maintenanceDev: Erro na resposta", {
      url: error.config?.url,
      status: error.response?.status,
      data: error.response?.data,
      message: error.message
    })
    return Promise.reject(error)
  }
)

// ✅ SERVIÇO DIRETO (RECOMENDADO) - Acessa core-service diretamente
export const maintenanceDev = {
  // Work Orders
  getWorkOrders(params: { status?: string; priority?: string; team?: string; skip?: number; limit?: number } = {}): Promise<AxiosResponse<{ data: WorkOrder[] }>> {
    const { status, priority, team, skip = 0, limit = 100 } = params
    return maintenanceDirect.get("/maintenance/orders", { params: { status, priority, team, skip, limit } })
  },

  getWorkOrder(id: number): Promise<AxiosResponse<{ data: WorkOrder }>> {
    return maintenanceDirect.get(`/maintenance/orders/${id}`)
  },

  createWorkOrder(data: {
    title: string
    description: string
    priority: string
    location: string
    estimated_duration?: number
    anomaly_id?: number
  }): Promise<AxiosResponse<{ data: WorkOrder }>> {
    return maintenanceDirect.post("/maintenance/orders", data)
  },

  updateWorkOrder(id: number, data: any): Promise<AxiosResponse<{ data: WorkOrder }>> {
    return maintenanceDirect.put(`/maintenance/orders/${id}`, data)
  },

  assignWorkOrder(id: number, teamName: string): Promise<AxiosResponse<{ data: WorkOrder }>> {
    return maintenanceDirect.put(`/maintenance/orders/${id}/assign`, null, { params: { team_name: teamName } })
  },

  getOrderProgress(id: number): Promise<AxiosResponse<{ data: any[] }>> {
    return maintenanceDirect.get(`/maintenance/orders/${id}/progress`)
  },

  addOrderProgress(id: number, data: {
    status: string
    progress_notes: string
    estimated_completion?: string
  }): Promise<AxiosResponse<{ data: any }>> {
    return maintenanceDirect.post(`/maintenance/orders/${id}/progress`, data)
  },

  // Teams
  getTeams(params: { active_only?: boolean; skip?: number; limit?: number } = {}): Promise<AxiosResponse<{ data: Team[] }>> {
    const { active_only = true, skip = 0, limit = 100 } = params
    return maintenanceDirect.get("/maintenance/teams", { params: { active_only, skip, limit } })
  },

  createTeam(data: {
    name: string
    description?: string
    specialization?: string
    members_count?: number
    max_concurrent_orders?: number
    supervisor_name?: string
    supervisor_contact?: string
    work_areas?: string[]
    equipment?: string[]
  }): Promise<AxiosResponse<{ data: Team }>> {
    return maintenanceDirect.post("/maintenance/teams", data)
  },

  updateTeam(id: number, data: any): Promise<AxiosResponse<{ data: Team }>> {
    return maintenanceDirect.put(`/maintenance/teams/${id}`, data)
  },

  deleteTeam(id: number): Promise<AxiosResponse<void>> {
    return maintenanceDirect.delete(`/maintenance/teams/${id}`)
  },

  getTeamMembers(teamId: number): Promise<AxiosResponse<{ data: TeamMember[] }>> {
    return maintenanceDirect.get(`/maintenance/teams/${teamId}/members`)
  },

  addTeamMember(teamId: number, data: {
    name: string
    role?: string
    contact?: string
    is_active?: boolean
  }): Promise<AxiosResponse<{ data: TeamMember }>> {
    return maintenanceDirect.post(`/maintenance/teams/${teamId}/members`, data)
  },

  updateTeamMember(teamId: number, memberId: number, data: any): Promise<AxiosResponse<{ data: TeamMember }>> {
    return maintenanceDirect.put(`/maintenance/teams/${teamId}/members/${memberId}`, data)
  },

  deleteTeamMember(teamId: number, memberId: number): Promise<AxiosResponse<void>> {
    return maintenanceDirect.delete(`/maintenance/teams/${teamId}/members/${memberId}`)
  },

  // Complaints
  getComplaints(params: { status?: string; category?: string; skip?: number; limit?: number } = {}): Promise<AxiosResponse<{ data: Complaint[] }>> {
    const { status, category, skip = 0, limit = 100 } = params
    return maintenanceDirect.get("/maintenance/complaints", { params: { status, category, skip, limit } })
  },

  createComplaint(data: {
    title: string
    description: string
    category: string
    location: string
    citizen_name: string
    citizen_contact: string
    citizen_email?: string
  }): Promise<AxiosResponse<{ data: Complaint }>> {
    return maintenanceDirect.post("/maintenance/public/complaints", data)
  },

  // Anomaly Integration
  createOrderFromAnomaly(data: {
    anomaly_id: number
    sensor_id: string
    sensor_type: string
    location: string
    description: string
    severity: string
    value: number
    threshold_value: number
  }): Promise<AxiosResponse<{ data: WorkOrder }>> {
    return maintenanceDirect.post("/maintenance/orders/from-anomaly", data)
  },
}
