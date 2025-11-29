import { useState, useEffect } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { maintenanceDev } from "../services/maintenanceService"
import {
  X,
  Clock,
  MapPin,
  AlertTriangle,
  CheckCircle2,
  Circle,
  Play,
  Users,
  Calendar,
  FileText,
  TrendingUp,
  MessageSquare,
  Edit,
  Save,
  XCircle
} from "lucide-react"

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
  protocol_number?: string
}

interface Progress {
  id: number
  status: string
  progress_notes: string
  created_at: string
  created_by_name?: string
  estimated_completion?: string
}

interface ServiceOrderDetailModalProps {
  order: WorkOrder
  onClose: () => void
  onUpdate?: () => void
}

export function ServiceOrderDetailModal({ order, onClose, onUpdate }: ServiceOrderDetailModalProps) {
  const queryClient = useQueryClient()
  const [orderDetail, setOrderDetail] = useState<any>(null)
  const [progressList, setProgressList] = useState<Progress[]>([])
  const [isEditing, setIsEditing] = useState(false)
  const [editedOrder, setEditedOrder] = useState<Partial<WorkOrder>>({})
  const [newProgress, setNewProgress] = useState({
    status: "in_progress" as WorkOrder["status"],
    progress_notes: "",
    estimated_completion: ""
  })

  useEffect(() => {
    loadOrderDetails()
  }, [order.id, order.status, order.updated_at])

  const loadOrderDetails = async () => {
    try {
      const [detailRes, progressRes] = await Promise.all([
        maintenanceDev.getWorkOrder(parseInt(order.id)),
        maintenanceDev.getOrderProgress(parseInt(order.id))
      ])
      const detail = detailRes.data as any
      setOrderDetail(detail)
      setProgressList(Array.isArray(progressRes.data) ? progressRes.data : [])
      // Se não estiver editando, atualiza com os dados mais recentes
      if (!isEditing) {
        setEditedOrder({
          title: detail.title,
          description: detail.description,
          priority: detail.priority,
          status: detail.status,
          location: detail.location,
          estimated_duration: detail.estimated_duration
        })
      }
    } catch (error) {
      console.error("Erro ao carregar detalhes:", error)
    }
  }

  const updateOrderMutation = useMutation({
    mutationFn: (data: Partial<WorkOrder>) =>
      maintenanceDev.updateWorkOrder(parseInt(order.id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workOrders'] })
      loadOrderDetails()
      setIsEditing(false)
      onUpdate?.()
    }
  })

  const addProgressMutation = useMutation({
    mutationFn: (data: typeof newProgress) =>
      maintenanceDev.addOrderProgress(parseInt(order.id), data),
    onSuccess: () => {
      loadOrderDetails()
      setNewProgress({ status: "in_progress", progress_notes: "", estimated_completion: "" })
    }
  })

  const getPriorityConfig = (priority: string) => {
    const configs = {
      low: { color: "bg-green-100 text-green-800 border-green-300", label: "Baixa", icon: "🟢" },
      medium: { color: "bg-yellow-100 text-yellow-800 border-yellow-300", label: "Média", icon: "🟡" },
      high: { color: "bg-orange-100 text-orange-800 border-orange-300", label: "Alta", icon: "🟠" },
      critical: { color: "bg-red-100 text-red-800 border-red-300", label: "Crítica", icon: "🔴" }
    }
    return configs[priority as keyof typeof configs] || configs.low
  }

  const getStatusConfig = (status: string) => {
    const configs = {
      open: { color: "bg-blue-100 text-blue-800", label: "Aberta", icon: Circle },
      assigned: { color: "bg-purple-100 text-purple-800", label: "Atribuída", icon: Users },
      in_progress: { color: "bg-amber-100 text-amber-800", label: "Em Progresso", icon: Play },
      completed: { color: "bg-green-100 text-green-800", label: "Concluída", icon: CheckCircle2 }
    }
    return configs[status as keyof typeof configs] || configs.open
  }

  if (!orderDetail) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-lg p-6">
          <div className="animate-pulse">Carregando...</div>
        </div>
      </div>
    )
  }

  const priorityConfig = getPriorityConfig(orderDetail.priority || order.priority)
  const statusConfig = getStatusConfig(orderDetail.status || order.status)
  const StatusIcon = statusConfig.icon

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center p-4 z-50 animate-fadeIn">
      <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl flex flex-col animate-slideUp">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6 flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <FileText className="w-8 h-8" />
              <div>
                {isEditing ? (
                  <input
                    type="text"
                    value={editedOrder.title || ""}
                    onChange={(e) => setEditedOrder({ ...editedOrder, title: e.target.value })}
                    className="text-2xl font-bold bg-white/20 rounded px-2 py-1 w-full"
                  />
                ) : (
                  <h2 className="text-2xl font-bold">{orderDetail.title}</h2>
                )}
                <p className="text-blue-100 text-sm mt-1">Protocolo: {orderDetail.protocol_number}</p>
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            {!isEditing ? (
              <button
                onClick={() => setIsEditing(true)}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                title="Editar"
              >
                <Edit className="w-5 h-5" />
              </button>
            ) : (
              <>
                <button
                  onClick={() => updateOrderMutation.mutate(editedOrder)}
                  className="p-2 bg-green-500 hover:bg-green-600 rounded-lg transition-colors"
                  title="Salvar"
                >
                  <Save className="w-5 h-5" />
                </button>
                <button
                  onClick={() => {
                    setIsEditing(false)
                    setEditedOrder(orderDetail)
                  }}
                  className="p-2 bg-red-500 hover:bg-red-600 rounded-lg transition-colors"
                  title="Cancelar"
                >
                  <XCircle className="w-5 h-5" />
                </button>
              </>
            )}
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              title="Fechar"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Info */}
            <div className="lg:col-span-2 space-y-6">
              {/* Status Cards */}
              <div className="grid grid-cols-2 gap-4">
                <div className={`${statusConfig.color} rounded-xl p-4 border-2 border-opacity-50`}>
                  <div className="flex items-center gap-2 mb-1">
                    <StatusIcon className="w-5 h-5" />
                    <span className="text-xs font-medium opacity-75">Status</span>
                  </div>
                  {isEditing ? (
                    <select
                      value={editedOrder.status}
                      onChange={(e) => setEditedOrder({ ...editedOrder, status: e.target.value as any })}
                      className="w-full font-bold text-lg bg-white/50 rounded px-2 py-1"
                    >
                      <option value="open">Aberta</option>
                      <option value="assigned">Atribuída</option>
                      <option value="in_progress">Em Progresso</option>
                      <option value="completed">Concluída</option>
                    </select>
                  ) : (
                    <p className="font-bold text-lg">{statusConfig.label}</p>
                  )}
                </div>

                <div className={`${priorityConfig.color} rounded-xl p-4 border-2`}>
                  <div className="flex items-center gap-2 mb-1">
                    <AlertTriangle className="w-5 h-5" />
                    <span className="text-xs font-medium opacity-75">Prioridade</span>
                  </div>
                  {isEditing ? (
                    <select
                      value={editedOrder.priority}
                      onChange={(e) => setEditedOrder({ ...editedOrder, priority: e.target.value as any })}
                      className="w-full font-bold text-lg bg-white/50 rounded px-2 py-1"
                    >
                      <option value="low">Baixa</option>
                      <option value="medium">Média</option>
                      <option value="high">Alta</option>
                      <option value="critical">Crítica</option>
                    </select>
                  ) : (
                    <p className="font-bold text-lg">
                      {priorityConfig.icon} {priorityConfig.label}
                    </p>
                  )}
                </div>
              </div>

              {/* Description */}
              <div className="bg-gray-50 rounded-xl p-5 border border-gray-200">
                <div className="flex items-center gap-2 mb-3">
                  <FileText className="w-5 h-5 text-gray-600" />
                  <h3 className="font-semibold text-gray-900">Descrição</h3>
                </div>
                {isEditing ? (
                  <textarea
                    value={editedOrder.description || ""}
                    onChange={(e) => setEditedOrder({ ...editedOrder, description: e.target.value })}
                    className="w-full border rounded-lg px-3 py-2 min-h-[100px]"
                  />
                ) : (
                  <p className="text-gray-700 leading-relaxed">{orderDetail.description}</p>
                )}
              </div>

              {/* Progress Timeline */}
              <div className="bg-white rounded-xl border-2 border-gray-200 p-5">
                <div className="flex items-center gap-2 mb-4">
                  <TrendingUp className="w-5 h-5 text-blue-600" />
                  <h3 className="font-semibold text-gray-900">Histórico de Andamentos</h3>
                  <span className="ml-auto bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">
                    {progressList.length} registro(s)
                  </span>
                </div>

                <div className="space-y-3 max-h-64 overflow-y-auto mb-4">
                  {progressList.length === 0 ? (
                    <div className="text-center py-8 text-gray-400">
                      <MessageSquare className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p>Nenhum andamento registrado ainda</p>
                    </div>
                  ) : (
                    progressList.map((progress, index) => (
                      <div
                        key={progress.id}
                        className="relative pl-8 pb-4 border-l-2 border-gray-200 last:border-l-0 last:pb-0"
                      >
                        <div className="absolute left-[-9px] top-0 w-4 h-4 rounded-full bg-blue-500 border-2 border-white" />
                        <div className="bg-gray-50 rounded-lg p-3">
                          <div className="flex justify-between items-start mb-2">
                            <span className={`${getStatusConfig(progress.status).color} px-2 py-1 rounded-lg text-xs font-medium`}>
                              {getStatusConfig(progress.status).label}
                            </span>
                            <span className="text-xs text-gray-500">
                              {new Date(progress.created_at).toLocaleString("pt-BR")}
                            </span>
                          </div>
                          <p className="text-sm text-gray-700 mb-1">{progress.progress_notes}</p>
                          {progress.created_by_name && (
                            <p className="text-xs text-gray-500">por {progress.created_by_name}</p>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>

                {/* Add Progress Form */}
                <form
                  onSubmit={(e) => {
                    e.preventDefault()
                    addProgressMutation.mutate(newProgress)
                  }}
                  className="border-t-2 pt-4 space-y-3"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <MessageSquare className="w-4 h-4 text-gray-600" />
                    <span className="text-sm font-medium text-gray-700">Adicionar Novo Andamento</span>
                  </div>
                  <select
                    value={newProgress.status}
                    onChange={(e) => setNewProgress({ ...newProgress, status: e.target.value as any })}
                    className="w-full border-2 border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="open">Aberta</option>
                    <option value="assigned">Atribuída</option>
                    <option value="in_progress">Em Progresso</option>
                    <option value="completed">Concluída</option>
                  </select>
                  <textarea
                    value={newProgress.progress_notes}
                    onChange={(e) => setNewProgress({ ...newProgress, progress_notes: e.target.value })}
                    placeholder="Descreva o andamento da ordem de serviço..."
                    className="w-full border-2 border-gray-300 rounded-lg px-3 py-2 min-h-[80px] focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                  <button
                    type="submit"
                    disabled={addProgressMutation.isPending}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {addProgressMutation.isPending ? "Adicionando..." : "Adicionar Andamento"}
                  </button>
                </form>
              </div>
            </div>

            {/* Sidebar Info */}
            <div className="space-y-4">
              <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-5 border border-gray-200">
                <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <Clock className="w-5 h-5 text-gray-600" />
                  Informações
                </h3>
                <div className="space-y-3">
                  <div className="flex items-start gap-3">
                    <MapPin className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="text-xs text-gray-500 mb-1">Localização</p>
                      {isEditing ? (
                        <input
                          type="text"
                          value={editedOrder.location || ""}
                          onChange={(e) => setEditedOrder({ ...editedOrder, location: e.target.value })}
                          className="w-full border rounded px-2 py-1 text-sm"
                        />
                      ) : (
                        <p className="text-sm font-medium text-gray-900">{orderDetail.location}</p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <Users className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="text-xs text-gray-500 mb-1">Equipe Atribuída</p>
                      <p className="text-sm font-medium text-gray-900">
                        {orderDetail.assigned_team || "Não atribuída"}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <Clock className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="text-xs text-gray-500 mb-1">Duração Estimada</p>
                      {isEditing ? (
                        <input
                          type="number"
                          value={editedOrder.estimated_duration || 0}
                          onChange={(e) => setEditedOrder({ ...editedOrder, estimated_duration: parseInt(e.target.value) })}
                          className="w-full border rounded px-2 py-1 text-sm"
                        />
                      ) : (
                        <p className="text-sm font-medium text-gray-900">{orderDetail.estimated_duration}h</p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <Calendar className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="text-xs text-gray-500 mb-1">Criado em</p>
                      <p className="text-sm font-medium text-gray-900">
                        {new Date(orderDetail.created_at).toLocaleString("pt-BR")}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <Calendar className="w-5 h-5 text-indigo-600 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="text-xs text-gray-500 mb-1">Última Atualização</p>
                      <p className="text-sm font-medium text-gray-900">
                        {new Date(orderDetail.updated_at).toLocaleString("pt-BR")}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-5 border border-blue-200">
                <h3 className="font-semibold text-gray-900 mb-3">Ações Rápidas</h3>
                <div className="space-y-2">
                  <button
                    onClick={() => {
                      setEditedOrder({ ...orderDetail, status: "in_progress" })
                      updateOrderMutation.mutate({ status: "in_progress" })
                    }}
                    disabled={orderDetail.status === "in_progress"}
                    className="w-full bg-amber-500 hover:bg-amber-600 text-white font-medium py-2 px-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm flex items-center justify-center gap-2"
                  >
                    <Play className="w-4 h-4" />
                    Iniciar Trabalho
                  </button>
                  <button
                    onClick={() => {
                      setEditedOrder({ ...orderDetail, status: "completed" })
                      updateOrderMutation.mutate({ status: "completed" })
                    }}
                    disabled={orderDetail.status === "completed"}
                    className="w-full bg-green-500 hover:bg-green-600 text-white font-medium py-2 px-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm flex items-center justify-center gap-2"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    Marcar como Concluída
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t bg-gray-50 px-6 py-4 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-6 py-2 border-2 border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-100 transition-colors"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  )
}
