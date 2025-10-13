"use client"

import { useEffect, useState } from "react"
import { monitoringDev } from "../services/monitoringService"
import { useWebSocket } from "../contexts/WebSocketContext"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

// --- INTERFACES (mantidas para estrutura) ---
interface SensorReading {
  id: string
  sensor_id: string
  sensor_type: string
  value: number
  unit: string
  timestamp: string
  location: string
  status: "normal" | "warning" | "critical"
}

interface Anomaly {
  id: string
  sensor_id: string
  description: string
  severity: "low" | "medium" | "high"
  status: "pending" | "confirmed" | "resolved"
  created_at: string
}

// --- DADOS MOCADOS ---
const mockSensors: SensorReading[] = [
  { id: "s1", sensor_id: "P-101", sensor_type: "pressure", value: 3.5, unit: "bar", timestamp: new Date().toISOString(), location: "Estação Central", status: "normal" },
  { id: "s2", sensor_id: "F-203", sensor_type: "flow", value: 150.2, unit: "m³/h", timestamp: new Date().toISOString(), location: "Reservatório Norte", status: "normal" },
  { id: "s3", sensor_id: "L-301", sensor_type: "level", value: 85, unit: "%", timestamp: new Date().toISOString(), location: "Reservatório Sul", status: "warning" },
  { id: "s4", sensor_id: "Q-405", sensor_type: "quality", value: 0.5, unit: "mg/L", timestamp: new Date().toISOString(), location: "Rede Distrital Leste", status: "normal" },
  { id: "s5", sensor_id: "P-102", sensor_type: "pressure", value: 4.8, unit: "bar", timestamp: new Date().toISOString(), location: "Zona Industrial", status: "critical" },
  { id: "s6", sensor_id: "PC-501", sensor_type: "precipitation", value: 2.1, unit: "mm", timestamp: new Date().toISOString(), location: "Estação Meteorológica", status: "normal" },
];

const mockAnomalies: Anomaly[] = [
  { id: "a1", sensor_id: "P-102", description: "Pressão 20% acima do limite superior.", severity: "high", status: "pending", created_at: new Date(Date.now() - 5 * 60 * 1000).toISOString() },
  { id: "a2", sensor_id: "L-301", description: "Nível do reservatório abaixo do limite de segurança.", severity: "medium", status: "pending", created_at: new Date(Date.now() - 30 * 60 * 1000).toISOString() },
  { id: "a3", sensor_id: "F-208", description: "Fluxo inconsistente detectado durante a madrugada.", severity: "low", status: "pending", created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString() },
];

const mockRealtimeChartData = Array.from({ length: 50 }, (_, i) => ({
    value: 3.5 + Math.sin(i / 5) * 0.5 + (Math.random() - 0.5) * 0.2,
    timestamp: new Date(Date.now() - (50 - i) * 60 * 1000).toISOString(),
}));


