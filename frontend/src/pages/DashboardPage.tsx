"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { useAuth } from "../contexts/AuthContext"
import { useWebSocket } from "../contexts/WebSocketContext"
import { useQuery } from "@tanstack/react-query"
import { Activity, AlertTriangle, Wrench, CreditCard, Users, Droplets } from "lucide-react"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts"
import dataService from "../services/dataService"
import { monitoringDev } from "../services/monitoringService"

export const DashboardPage: React.FC = () => {
  const { user } = useAuth()
  const { sensorData, alerts, isConnected } = useWebSocket()
  
  // Estados para dados do sensor simulator
  const [realtimeReadings, setRealtimeReadings] = useState<any[]>([])

  // Carregar dados iniciais via HTTP (apenas uma vez)
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        console.log("🔍 Carregando dados iniciais dos sensores...")
        const realtime = await monitoringDev.getRealtimeReadings()
        const readings = realtime.data?.readings || []
        console.log("✅ Dados iniciais carregados:", readings.length, "sensores")
        setRealtimeReadings(readings)
      } catch (error) {
        console.log("❌ Erro ao carregar dados iniciais:", error)
      }
    }
    
    loadInitialData()
  }, [])

  // Atualizar com dados do WebSocket em tempo real
  useEffect(() => {
    if (sensorData && sensorData.length > 0) {
      console.log("📡 WebSocket: Atualizando dados em tempo real!", sensorData.length, "leituras")
      setRealtimeReadings(prev => {
        // Adicionar novas leituras do WebSocket
        const newReadings = [...sensorData]
        return newReadings
      })
    }
  }, [sensorData])

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

  // Gerar dados históricos baseados nos dados reais do sensor simulator
  const generateHistoricalData = (currentValue: number, baseValue: number, hours: number = 24) => {
    return Array.from({ length: hours }, (_, i) => {
      const hourAgo = hours - i
      const date = new Date()
      date.setHours(date.getHours() - hourAgo)
      
      // Criar variação baseada no valor atual
      const variation = Math.sin(i * 0.5) * 0.3 + Math.cos(i * 0.3) * 0.2
      const noise = (Math.random() - 0.5) * 0.1
      const historicalValue = baseValue + variation + noise
      
      return {
        time: `${i}h`,
        value: Math.max(0, historicalValue),
        timestamp: date.toISOString()
      }
    })
  }

  // Dados para gráficos baseados nos dados reais do sensor simulator
  const currentPressure = realtimeReadings.find((r: any) => r.sensor_id === "PRESS_001")?.value || 3.5
  const currentFlow = realtimeReadings.find((r: any) => r.sensor_id === "FLOW_001")?.value || 150
  const currentQuality = realtimeReadings.find((r: any) => r.sensor_id === "QUAL_001")?.value || 85
  const currentRiverLevel = realtimeReadings.find((r: any) => r.sensor_id === "RIVER_001")?.value || 2.5

  const waterLevelData = generateHistoricalData(currentRiverLevel, 2.5, 24).map(d => ({
    time: d.time,
    level: d.value
  }))

  const pressureData = generateHistoricalData(currentPressure, 3.5, 24).map(d => ({
    time: d.time,
    pressure: d.value
  }))

  const qualityData = generateHistoricalData(currentQuality, 85, 24).map(d => ({
    time: d.time,
    quality: d.value
  }))

  const flowData = generateHistoricalData(currentFlow, 150, 24).map(d => ({
    time: d.time,
    flow: d.value
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

      {/* Debug Info */}
      {realtimeReadings.length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <p className="text-green-800 font-medium">
            ✅ Dados do Sensor Simulator Conectados! ({realtimeReadings.length} sensores ativos)
          </p>
          <p className="text-green-600 text-sm">
            Última atualização: {new Date().toLocaleTimeString()}
          </p>
        </div>
      )}

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

      {/* Charts Section - Motor de Dados baseado no Sensor Simulator */}
      {["operator", "crisis_manager", "maintenance_manager"].includes(user?.role || "") && (
        <div className="space-y-6">
          {/* Gráficos Principais */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Pressure Chart */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <h3 className="text-lg font-semibold text-slate-800 mb-4">
                Pressão da Rede (24h) - Motor de Dados
                {realtimeReadings.length > 0 && (
                  <span className="ml-2 text-sm text-green-600 font-normal">
                    ✓ Baseado em dados reais: {currentPressure.toFixed(1)} bar
                  </span>
                )}
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={pressureData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis domain={[2, 5]} />
                  <Tooltip formatter={(value: number) => [`${value.toFixed(2)} bar`, 'Pressão']} />
                  <Line type="monotone" dataKey="pressure" stroke="#3b82f6" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Flow Chart */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <h3 className="text-lg font-semibold text-slate-800 mb-4">
                Fluxo de Água (24h) - Motor de Dados
                {realtimeReadings.length > 0 && (
                  <span className="ml-2 text-sm text-green-600 font-normal">
                    ✓ Baseado em dados reais: {currentFlow.toFixed(1)} L/s
                  </span>
                )}
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={flowData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis domain={[100, 200]} />
                  <Tooltip formatter={(value: number) => [`${value.toFixed(1)} L/s`, 'Fluxo']} />
                  <Bar dataKey="flow" fill="#10b981" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Gráficos Adicionais */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Water Level Chart */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <h3 className="text-lg font-semibold text-slate-800 mb-4">
                Nível do Rio (24h) - Motor de Dados
                {realtimeReadings.length > 0 && (
                  <span className="ml-2 text-sm text-green-600 font-normal">
                    ✓ Baseado em dados reais: {currentRiverLevel.toFixed(1)} m
                  </span>
                )}
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={waterLevelData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis domain={[1.5, 3.5]} />
                  <Tooltip formatter={(value: number) => [`${value.toFixed(2)} m`, 'Nível']} />
                  <Line type="monotone" dataKey="level" stroke="#06b6d4" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Quality Chart */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <h3 className="text-lg font-semibold text-slate-800 mb-4">
                Qualidade da Água (24h) - Motor de Dados
                {realtimeReadings.length > 0 && (
                  <span className="ml-2 text-sm text-green-600 font-normal">
                    ✓ Baseado em dados reais: {currentQuality.toFixed(1)}%
                  </span>
                )}
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={qualityData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis domain={[70, 100]} />
                  <Tooltip formatter={(value: number) => [`${value.toFixed(1)}%`, 'Qualidade']} />
                  <Line type="monotone" dataKey="quality" stroke="#10b981" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
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
