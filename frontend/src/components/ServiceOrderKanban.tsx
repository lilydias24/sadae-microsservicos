import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { maintenanceDev } from "../services/maintenanceService"
import { Clock, MapPin, AlertCircle, Users, Calendar, CheckCircle2, Circle, Play, Package } from "lucide-react"

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

interface KanbanColumn {
  id: string
  title: string
  status: WorkOrder["status"]
  icon: any
  color: string
}

interface ServiceOrderKanbanProps {
  orders: WorkOrder[]
  onOrderClick: (order: WorkOrder) => void
}

const COLUMNS: KanbanColumn[] = [
  {
    id: "open",
    title: "Abertas",
    status: "open",
    icon: Circle,
    color: "blue"
  },
  {
    id: "assigned",
    title: "Atribuídas",
    status: "assigned",
    icon: Users,
    color: "purple"
  },
  {
    id: "in_progress",
    title: "Em Progresso",
    status: "in_progress",
    icon: Play,
    color: "yellow"
  },
  {
    id: "completed",
    title: "Concluídas",
    status: "completed",
    icon: CheckCircle2,
    color: "green"
  }
]

export function ServiceOrderKanban({ orders, onOrderClick }: ServiceOrderKanbanProps) {
  const queryClient = useQueryClient()
  const [draggedOrder, setDraggedOrder] = useState<WorkOrder | null>(null)

  const updateOrderMutation = useMutation({
    mutationFn: ({ orderId, status }: { orderId: number; status: WorkOrder["status"] }) =>
      maintenanceDev.updateWorkOrder(orderId, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["work-orders"] })
    }
  })

  const handleDragStart = (order: WorkOrder) => {
    setDraggedOrder(order)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  const handleDrop = (status: WorkOrder["status"]) => {
    if (draggedOrder && draggedOrder.status !== status) {
      updateOrderMutation.mutate({
        orderId: parseInt(draggedOrder.id),
        status
      })
    }
    setDraggedOrder(null)
  }

  const getPriorityConfig = (priority: string) => {
    switch (priority) {
      case "low":
        return { color: "bg-green-100 text-green-800 border-green-200", label: "Baixa", icon: "🟢" }
      case "medium":
        return { color: "bg-yellow-100 text-yellow-800 border-yellow-200", label: "Média", icon: "🟡" }
      case "high":
        return { color: "bg-orange-100 text-orange-800 border-orange-200", label: "Alta", icon: "🟠" }
      case "critical":
        return { color: "bg-red-100 text-red-800 border-red-200", label: "Crítica", icon: "🔴" }
      default:
        return { color: "bg-gray-100 text-gray-800 border-gray-200", label: "Normal", icon: "⚪" }
    }
  }

  const getColumnColor = (color: string) => {
    const colors: Record<string, any> = {
      blue: {
        bg: "bg-blue-50",
        border: "border-blue-200",
        header: "bg-gradient-to-r from-blue-500 to-blue-600",
        count: "bg-blue-600",
        text: "text-blue-700"
      },
      purple: {
        bg: "bg-purple-50",
        border: "border-purple-200",
        header: "bg-gradient-to-r from-purple-500 to-purple-600",
        count: "bg-purple-600",
        text: "text-purple-700"
      },
      yellow: {
        bg: "bg-yellow-50",
        border: "border-yellow-200",
        header: "bg-gradient-to-r from-yellow-500 to-yellow-600",
        count: "bg-yellow-600",
        text: "text-yellow-700"
      },
      green: {
        bg: "bg-green-50",
        border: "border-green-200",
        header: "bg-gradient-to-r from-green-500 to-green-600",
        count: "bg-green-600",
        text: "text-green-700"
      }
    }
    return colors[color] || colors.blue
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString("pt-BR")
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 h-[calc(100vh-250px)]">
      {COLUMNS.map((column) => {
        const columnOrders = orders.filter(order => order.status === column.status)
        const colorConfig = getColumnColor(column.color)
        const Icon = column.icon

        return (
          <div
            key={column.id}
            className={`flex flex-col rounded-lg border-2 ${colorConfig.border} ${colorConfig.bg} overflow-hidden`}
            onDragOver={handleDragOver}
            onDrop={() => handleDrop(column.status)}
          >
            {/* Column Header */}
            <div className={`${colorConfig.header} text-white px-4 py-3 flex items-center justify-between shadow-md`}>
              <div className="flex items-center gap-2">
                <Icon className="w-5 h-5" />
                <h3 className="font-semibold text-lg">{column.title}</h3>
              </div>
              <span className={`${colorConfig.count} text-white text-sm font-bold px-2.5 py-1 rounded-full`}>
                {columnOrders.length}
              </span>
            </div>

            {/* Cards Container */}
            <div className="flex-1 overflow-y-auto p-3 space-y-3">
              {columnOrders.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-32 text-gray-400">
                  <Package className="w-12 h-12 mb-2 opacity-50" />
                  <p className="text-sm">Nenhuma ordem</p>
                </div>
              ) : (
                columnOrders.map((order) => {
                  const priorityConfig = getPriorityConfig(order.priority)

                  return (
                    <div
                      key={order.id}
                      draggable
                      onDragStart={() => handleDragStart(order)}
                      onClick={() => onOrderClick(order)}
                      className={`bg-white rounded-lg border-2 ${priorityConfig.color} p-4 cursor-move hover:shadow-xl transition-all duration-200 transform hover:-translate-y-1`}
                    >
                      {/* Priority Badge */}
                      <div className="flex items-center justify-between mb-3">
                        <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${priorityConfig.color}`}>
                          {priorityConfig.icon} {priorityConfig.label}
                        </span>
                        {order.assigned_team && (
                          <div className="flex items-center gap-1 text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded-full">
                            <Users className="w-3 h-3" />
                            <span className="font-medium">{order.assigned_team}</span>
                          </div>
                        )}
                      </div>

                      {/* Title */}
                      <h4 className="font-bold text-gray-900 mb-2 line-clamp-2 text-sm">
                        {order.title}
                      </h4>

                      {/* Description */}
                      <p className="text-gray-600 text-xs mb-3 line-clamp-2">
                        {order.description}
                      </p>

                      {/* Footer Info */}
                      <div className="space-y-2 text-xs text-gray-500">
                        <div className="flex items-center gap-2">
                          <MapPin className="w-3.5 h-3.5 text-gray-400" />
                          <span className="truncate">{order.location}</span>
                        </div>

                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Clock className="w-3.5 h-3.5 text-gray-400" />
                            <span>{order.estimated_duration}h</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Calendar className="w-3.5 h-3.5 text-gray-400" />
                            <span>{formatDate(order.created_at)}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