export function MonitoringPage() {
  const [selectedSensorType, setSelectedSensorType] = useState<string>("all")
  const { sensorData, alerts, isConnected, lastMessage } = useWebSocket()

  // Estado vindo do backend, com fallback para mocks
  const [realtimeData, setRealtimeData] = useState<any[]>([])
  const [anomalies, setAnomalies] = useState<{ data: Anomaly[] }>({ data: [] })
  const [anomaliesLimit, setAnomaliesLimit] = useState<number>(20)
  const [isUpdating, setIsUpdating] = useState<number | null>(null)

  // Carregar dados iniciais (apenas uma vez)
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const [hist, an] = await Promise.all([
          monitoringDev.getHistory({ sensor_id: "PRESS_001", limit: 50 }),
          monitoringDev.getAnomalies({ status: "pending", limit: anomaliesLimit }),
        ])
        const readings = Array.isArray(hist.data.readings) ? hist.data.readings : []
        const series = readings
          .filter((r: any) => r.sensor_id === "PRESS_001")
          .sort((a: any, b: any) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
          .map((r: any) => ({ value: Number(r.value), timestamp: r.timestamp }))
        setRealtimeData(series)
        setAnomalies({ data: an.data?.map((a: any) => ({
          id: String(a.id),
          sensor_id: a.sensor_id,
          description: a.description,
          severity: a.severity,
          status: a.status,
          created_at: a.created_at,
        })) ?? [] })
        console.log("✅ Monitoring: Dados iniciais carregados")
      } catch (error) {
        console.log("❌ Monitoring: Erro ao carregar dados iniciais:", error)
      }
    }
    loadInitialData()
  }, [])

  // Processar dados do WebSocket em tempo real
  useEffect(() => {
    if (lastMessage && lastMessage.type === "sensor_reading") {
      const reading = lastMessage.data
      console.log("📡 WebSocket: Nova leitura recebida!", reading)
      
      // Atualizar gráfico em tempo real
      setRealtimeData(prev => {
        const newData = [...prev, { value: Number(reading.value), timestamp: reading.timestamp }]
        // Manter apenas as últimas 50 leituras
        return newData.slice(-50)
      })
    }
    
    if (lastMessage && lastMessage.type === "anomaly_detected") {
      console.log("⚠️ WebSocket: Nova anomalia detectada!", lastMessage.data)
      // Adicionar anomalia à lista
      setAnomalies(prev => ({
        data: [lastMessage.data, ...prev.data]
      }))
    }
  }, [lastMessage])

  const handleAnomalyAction = async (id: number, action: "confirm" | "resolve") => {
    try {
      setIsUpdating(id)
      const newStatus = action === "confirm" ? "confirmed" : "resolved"
      await monitoringDev.updateAnomalyStatus(id, newStatus as any)
      // refresh list
      const an = await monitoringDev.getAnomalies({ status: "pending", limit: anomaliesLimit })
      setAnomalies({ data: an.data?.map((a: any) => ({
        id: String(a.id),
        sensor_id: a.sensor_id,
        description: a.description,
        severity: a.severity,
        status: a.status,
        created_at: a.created_at,
      })) ?? [] })
    } catch (e) {
      // noop
    } finally {
      setIsUpdating(null)
    }
  }
  
  // Filtrando os sensores mocados com base no seletor
  const filteredSensors = selectedSensorType === "all"
    ? mockSensors
    : mockSensors.filter(s => s.sensor_type === selectedSensorType);
  const sensors = { data: filteredSensors };

  const sensorsLoading = false;
  const anomaliesLoading = false;

  const sensorTypes = [
    { value: "all", label: "Todos os Sensores" },
    { value: "pressure", label: "Pressão" },
    { value: "flow", label: "Fluxo" },
    { value: "level", label: "Nível" },
    { value: "quality", label: "Qualidade" },
    { value: "precipitation", label: "Precipitação" },
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case "normal": return "text-green-600 bg-green-100"
      case "warning": return "text-yellow-600 bg-yellow-100"
      case "critical": return "text-red-600 bg-red-100"
      default: return "text-gray-600 bg-gray-100"
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "low": return "text-blue-600 bg-blue-100"
      case "medium": return "text-yellow-600 bg-yellow-100"
      case "high": return "text-red-600 bg-red-100"
      default: return "text-gray-600 bg-gray-100"
    }
  }

  if (sensorsLoading || anomaliesLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Monitoramento em Tempo Real</h1>
          <p className="text-gray-600">Acompanhe os dados dos sensores da rede de abastecimento</p>
        </div>

        <div className="flex items-center space-x-4">
          <select
            value={selectedSensorType}
            onChange={(e) => setSelectedSensorType(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {sensorTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>

          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-600">Ao vivo</span>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Sensores Ativos</p>
              <p className="text-2xl font-bold text-gray-900">{mockSensors.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Status Normal</p>
              <p className="text-2xl font-bold text-gray-900">
                {mockSensors.filter((s: SensorReading) => s.status === "normal").length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Alertas</p>
              <p className="text-2xl font-bold text-gray-900">
                {mockSensors.filter((s: SensorReading) => s.status === "warning").length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-red-100 rounded-lg">
              <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Críticos</p>
              <p className="text-2xl font-bold text-gray-900">
                {mockSensors.filter((s: SensorReading) => s.status === "critical").length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Real-time Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Dados em Tempo Real (Sensor de Pressão P-101)</h3>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={realtimeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" tickFormatter={(value) => new Date(value).toLocaleTimeString()} />
              <YAxis domain={[2, 5]} />
              <Tooltip
                labelFormatter={(value) => new Date(value).toLocaleString()}
                formatter={(value: number) => [`${value.toFixed(2)} bar`, "Pressão"]}
              />
              <Line type="monotone" dataKey="value" stroke="#2563eb" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sensors List */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Sensores Ativos</h3>
          </div>
          <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
            {sensors?.data?.map((sensor: SensorReading) => (
              <div key={sensor.id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {sensor.sensor_type.charAt(0).toUpperCase() + sensor.sensor_type.slice(1)} - {sensor.sensor_id}
                    </p>
                    <p className="text-sm text-gray-600">{sensor.location}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">
                      {sensor.value} {sensor.unit}
                    </p>
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(sensor.status)}`}>
                      {sensor.status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Anomalies */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Anomalias Pendentes</h3>
          </div>
          <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
            {anomalies?.data?.map((anomaly: Anomaly) => (
              <div key={anomaly.id} className="px-6 py-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">Sensor {anomaly.sensor_id}</p>
                    <p className="text-sm text-gray-600 mt-1">{anomaly.description}</p>
                    <p className="text-xs text-gray-500 mt-1">{new Date(anomaly.created_at).toLocaleString("pt-BR")}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getSeverityColor(anomaly.severity)}`}>
                      {anomaly.severity}
                    </span>
                    <button
                      onClick={() => handleAnomalyAction(Number(anomaly.id), "confirm")}
                      disabled={isUpdating === Number(anomaly.id)}
                      className="px-2 py-1 text-xs rounded-md bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
                    >
                      {isUpdating === Number(anomaly.id) ? "..." : "Confirmar"}
                    </button>
                    <button
                      onClick={() => handleAnomalyAction(Number(anomaly.id), "resolve")}
                      disabled={isUpdating === Number(anomaly.id)}
                      className="px-2 py-1 text-xs rounded-md bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
                    >
                      {isUpdating === Number(anomaly.id) ? "..." : "Fechar"}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
