import { maintenanceApi, api } from "./api"
import { WorkOrder, ServiceOrderUpdate, Team } from "../types/maintenance"

// ORDERS
export const getOrders = () => maintenanceApi.get<WorkOrder[]>("/orders")
export const getOrder = (id: string) => maintenanceApi.get<WorkOrder>(`/orders/${id}`)
export const createOrder = (data: Partial<WorkOrder>) => maintenanceApi.post<WorkOrder>("/orders", data)
export const updateOrder = (id: string, data: ServiceOrderUpdate) => maintenanceApi.put<WorkOrder>(`/orders/${id}`, data)
export const assignOrder = (id: string, teamName: string) => maintenanceApi.put<WorkOrder>(`/orders/${Number(id)}/assign`, { team_name: teamName })
// Não há endpoint DELETE para orders

// TEAMS
export const getTeams = () => maintenanceApi.get<Team[]>("/teams")
export const createTeam = (data: Partial<Team>) => maintenanceApi.post<Team>("/teams", data)
// Não há endpoint DELETE ou PUT para teams
export const updateTeam = (id: string, data: any) => Promise.reject("Endpoint não implementado no backend")

// COMPLAINTS
export const getComplaints = () => api.get("/complaints")
export const createComplaint = (data: any) => api.post("/public/complaints", data)
export const updateComplaintStatus = (id: string, data: any) => api.put(`/complaints/${id}/status`, data)
// Não há endpoint DELETE para complaints

// MAINTENANCES
export const getMaintenances = () => api.get("/maintenances")
export const createMaintenance = (data: any) => api.post("/maintenances", data)
