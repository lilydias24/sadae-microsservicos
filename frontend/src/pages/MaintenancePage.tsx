import { useState, useEffect } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { maintenanceService } from "../services/api"
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
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<"orders" | "teams" | "complaints">("orders")
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
  const workOrders = workOrdersResponse && Array.isArray(workOrdersResponse.data) ? workOrdersResponse.data : []
  const teams = teamsResponse && Array.isArray(teamsResponse.data) ? teamsResponse.data : []
  const complaints = complaintsResponse && Array.isArray(complaintsResponse.data) ? complaintsResponse.data : []

  // Mutations para criar e atualizar ordens
  const createOrderMutation = useMutation({
    mutationFn: (orderData: any) => maintenanceService.createWorkOrder(orderData),
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

  const createTeamMutation = useMutation({
    mutationFn: (data: any) => maintenanceService.createTeam(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams'] })
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
    }
  })

  const updateTeamMutation = useMutation({
    mutationFn: ({ id, data }: { id: number, data: any }) => maintenanceService.updateTeam(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams'] })
      setEditingTeam(null)
    }
  })

  const addMemberMutation = useMutation({
    mutationFn: ({ teamId, data }: { teamId: number, data: any }) => maintenanceService.addTeamMember(teamId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams'] })
      setNewMember({ name: "", role: "", contact: "" })
    }
  })

  const openOrderDetail = async (order: WorkOrder) => {
    try {
      const res = await maintenanceService.getWorkOrder(parseInt(order.id))
      setOrderDetail(res.data)
      const prog = await maintenanceService.getOrderProgress(parseInt(order.id))
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
                  <option value="low">Baixa</option>
                  <option value="medium">Média</option>
                  <option value="high">Alta</option>
                  <option value="critical">Urgente</option>
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

      {/* Create Team Modal */}
      {showCreateTeam && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Nova Equipe</h3>
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
                work_areas: (teamForm.work_areas_csv || '').split(',').map((s: string) => s.trim()).filter(Boolean),
                equipment: (teamForm.equipment_csv || '').split(',').map((s: string) => s.trim()).filter(Boolean),
              };
              createTeamMutation.mutate(payload)
            }} className="space-y-3">
              <input className="w-full border rounded px-2 py-1" placeholder="Nome" value={teamForm.name} onChange={e => setTeamForm({ ...teamForm, name: e.target.value })} required />
              <input className="w-full border rounded px-2 py-1" placeholder="Descrição" value={teamForm.description} onChange={e => setTeamForm({ ...teamForm, description: e.target.value })} />
              <input className="w-full border rounded px-2 py-1" placeholder="Especialização" value={teamForm.specialization} onChange={e => setTeamForm({ ...teamForm, specialization: e.target.value })} />
              <div className="grid grid-cols-2 gap-3">
                <input type="number" min={0} className="border rounded px-2 py-1" placeholder="Qtd. Membros" value={teamForm.members_count} onChange={e => setTeamForm({ ...teamForm, members_count: Number(e.target.value) })} />
                <input type="number" min={1} className="border rounded px-2 py-1" placeholder="Capacidade" value={teamForm.max_concurrent_orders} onChange={e => setTeamForm({ ...teamForm, max_concurrent_orders: Number(e.target.value) })} />
                <input className="border rounded px-2 py-1 col-span-2" placeholder="Supervisor" value={teamForm.supervisor_name} onChange={e => setTeamForm({ ...teamForm, supervisor_name: e.target.value })} />
                <input className="border rounded px-2 py-1 col-span-2" placeholder="Contato do Supervisor" value={teamForm.supervisor_contact} onChange={e => setTeamForm({ ...teamForm, supervisor_contact: e.target.value })} />
                <input className="border rounded px-2 py-1 col-span-2" placeholder="Áreas de trabalho (sep. por vírgula)" value={teamForm.work_areas_csv} onChange={e => setTeamForm({ ...teamForm, work_areas_csv: e.target.value })} />
                <input className="border rounded px-2 py-1 col-span-2" placeholder="Equipamentos (sep. por vírgula)" value={teamForm.equipment_csv} onChange={e => setTeamForm({ ...teamForm, equipment_csv: e.target.value })} />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setShowCreateTeam(false)} className="px-3 py-1 border rounded">Cancelar</button>
                <button type="submit" disabled={createTeamMutation.isPending} className="px-3 py-1 bg-blue-600 text-white rounded">{createTeamMutation.isPending ? 'Criando...' : 'Criar'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Team & Members Modal */}
      {editingTeam && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-lg w-full p-6 space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Editar Equipe - {editingTeam.name}</h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-gray-600">Nome</label>
                <input className="w-full border rounded px-2 py-1" value={teamForm.name} onChange={e => setTeamForm({ ...teamForm, name: e.target.value })} />
              </div>
              <div>
                <label className="text-xs text-gray-600">Capacidade</label>
                <input type="number" min={1} className="w-full border rounded px-2 py-1" value={teamForm.max_concurrent_orders} onChange={e => setTeamForm({ ...teamForm, max_concurrent_orders: Number(e.target.value) })} />
              </div>
              <div className="col-span-2">
                <label className="text-xs text-gray-600">Especialização</label>
                <input className="w-full border rounded px-2 py-1" value={teamForm.specialization || ''} onChange={e => setTeamForm({ ...teamForm, specialization: e.target.value })} />
              </div>
              <label className="col-span-2 flex items-center gap-2 text-sm"><input type="checkbox" checked={teamForm.is_active} onChange={e => setTeamForm({ ...teamForm, is_active: e.target.checked })} /> Ativa</label>
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={() => setEditingTeam(null)} className="px-3 py-1 border rounded">Fechar</button>
              <button onClick={() => updateTeamMutation.mutate({ id: parseInt(editingTeam.id), data: teamForm })} className="px-3 py-1 bg-blue-600 text-white rounded">Salvar</button>
            </div>
            <div className="border-t pt-3">
              <h4 className="font-semibold mb-2">Membros</h4>
              <div className="space-y-2 max-h-48 overflow-auto">
                {(editingTeam.members || []).map(m => (
                  <div key={m.id} className="flex items-center justify-between text-sm border rounded px-2 py-1">
                    <div>
                      <div className="font-medium">{m.name}</div>
                      <div className="text-gray-600">{m.role}</div>
                    </div>
                    {/* For brevity, only delete here */}
                    <button onClick={() => maintenanceService.deleteTeamMember(parseInt(editingTeam.id), m.id).then(() => queryClient.invalidateQueries({ queryKey: ['teams'] }))} className="text-red-600">Remover</button>
                  </div>
                ))}
              </div>
              <form onSubmit={(e) => { e.preventDefault(); if (editingTeam) addMemberMutation.mutate({ teamId: parseInt(editingTeam.id), data: newMember }) }} className="flex gap-2 mt-3">
                <input className="flex-1 border rounded px-2 py-1" placeholder="Nome" value={newMember.name || ''} onChange={e => setNewMember({ ...newMember, name: e.target.value })} required />
                <input className="w-40 border rounded px-2 py-1" placeholder="Função" value={newMember.role || ''} onChange={e => setNewMember({ ...newMember, role: e.target.value })} />
                <button type="submit" className="px-3 py-1 bg-green-600 text-white rounded">Adicionar</button>
              </form>
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
                  await maintenanceService.addOrderProgress(orderDetail.id, newProgress)
                  const prog = await maintenanceService.getOrderProgress(orderDetail.id)
                  setOrderProgress(Array.isArray(prog.data) ? prog.data : [])
                  const updated = await maintenanceService.getWorkOrder(orderDetail.id)
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
