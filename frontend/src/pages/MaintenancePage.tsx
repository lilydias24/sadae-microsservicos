import { useState, useEffect } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"
import { maintenanceDev } from "../services/maintenanceService"
import { useAuth } from "../contexts/AuthContext"

interface WorkOrder {
  id: string
  title: string
  description: string
  priority: "low" | "medium" | "high" | "critical"
  status: "open" | "assigned" | "in_progress" | "completed"
  assigned_team: string | null
  created_at: string
  updated_at: string
  location: string
  estimated_duration: number
}

interface TeamMember { id: number; name: string; role?: string; contact?: string; is_active: boolean }
interface Team {
  id: string
  name: string
  status: "available" | "busy"
  members_count: number
  is_active?: boolean
  max_concurrent_orders?: number
  members?: TeamMember[]
}

interface Complaint {
  id: string
  citizen_name: string
  description: string
  location: string
  status: "open" | "in_progress" | "resolved"
  created_at: string
}

export function MaintenancePage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<"orders" | "teams" | "complaints" | "chat">("orders")
  const [selectedOrder, setSelectedOrder] = useState<WorkOrder | null>(null)
  const [showCreateOrder, setShowCreateOrder] = useState(false)
  const [showCreateTeam, setShowCreateTeam] = useState(false)
  const [editingTeam, setEditingTeam] = useState<Team | null>(null)
  const [teamForm, setTeamForm] = useState<any>({
    name: "",
    description: "",
    specialization: "",
    members_count: 0,
    max_concurrent_orders: 5,
    supervisor_name: "",
    supervisor_contact: "",
    work_areas_csv: "",
    equipment_csv: "",
  })
  const [newMember, setNewMember] = useState<Partial<TeamMember>>({ name: "", role: "", contact: "" })
  const [orderDetail, setOrderDetail] = useState<any | null>(null)
  const [showOrderDetail, setShowOrderDetail] = useState(false)
  const [orderProgress, setOrderProgress] = useState<any[]>([])
  const [newProgress, setNewProgress] = useState<{status: WorkOrder["status"], progress_notes: string, estimated_completion?: string}>({ status: "in_progress", progress_notes: "" })
  
  // Estados para tags dinâmicas
  const [workAreaTags, setWorkAreaTags] = useState<string[]>([])
  const [equipmentTags, setEquipmentTags] = useState<string[]>([])
  const [workAreaInput, setWorkAreaInput] = useState("")
  const [equipmentInput, setEquipmentInput] = useState("")

  // Especializações pré-definidas
  const SPECIALIZATIONS = [
    { value: "Hidráulica", icon: "🚰", label: "Hidráulica" },
    { value: "Elétrica", icon: "⚡", label: "Elétrica" },
    { value: "Civil", icon: "🏗️", label: "Civil / Estrutural" },
    { value: "Paisagismo", icon: "🌳", label: "Paisagismo" },
    { value: "Limpeza", icon: "🧹", label: "Limpeza Urbana" },
    { value: "Sinalização", icon: "🚦", label: "Sinalização" },
    { value: "Geral", icon: "🔧", label: "Manutenção Geral" },
  ]

  // Sugestões de áreas de trabalho
  const WORK_AREAS_SUGGESTIONS = [
    "Centro", "Zona Norte", "Zona Sul", "Zona Leste", "Zona Oeste",
    "Industrial", "Residencial", "Comercial", "Rural"
  ]

  // Sugestões de equipamentos
  const EQUIPMENT_SUGGESTIONS = [
    "Caminhão", "Escavadeira", "Retroescavadeira", "Betoneira",
    "Ferramentas Elétricas", "Ferramentas Hidráulicas", "EPI Completo",
    "Guincho", "Compressor", "Gerador", "Solda Elétrica"
  ]

  // Função para resetar o formulário de equipe
  const resetTeamForm = () => {
    setShowCreateTeam(false)
    setTeamForm({
      name: "",
      description: "",
      specialization: "",
      members_count: 0,
      max_concurrent_orders: 5,
      supervisor_name: "",
      supervisor_contact: "",
      work_areas_csv: "",
      equipment_csv: "",
    })
    setWorkAreaTags([])
    setEquipmentTags([])
    setWorkAreaInput("")
    setEquipmentInput("")
  }
  
  // Estado para o formulário de criação de ordem de serviço
  const [newOrder, setNewOrder] = useState<Partial<WorkOrder>>({
    title: "",
    description: "",
    priority: "medium",
    location: "",
    estimated_duration: 1,
  })

  // Queries para buscar dados da API
  const { data: workOrdersResponse, isLoading: loadingOrders } = useQuery({
    queryKey: ['workOrders'],
    queryFn: () => maintenanceDev.getWorkOrders(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  const { data: teamsResponse, isLoading: loadingTeams } = useQuery({
    queryKey: ['teams'],
    queryFn: () => maintenanceDev.getTeams(),
    staleTime: 10 * 60 * 1000, // 10 minutes
  })

  const { data: complaintsResponse, isLoading: loadingComplaints } = useQuery({
    queryKey: ['complaints'],
    queryFn: () => maintenanceDev.getComplaints(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  // Extrair dados das respostas da API
  const workOrders = workOrdersResponse && Array.isArray(workOrdersResponse.data) ? workOrdersResponse.data : []
  const teams = teamsResponse && Array.isArray(teamsResponse.data) ? teamsResponse.data : []
  const complaints = complaintsResponse && Array.isArray(complaintsResponse.data) ? complaintsResponse.data : []

  // Mutations para criar e atualizar ordens
  const createOrderMutation = useMutation({
    mutationFn: (orderData: any) => maintenanceDev.createWorkOrder(orderData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workOrders'] })
      setShowCreateOrder(false)
      setNewOrder({
        title: "",
        description: "",
        priority: "medium",
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
      maintenanceDev.assignWorkOrder(parseInt(orderId), teamName),
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

  const createTeamMutation = useMutation({
    mutationFn: (data: any) => maintenanceDev.createTeam(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams'] })
      resetTeamForm()
    }
  })

  const updateTeamMutation = useMutation({
    mutationFn: ({ id, data }: { id: number, data: any }) => maintenanceDev.updateTeam(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams'] })
      setEditingTeam(null)
    }
  })

  const addMemberMutation = useMutation({
    mutationFn: ({ teamId, data }: { teamId: number, data: any }) => maintenanceDev.addTeamMember(teamId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams'] })
      setNewMember({ name: "", role: "", contact: "" })
    }
  })

  const openOrderDetail = async (order: WorkOrder) => {
    try {
      const res = await maintenanceDev.getWorkOrder(parseInt(order.id))
      setOrderDetail(res.data)
      const prog = await maintenanceDev.getOrderProgress(parseInt(order.id))
      setOrderProgress(Array.isArray(prog.data) ? prog.data : [])
      setShowOrderDetail(true)
    } catch (e) {
      console.error(e)
    }
  }

  // Mapeamento de status e prioridades para exibição
  const statusDisplayMapping = {
    "open": "aberto",
    "assigned": "atribuido", 
    "in_progress": "em progresso",
    "completed": "completo"
  }

  // Mapeamento de prioridades para exibição
  const priorityDisplayMapping = {
    "low": "baixa",
    "medium": "média",
    "high": "alta", 
    "critical": "urgente"
  }

  const createOrder = (orderData: Partial<WorkOrder>) => {
    const orderPayload = {
      title: orderData.title || "",
      description: orderData.description || "",
      priority: orderData.priority || "medium",
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

      

      {/* Modal de criação de ordem de serviço - MELHORADO */}
      {showCreateOrder && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="sticky top-0 bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4 rounded-t-xl">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-white flex items-center">
                  <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  Nova Ordem de Serviço
                </h3>
                <button onClick={() => setShowCreateOrder(false)} className="text-white hover:text-gray-200">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <p className="text-blue-100 text-sm mt-1">Preencha os dados para criar uma nova ordem de manutenção</p>
            </div>

            {/* Body */}
            <form
              className="p-6"
              onSubmit={e => {
                e.preventDefault()
                createOrder(newOrder)
              }}
            >
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Título */}
                <div className="md:col-span-2">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Título da Ordem <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                    placeholder="Ex: Reparo de vazamento na Rua Principal"
                    value={newOrder.title}
                    onChange={e => setNewOrder({ ...newOrder, title: e.target.value })}
                    required
                  />
                </div>

                {/* Descrição */}
                <div className="md:col-span-2">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Descrição Detalhada <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition resize-none"
                    rows={4}
                    placeholder="Descreva detalhadamente o problema ou serviço necessário..."
                    value={newOrder.description}
                    onChange={e => setNewOrder({ ...newOrder, description: e.target.value })}
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    {newOrder.description?.length || 0} caracteres
                  </p>
                </div>

                {/* Prioridade */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Nível de Prioridade <span className="text-red-500">*</span>
                  </label>
                  <select
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                    value={newOrder.priority}
                    onChange={e => setNewOrder({ ...newOrder, priority: e.target.value as WorkOrder["priority"] })}
                  >
                    <option value="low">🟢 Baixa - Pode aguardar</option>
                    <option value="medium">🟡 Média - Atenção necessária</option>
                    <option value="high">🟠 Alta - Resolver logo</option>
                    <option value="critical">🔴 Crítica - Urgente!</option>
                  </select>
                </div>

                {/* Duração Estimada */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Duração Estimada <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type="number"
                      min={0.5}
                      step={0.5}
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                      placeholder="Ex: 2"
                      value={newOrder.estimated_duration}
                      onChange={e => setNewOrder({ ...newOrder, estimated_duration: Number(e.target.value) })}
                      required
                    />
                    <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 text-sm">horas</span>
                  </div>
                </div>

                {/* Localização */}
                <div className="md:col-span-2">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Localização <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <svg className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    <input
                      type="text"
                      className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                      placeholder="Ex: Rua das Flores, 123 - Centro"
                      value={newOrder.location}
                      onChange={e => setNewOrder({ ...newOrder, location: e.target.value })}
                      required
                    />
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-200">
                <p className="text-sm text-gray-500">
                  <span className="text-red-500">*</span> Campos obrigatórios
                </p>
                <div className="flex space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowCreateOrder(false)}
                    className="px-6 py-2.5 text-gray-700 bg-white border-2 border-gray-300 rounded-lg hover:bg-gray-50 font-medium transition"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    disabled={createOrderMutation.isPending}
                    className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 disabled:cursor-not-allowed font-medium shadow-lg shadow-blue-500/50 transition"
                  >
                    {createOrderMutation.isPending ? (
                      <span className="flex items-center">
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Criando...
                      </span>
                    ) : (
                      <span className="flex items-center">
                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                        Criar Ordem
                      </span>
                    )}
                  </button>
                </div>
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
            { id: "chat", name: "Chat", icon: "🛠️" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => {
                if (tab.id === "chat") {
                  navigate("/maintenance-chat")
                } else {
                  setActiveTab(tab.id as any)
                }
              }}
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
                          {statusDisplayMapping[order.status as keyof typeof statusDisplayMapping] || order.status}
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
                      {order.status === "open" && (
                        <button
                          onClick={() => setSelectedOrder(order)}
                          className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                          Atribuir Equipe
                        </button>
                      )}
                      <button onClick={() => openOrderDetail(order)} className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200">Ver Detalhes</button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {activeTab === "teams" && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button onClick={() => setShowCreateTeam(true)} className="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Nova Equipe</button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {teams.map((team: Team) => (
            <div key={team.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">{team.name}</h3>
                <span
                  className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                    team.status === "available" ? "text-green-600 bg-green-100" : "text-red-600 bg-red-100"
                  }`}
                >
                  {team.status === "available" ? "Disponível" : "Ocupado"}
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
                <div className="pt-2">
                  <button onClick={() => { setEditingTeam(team); setTeamForm({ name: team.name, description: '', specialization: '', max_concurrent_orders: team.max_concurrent_orders || 5, supervisor_name: '', supervisor_contact: '', work_areas_csv: '', equipment_csv: '', members_count: team.members_count || 0 }) }} className="text-sm px-3 py-1 border rounded">Editar</button>
                </div>
              </div>
            </div>
          ))}
          </div>
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
                .filter((t: Team) => t.status === "available")
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

      {/* Create Team Modal - MELHORADO */}
      {showCreateTeam && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="sticky top-0 bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4 rounded-t-xl">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-white flex items-center">
                  <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                  Nova Equipe de Manutenção
                </h3>
                <button onClick={resetTeamForm} className="text-white hover:text-gray-200">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <p className="text-blue-100 text-sm mt-1">Configure os dados da nova equipe de manutenção</p>
            </div>

            {/* Body */}
            <form onSubmit={(e) => {
              e.preventDefault();
              const payload = {
                name: teamForm.name,
                description: teamForm.description || undefined,
                specialization: teamForm.specialization || undefined,
                members_count: Number(teamForm.members_count) || 0,
                max_concurrent_orders: Number(teamForm.max_concurrent_orders) || 5,
                supervisor_name: teamForm.supervisor_name || undefined,
                supervisor_contact: teamForm.supervisor_contact || undefined,
                work_areas: workAreaTags.length > 0 ? workAreaTags : [],
                equipment: equipmentTags.length > 0 ? equipmentTags : [],
              };
              createTeamMutation.mutate(payload)
            }} className="p-6">
              
              {/* Informações Básicas */}
              <div className="mb-6">
                <h4 className="text-sm font-bold text-gray-700 mb-4 pb-2 border-b flex items-center">
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Informações Básicas
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="md:col-span-2">
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Nome da Equipe <span className="text-red-500">*</span>
                    </label>
                    <input 
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition" 
                      placeholder="Ex: Equipe de Hidráulica Norte" 
                      value={teamForm.name} 
                      onChange={e => setTeamForm({ ...teamForm, name: e.target.value })} 
                      required 
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Descrição</label>
                    <textarea 
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition resize-none" 
                      rows={3}
                      placeholder="Descreva as responsabilidades e características da equipe..." 
                      value={teamForm.description} 
                      onChange={e => setTeamForm({ ...teamForm, description: e.target.value })} 
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Especialização</label>
                    <select 
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition" 
                      value={teamForm.specialization} 
                      onChange={e => setTeamForm({ ...teamForm, specialization: e.target.value })}
                    >
                      <option value="">Selecione uma especialização</option>
                      <option value="Hidráulica">🚰 Hidráulica</option>
                      <option value="Elétrica">⚡ Elétrica</option>
                      <option value="Civil">🏗️ Civil / Estrutural</option>
                      <option value="Paisagismo">🌳 Paisagismo</option>
                      <option value="Limpeza">🧹 Limpeza Urbana</option>
                      <option value="Sinalização">🚦 Sinalização</option>
                      <option value="Geral">🔧 Manutenção Geral</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Capacidade e Recursos */}
              <div className="mb-6">
                <h4 className="text-sm font-bold text-gray-700 mb-4 pb-2 border-b flex items-center">
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  Capacidade e Recursos
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Número de Membros</label>
                    <input 
                      type="number" 
                      min={0} 
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition" 
                      placeholder="Ex: 5" 
                      value={teamForm.members_count} 
                      onChange={e => setTeamForm({ ...teamForm, members_count: Number(e.target.value) })} 
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Capacidade de Ordens Simultâneas <span className="text-red-500">*</span>
                    </label>
                    <input 
                      type="number" 
                      min={1} 
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition" 
                      placeholder="Ex: 3" 
                      value={teamForm.max_concurrent_orders} 
                      onChange={e => setTeamForm({ ...teamForm, max_concurrent_orders: Number(e.target.value) })} 
                      required
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Áreas de Atuação
                      <span className="ml-2 text-xs font-normal text-gray-500">(Clique nas sugestões ou digite e pressione Enter)</span>
                    </label>
                    
                    {/* Input com botão */}
                    <div className="flex gap-2 mb-3">
                      <input 
                        type="text"
                        className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition" 
                        placeholder="Digite uma área..." 
                        value={workAreaInput}
                        onChange={e => setWorkAreaInput(e.target.value)}
                        onKeyPress={e => {
                          if (e.key === 'Enter') {
                            e.preventDefault()
                            if (workAreaInput.trim() && !workAreaTags.includes(workAreaInput.trim())) {
                              setWorkAreaTags([...workAreaTags, workAreaInput.trim()])
                              setWorkAreaInput("")
                            }
                          }
                        }}
                      />
                      <button
                        type="button"
                        onClick={() => {
                          if (workAreaInput.trim() && !workAreaTags.includes(workAreaInput.trim())) {
                            setWorkAreaTags([...workAreaTags, workAreaInput.trim()])
                            setWorkAreaInput("")
                          }
                        }}
                        className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition font-medium"
                      >
                        + Adicionar
                      </button>
                    </div>

                    {/* Sugestões */}
                    <div className="flex flex-wrap gap-2 mb-3">
                      {WORK_AREAS_SUGGESTIONS.map(area => (
                        <button
                          key={area}
                          type="button"
                          onClick={() => {
                            if (!workAreaTags.includes(area)) {
                              setWorkAreaTags([...workAreaTags, area])
                            }
                          }}
                          disabled={workAreaTags.includes(area)}
                          className={`px-3 py-1 text-xs rounded-full transition ${
                            workAreaTags.includes(area)
                              ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                              : 'bg-blue-50 text-blue-600 hover:bg-blue-100'
                          }`}
                        >
                          + {area}
                        </button>
                      ))}
                    </div>

                    {/* Tags adicionadas */}
                    {workAreaTags.length > 0 && (
                      <div className="flex flex-wrap gap-2 p-3 bg-gray-50 rounded-lg border border-gray-200">
                        {workAreaTags.map(tag => (
                          <span
                            key={tag}
                            className="inline-flex items-center gap-1 px-3 py-1.5 bg-blue-100 text-blue-700 rounded-full text-sm font-medium"
                          >
                            📍 {tag}
                            <button
                              type="button"
                              onClick={() => setWorkAreaTags(workAreaTags.filter(t => t !== tag))}
                              className="ml-1 hover:text-blue-900 font-bold"
                            >
                              ×
                            </button>
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Equipamentos Disponíveis
                      <span className="ml-2 text-xs font-normal text-gray-500">(Clique nas sugestões ou digite e pressione Enter)</span>
                    </label>
                    
                    {/* Input com botão */}
                    <div className="flex gap-2 mb-3">
                      <input 
                        type="text"
                        className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition" 
                        placeholder="Digite um equipamento..." 
                        value={equipmentInput}
                        onChange={e => setEquipmentInput(e.target.value)}
                        onKeyPress={e => {
                          if (e.key === 'Enter') {
                            e.preventDefault()
                            if (equipmentInput.trim() && !equipmentTags.includes(equipmentInput.trim())) {
                              setEquipmentTags([...equipmentTags, equipmentInput.trim()])
                              setEquipmentInput("")
                            }
                          }
                        }}
                      />
                      <button
                        type="button"
                        onClick={() => {
                          if (equipmentInput.trim() && !equipmentTags.includes(equipmentInput.trim())) {
                            setEquipmentTags([...equipmentTags, equipmentInput.trim()])
                            setEquipmentInput("")
                          }
                        }}
                        className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition font-medium"
                      >
                        + Adicionar
                      </button>
                    </div>

                    {/* Sugestões */}
                    <div className="flex flex-wrap gap-2 mb-3">
                      {EQUIPMENT_SUGGESTIONS.map(equip => (
                        <button
                          key={equip}
                          type="button"
                          onClick={() => {
                            if (!equipmentTags.includes(equip)) {
                              setEquipmentTags([...equipmentTags, equip])
                            }
                          }}
                          disabled={equipmentTags.includes(equip)}
                          className={`px-3 py-1 text-xs rounded-full transition ${
                            equipmentTags.includes(equip)
                              ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                              : 'bg-green-50 text-green-600 hover:bg-green-100'
                          }`}
                        >
                          + {equip}
                        </button>
                      ))}
                    </div>

                    {/* Tags adicionadas */}
                    {equipmentTags.length > 0 && (
                      <div className="flex flex-wrap gap-2 p-3 bg-gray-50 rounded-lg border border-gray-200">
                        {equipmentTags.map(tag => (
                          <span
                            key={tag}
                            className="inline-flex items-center gap-1 px-3 py-1.5 bg-green-100 text-green-700 rounded-full text-sm font-medium"
                          >
                            🔧 {tag}
                            <button
                              type="button"
                              onClick={() => setEquipmentTags(equipmentTags.filter(t => t !== tag))}
                              className="ml-1 hover:text-green-900 font-bold"
                            >
                              ×
                            </button>
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Supervisor */}
              <div className="mb-6">
                <h4 className="text-sm font-bold text-gray-700 mb-4 pb-2 border-b flex items-center">
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  Informações do Supervisor
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Nome do Supervisor</label>
                    <input 
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition" 
                      placeholder="Ex: João Silva" 
                      value={teamForm.supervisor_name} 
                      onChange={e => setTeamForm({ ...teamForm, supervisor_name: e.target.value })} 
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Contato do Supervisor</label>
                    <input 
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition" 
                      placeholder="Ex: (11) 98765-4321" 
                      value={teamForm.supervisor_contact} 
                      onChange={e => setTeamForm({ ...teamForm, supervisor_contact: e.target.value })} 
                    />
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between pt-6 border-t border-gray-200">
                <p className="text-sm text-gray-500">
                  <span className="text-red-500">*</span> Campos obrigatórios
                </p>
                <div className="flex space-x-3">
                  <button 
                    type="button" 
                    onClick={resetTeamForm} 
                    className="px-6 py-2.5 text-gray-700 bg-white border-2 border-gray-300 rounded-lg hover:bg-gray-50 font-medium transition"
                  >
                    Cancelar
                  </button>
                  <button 
                    type="submit" 
                    disabled={createTeamMutation.isPending} 
                    className="px-6 py-2.5 bg-gradient-to-r from-green-600 to-green-700 text-white rounded-lg hover:from-green-700 hover:to-green-800 disabled:opacity-50 disabled:cursor-not-allowed font-medium shadow-lg shadow-green-500/50 transition"
                  >
                    {createTeamMutation.isPending ? (
                      <span className="flex items-center">
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Criando...
                      </span>
                    ) : (
                      <span className="flex items-center">
                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                        Criar Equipe
                      </span>
                    )}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Team & Members Modal - MELHORADO */}
      {editingTeam && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="sticky top-0 bg-gradient-to-r from-amber-600 to-amber-700 px-6 py-4 rounded-t-xl">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-white flex items-center">
                  <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  Editar Equipe - {editingTeam.name}
                </h3>
                <button onClick={() => setEditingTeam(null)} className="text-white hover:text-gray-200 transition">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <p className="text-amber-100 text-sm mt-1">Atualize as informações e gerencie os membros da equipe</p>
            </div>

            {/* Body */}
            <div className="p-6 space-y-6">
              {/* Informações da Equipe */}
              <div>
                <h4 className="text-sm font-bold text-gray-700 mb-4 pb-2 border-b flex items-center">
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Informações da Equipe
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Nome da Equipe</label>
                    <input 
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent transition" 
                      value={teamForm.name} 
                      onChange={e => setTeamForm({ ...teamForm, name: e.target.value })} 
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Capacidade de Ordens</label>
                    <input 
                      type="number" 
                      min={1} 
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent transition" 
                      value={teamForm.max_concurrent_orders} 
                      onChange={e => setTeamForm({ ...teamForm, max_concurrent_orders: Number(e.target.value) })} 
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Especialização</label>
                    <select 
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent transition" 
                      value={teamForm.specialization || ''} 
                      onChange={e => setTeamForm({ ...teamForm, specialization: e.target.value })}
                    >
                      <option value="">Selecione uma especialização</option>
                      <option value="Hidráulica">🚰 Hidráulica</option>
                      <option value="Elétrica">⚡ Elétrica</option>
                      <option value="Civil">🏗️ Civil / Estrutural</option>
                      <option value="Paisagismo">🌳 Paisagismo</option>
                      <option value="Limpeza">🧹 Limpeza Urbana</option>
                      <option value="Sinalização">🚦 Sinalização</option>
                      <option value="Geral">🔧 Manutenção Geral</option>
                    </select>
                  </div>
                  <div className="md:col-span-2 flex items-center p-4 bg-gray-50 rounded-lg">
                    <input 
                      type="checkbox" 
                      id="teamActive"
                      checked={teamForm.is_active} 
                      onChange={e => setTeamForm({ ...teamForm, is_active: e.target.checked })} 
                      className="w-5 h-5 text-amber-600 border-gray-300 rounded focus:ring-2 focus:ring-amber-500"
                    />
                    <label htmlFor="teamActive" className="ml-3 text-sm font-medium text-gray-700 cursor-pointer">
                      Equipe Ativa {teamForm.is_active ? '✅' : '❌'}
                    </label>
                  </div>
                </div>
              </div>

              {/* Membros da Equipe */}
              <div>
                <h4 className="text-sm font-bold text-gray-700 mb-4 pb-2 border-b flex items-center">
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                  Membros da Equipe ({(editingTeam.members || []).length})
                </h4>
                
                {/* Lista de membros */}
                <div className="space-y-2 max-h-64 overflow-auto mb-4 p-2 bg-gray-50 rounded-lg">
                  {(editingTeam.members || []).length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <svg className="w-12 h-12 mx-auto mb-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                      </svg>
                      <p className="text-sm">Nenhum membro cadastrado</p>
                      <p className="text-xs text-gray-400 mt-1">Adicione membros usando o formulário abaixo</p>
                    </div>
                  ) : (
                    (editingTeam.members || []).map(m => (
                      <div key={m.id} className="flex items-center justify-between bg-white border border-gray-200 rounded-lg px-4 py-3 hover:border-amber-300 transition">
                        <div className="flex items-center space-x-3">
                          <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-amber-600 rounded-full flex items-center justify-center text-white font-bold">
                            {m.name.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <div className="font-semibold text-gray-900">{m.name}</div>
                            <div className="text-sm text-gray-600">{m.role || 'Sem função definida'}</div>
                          </div>
                        </div>
                        <button 
                          onClick={() => maintenanceDev.deleteTeamMember(parseInt(editingTeam.id), m.id).then(() => queryClient.invalidateQueries({ queryKey: ['teams'] }))} 
                          className="px-3 py-1.5 text-red-600 hover:bg-red-50 rounded-lg font-medium transition flex items-center"
                        >
                          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                          Remover
                        </button>
                      </div>
                    ))
                  )}
                </div>

                {/* Form para adicionar membro */}
                <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4">
                  <h5 className="text-sm font-bold text-green-800 mb-3 flex items-center">
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    Adicionar Novo Membro
                  </h5>
                  <form onSubmit={(e) => { e.preventDefault(); if (editingTeam) addMemberMutation.mutate({ teamId: parseInt(editingTeam.id), data: newMember }) }} className="flex flex-col md:flex-row gap-3">
                    <div className="flex-1">
                      <input 
                        className="w-full px-4 py-2.5 border border-green-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition" 
                        placeholder="Nome completo do membro" 
                        value={newMember.name || ''} 
                        onChange={e => setNewMember({ ...newMember, name: e.target.value })} 
                        required 
                      />
                    </div>
                    <div className="md:w-48">
                      <input 
                        className="w-full px-4 py-2.5 border border-green-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition" 
                        placeholder="Função / Cargo" 
                        value={newMember.role || ''} 
                        onChange={e => setNewMember({ ...newMember, role: e.target.value })} 
                      />
                    </div>
                    <button 
                      type="submit" 
                      disabled={addMemberMutation.isPending}
                      className="px-6 py-2.5 bg-gradient-to-r from-green-600 to-green-700 text-white rounded-lg hover:from-green-700 hover:to-green-800 disabled:opacity-50 font-medium shadow-lg shadow-green-500/50 transition flex items-center justify-center"
                    >
                      {addMemberMutation.isPending ? (
                        <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                      ) : (
                        <>
                          <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                          </svg>
                          Adicionar
                        </>
                      )}
                    </button>
                  </form>
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-end pt-4 border-t border-gray-200 gap-3">
                <button 
                  type="button" 
                  onClick={() => setEditingTeam(null)} 
                  className="px-6 py-2.5 text-gray-700 bg-white border-2 border-gray-300 rounded-lg hover:bg-gray-50 font-medium transition"
                >
                  Fechar
                </button>
                <button 
                  onClick={() => updateTeamMutation.mutate({ id: parseInt(editingTeam.id), data: teamForm })} 
                  disabled={updateTeamMutation.isPending}
                  className="px-6 py-2.5 bg-gradient-to-r from-amber-600 to-amber-700 text-white rounded-lg hover:from-amber-700 hover:to-amber-800 disabled:opacity-50 disabled:cursor-not-allowed font-medium shadow-lg shadow-amber-500/50 transition flex items-center"
                >
                  {updateTeamMutation.isPending ? (
                    <span className="flex items-center">
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Salvando...
                    </span>
                  ) : (
                    <span className="flex items-center">
                      <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      Salvar Alterações
                    </span>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Order Detail Modal */}
      {showOrderDetail && orderDetail && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-lg w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900">Detalhes da OS - {orderDetail.title}</h3>
            <div className="mt-3 text-sm space-y-1">
              <div><b>Protocolo:</b> {orderDetail.protocol_number}</div>
              <div><b>Status:</b> {orderDetail.status}</div>
              <div><b>Prioridade:</b> {orderDetail.priority}</div>
              <div><b>Equipe:</b> {orderDetail.assigned_team || '—'}</div>
              <div><b>Local:</b> {orderDetail.location}</div>
              <div className="pt-2"><b>Descrição:</b> {orderDetail.description}</div>
              <div className="text-xs text-gray-500 pt-2">Criado em {new Date(orderDetail.created_at).toLocaleString()}</div>
            </div>
            <div className="mt-4 border-t pt-3">
              <h4 className="font-semibold mb-2">Andamentos</h4>
              <div className="max-h-40 overflow-auto space-y-2">
                {orderProgress.map((p: any) => (
                  <div key={p.id} className="border rounded px-2 py-1 text-sm">
                    <div className="flex justify-between">
                      <div className="font-medium">{p.status}</div>
                      <div className="text-xs text-gray-500">{new Date(p.created_at).toLocaleString()}</div>
                    </div>
                    <div className="text-gray-700">{p.progress_notes}</div>
                    {p.created_by_name && <div className="text-xs text-gray-500">por {p.created_by_name}</div>}
                  </div>
                ))}
                {orderProgress.length === 0 && <div className="text-sm text-gray-500">Sem andamentos.</div>}
              </div>
              <form
                className="mt-3 grid grid-cols-1 gap-2"
                onSubmit={async (e) => {
                  e.preventDefault()
                  await maintenanceDev.addOrderProgress(orderDetail.id, newProgress)
                  const prog = await maintenanceDev.getOrderProgress(orderDetail.id)
                  setOrderProgress(Array.isArray(prog.data) ? prog.data : [])
                  const updated = await maintenanceDev.getWorkOrder(orderDetail.id)
                  setOrderDetail(updated.data)
                  setNewProgress({ status: "in_progress", progress_notes: "" })
                }}
              >
                <select className="border rounded px-2 py-1" value={newProgress.status} onChange={(e) => setNewProgress({ ...newProgress, status: e.target.value as any })}>
                  <option value="in_progress">Em progresso</option>
                  <option value="completed">Concluída</option>
                </select>
                <textarea className="border rounded px-2 py-1" placeholder="Notas de andamento" value={newProgress.progress_notes} onChange={(e) => setNewProgress({ ...newProgress, progress_notes: e.target.value })} required />
                <div className="flex justify-end">
                  <button type="submit" className="px-3 py-1 bg-blue-600 text-white rounded">Adicionar Andamento</button>
                </div>
              </form>
            </div>
            <div className="flex justify-end gap-2 mt-4">
              <button onClick={() => setShowOrderDetail(false)} className="px-3 py-1 border rounded">Fechar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
