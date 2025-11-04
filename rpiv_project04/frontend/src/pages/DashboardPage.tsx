"use client"

import type React from "react"
import { useAuth } from "../contexts/AuthContext"
import { useWebSocket } from "../contexts/WebSocketContext"
import { useQuery } from "@tanstack/react-query"
import { Activity, AlertTriangle, Wrench, CreditCard, Users, Droplets } from "lucide-react"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts"
import dataService from "../services/dataService"

export const DashboardPage: React.FC = () => {
  const { user } = useAuth()
  const { sensorData, alerts, isConnected } = useWebSocket()

  // Financial data queries for financial_manager role
  const { data: bills = [] } = useQuery({
    queryKey: ["bills"],
    queryFn: () => dataService.getBills(),
    enabled: user?.role === "financial_manager",
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  const { data: disputes = [] } = useQuery({
    queryKey: ["disputes"],
    queryFn: () => dataService.getBillDisputes(),
    enabled: user?.role === "financial_manager",
    staleTime: 5 * 60 * 1000,
  })

  const { data: negotiations = [] } = useQuery({
    queryKey: ["negotiations"],
    queryFn: () => dataService.getDebtNegotiations(),
    enabled: user?.role === "financial_manager",
    staleTime: 5 * 60 * 1000,
  })

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
        // Calculate real statistics from database
        const totalBills = bills.length
        const totalDisputes = disputes.length
        const paidBills = bills.filter(bill => bill.status === "paid").length
        const overdueBills = bills.filter(bill => bill.status === "overdue").length
        const pendingBills = bills.filter(bill => bill.status === "pending").length
        
        const collectionRate = totalBills > 0 ? Math.round((paidBills / totalBills) * 100) : 0
        const defaultRate = totalBills > 0 ? Math.round((overdueBills / totalBills) * 100) : 0
        
        return [
          { title: "Faturas Emitidas", value: totalBills.toString(), icon: CreditCard, color: "bg-blue-500" },
          { title: "Contestações", value: totalDisputes.toString(), icon: AlertTriangle, color: "bg-yellow-500" },
          { title: "Taxa de Cobrança", value: `${collectionRate}%`, icon: CreditCard, color: "bg-green-500" },
          { title: "Inadimplência", value: `${defaultRate}%`, icon: AlertTriangle, color: defaultRate > 10 ? "bg-red-500" : "bg-orange-500" },
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
                <Line type="monotone" dataKey="level" stroke="#3b82f6" strokeWidth={2} />
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

      {/* Financial Charts - Only for financial_manager */}
      {user?.role === "financial_manager" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Bill Status Distribution */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h3 className="text-lg font-semibold text-slate-800 mb-4">Distribuição de Faturas</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={[
                { status: "Pagas", count: bills.filter(b => b.status === "paid").length, fill: "#10b981" },
                { status: "Pendentes", count: bills.filter(b => b.status === "pending").length, fill: "#f59e0b" },
                { status: "Vencidas", count: bills.filter(b => b.status === "overdue").length, fill: "#ef4444" },
                { status: "Contestadas", count: bills.filter(b => b.status === "contested").length, fill: "#8b5cf6" }
              ]}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="status" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Monthly Revenue Trend */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h3 className="text-lg font-semibold text-slate-800 mb-4">Valor Total por Status</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={[
                { 
                  status: "Pagas", 
                  value: bills.filter(b => b.status === "paid").reduce((sum, b) => sum + b.amount, 0),
                  fill: "#10b981"
                },
                { 
                  status: "Pendentes", 
                  value: bills.filter(b => b.status === "pending").reduce((sum, b) => sum + b.amount, 0),
                  fill: "#f59e0b"
                },
                { 
                  status: "Vencidas", 
                  value: bills.filter(b => b.status === "overdue").reduce((sum, b) => sum + b.amount, 0),
                  fill: "#ef4444"
                }
              ]}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="status" />
                <YAxis />
                <Tooltip formatter={(value) => [`R$ ${Number(value).toFixed(2)}`, 'Valor']} />
                <Bar dataKey="value" fill="#3b82f6" />
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
                    {alert.description || alert.message || "Alerta do sistema"}
                  </p>
                  <p className="text-xs text-slate-600">
                    {new Date(alert.timestamp || alert.created_at).toLocaleString("pt-BR")}
                  </p>
                </div>
                <span
                  className={`px-2 py-1 text-xs rounded-full ${
                    alert.severity === "high" || alert.urgency_level === "high"
                      ? "bg-red-100 text-red-800"
                      : "bg-yellow-100 text-yellow-800"
                  }`}
                >
                  {alert.severity || alert.urgency_level || "Médio"}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
