"use client"

import type React from "react"
import { NavLink } from "react-router-dom"
import { LayoutDashboard, Activity, Wrench, CreditCard, AlertTriangle, MessageSquare, FileText, User, Droplets } from "lucide-react"
import { useAuth } from "../contexts/AuthContext"

const navigation = [
  { name: "Painel", href: "/dashboard", icon: LayoutDashboard, roles: ["all"] },
  { name: "Monitoramento", href: "/monitoring", icon: Activity, roles: ["operator", "crisis_manager"] },
  { name: "Manutenção", href: "/maintenance", icon: Wrench, roles: ["maintenance_manager", "operator"] },
  { name: "Faturamento", href: "/billing", icon: CreditCard, roles: ["all"] },
  { name: "Gestão de Crises", href: "/crisis", icon: AlertTriangle, roles: ["crisis_manager"] },
  { name: "Atendimento", href: "/support", icon: MessageSquare, roles: ["all"] },
  {
    name: "Relatórios",
    href: "/reports",
    icon: FileText,
    roles: ["operator", "maintenance_manager", "financial_manager", "crisis_manager"],
  },
  { name: "Perfil", href: "/profile", icon: User, roles: ["all"] },
]

export const Sidebar: React.FC = () => {
  const { user } = useAuth()

  const hasAccess = (roles: string[]) => {
    if (roles.includes("all")) return true
    return user?.role && roles.includes(user.role)
  }

  return (
    <div className="w-64 bg-white border-r border-slate-200 flex flex-col">
      <div className="p-6 border-b border-slate-200">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
            <Droplets className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-800">SADAE</h2>
            <p className="text-xs text-slate-600">Sistema de Abastecimento</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-2">
        {navigation.map((item) => {
          if (!hasAccess(item.roles)) return null

          return (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                `flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive ? "bg-blue-50 text-blue-700 border-r-2 border-blue-700" : "text-slate-700 hover:bg-slate-100"
                }`
              }
            >
              <item.icon className="w-5 h-5" />
              <span>{item.name}</span>
            </NavLink>
          )
        })}
      </nav>

      <div className="p-4 border-t border-slate-200">
        <div className="text-xs text-slate-500 text-center">SADAE v1.0.0</div>
      </div>
    </div>
  )
}
