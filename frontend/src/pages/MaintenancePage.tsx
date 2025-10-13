import { useState, useEffect } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { maintenanceService } from "../services/api"
import { useAuth } from "../contexts/AuthContext"

interface WorkOrder {
  id: string
  title: string
  description: string
  priority: "baixa" | "média" | "alta" | "urgente"
  status: "aberto" | "atribuido" | "em progresso" | "completo"
  assigned_team: string | null
  created_at: string
  updated_at: string
  location: string
  estimated_duration: number
}

interface Team {
  id: string
  name: string
  status: "disponivel" | "ocupado"
  members_count: number
}

interface Complaint {
  id: string
  citizen_name: string
  description: string
  location: string
  status: "aberto" | "em progresso" | "resolvido"
  created_at: string
}

export function MaintenancePage() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<"orders" | "teams" | "complaints">("orders")
  const [selectedOrder, setSelectedOrder] = useState<WorkOrder | null>(null)
  const [showCreateOrder, setShowCreateOrder] = useState(false)
  
  // Estado para o formulário de criação de ordem de serviço
  const [newOrder, setNewOrder] = useState<Partial<WorkOrder>>({
    title: "",
    description: "",
    priority: "média",
    location: "",
    estimated_duration: 1,
  })

  // Queries para buscar dados da API
  const { data: workOrdersResponse, isLoading: loadingOrders } = useQuery({
    queryKey: ['workOrders'],
    queryFn: () => maintenanceService.getWorkOrders(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  const { data: teamsResponse, isLoading: loadingTeams } = useQuery({
    queryKey: ['teams'],
    queryFn: () => maintenanceService.getTeams(),
    staleTime: 10 * 60 * 1000, // 10 minutes
  })

  const { data: complaintsResponse, isLoading: loadingComplaints } = useQuery({
    queryKey: ['complaints'],
    queryFn: () => maintenanceService.getComplaints(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  // Extrair dados das respostas da API
  const workOrders = Array.isArray(workOrdersResponse?.data) ? workOrdersResponse.data : []
  const teams = Array.isArray(teamsResponse?.data) ? teamsResponse.data : []
  const complaints = Array.isArray(complaintsResponse?.data) ? complaintsResponse.data : []

  // Mutations para criar e atualizar ordens
  const createOrderMutation = useMutation({
    mutationFn: (orderData: any) => maintenanceService.createWorkOrder(orderData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workOrders'] })
      setShowCreateOrder(false)
      setNewOrder({
        title: "",
        description: "",
        priority: "média",
        location: "",
        estimated_duration: 1,
      })
    },
    onError: (error) => {
      console.error('Erro ao criar ordem de serviço:', error)
    }
  })

  const assignTeamMutation = useMutation({
    mutationFn: ({ orderId, teamName }: { orderId: string, teamName: string }) => 
      maintenanceService.assignWorkOrder(parseInt(orderId), teamName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workOrders'] })
      setSelectedOrder(null)
    },
    onError: (error) => {
      console.error('Erro ao atribuir equipe:', error)
    }
  })
  const assignTeam = (orderId: string, teamId: string) => {
    const team = teams.find(t => t.id === teamId)
    if (team) {
      assignTeamMutation.mutate({ orderId, teamName: team.name })
    }
  }

  // Mapeamento de prioridades do português (UI) para inglês (API)
  const priorityMapping = {
    "baixa": "low",
    "média": "medium", 
    "alta": "high",
    "urgente": "critical"
  }

  const createOrder = (orderData: Partial<WorkOrder>) => {
    const orderPayload = {
      title: orderData.title || "",
      description: orderData.description || "",
      priority: priorityMapping[orderData.priority as keyof typeof priorityMapping] || "medium",
      location: orderData.location || "",
      estimated_duration: orderData.estimated_duration || 1
    }
    createOrderMutation.mutate(orderPayload)
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "low":
        return "text-green-600 bg-green-100"
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

  // Mapeamento reverso para exibição (inglês -> português)
  const priorityDisplayMapping = {
    "low": "baixa",
    "medium": "média",
    "high": "alta", 
    "critical": "urgente"
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "open":
        return "text-blue-600 bg-blue-100"
      case "assigned":
        return "text-purple-600 bg-purple-100"
      case "in_progress":
        return "text-yellow-600 bg-yellow-100"
      case "completed":
        return "text-green-600 bg-green-100"
      default:
        return "text-gray-600 bg-gray-100"
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Gestão de Manutenção</h1>
          <p className="text-gray-600">Gerencie ordens de serviço, equipes e reclamações</p>
        </div>

        <button
          onClick={() => setShowCreateOrder(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Nova Ordem de Serviço
        </button>
      </div>

      

      {/* Modal de criação de ordem de serviço */}
      {showCreateOrder && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Nova Ordem de Serviço</h3>
            <form
              className="space-y-4"
              onSubmit={e => {
                e.preventDefault()
                createOrder(newOrder)
                setNewOrder({
                  title: "",
                  description: "",
                  priority: "média",
                  location: "",
                  estimated_duration: 1,
                })
              }}
            >
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Título</label>
                <input
                  type="text"
                  className="form-input w-full border border-gray-300 rounded px-2 py-1"
                  value={newOrder.title}
                  onChange={e => setNewOrder({ ...newOrder, title: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Descrição</label>
                <textarea
                  className="form-input w-full border border-gray-300 rounded px-2 py-1"
                  value={newOrder.description}
                  onChange={e => setNewOrder({ ...newOrder, description: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Prioridade</label>
                <select
                  className="form-input w-full border border-gray-300 rounded px-2 py-1"
                  value={newOrder.priority}
                  onChange={e => setNewOrder({ ...newOrder, priority: e.target.value as WorkOrder["priority"] })}
                >
                  <option value="baixa">Baixa</option>
                  <option value="média">Média</option>
                  <option value="alta">Alta</option>
                  <option value="urgente">Urgente</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Localização</label>
                <input
                  type="text"
                  className="form-input w-full border border-gray-300 rounded px-2 py-1"
                  value={newOrder.location}
                  onChange={e => setNewOrder({ ...newOrder, location: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Duração Estimada (h)</label>
                <input
                  type="number"
                  min={1}
                  className="form-input w-full border border-gray-300 rounded px-2 py-1"
                  value={newOrder.estimated_duration}
                  onChange={e => setNewOrder({ ...newOrder, estimated_duration: Number(e.target.value) })}
                  required
                />
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowCreateOrder(false)}
                  className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={createOrderMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {createOrderMutation.isPending ? "Criando..." : "Criar Ordem"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: "orders", name: "Ordens de Serviço", icon: "" },
            { id: "teams", name: "Equipes", icon: "" },
            { id: "complaints", name: "Reclamações", icon: "" },
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

      {/* Content */}
      {activeTab === "orders" && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Ordens de Serviço</h3>
          </div>
          <div className="divide-y divide-gray-200">
            {loadingOrders ? (
              <div className="px-6 py-8 text-center text-gray-500">
                Carregando ordens de serviço...
              </div>
            ) : workOrders.length === 0 ? (
              <div className="px-6 py-8 text-center text-gray-500">
                Nenhuma ordem de serviço encontrada.
              </div>
            ) : (
              workOrders.map((order: WorkOrder) => (
                <div key={order.id} className="px-6 py-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <h4 className="text-sm font-medium text-gray-900">{order.title}</h4>
                        <span
                          className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getPriorityColor(order.priority)}`}
                        >
                          {priorityDisplayMapping[order.priority as keyof typeof priorityDisplayMapping] || order.priority}
                        </span>
                        <span
                          className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(order.status)}`}
                        >
                          {order.status}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{order.description}</p>
                      <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                        <span>📍 {order.location}</span>
                        <span>⏱️ {order.estimated_duration}h</span>
                        <span>📅 {new Date(order.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {order.status === "aberto" && (
                        <button
                          onClick={() => setSelectedOrder(order)}
                          className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                          Atribuir Equipe
                        </button>
                      )}
                      <button className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200">
                        Ver Detalhes
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {activeTab === "teams" && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {teams.map((team: Team) => (
            <div key={team.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">{team.name}</h3>
                <span
                  className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                    team.status === "disponivel" ? "text-green-600 bg-green-100" : "text-red-600 bg-red-100"
                  }`}
                >
                  {team.status}
                </span>
              </div>
              <div className="space-y-2">
                <div className="flex items-center text-sm text-gray-600">
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                    />
                  </svg>
                  {team.members_count} membros
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === "complaints" && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Reclamações dos Cidadãos</h3>
          </div>
          <div className="divide-y divide-gray-200">
            {complaints.map((complaint: Complaint) => (
              <div key={complaint.id} className="px-6 py-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <h4 className="text-sm font-medium text-gray-900">{complaint.citizen_name}</h4>
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(complaint.status)}`}
                      >
                        {complaint.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{complaint.description}</p>
                    <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                      <span>📍 {complaint.location}</span>
                      <span>📅 {new Date(complaint.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <button className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
                    Criar OS
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Assign Team Modal */}
      {selectedOrder && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Atribuir Equipe - {selectedOrder.title}</h3>
            <div className="space-y-3">
              {teams
                .filter((t: Team) => t.status === "disponivel")
                .map((team: Team) => (
                  <button
                    key={team.id}
                    onClick={() => assignTeam(selectedOrder.id, team.id)}
                    className="w-full text-left p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
                  >
                    <div className="font-medium">{team.name}</div>
                    <div className="text-sm text-gray-600">{team.members_count} membros</div>
                  </button>
                ))}
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setSelectedOrder(null)}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
