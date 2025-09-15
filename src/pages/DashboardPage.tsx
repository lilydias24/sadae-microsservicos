"use client"

import type React from "react"
import { useAuth } from "../contexts/AuthContext"
// import { useWebSocket } from "../contexts/WebSocketContext" // Removido para usar mocks
import { Activity, AlertTriangle, Wrench, CreditCard, Users, Droplets } from "lucide-react"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts"

// --- INÍCIO DOS DADOS MOCADOS ---

// Mock para os dados dos sensores (nível da água e pressão)
const mockSensorData = Array.from({ length: 48 }, (_, i) => {
  const hourAgo = 24 - Math.floor(i / 2)
  const date = new Date()
  date.setHours(date.getHours() - hourAgo)

  if (i % 2 === 0) {
    return {
      parameter_type: "water_level",
      value: (8 + Math.sin(i) * 1.5 + Math.random()).toFixed(2),
      timestamp: date.toISOString(),
    }
  }
  return {
    parameter_type: "pressure",
    value: (3 + Math.cos(i) * 0.3 + Math.random() * 0.2).toFixed(2),
    timestamp: date.toISOString(),
  }
})

// Mock para os alertas
const mockAlerts = [
  {
    message: "Pressão elevada detectada no Setor Central.",
    urgency_level: "high",
    created_at: new Date(Date.now() - 5 * 60 * 1000).toISOString(), // 5 minutos atrás
  },
  {
    message: "Nível do reservatório R-02 abaixo de 30%.",
    urgency_level: "medium",
    created_at: new Date(Date.now() - 15 * 60 * 1000).toISOString(), // 15 minutos atrás
  },
  {
    message: "Falha de comunicação com sensor de cloro S-45.",
    urgency_level: "medium",
    created_at: new Date(Date.now() - 60 * 60 * 1000).toISOString(), // 1 hora atrás
  },
]

// --- FIM DOS DADOS MOCADOS ---

export const DashboardPage: React.FC = () => {
  const { user } = useAuth()
  // const { sensorData, alerts, isConnected } = useWebSocket() // Linha original comentada

  // Usando os dados mocados
  const sensorData = mockSensorData
  const alerts = mockAlerts
  const isConnected = true // Força o status para "Online"

  // Mock data for charts
  const waterLevelData = sensorData
    .filter((reading) => reading.parameter_type === "water_level")
    .slice(0, 24)
    .reverse()
    .map((reading, index) => ({
      time: `${index}h`,
      level: reading.value,
    }))

  const pressureData = sensorData
    .filter((reading) => reading.parameter_type === "pressure")
    .slice(0, 24)
    .reverse()
    .map((reading, index) => ({
      time: `${index}h`,
      pressure: reading.value,
    }))

  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return "Bom dia"
    if (hour < 18) return "Boa tarde"
    return "Boa noite"
  }

  const getRoleSpecificStats = () => {
    switch (user?.role) {
      case "operator":
        return [
          { title: "Sensores Ativos", value: "24", icon: Activity, color: "bg-green-500" },
          { title: "Alertas Pendentes", value: alerts.length.toString(), icon: AlertTriangle, color: "bg-red-500" },
          { title: "Pressão Média", value: "3.2 bar", icon: Droplets, color: "bg-blue-500" },
          { title: "Qualidade da Água", value: "98%", icon: Activity, color: "bg-emerald-500" },
        ]
      case "maintenance_manager":
        return [
          { title: "Ordens Abertas", value: "12", icon: Wrench, color: "bg-orange-500" },
          { title: "Equipes Ativas", value: "8", icon: Users, color: "bg-purple-500" },
          { title: "Manutenções Hoje", value: "5", icon: Wrench, color: "bg-blue-500" },
          { title: "Eficiência", value: "94%", icon: Activity, color: "bg-green-500" },
        ]
      case "financial_manager":
        return [
          { title: "Faturas Emitidas", value: "1,234", icon: CreditCard, color: "bg-blue-500" },
          { title: "Contestações", value: "23", icon: AlertTriangle, color: "bg-yellow-500" },
          { title: "Taxa de Cobrança", value: "96%", icon: CreditCard, color: "bg-green-500" },
          { title: "Inadimplência", value: "4%", icon: AlertTriangle, color: "bg-red-500" },
        ]
      case "crisis_manager":
        return [
          { title: "Eventos Críticos", value: "2", icon: AlertTriangle, color: "bg-red-500" },
          { title: "Simulações Ativas", value: "1", icon: Activity, color: "bg-blue-500" },
          { title: "Rotas de Evacuação", value: "15", icon: Activity, color: "bg-green-500" },
          { title: "População Monitorada", value: "85k", icon: Users, color: "bg-purple-500" },
        ]
      default:
        return [
          { title: "Minha Conta", value: "Ativa", icon: Users, color: "bg-green-500" },
          { title: "Última Fatura", value: "R$ 45,20", icon: CreditCard, color: "bg-blue-500" },
          { title: "Consumo Médio", value: "15m³", icon: Droplets, color: "bg-blue-500" },
          { title: "Status", value: "Em dia", icon: Activity, color: "bg-green-500" },
        ]
    }
  }

  const stats = getRoleSpecificStats()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-800">
            {getGreeting()}, {user?.full_name?.split(" ")[0]}!
          </h1>
          <p className="text-slate-600 mt-1">Bem-vindo ao painel do SADAE</p>
        </div>
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${isConnected ? "bg-green-500" : "bg-red-500"}`} />
          <span className="text-sm text-slate-600">{isConnected ? "Sistema Online" : "Sistema Offline"}</span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <div key={index} className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-600">{stat.title}</p>
                <p className="text-2xl font-bold text-slate-800 mt-1">{stat.value}</p>
              </div>
              <div className={`w-12 h-12 ${stat.color} rounded-lg flex items-center justify-center`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Section - Only for technical users */}
      {["operator", "crisis_manager", "maintenance_manager"].includes(user?.role || "") && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Water Level Chart */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h3 className="text-lg font-semibold text-slate-800 mb-4">Nível de Água (24h)</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={waterLevelData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="level" stroke="#3b82f6" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Pressure Chart */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h3 className="text-lg font-semibold text-slate-800 mb-4">Pressão da Rede (24h)</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={pressureData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="pressure" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Recent Alerts */}
     {alerts.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">Alertas Recentes</h3>
          <div className="space-y-3">
            {alerts.slice(0, 5).map((alert, index) => (
              <div key={index} className="flex items-center space-x-3 p-3 bg-slate-50 rounded-lg">
                <AlertTriangle className="w-5 h-5 text-red-500" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-slate-800">
                    {alert.message || "Alerta do sistema"}
                  </p>
                  <p className="text-xs text-slate-600">
                    {new Date(alert.created_at).toLocaleString("pt-BR")}
                  </p>
                </div>
                <span
                  className={`px-2 py-1 text-xs rounded-full ${
                    alert.urgency_level === "high"
                      ? "bg-red-100 text-red-800"
                      : "bg-yellow-100 text-yellow-800"
                  }`}
                >
                  {alert.urgency_level || "Médio"}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}