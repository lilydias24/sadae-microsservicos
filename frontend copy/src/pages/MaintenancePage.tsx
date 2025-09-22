"use client"

import { useState, useEffect } from "react"
import * as maintenanceService from "../services/maintenanceService"
import { WorkOrder, AlertLevel, OrderStatus } from '../types/maintenance'

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

const mockComplaints: Complaint[] = [
  {
    id: "1",
    citizen_name: "João Silva",
    description: "Água com gosto estranho",
    location: "Setor Norte",
    status: "aberto",
    created_at: new Date().toISOString()
  }
]

export function MaintenancePage() {
  // Estado para modal de criação de OS a partir de reclamação
  const [createOrderFromComplaint, setCreateOrderFromComplaint] = useState<Complaint | null>(null)
  // Estado para modal de criação/edição de equipe
  const [showCreateTeam, setShowCreateTeam] = useState(false)
  const [newTeam, setNewTeam] = useState<Partial<Team>>({ name: '', members_count: 1 })
  const [editTeam, setEditTeam] = useState<Team | null>(null)
  const [editTeamData, setEditTeamData] = useState<Partial<Team>>({})

  // Função para criar equipe
  const createTeam = (teamData: Partial<Team>) => {
    const newT: Team = {
      id: Date.now().toString(),
      name: teamData.name || '',
      members_count: teamData.members_count || 1,
      status: 'disponivel',
    }
    setTeams(prev => [...prev, newT])
    setShowCreateTeam(false)
    setNewTeam({ name: '', members_count: 1 })
  }

  // Função para salvar edição de equipe
  const saveEditTeam = () => {
    if (!editTeam) return
    setTeams(prev => prev.map(team =>
      team.id === editTeam.id ? { ...team, ...editTeamData } : team
    ))
    setEditTeam(null)
    setEditTeamData({})
  }
  // Estado para modal de edição
  const [editOrder, setEditOrder] = useState<WorkOrder | null>(null)
  const [editOrderData, setEditOrderData] = useState<Partial<WorkOrder>>({})

  // Função para salvar edição
  const saveEditOrder = async () => {
    if (!editOrder) return
    try {
      const updatePayload = {
        title: editOrderData.title,
        description: editOrderData.description,
        priority: editOrderData.priority,
        location: editOrderData.location,
        status: editOrderData.status
      }
      const res = await maintenanceService.updateOrder(editOrder.id, updatePayload)
      setWorkOrders(prev => prev.map(order =>
        order.id === editOrder.id ? { ...order, ...res.data } : order
      ))
      setEditOrder(null)
      setEditOrderData({})
    } catch (e) {
      console.error('Error updating order:', e)
    }
  }

  // Função para fechar chamado
  const completeOrder = async () => {
    if (!editOrder) return
    try {
      const updatePayload = {
        status: "completed" as const,
        completed_at: new Date().toISOString()
      }
      await maintenanceService.updateOrder(editOrder.id, updatePayload)
      
      // Update the order status to completed
      setWorkOrders(prev => prev.map(order => 
        order.id === editOrder.id 
          ? { ...order, status: "completed" } 
          : order
      ))
      
      // If there's an assigned team, update its status to available
      if (editOrder.assigned_team) {
        setTeams(prev => prev.map(team =>
          team.name === editOrder.assigned_team ? { ...team, status: "disponivel" } : team
        ))
      }
      
      setEditOrder(null)
      setEditOrderData({})
    } catch (e) {
      console.error('Error completing order:', e)
    }
  }
  const [activeTab, setActiveTab] = useState<"orders" | "teams" | "complaints">("orders")
  const [selectedOrder, setSelectedOrder] = useState<WorkOrder | null>(null)
  const [showCreateOrder, setShowCreateOrder] = useState(false)
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([])
  const [teams, setTeams] = useState<Team[]>([])
  const [complaints, setComplaints] = useState<Complaint[]>(mockComplaints)
  const [loadingOrders, setLoadingOrders] = useState(true)
  // Buscar ordens e equipes da API ao carregar e a cada 30 segundos
  useEffect(() => {
    const fetchData = async () => {
      setLoadingOrders(true)
      try {
        const [ordersRes, teamsRes] = await Promise.all([
          maintenanceService.getOrders(),
          maintenanceService.getTeams()
        ])
        
        if (ordersRes.data) {
          // Ordenar as ordens por data de criação (mais recentes primeiro)
          const sortedOrders = [...ordersRes.data].sort((a, b) => 
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
          )
          setWorkOrders(sortedOrders)
        }
        
        if (teamsRes.data) {
          setTeams(teamsRes.data)
        }
      } catch (e) {
        console.error('Error loading data:', e)
      } finally {
        setLoadingOrders(false)
      }
    }

    // Fazer a primeira chamada
    fetchData()

    // Configurar o intervalo para atualizar a cada 30 segundos
    const interval = setInterval(fetchData, 30000)

    // Limpar o intervalo quando o componente for desmontado
    return () => clearInterval(interval)
  }, [])
  // Estado do formulário de nova ordem
  const [newOrder, setNewOrder] = useState<Partial<WorkOrder>>({
    title: "",
    description: "",
    priority: "medium" as AlertLevel,
    location: "",
    status: "open" as OrderStatus,
    estimated_duration: 1,
  })
  const assignTeam = async (orderId: string, teamName: string) => {
    try {
      const res = await maintenanceService.assignOrder(orderId, teamName)
      
      if (res.data) {
        // Update order list with the response data
        setWorkOrders(prev => prev.map(order =>
          order.id === orderId ? { ...res.data } : order
        ))
        
        // Update team status to busy
        setTeams(prev => prev.map(team =>
          team.name === teamName ? { ...team, status: "ocupado" } : team
        ))
        
        // Close assign team modal
        setSelectedOrder(null)
      } else {
        console.error('No response data from assign team request')
      }
    } catch (e) {
      console.error('Error assigning team:', e)
      // TODO: Adicionar notificação de erro quando o toast estiver implementado
    }
  }

  const createOrder = async (orderData: Partial<WorkOrder>) => {
    try {
      // Ensure the order starts with status "open"
      const orderWithStatus = {
        ...orderData,
        status: "open" as OrderStatus
      }
      const res = await maintenanceService.createOrder(orderWithStatus)
      setWorkOrders(prev => [...prev, res.data])
      setShowCreateOrder(false)
    } catch (e) {
      console.error('Error creating order:', e)
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "baixo":
        return "text-green-600 bg-green-100"
      case "médio":
        return "text-yellow-600 bg-yellow-100"
      case "alto":
        return "text-orange-600 bg-orange-100"
      case "urgente":
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
        return "text-green-600 bg-green-100 font-semibold"
      case "cancelled":
        return "text-red-600 bg-red-100"
      default:
        return "text-gray-600 bg-gray-100"
    }
  }

  return (
    <div className="space-y-6">
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
                  priority: "medium",
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
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
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
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Criar Ordem
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal de criação de OS a partir de reclamação */}
      {createOrderFromComplaint && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Nova Ordem de Serviço</h3>
            <form
              className="space-y-4"
              onSubmit={e => {
                e.preventDefault()
                createOrder({
                  title: createOrderFromComplaint.citizen_name,
                  description: createOrderFromComplaint.description,
                  location: createOrderFromComplaint.location,
                  priority: newOrder.priority,
                  estimated_duration: newOrder.estimated_duration
                })
                setComplaints(prev => prev.filter(c => c.id !== createOrderFromComplaint.id))
                setCreateOrderFromComplaint(null)
                setNewOrder({
                  title: '',
                  description: '',
                  priority: 'medium',
                  location: '',
                  estimated_duration: 1,
                })
              }}
            >
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Título</label>
                <input
                  type="text"
                  className="form-input w-full border border-gray-300 rounded px-2 py-1"
                  value={createOrderFromComplaint.citizen_name}
                  disabled
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Descrição</label>
                <textarea
                  className="form-input w-full border border-gray-300 rounded px-2 py-1"
                  value={createOrderFromComplaint.description}
                  disabled
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Prioridade</label>
                <select
                  className="form-input w-full border border-gray-300 rounded px-2 py-1"
                  value={newOrder.priority}
                  onChange={e => setNewOrder({ ...newOrder, priority: e.target.value as WorkOrder["priority"] })}
                >
                  <option value="baixo">Baixo</option>
                  <option value="médio">Médio</option>
                  <option value="alto">Alto</option>
                  <option value="urgente">Urgente</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Localização</label>
                <input
                  type="text"
                  className="form-input w-full border border-gray-300 rounded px-2 py-1"
                  value={createOrderFromComplaint.location}
                  disabled
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
                  onClick={() => setCreateOrderFromComplaint(null)}
                  className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Criar Ordem
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Ordens Abertas</p>
              <p className="text-2xl font-bold text-gray-900">
                {workOrders.filter((o: WorkOrder) => o.status === "open").length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Em Andamento</p>
              <p className="text-2xl font-bold text-gray-900">
                {workOrders.filter((o: WorkOrder) => o.status === "in_progress").length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Concluídas</p>
              <p className="text-2xl font-bold text-gray-900">
                {workOrders.filter((o: WorkOrder) => o.status === "completed").length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Equipes Ativas</p>
              <p className="text-2xl font-bold text-gray-900">
                {teams.filter((t: Team) => t.status === "disponivel").length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: "orders", name: "Ordens de Serviço", icon: "📋" },
            { id: "teams", name: "Equipes", icon: "👥" },
            { id: "complaints", name: "Reclamações", icon: "📞" },
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
            {workOrders.map((order: WorkOrder) => (
              <div key={order.id} className={`px-6 py-4 hover:bg-gray-50 ${order.status === 'completed' ? 'opacity-75' : ''}`}>
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <h4 className="text-sm font-medium text-gray-900">{order.title}</h4>
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getPriorityColor(order.priority)}`}
                      >
                        {order.priority}
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
                    <button
                      className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                      onClick={() => {
                        setEditOrder(order)
                        setEditOrderData({ ...order })
                      }}
                    >
                      Ver Detalhes
                    </button>
                    {!order.assigned_team && order.status !== "completed" && order.status !== "cancelled" && (
                      <button
                        onClick={() => setSelectedOrder(order)}
                        className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                      >
                        Atribuir Equipe
                      </button>
                    )}
      {/* Modal de edição de OS */}
      {editOrder && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Editar Ordem de Serviço</h3>
            <form
              className="space-y-4"
              onSubmit={e => {
                e.preventDefault()
                saveEditOrder()
              }}
            >
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Título</label>
                <input
                  type="text"
                  className="form-input w-full border border-gray-300 rounded px-2 py-1"
                  value={editOrderData.title || ''}
                  onChange={e => setEditOrderData({ ...editOrderData, title: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Descrição</label>
                <textarea
                  className="form-input w-full border border-gray-300 rounded px-2 py-1"
                  value={editOrderData.description || ''}
                  onChange={e => setEditOrderData({ ...editOrderData, description: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Prioridade</label>
                <select
                  className="form-input w-full border border-gray-300 rounded px-2 py-1"
                  value={editOrderData.priority || 'medium'}
                  onChange={e => setEditOrderData({ ...editOrderData, priority: e.target.value as WorkOrder["priority"] })}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Localização</label>
                <input
                  type="text"
                  className="form-input w-full border border-gray-300 rounded px-2 py-1"
                  value={editOrderData.location || ''}
                  onChange={e => setEditOrderData({ ...editOrderData, location: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Duração Estimada (h)</label>
                <input
                  type="number"
                  min={1}
                  className="form-input w-full border border-gray-300 rounded px-2 py-1"
                  value={editOrderData.estimated_duration || 1}
                  onChange={e => setEditOrderData({ ...editOrderData, estimated_duration: Number(e.target.value) })}
                  required
                />
              </div>
              {editOrder.assigned_team && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Equipe Atribuída</label>
                  <input
                    type="text"
                    className="form-input w-full border border-gray-300 rounded px-2 py-1 bg-gray-100"
                    value={editOrder.assigned_team}
                    disabled
                  />
                </div>
              )}
              <div className="flex justify-between space-x-3 mt-6">
                <div>
                  <button
                    type="button"
                    onClick={() => { setEditOrder(null); setEditOrderData({}) }}
                    className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancelar
                  </button>
                </div>
                <div className="flex space-x-3">
                  {editOrder.assigned_team && (
                    <button
                      type="button"
                      onClick={completeOrder}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                    >
                      Concluir OS
                    </button>
                  )}
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    Salvar
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "teams" && (
        <div>
          <div className="flex justify-end mb-4">
            <button
              onClick={() => setShowCreateTeam(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Nova Equipe
            </button>
          </div>
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
                <div className="space-y-2 flex items-center justify-between">
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
                  <button
                    className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                    onClick={() => {
                      setEditTeam(team)
                      setEditTeamData({ name: team.name, members_count: team.members_count })
                    }}
                  >
                    Editar
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Modal de criação de equipe */}
      {showCreateTeam && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Nova Equipe</h3>
            <form
              className="space-y-4"
              onSubmit={e => {
                e.preventDefault()
                createTeam(newTeam)
              }}
            >
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nome da Equipe</label>
                <input
                  type="text"
                  className="form-input w-full border border-gray-300 rounded px-2 py-1"
                  value={newTeam.name || ''}
                  onChange={e => setNewTeam({ ...newTeam, name: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Número de Membros</label>
                <input
                  type="number"
                  min={1}
                  className="form-input w-full border border-gray-300 rounded px-2 py-1"
                  value={newTeam.members_count || 1}
                  onChange={e => setNewTeam({ ...newTeam, members_count: Number(e.target.value) })}
                  required
                />
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowCreateTeam(false)}
                  className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Criar Equipe
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal de edição de equipe */}
      {editTeam && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Editar Equipe</h3>
            <form
              className="space-y-4"
              onSubmit={e => {
                e.preventDefault()
                saveEditTeam()
              }}
            >
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nome da Equipe</label>
                <input
                  type="text"
                  className="form-input w-full border border-gray-300 rounded px-2 py-1"
                  value={editTeamData.name || ''}
                  onChange={e => setEditTeamData({ ...editTeamData, name: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Número de Membros</label>
                <input
                  type="number"
                  min={1}
                  className="form-input w-full border border-gray-300 rounded px-2 py-1"
                  value={editTeamData.members_count || 1}
                  onChange={e => setEditTeamData({ ...editTeamData, members_count: Number(e.target.value) })}
                  required
                />
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => { setEditTeam(null); setEditTeamData({}) }}
                  className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Salvar
                </button>
              </div>
            </form>
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
                  <button
                    className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                    onClick={() => {
                      setCreateOrderFromComplaint(complaint)
                      setNewOrder({
                        ...newOrder,
                        priority: 'medium',
                        estimated_duration: 1
                      })
                    }}
                  >
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
                .map((team: Team) => (
                  <button
                    key={team.id}
                    onClick={() => assignTeam(selectedOrder.id, team.name)}
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
