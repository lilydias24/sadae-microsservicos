"use client"

import { useState, useEffect } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "../services/api"
import { AlertTriangle, MapPin, Play, FileText, Users } from "lucide-react"

interface CriticalEvent {
  id: string
  event_type: "flood" | "drought" | "contamination" | "infrastructure_failure"
  severity: "low" | "medium" | "high" | "critical"
  location: string
  description: string
  status: "active" | "monitoring" | "resolved"
  created_at: string
  affected_population: number
}

interface Simulation {
  id: string
  scenario_type: "drought" | "flood" | "contamination"
  parameters: any
  status: "running" | "completed" | "failed"
  results?: any
  created_at: string
}

interface MitigationPlan {
  id: string
  simulation_id: string
  title: string
  actions: string[]
  estimated_cost: number
  implementation_time: number
  created_at: string
}

export function CrisisPage() {
  const [activeTab, setActiveTab] = useState<"events" | "simulations" | "plans">("events")
  const [showSimulationForm, setShowSimulationForm] = useState(false)
  const [simulationParams, setSimulationParams] = useState({
    scenario_type: "drought",
    duration: 30,
    severity: "medium",
    affected_areas: "",
  })

  const queryClient = useQueryClient()

  // Fetch critical events
  const { data: events, isLoading: eventsLoading } = useQuery({
    queryKey: ["critical-events"],
    queryFn: () => api.get("/crisis/events"),
    refetchInterval: 30000,
  })

  // Fetch simulations
  const { data: simulations, isLoading: simulationsLoading } = useQuery({
    queryKey: ["simulations"],
    queryFn: () => api.get("/crisis/simulations"),
  })

  // Fetch mitigation plans
  const { data: plans, isLoading: plansLoading } = useQuery({
    queryKey: ["mitigation-plans"],
    queryFn: () => api.get("/crisis/mitigation-plans"),
  })

  // Create simulation mutation
  const createSimulationMutation = useMutation({
    mutationFn: (params: any) => api.post("/crisis/simulations", params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["simulations"] })
      setShowSimulationForm(false)
      setSimulationParams({
        scenario_type: "drought",
        duration: 30,
        severity: "medium",
        affected_areas: "",
      })
    },
  })

  // Send alert to civil defense
  const sendAlertMutation = useMutation({
    mutationFn: (eventId: string) => api.post(`/crisis/events/${eventId}/alert`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["critical-events"] })
    },
  })

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "low":
        return "text-blue-600 bg-blue-100"
      case "medium":
        return "text-yellow-600 bg-yellow-100"
      case "high":
        return "text-orange-600 bg-orange-100"
      case "critical":
        return "text-red-600 bg-red-100"
      default:
        return "text-gray-600 bg-gray-100"
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "text-red-600 bg-red-100"
      case "monitoring":
        return "text-yellow-600 bg-yellow-100"
      case "resolved":
        return "text-green-600 bg-green-100"
      case "running":
        return "text-blue-600 bg-blue-100"
      case "completed":
        return "text-green-600 bg-green-100"
      case "failed":
        return "text-red-600 bg-red-100"
      default:
        return "text-gray-600 bg-gray-100"
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
    }).format(amount)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Gestão de Crises</h1>
          <p className="text-gray-600">Monitore eventos críticos e simule cenários de emergência</p>
        </div>

        <button
          onClick={() => setShowSimulationForm(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <Play className="w-4 h-4 inline mr-2" />
          Nova Simulação
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-red-100 rounded-lg">
              <AlertTriangle className="w-6 h-6 text-red-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Eventos Ativos</p>
              <p className="text-2xl font-bold text-gray-900">
                {events?.data?.filter((e: CriticalEvent) => e.status === "active").length || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Play className="w-6 h-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Simulações</p>
              <p className="text-2xl font-bold text-gray-900">{simulations?.data?.length || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <FileText className="w-6 h-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Planos de Mitigação</p>
              <p className="text-2xl font-bold text-gray-900">{plans?.data?.length || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Users className="w-6 h-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">População Monitorada</p>
              <p className="text-2xl font-bold text-gray-900">
                {events?.data?.reduce((acc: number, e: CriticalEvent) => acc + (e.affected_population || 0), 0) || 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: "events", name: "Eventos Críticos", icon: "🚨" },
            { id: "simulations", name: "Simulações", icon: "🔬" },
            { id: "plans", name: "Planos de Mitigação", icon: "📋" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              {tab.icon} {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Events Content */}
      {activeTab === "events" && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Eventos Críticos</h3>
          </div>
          <div className="divide-y divide-gray-200">
            {events?.data?.map((event: CriticalEvent) => (
              <div key={event.id} className="px-6 py-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <h4 className="text-sm font-medium text-gray-900">
                        {event.event_type.replace("_", " ").toUpperCase()}
                      </h4>
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getSeverityColor(event.severity)}`}
                      >
                        {event.severity}
                      </span>
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(event.status)}`}
                      >
                        {event.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{event.description}</p>
                    <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                      <span>
                        <MapPin className="w-3 h-3 inline mr-1" />
                        {event.location}
                      </span>
                      <span>
                        <Users className="w-3 h-3 inline mr-1" />
                        {event.affected_population} pessoas afetadas
                      </span>
                      <span>📅 {new Date(event.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {event.status === "active" && (
                      <button
                        onClick={() => sendAlertMutation.mutate(event.id)}
                        className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
                      >
                        Alertar Defesa Civil
                      </button>
                    )}
                    <button className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200">
                      Ver Detalhes
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Simulations Content */}
      {activeTab === "simulations" && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Simulações de Cenários</h3>
          </div>
          <div className="divide-y divide-gray-200">
            {simulations?.data?.map((simulation: Simulation) => (
              <div key={simulation.id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <h4 className="text-sm font-medium text-gray-900">
                        Simulação de {simulation.scenario_type.toUpperCase()}
                      </h4>
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(simulation.status)}`}
                      >
                        {simulation.status}
                      </span>
                    </div>
                    <div className="mt-1 text-xs text-gray-500">
                      📅 {new Date(simulation.created_at).toLocaleDateString()}
                    </div>
                    {simulation.results && (
                      <div className="mt-2 text-sm text-gray-600">
                        <strong>Resultados:</strong> {JSON.stringify(simulation.results).substring(0, 100)}...
                      </div>
                    )}
                  </div>
                  <div className="flex items-center space-x-2">
                    {simulation.status === "completed" && (
                      <button className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700">
                        Criar Plano
                      </button>
                    )}
                    <button className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200">
                      Ver Resultados
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Plans Content */}
      {activeTab === "plans" && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Planos de Mitigação</h3>
          </div>
          <div className="divide-y divide-gray-200">
            {plans?.data?.map((plan: MitigationPlan) => (
              <div key={plan.id} className="px-6 py-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="text-sm font-medium text-gray-900">{plan.title}</h4>
                    <div className="mt-2 space-y-1">
                      {plan.actions.slice(0, 3).map((action, index) => (
                        <div key={index} className="text-sm text-gray-600">
                          • {action}
                        </div>
                      ))}
                      {plan.actions.length > 3 && (
                        <div className="text-sm text-gray-500">+{plan.actions.length - 3} ações adicionais</div>
                      )}
                    </div>
                    <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                      <span>💰 {formatCurrency(plan.estimated_cost)}</span>
                      <span>⏱️ {plan.implementation_time} dias</span>
                      <span>📅 {new Date(plan.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <button className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
                    Implementar
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Simulation Form Modal */}
      {showSimulationForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Nova Simulação de Cenário</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Tipo de Cenário</label>
                <select
                  value={simulationParams.scenario_type}
                  onChange={(e) => setSimulationParams((prev) => ({ ...prev, scenario_type: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="drought">Seca</option>
                  <option value="flood">Enchente</option>
                  <option value="contamination">Contaminação</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Duração (dias)</label>
                <input
                  type="number"
                  value={simulationParams.duration}
                  onChange={(e) =>
                    setSimulationParams((prev) => ({ ...prev, duration: Number.parseInt(e.target.value) }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Severidade</label>
                <select
                  value={simulationParams.severity}
                  onChange={(e) => setSimulationParams((prev) => ({ ...prev, severity: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="low">Baixa</option>
                  <option value="medium">Média</option>
                  <option value="high">Alta</option>
                  <option value="critical">Crítica</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Áreas Afetadas</label>
                <textarea
                  value={simulationParams.affected_areas}
                  onChange={(e) => setSimulationParams((prev) => ({ ...prev, affected_areas: e.target.value }))}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Descreva as áreas que serão afetadas..."
                />
              </div>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowSimulationForm(false)}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                onClick={() => createSimulationMutation.mutate(simulationParams)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Iniciar Simulação
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
