"use client"

import type React from "react"
import { Bell, User, LogOut } from "lucide-react"
import { useAuth } from "../contexts/AuthContext"
import { useWebSocket } from "../contexts/WebSocketContext"

export const Header: React.FC = () => {
  const { user, logout } = useAuth()
  const { alerts, isConnected } = useWebSocket()

  const unreadAlerts = alerts.filter((alert) => !alert.read).length

  return (
    <header className="bg-white border-b border-slate-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold text-slate-800">SADAE</h1>
          <div className="flex items-center space-x-2">
            
            <span className="text-sm text-slate-600">{isConnected ? "" : ""}</span>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          {/* Notifications */}
          <div className="relative">
            
          </div>

          {/* User menu */}
          <div className="flex items-center space-x-3">
            <div className="text-right">
              <p className="text-sm font-medium text-slate-800">{user?.full_name}</p>
              <p className="text-xs text-slate-600 capitalize">{user?.role?.replace("_", " ")}</p>
            </div>
            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-white" />
            </div>
            <button
              onClick={logout}
              className="p-2 text-slate-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              title="Sair"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}
