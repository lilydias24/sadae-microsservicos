"use client"

import React, { useState, useEffect } from "react"
import { useAuth } from "../contexts/AuthContext"
import { useMutation, useQuery } from "@tanstack/react-query"
import { api } from "../services/api"
import { 
  User, 
  Mail, 
  Phone, 
  MapPin, 
  Shield, 
  Key, 
  Bell, 
  Save, 
  Edit, 
  X, 
  CheckCircle,
  AlertCircle,
  Calendar,
  Lock,
  Eye,
  EyeOff,
  Activity,
  FileText,
  MessageSquare
} from "lucide-react"

export function ProfilePage() {
  const { user, updateUser } = useAuth()
  const [activeTab, setActiveTab] = useState<"profile" | "security" | "notifications" | "activity">("profile")
  const [isEditing, setIsEditing] = useState(false)
  const [showPassword, setShowPassword] = useState({
    current: false,
    new: false,
    confirm: false
  })
  
  const [profileData, setProfileData] = useState({
    full_name: "",
    email: "",
    phone: "",
    address: "",
  })

  const [passwordData, setPasswordData] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  })

  const [notifications, setNotifications] = useState({
    email_alerts: true,
    sms_alerts: false,
    system_notifications: true,
    maintenance_updates: true,
    billing_notifications: true,
    ticket_updates: true,
  })

  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

  // Load user data when component mounts or user changes
  useEffect(() => {
    if (user) {
      setProfileData({
        full_name: user.full_name || "",
        email: user.email || "",
        phone: user.phone || "",
        address: user.address || "",
      })
    }
  }, [user])

  // Fetch current user info
  const { data: currentUserInfo, refetch: refetchUser } = useQuery({
    queryKey: ['currentUser'],
    queryFn: async () => {
      const { data } = await api.get('/auth/me')
      return data
    },
    enabled: !!user,
  })

  // Update profile mutation
  const updateProfileMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.put('/auth/me', {
        name: data.full_name,
        email: data.email,
      })
      return response.data
    },
    onSuccess: (response) => {
      // Update local user state
      const updatedUser = {
        ...user!,
        full_name: response.name || profileData.full_name,
        email: response.email || profileData.email,
        phone: profileData.phone,
        address: profileData.address,
      }
      updateUser(updatedUser)
      setIsEditing(false)
      setValidationErrors({})
      refetchUser()
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || "Erro ao atualizar perfil"
      setValidationErrors({ submit: message })
    },
  })

  // Change password mutation
  const changePasswordMutation = useMutation({
    mutationFn: async (data: any) => {
      return await api.put('/auth/me', {
        password: data.new_password,
      })
    },
    onSuccess: () => {
      setPasswordData({
        current_password: "",
        new_password: "",
        confirm_password: "",
      })
      setValidationErrors({})
      setShowPassword({ current: false, new: false, confirm: false })
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || "Erro ao alterar senha"
      setValidationErrors({ password: message })
    },
  })

  // Update notifications mutation (mock - would need backend endpoint)
  const updateNotificationsMutation = useMutation({
    mutationFn: async (data: any) => {
      // Mock endpoint - would need actual backend implementation
      return new Promise((resolve) => {
        setTimeout(() => resolve({ data }), 500)
      })
    },
    onSuccess: () => {
      // Save to localStorage as fallback
      localStorage.setItem('notification_preferences', JSON.stringify(notifications))
    },
  })

  const validateProfile = () => {
    const errors: Record<string, string> = {}
    
    if (!profileData.full_name.trim()) {
      errors.full_name = "Nome completo é obrigatório"
    }
    
    if (!profileData.email.trim()) {
      errors.email = "Email é obrigatório"
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(profileData.email)) {
      errors.email = "Email inválido"
    }
    
    if (profileData.phone && !/^[\d\s\(\)\-\+]+$/.test(profileData.phone)) {
      errors.phone = "Telefone inválido"
    }
    
    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const validatePassword = () => {
    const errors: Record<string, string> = {}
    
    if (!passwordData.current_password) {
      errors.current_password = "Senha atual é obrigatória"
    }
    
    if (!passwordData.new_password) {
      errors.new_password = "Nova senha é obrigatória"
    } else if (passwordData.new_password.length < 6) {
      errors.new_password = "Senha deve ter pelo menos 6 caracteres"
    }
    
    if (passwordData.new_password !== passwordData.confirm_password) {
      errors.confirm_password = "As senhas não coincidem"
    }
    
    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleProfileSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (validateProfile()) {
      updateProfileMutation.mutate(profileData)
    }
  }

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (validatePassword()) {
      changePasswordMutation.mutate(passwordData)
    }
  }

  const handleNotificationsSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    updateNotificationsMutation.mutate(notifications)
  }

  const getRoleLabel = (role: string) => {
    const roles: Record<string, string> = {
      citizen: "Cidadão",
      operator: "Operador",
      maintenance_manager: "Gestor de Manutenção",
      financial_manager: "Gestor Financeiro",
      crisis_manager: "Gestor de Crise",
      support_agent: "Atendente de Suporte",
      admin: "Administrador",
    }
    return roles[role] || role
  }

  const getRoleColor = (role: string) => {
    const colors: Record<string, string> = {
      citizen: "bg-blue-100 text-blue-800",
      operator: "bg-green-100 text-green-800",
      maintenance_manager: "bg-orange-100 text-orange-800",
      financial_manager: "bg-purple-100 text-purple-800",
      crisis_manager: "bg-red-100 text-red-800",
      support_agent: "bg-indigo-100 text-indigo-800",
      admin: "bg-gray-100 text-gray-800",
    }
    return colors[role] || "bg-gray-100 text-gray-800"
  }

  // Mock activity data
  const activityData = [
    { id: 1, type: "login", description: "Login realizado", timestamp: new Date().toISOString() },
    { id: 2, type: "ticket", description: "Ticket criado", timestamp: new Date(Date.now() - 86400000).toISOString() },
    { id: 3, type: "profile", description: "Perfil atualizado", timestamp: new Date(Date.now() - 172800000).toISOString() },
  ]

  return (
    <div className="space-y-6">
      {/* Header with User Info */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-6">
          <div className="w-20 h-20 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-full flex items-center justify-center shadow-lg">
            <User className="w-10 h-10 text-white" />
          </div>
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-gray-900">{user?.full_name || "Usuário"}</h1>
            <p className="text-gray-600 mt-1">{user?.email}</p>
            <div className="flex items-center space-x-3 mt-3">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRoleColor(user?.role || "")}`}>
                {getRoleLabel(user?.role || "")}
              </span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                user?.is_active ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
              }`}>
                {user?.is_active ? "Ativo" : "Inativo"}
              </span>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-500">Membro desde</div>
            <div className="text-sm font-medium text-gray-900">
              {currentUserInfo?.created_at 
                ? new Date(currentUserInfo.created_at).toLocaleDateString('pt-BR')
                : "N/A"}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 bg-white rounded-t-lg">
        <nav className="flex space-x-8 px-6" aria-label="Tabs">
          {[
            { id: "profile", name: "Perfil", icon: User },
            { id: "security", name: "Segurança", icon: Shield },
            { id: "notifications", name: "Notificações", icon: Bell },
            { id: "activity", name: "Atividade", icon: Activity },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 transition-colors ${
                activeTab === tab.id
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              <tab.icon className="w-4 h-4" />
              <span>{tab.name}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Profile Tab */}
      {activeTab === "profile" && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Informações Pessoais</h3>
            {!isEditing && (
              <button
                onClick={() => setIsEditing(true)}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2 transition-colors"
              >
                <Edit className="w-4 h-4" />
                <span>Editar</span>
              </button>
            )}
          </div>

          {validationErrors.submit && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2 text-red-800">
              <AlertCircle className="w-5 h-5" />
              <span className="text-sm">{validationErrors.submit}</span>
            </div>
          )}

          <form onSubmit={handleProfileSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <User className="w-4 h-4 inline mr-2" />
                  Nome Completo
                </label>
                <input
                  type="text"
                  disabled={!isEditing}
                  value={profileData.full_name}
                  onChange={(e) => {
                    setProfileData((prev) => ({ ...prev, full_name: e.target.value }))
                    if (validationErrors.full_name) {
                      setValidationErrors((prev) => ({ ...prev, full_name: "" }))
                    }
                  }}
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 ${
                    validationErrors.full_name ? "border-red-300" : "border-gray-300"
                  }`}
                />
                {validationErrors.full_name && (
                  <p className="mt-1 text-sm text-red-600">{validationErrors.full_name}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Mail className="w-4 h-4 inline mr-2" />
                  Email
                </label>
                <input
                  type="email"
                  disabled={!isEditing}
                  value={profileData.email}
                  onChange={(e) => {
                    setProfileData((prev) => ({ ...prev, email: e.target.value }))
                    if (validationErrors.email) {
                      setValidationErrors((prev) => ({ ...prev, email: "" }))
                    }
                  }}
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 ${
                    validationErrors.email ? "border-red-300" : "border-gray-300"
                  }`}
                />
                {validationErrors.email && (
                  <p className="mt-1 text-sm text-red-600">{validationErrors.email}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Phone className="w-4 h-4 inline mr-2" />
                  Telefone
                </label>
                <input
                  type="tel"
                  disabled={!isEditing}
                  value={profileData.phone}
                  onChange={(e) => {
                    setProfileData((prev) => ({ ...prev, phone: e.target.value }))
                    if (validationErrors.phone) {
                      setValidationErrors((prev) => ({ ...prev, phone: "" }))
                    }
                  }}
                  placeholder="(11) 99999-9999"
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 ${
                    validationErrors.phone ? "border-red-300" : "border-gray-300"
                  }`}
                />
                {validationErrors.phone && (
                  <p className="mt-1 text-sm text-red-600">{validationErrors.phone}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Shield className="w-4 h-4 inline mr-2" />
                  Tipo de Usuário
                </label>
                <input
                  type="text"
                  disabled
                  value={getRoleLabel(user?.role || "")}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg bg-gray-50"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <MapPin className="w-4 h-4 inline mr-2" />
                Endereço
              </label>
              <input
                type="text"
                disabled={!isEditing}
                value={profileData.address}
                onChange={(e) => setProfileData((prev) => ({ ...prev, address: e.target.value }))}
                placeholder="Rua, número, bairro, cidade"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
              />
            </div>

            {isEditing && (
              <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
                <button
                  type="button"
                  onClick={() => {
                    setIsEditing(false)
                    setValidationErrors({})
                    if (user) {
                      setProfileData({
                        full_name: user.full_name || "",
                        email: user.email || "",
                        phone: user.phone || "",
                        address: user.address || "",
                      })
                    }
                  }}
                  className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center space-x-2"
                >
                  <X className="w-4 h-4" />
                  <span>Cancelar</span>
                </button>
                <button
                  type="submit"
                  disabled={updateProfileMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
                >
                  <Save className="w-4 h-4" />
                  <span>{updateProfileMutation.isPending ? "Salvando..." : "Salvar Alterações"}</span>
                </button>
              </div>
            )}
          </form>
        </div>
      )}

      {/* Security Tab */}
      {activeTab === "security" && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center space-x-2">
            <Lock className="w-5 h-5" />
            <span>Alterar Senha</span>
          </h3>

          {validationErrors.password && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2 text-red-800">
              <AlertCircle className="w-5 h-5" />
              <span className="text-sm">{validationErrors.password}</span>
            </div>
          )}

          <form onSubmit={handlePasswordSubmit} className="space-y-6 max-w-2xl">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Key className="w-4 h-4 inline mr-2" />
                Senha Atual
              </label>
              <div className="relative">
                <input
                  type={showPassword.current ? "text" : "password"}
                  required
                  value={passwordData.current_password}
                  onChange={(e) => {
                    setPasswordData((prev) => ({ ...prev, current_password: e.target.value }))
                    if (validationErrors.current_password) {
                      setValidationErrors((prev) => ({ ...prev, current_password: "" }))
                    }
                  }}
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 pr-10 ${
                    validationErrors.current_password ? "border-red-300" : "border-gray-300"
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => ({ ...prev, current: !prev.current }))}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                >
                  {showPassword.current ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {validationErrors.current_password && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.current_password}</p>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Nova Senha</label>
                <div className="relative">
                  <input
                    type={showPassword.new ? "text" : "password"}
                    required
                    value={passwordData.new_password}
                    onChange={(e) => {
                      setPasswordData((prev) => ({ ...prev, new_password: e.target.value }))
                      if (validationErrors.new_password) {
                        setValidationErrors((prev) => ({ ...prev, new_password: "" }))
                      }
                    }}
                    className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 pr-10 ${
                      validationErrors.new_password ? "border-red-300" : "border-gray-300"
                    }`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((prev) => ({ ...prev, new: !prev.new }))}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  >
                    {showPassword.new ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
                {validationErrors.new_password && (
                  <p className="mt-1 text-sm text-red-600">{validationErrors.new_password}</p>
                )}
                <p className="mt-1 text-xs text-gray-500">Mínimo de 6 caracteres</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Confirmar Nova Senha</label>
                <div className="relative">
                  <input
                    type={showPassword.confirm ? "text" : "password"}
                    required
                    value={passwordData.confirm_password}
                    onChange={(e) => {
                      setPasswordData((prev) => ({ ...prev, confirm_password: e.target.value }))
                      if (validationErrors.confirm_password) {
                        setValidationErrors((prev) => ({ ...prev, confirm_password: "" }))
                      }
                    }}
                    className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 pr-10 ${
                      validationErrors.confirm_password ? "border-red-300" : "border-gray-300"
                    }`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((prev) => ({ ...prev, confirm: !prev.confirm }))}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  >
                    {showPassword.confirm ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
                {validationErrors.confirm_password && (
                  <p className="mt-1 text-sm text-red-600">{validationErrors.confirm_password}</p>
                )}
              </div>
            </div>

            <button
              type="submit"
              disabled={changePasswordMutation.isPending}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
            >
              <Lock className="w-4 h-4" />
              <span>{changePasswordMutation.isPending ? "Alterando..." : "Alterar Senha"}</span>
            </button>
          </form>
        </div>
      )}

      {/* Notifications Tab */}
      {activeTab === "notifications" && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center space-x-2">
            <Bell className="w-5 h-5" />
            <span>Preferências de Notificação</span>
          </h3>

          <form onSubmit={handleNotificationsSubmit} className="space-y-6">
            <div className="space-y-4">
              {[
                {
                  key: "email_alerts",
                  title: "Alertas por Email",
                  description: "Receber alertas importantes por email",
                  icon: Mail,
                },
                {
                  key: "sms_alerts",
                  title: "Alertas por SMS",
                  description: "Receber alertas críticos por SMS",
                  icon: Phone,
                },
                {
                  key: "system_notifications",
                  title: "Notificações do Sistema",
                  description: "Notificações gerais do sistema",
                  icon: Bell,
                },
                {
                  key: "maintenance_updates",
                  title: "Atualizações de Manutenção",
                  description: "Informações sobre manutenções programadas",
                  icon: Activity,
                },
                {
                  key: "billing_notifications",
                  title: "Notificações de Faturamento",
                  description: "Alertas sobre faturas e pagamentos",
                  icon: FileText,
                },
                {
                  key: "ticket_updates",
                  title: "Atualizações de Tickets",
                  description: "Notificações sobre seus tickets de suporte",
                  icon: MessageSquare,
                },
              ].map((item) => (
                <div key={item.key} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="flex items-center space-x-4">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                      <item.icon className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">{item.title}</h4>
                      <p className="text-sm text-gray-600">{item.description}</p>
                    </div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notifications[item.key as keyof typeof notifications] as boolean}
                      onChange={(e) =>
                        setNotifications((prev) => ({
                          ...prev,
                          [item.key]: e.target.checked,
                        }))
                      }
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              ))}
            </div>

            <div className="flex justify-end pt-4 border-t border-gray-200">
              <button
                type="submit"
                disabled={updateNotificationsMutation.isPending}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
              >
                <Save className="w-4 h-4" />
                <span>{updateNotificationsMutation.isPending ? "Salvando..." : "Salvar Preferências"}</span>
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Activity Tab */}
      {activeTab === "activity" && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center space-x-2">
            <Activity className="w-5 h-5" />
            <span>Histórico de Atividade</span>
          </h3>

          <div className="space-y-4">
            {activityData.map((activity) => (
              <div
                key={activity.id}
                className="flex items-start space-x-4 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                  {activity.type === "login" && <Lock className="w-5 h-5 text-blue-600" />}
                  {activity.type === "ticket" && <MessageSquare className="w-5 h-5 text-blue-600" />}
                  {activity.type === "profile" && <User className="w-5 h-5 text-blue-600" />}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{activity.description}</p>
                  <p className="text-xs text-gray-500 mt-1 flex items-center space-x-1">
                    <Calendar className="w-3 h-3" />
                    <span>
                      {new Date(activity.timestamp).toLocaleString("pt-BR", {
                        day: "2-digit",
                        month: "2-digit",
                        year: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </p>
                </div>
                <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
