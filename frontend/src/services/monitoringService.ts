import type { AxiosResponse } from "axios"
import axios from "axios"
import { api } from "./api"

// Tipos básicos para o módulo de Monitoramento
export interface Sensor {
  sensor_id: number
  name: string
  location?: string
  sensor_type: "pressure" | "flow" | "level" | "quality" | "precipitation"
  status: "normal" | "warning" | "critical"
  last_read_at?: string
}

export interface SensorReading {
  sensor_id: number
  parameter_type: string
  value: number
  timestamp: string
}

export interface Anomaly {
  anomaly_id: number
  sensor_id: number
  description: string
  severity: "low" | "medium" | "high" | "critical"
  detected_at: string
  status: "new" | "ack" | "resolved"
}

export interface CreateObservationInput {
  sensor_id: number
  note: string
}

export interface ReportParams {
  from?: string
  to?: string
  sensor_id?: number
  format?: "pdf" | "csv"
}

// Serviço de Monitoramento (chama o backend via API Gateway)
export const monitoringService = {
  getSensors(): Promise<AxiosResponse<Sensor[]>> {
    return api.get("/monitoring/sensors")
  },

  getSensorReadings(params: { sensor_id?: number; limit?: number } = {}): Promise<AxiosResponse<SensorReading[]>> {
    const { sensor_id, limit = 100 } = params
    return api.get("/monitoring/sensors/readings", { params: { sensor_id, limit } })
  },

  getAnomalies(params: { status?: string } = {}): Promise<AxiosResponse<Anomaly[]>> {
    const { status } = params
    return api.get("/monitoring/anomalies", { params: { status } })
  },

  createObservation(data: CreateObservationInput): Promise<AxiosResponse<{ success: boolean }>> {
    return api.post("/monitoring/observations", data)
  },

  generateReport(params: ReportParams): Promise<AxiosResponse<{ url: string }>> {
    return api.post("/monitoring/reports/generate", params)
  },

  reportLeak(data: { location: string; description?: string }): Promise<AxiosResponse<{ ticket_id: string }>> {
    return api.post("/monitoring/leaks/report", data)
  },
}

// Acesso direto ao monitoring-service (bypass gateway) para desenvolvimento
const monitoringDirect = axios.create({ baseURL: "http://localhost:8003", timeout: 10000 })

export const monitoringDev = {
  getRealtimeReadings(): Promise<AxiosResponse<{ readings: any[]; timestamp: string }>> {
    return monitoringDirect.get("/readings/realtime")
  },

  getAnomalies(params: { status?: string; severity?: string; limit?: number; skip?: number } = {}): Promise<AxiosResponse<any[]>> {
    const { status, severity, limit = 50, skip = 0 } = params
    return monitoringDirect.get("/anomalies", { params: { status, severity, limit, skip } })
  },

  getHistory(params: { sensor_id?: string; sensor_type?: string; limit?: number } = {}): Promise<AxiosResponse<{ readings: any[] }>> {
    const { sensor_id, sensor_type, limit = 50 } = params
    return monitoringDirect.get("/readings/history", { params: { sensor_id, sensor_type, limit } })
  },

  updateAnomalyStatus(anomalyId: number, newStatus: "pending" | "confirmed" | "resolved"): Promise<AxiosResponse<{ message: string }>> {
    // Backend espera new_status como query param (tipo primitivo), não no corpo
    return monitoringDirect.put(`/anomalies/${anomalyId}/status`, null, { params: { new_status: newStatus } })
  },
}


