"use client"

import React, { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { api } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import { 
  FileText, 
  Download, 
  Calendar, 
  Filter, 
  BarChart3, 
  TrendingUp,
  Activity,
  Wrench,
  CreditCard,
  MessageSquare,
  Loader2,
  CheckCircle,
  AlertCircle
} from 'lucide-react'

interface ReportType {
  id: string
  name: string
  description: string
  icon: any
  roles: string[]
}

export function ReportsPage() {
  const { user } = useAuth()
  const [selectedReportType, setSelectedReportType] = useState<string | null>(null)
  const [reportFilters, setReportFilters] = useState({
    start_date: '',
    end_date: '',
    sensor_type: '',
    sensor_id: '',
    location: '',
    status: '',
    customer_id: '',
    category: ''
  })

  const reportTypes: ReportType[] = [
    {
      id: 'monitoring',
      name: 'Monitoramento de Sensores',
      description: 'Relatórios de leituras de sensores, anomalias e dados de monitoramento',
      icon: Activity,
      roles: ['operator', 'crisis_manager']
    },
    {
      id: 'maintenance',
      name: 'Manutenção e Intervenções',
      description: 'Relatórios de ordens de serviço, manutenções e intervenções',
      icon: Wrench,
      roles: ['maintenance_manager', 'operator']
    },
    {
      id: 'billing',
      name: 'Faturamento',
      description: 'Relatórios de faturas, pagamentos e análise financeira',
      icon: CreditCard,
      roles: ['financial_manager', 'operator']
    },
    {
      id: 'support',
      name: 'Atendimento ao Cliente',
      description: 'Relatórios de tickets, satisfação e métricas de atendimento',
      icon: MessageSquare,
      roles: ['operator', 'support_agent']
    }
  ]

  // Filtro de tipos de relatório baseado no papel do usuário
  const availableReports = reportTypes.filter(report => 
    report.roles.includes('all') || (user?.role && report.roles.includes(user.role))
  )

  // Mutation para gerar relatório de monitoramento
  const generateMonitoringReport = useMutation({
    mutationFn: async (filters: any) => {
      const { data } = await api.post('/monitoring/reports/generate', filters)
      return data
    },
    onSuccess: (data) => {
      alert(`Relatório gerado com sucesso! ID: ${data.report_id}`)
    },
    onError: (error: any) => {
      alert(`Erro ao gerar relatório: ${error.response?.data?.detail || error.message}`)
    }
  })

  // Mutation para gerar relatório de manutenção
  const generateMaintenanceReport = useMutation({
    mutationFn: async (filters: any) => {
      const { data } = await api.post('/maintenance/reports/interventions', filters)
      return data
    },
    onSuccess: (data) => {
      alert('Relatório de manutenção gerado com sucesso!')
    },
    onError: (error: any) => {
      alert(`Erro ao gerar relatório: ${error.response?.data?.detail || error.message}`)
    }
  })

  const handleGenerateReport = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!selectedReportType) {
      alert('Por favor, selecione um tipo de relatório')
      return
    }

    const filters: any = {}
    
    if (reportFilters.start_date) {
      filters.start_date = new Date(reportFilters.start_date).toISOString()
    }
    if (reportFilters.end_date) {
      filters.end_date = new Date(reportFilters.end_date).toISOString()
    }
    if (reportFilters.sensor_type) filters.sensor_type = reportFilters.sensor_type
    if (reportFilters.sensor_id) filters.sensor_id = parseInt(reportFilters.sensor_id)
    if (reportFilters.location) filters.location = reportFilters.location
    if (reportFilters.status) filters.status = reportFilters.status
    if (reportFilters.customer_id) filters.customer_id = parseInt(reportFilters.customer_id)
    if (reportFilters.category) filters.category = reportFilters.category

    try {
      if (selectedReportType === 'monitoring') {
        await generateMonitoringReport.mutateAsync(filters)
      } else if (selectedReportType === 'maintenance') {
        await generateMaintenanceReport.mutateAsync(filters)
      } else {
        alert('Tipo de relatório ainda não implementado')
      }
    } catch (error) {
      console.error('Erro ao gerar relatório:', error)
    }
  }

  const getDefaultDateRange = () => {
    const end = new Date()
    const start = new Date()
    start.setMonth(start.getMonth() - 1)
    
    return {
      start: start.toISOString().split('T')[0],
      end: end.toISOString().split('T')[0]
    }
  }

  React.useEffect(() => {
    const { start, end } = getDefaultDateRange()
    setReportFilters(prev => ({
      ...prev,
      start_date: start,
      end_date: end
    }))
  }, [])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Relatórios</h1>
          <p className="text-gray-600 mt-1">Gere relatórios detalhados do sistema</p>
        </div>
      </div>

      {/* Report Types */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {availableReports.map((report) => {
          const Icon = report.icon
          const isSelected = selectedReportType === report.id
          
          return (
            <button
              key={report.id}
              onClick={() => setSelectedReportType(report.id)}
              className={`p-6 rounded-lg border-2 transition-all text-left ${
                isSelected
                  ? 'border-blue-500 bg-blue-50 shadow-md'
                  : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow'
              }`}
            >
              <div className="flex items-start space-x-4">
                <div className={`p-3 rounded-lg ${isSelected ? 'bg-blue-600' : 'bg-gray-100'}`}>
                  <Icon className={`w-6 h-6 ${isSelected ? 'text-white' : 'text-gray-600'}`} />
                </div>
                <div className="flex-1">
                  <h3 className={`font-semibold text-lg mb-1 ${isSelected ? 'text-blue-900' : 'text-gray-900'}`}>
                    {report.name}
                  </h3>
                  <p className={`text-sm ${isSelected ? 'text-blue-700' : 'text-gray-600'}`}>
                    {report.description}
                  </p>
                </div>
                {isSelected && (
                  <CheckCircle className="w-5 h-5 text-blue-600 flex-shrink-0" />
                )}
              </div>
            </button>
          )
        })}
      </div>

      {/* Report Form */}
      {selectedReportType && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center space-x-3 mb-6">
            <Filter className="w-5 h-5 text-gray-600" />
            <h2 className="text-xl font-semibold text-gray-900">Filtros do Relatório</h2>
          </div>

          <form onSubmit={handleGenerateReport} className="space-y-6">
            {/* Date Range */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Calendar className="w-4 h-4 inline mr-2" />
                  Data Inicial
                </label>
                <input
                  type="date"
                  value={reportFilters.start_date}
                  onChange={(e) => setReportFilters(prev => ({ ...prev, start_date: e.target.value }))}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Calendar className="w-4 h-4 inline mr-2" />
                  Data Final
                </label>
                <input
                  type="date"
                  value={reportFilters.end_date}
                  onChange={(e) => setReportFilters(prev => ({ ...prev, end_date: e.target.value }))}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
            </div>

            {/* Monitoring-specific filters */}
            {selectedReportType === 'monitoring' && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tipo de Sensor
                  </label>
                  <select
                    value={reportFilters.sensor_type}
                    onChange={(e) => setReportFilters(prev => ({ ...prev, sensor_type: e.target.value }))}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Todos os tipos</option>
                    <option value="flow">Fluxo</option>
                    <option value="pressure">Pressão</option>
                    <option value="quality">Qualidade</option>
                    <option value="level">Nível</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    ID do Sensor
                  </label>
                  <input
                    type="number"
                    value={reportFilters.sensor_id}
                    onChange={(e) => setReportFilters(prev => ({ ...prev, sensor_id: e.target.value }))}
                    placeholder="Opcional"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Localização
                  </label>
                  <input
                    type="text"
                    value={reportFilters.location}
                    onChange={(e) => setReportFilters(prev => ({ ...prev, location: e.target.value }))}
                    placeholder="Filtrar por localização"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            )}

            {/* Maintenance-specific filters */}
            {selectedReportType === 'maintenance' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Status
                  </label>
                  <select
                    value={reportFilters.status}
                    onChange={(e) => setReportFilters(prev => ({ ...prev, status: e.target.value }))}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Todos os status</option>
                    <option value="pending">Pendente</option>
                    <option value="in_progress">Em Andamento</option>
                    <option value="completed">Concluído</option>
                    <option value="cancelled">Cancelado</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Categoria
                  </label>
                  <select
                    value={reportFilters.category}
                    onChange={(e) => setReportFilters(prev => ({ ...prev, category: e.target.value }))}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Todas as categorias</option>
                    <option value="preventive">Preventiva</option>
                    <option value="corrective">Corretiva</option>
                    <option value="emergency">Emergência</option>
                  </select>
                </div>
              </div>
            )}

            {/* Billing-specific filters */}
            {selectedReportType === 'billing' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Status
                  </label>
                  <select
                    value={reportFilters.status}
                    onChange={(e) => setReportFilters(prev => ({ ...prev, status: e.target.value }))}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Todos os status</option>
                    <option value="pending">Pendente</option>
                    <option value="paid">Pago</option>
                    <option value="overdue">Vencido</option>
                    <option value="contested">Contestado</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    ID do Cliente
                  </label>
                  <input
                    type="number"
                    value={reportFilters.customer_id}
                    onChange={(e) => setReportFilters(prev => ({ ...prev, customer_id: e.target.value }))}
                    placeholder="Opcional - Filtrar por cliente"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            )}

            {/* Support-specific filters */}
            {selectedReportType === 'support' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Status
                  </label>
                  <select
                    value={reportFilters.status}
                    onChange={(e) => setReportFilters(prev => ({ ...prev, status: e.target.value }))}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Todos os status</option>
                    <option value="open">Aberto</option>
                    <option value="in_progress">Em Andamento</option>
                    <option value="resolved">Resolvido</option>
                    <option value="closed">Fechado</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Categoria
                  </label>
                  <select
                    value={reportFilters.category}
                    onChange={(e) => setReportFilters(prev => ({ ...prev, category: e.target.value }))}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Todas as categorias</option>
                    <option value="billing">Faturamento</option>
                    <option value="technical">Técnico</option>
                    <option value="complaint">Reclamação</option>
                    <option value="request">Solicitação</option>
                    <option value="information">Informação</option>
                    <option value="emergency">Emergência</option>
                  </select>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
              <button
                type="button"
                onClick={() => {
                  setSelectedReportType(null)
                  const { start, end } = getDefaultDateRange()
                  setReportFilters({
                    start_date: start,
                    end_date: end,
                    sensor_type: '',
                    sensor_id: '',
                    location: '',
                    status: '',
                    customer_id: '',
                    category: ''
                  })
                }}
                className="px-6 py-3 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={
                  generateMonitoringReport.isPending || 
                  generateMaintenanceReport.isPending ||
                  !reportFilters.start_date ||
                  !reportFilters.end_date
                }
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {(generateMonitoringReport.isPending || generateMaintenanceReport.isPending) ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Gerando...</span>
                  </>
                ) : (
                  <>
                    <Download className="w-5 h-5" />
                    <span>Gerar Relatório</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Info Section */}
      {!selectedReportType && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-blue-900 mb-2">Como usar</h3>
              <p className="text-blue-800 text-sm mb-2">
                Selecione um tipo de relatório acima para começar. Os relatórios são gerados com base nos filtros que você definir.
              </p>
              <ul className="text-blue-800 text-sm list-disc list-inside space-y-1">
                <li>Defina o período de análise (data inicial e final)</li>
                <li>Ajuste os filtros específicos para cada tipo de relatório</li>
                <li>Clique em "Gerar Relatório" para criar o documento</li>
                <li>Os relatórios podem ser exportados em PDF ou CSV</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

