"use client"

import React, { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import jsPDF from 'jspdf'
import { formatDate } from '../utils/cn'
import { 
  Download, 
  Calendar, 
  Filter, 
  Activity,
  Wrench,
  CreditCard,
  MessageSquare,
  Loader2,
  CheckCircle,
  AlertCircle,
  X,
  FileText
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
  const [generatedReport, setGeneratedReport] = useState<any>(null)
  const [showReportModal, setShowReportModal] = useState(false)

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
      setGeneratedReport(data)
      setShowReportModal(true)
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
      setGeneratedReport(data)
      setShowReportModal(true)
    },
    onError: (error: any) => {
      alert(`Erro ao gerar relatório: ${error.response?.data?.detail || error.message}`)
    }
  })

  // Mutation para gerar relatório de faturamento
  const generateBillingReport = useMutation({
    mutationFn: async (filters: any) => {
      const { data } = await api.post('/billing/reports/billing', filters)
      return data
    },
    onSuccess: (data) => {
      setGeneratedReport(data)
      setShowReportModal(true)
    },
    onError: (error: any) => {
      alert(`Erro ao gerar relatório: ${error.response?.data?.detail || error.message}`)
    }
  })

  // Mutation para gerar relatório de atendimento
  const generateSupportReport = useMutation({
    mutationFn: async (filters: any) => {
      const { data } = await api.post('/support/reports/support', filters)
      return data
    },
    onSuccess: (data) => {
      setGeneratedReport(data)
      setShowReportModal(true)
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
      } else if (selectedReportType === 'billing') {
        await generateBillingReport.mutateAsync(filters)
      } else if (selectedReportType === 'support') {
        await generateSupportReport.mutateAsync(filters)
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

  const downloadReport = () => {
    if (!generatedReport) return
    
    const dataStr = JSON.stringify(generatedReport, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `relatorio-${generatedReport.report_id || 'report'}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const downloadReportPDF = () => {
    if (!generatedReport) return

    const doc = new jsPDF()
    const pageWidth = doc.internal.pageSize.getWidth()
    const pageHeight = doc.internal.pageSize.getHeight()
    const margin = 20
    let yPosition = margin
    const lineHeight = 7
    const maxWidth = pageWidth - (margin * 2)

    // Helper function to add new page if needed
    const checkNewPage = (requiredSpace: number) => {
      if (yPosition + requiredSpace > pageHeight - margin) {
        doc.addPage()
        yPosition = margin
        return true
      }
      return false
    }

    // Helper function to add text with word wrap
    const addText = (text: string, fontSize: number = 10, isBold: boolean = false, color: number[] = [0, 0, 0], xOffset: number = 0) => {
      doc.setFontSize(fontSize)
      doc.setTextColor(color[0], color[1], color[2])
      if (isBold) {
        doc.setFont('helvetica', 'bold')
      } else {
        doc.setFont('helvetica', 'normal')
      }
      
      const lines = doc.splitTextToSize(text, maxWidth - xOffset)
      lines.forEach((line: string) => {
        checkNewPage(lineHeight)
        doc.text(line, margin + xOffset, yPosition)
        yPosition += lineHeight
      })
    }

    // Helper to add section title
    const addSectionTitle = (title: string) => {
      yPosition += 5
      checkNewPage(15)
      doc.setFillColor(37, 99, 235)
      doc.rect(margin, yPosition - 3, pageWidth - (margin * 2), 8, 'F')
      doc.setTextColor(255, 255, 255)
      doc.setFontSize(12)
      doc.setFont('helvetica', 'bold')
      doc.text(title, margin + 5, yPosition + 4)
      yPosition += 10
      doc.setTextColor(0, 0, 0)
    }

    // Header with gradient effect
    doc.setFillColor(37, 99, 235) // Blue
    doc.rect(0, 0, pageWidth, 45, 'F')
    doc.setTextColor(255, 255, 255)
    doc.setFontSize(22)
    doc.setFont('helvetica', 'bold')
    doc.text('SADAE', pageWidth / 2, 18, { align: 'center' })
    doc.setFontSize(12)
    doc.text('Sistema de Análise de Dados de Abastecimento e Esgoto', pageWidth / 2, 28, { align: 'center' })
    doc.setFontSize(14)
    doc.setFont('helvetica', 'bold')
    doc.text('RELATÓRIO GERADO', pageWidth / 2, 38, { align: 'center' })
    
    yPosition = 55
    doc.setTextColor(0, 0, 0)

    // Report ID and Info Box
    doc.setDrawColor(37, 99, 235)
    doc.setLineWidth(0.5)
    doc.rect(margin, yPosition, pageWidth - (margin * 2), 20, 'S')
    yPosition += 6
    
    doc.setFontSize(11)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(37, 99, 235)
    doc.text('ID do Relatório:', margin + 5, yPosition)
    doc.setFont('helvetica', 'normal')
    doc.setTextColor(0, 0, 0)
    doc.text(generatedReport.report_id || 'N/A', margin + 50, yPosition)
    yPosition += 6

    const generatedDate = generatedReport.generated_at 
      ? new Date(generatedReport.generated_at).toLocaleString('pt-BR', {
          day: '2-digit',
          month: 'long',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        })
      : new Date().toLocaleString('pt-BR', {
          day: '2-digit',
          month: 'long',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        })
    
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(100, 100, 100)
    doc.text('Gerado em:', margin + 5, yPosition)
    doc.setFont('helvetica', 'normal')
    doc.setTextColor(0, 0, 0)
    doc.text(generatedDate, margin + 50, yPosition)
    yPosition += 6

    if (generatedReport.generated_by) {
      doc.setFont('helvetica', 'bold')
      doc.setTextColor(100, 100, 100)
      doc.text('Gerado por:', margin + 5, yPosition)
      doc.setFont('helvetica', 'normal')
      doc.setTextColor(0, 0, 0)
      doc.text(generatedReport.generated_by, margin + 50, yPosition)
    }
    yPosition += 8

    // Summary Section
    if (generatedReport.summary) {
      addSectionTitle('RESUMO')
      
      // Create summary cards layout
      const summaryEntries = Object.entries(generatedReport.summary).filter(([key]) => key !== 'period')
      
      summaryEntries.forEach(([key, value]: [string, any], index: number) => {
        // Translate labels to Portuguese
        const labelMap: { [key: string]: string } = {
          'total_readings': 'Total de Leituras',
          'average_value': 'Valor Médio',
          'min_value': 'Valor Mínimo',
          'max_value': 'Valor Máximo',
          'total_interventions': 'Total de Intervenções',
          'total_cost': 'Custo Total',
          'average_repair_time': 'Tempo Médio de Reparo',
          'period': 'Período',
          'team_statistics': 'Estatísticas por Equipe',
          'total_bills': 'Total de Faturas',
          'total_amount': 'Valor Total',
          'total_consumption': 'Consumo Total',
          'average_amount': 'Valor Médio',
          'average_consumption': 'Consumo Médio',
          'paid_amount': 'Valor Pago',
          'unpaid_amount': 'Valor Não Pago',
          'status_breakdown': 'Distribuição por Status',
          'total_tickets': 'Total de Tickets',
          'resolved_tickets': 'Tickets Resolvidos',
          'open_tickets': 'Tickets Abertos',
          'average_resolution_time_hours': 'Tempo Médio de Resolução (horas)',
          'average_satisfaction_rating': 'Avaliação Média de Satisfação',
          'category_breakdown': 'Distribuição por Categoria'
        }
        const label = labelMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
        let displayValue = value
        
        if (typeof value === 'number') {
          if (key.includes('value') || key.includes('average') || key.includes('min') || key.includes('max')) {
            displayValue = value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
          } else {
            displayValue = value.toLocaleString('pt-BR')
          }
        } else if (typeof value === 'object' && value !== null) {
          displayValue = JSON.stringify(value)
        }
        
        // Draw card background
        const cardY = yPosition - 3
        doc.setFillColor(240, 247, 255) // Light blue
        doc.setDrawColor(200, 220, 255)
        doc.rect(margin, cardY, pageWidth - (margin * 2), 12, 'FD')
        
        doc.setFontSize(9)
        doc.setFont('helvetica', 'bold')
        doc.setTextColor(37, 99, 235)
        doc.text(label, margin + 5, yPosition + 3)
        
        doc.setFontSize(11)
        doc.setFont('helvetica', 'bold')
        doc.setTextColor(0, 0, 0)
        doc.text(String(displayValue), pageWidth - margin - 5, yPosition + 3, { align: 'right' })
        
        yPosition += 14
        checkNewPage(15)
      })
      
      // Period display
      if (generatedReport.summary.period) {
        yPosition += 3
        checkNewPage(20)
        doc.setFillColor(248, 250, 252) // Light gray
        doc.setDrawColor(200, 200, 200)
        doc.rect(margin, yPosition - 3, pageWidth - (margin * 2), 18, 'FD')
        
        doc.setFontSize(10)
        doc.setFont('helvetica', 'bold')
        doc.setTextColor(37, 99, 235)
        doc.text('Período de Análise', margin + 5, yPosition + 4)
        
        yPosition += 6
        doc.setFontSize(9)
        doc.setFont('helvetica', 'normal')
        doc.setTextColor(0, 0, 0)
        
        if (generatedReport.summary.period.start) {
          const startDate = new Date(generatedReport.summary.period.start).toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: 'long',
            year: 'numeric'
          })
          doc.text(`Início: ${startDate}`, margin + 5, yPosition + 3)
        }
        
        if (generatedReport.summary.period.end) {
          const endDate = new Date(generatedReport.summary.period.end).toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: 'long',
            year: 'numeric'
          })
          doc.text(`Fim: ${endDate}`, margin + 5, yPosition + 9)
        }
        
        yPosition += 12
      }
    }

    // Filters Section
    if (generatedReport.filters) {
      addSectionTitle('FILTROS APLICADOS')
      
      const filters = Object.entries(generatedReport.filters).filter(([_, value]) => 
        value !== null && value !== undefined && value !== ''
      )
      
      if (filters.length > 0) {
        doc.setFillColor(248, 250, 252)
        doc.setDrawColor(200, 200, 200)
        const filterBoxHeight = filters.length * 8 + 4
        doc.rect(margin, yPosition - 3, pageWidth - (margin * 2), filterBoxHeight, 'FD')
        
        filters.forEach(([key, value]: [string, any], index: number) => {
          // Translate filter labels to Portuguese
          const filterLabelMap: { [key: string]: string } = {
            'start_date': 'Data Inicial',
            'end_date': 'Data Final',
            'sensor_type': 'Tipo de Sensor',
            'sensor_id': 'ID do Sensor',
            'location': 'Localização',
            'status': 'Status',
            'team_name': 'Equipe',
            'category': 'Categoria'
          }
          const label = filterLabelMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
          let displayValue = value
          
          if (key.includes('date') || (typeof value === 'string' && value.includes('T'))) {
            try {
              displayValue = new Date(value).toLocaleDateString('pt-BR', {
                day: '2-digit',
                month: 'short',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              })
            } catch (e) {
              displayValue = String(value)
            }
          } else if (typeof value === 'object') {
            displayValue = JSON.stringify(value)
          }
          
          doc.setFontSize(9)
          doc.setFont('helvetica', 'bold')
          doc.setTextColor(100, 100, 100)
          doc.text(`${label}:`, margin + 5, yPosition + 3)
          doc.setFont('helvetica', 'normal')
          doc.setTextColor(0, 0, 0)
          doc.text(String(displayValue), margin + 60, yPosition + 3)
          yPosition += 8
        })
        
        yPosition += 3
      }
    }

    // Data Section
    const data = generatedReport.readings || generatedReport.interventions || generatedReport.bills || generatedReport.tickets || []
    if (data.length > 0) {
      addSectionTitle(`DADOS (${data.length} registros)`)

      // Limit to first 30 records for PDF (to avoid huge files)
      const recordsToShow = data.slice(0, 30)
      
      recordsToShow.forEach((record: any, index: number) => {
        checkNewPage(25)
        
        // Record header
        doc.setFillColor(240, 247, 255)
        doc.setDrawColor(200, 220, 255)
        doc.rect(margin, yPosition - 3, pageWidth - (margin * 2), 8, 'FD')
        
        doc.setFontSize(10)
        doc.setFont('helvetica', 'bold')
        doc.setTextColor(37, 99, 235)
        doc.text(`Registro ${index + 1}`, margin + 5, yPosition + 3)
        yPosition += 10
        
        // Record fields (limit to 5 most important fields)
        const entries = Object.entries(record).slice(0, 5)
        entries.forEach(([key, value]: [string, any]) => {
          // Translate field labels to Portuguese
          const fieldLabelMap: { [key: string]: string } = {
            'sensor_id': 'ID do Sensor',
            'sensor_type': 'Tipo de Sensor',
            'value': 'Valor',
            'unit': 'Unidade',
            'location': 'Localização',
            'timestamp': 'Data/Hora',
            'id': 'ID',
            'service_order_id': 'ID da Ordem de Serviço',
            'team_name': 'Equipe',
            'completed_at': 'Concluído em',
            'cost': 'Custo',
            'description': 'Descrição',
            'reading_id': 'ID da Leitura',
            'operator_id': 'ID do Operador',
            'operator_name': 'Nome do Operador',
            'observation_type': 'Tipo de Observação',
            'text': 'Texto',
            'created_at': 'Criado em',
            'updated_at': 'Atualizado em',
            'status': 'Status',
            'priority': 'Prioridade',
            'assigned_team': 'Equipe Atribuída',
            'repair_time': 'Tempo de Reparo',
            'material_cost': 'Custo de Material',
            'labor_cost': 'Custo de Mão de Obra',
            'customer_id': 'ID do Cliente',
            'meter_id': 'ID do Medidor',
            'amount': 'Valor',
            'consumption': 'Consumo',
            'billing_period_start': 'Início do Período',
            'billing_period_end': 'Fim do Período',
            'due_date': 'Data de Vencimento',
            'paid_at': 'Pago em',
            'ticket_number': 'Número do Ticket',
            'title': 'Título',
            'category': 'Categoria',
            'resolved_at': 'Resolvido em',
            'satisfaction_rating': 'Avaliação de Satisfação',
            'assigned_agent_id': 'ID do Agente Atribuído'
          }
          const label = fieldLabelMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
          let displayValue = value
          
          if (key.includes('date') || key.includes('timestamp') || key.includes('at') || 
              (typeof value === 'string' && value.includes('T'))) {
            try {
              displayValue = new Date(value).toLocaleString('pt-BR')
            } catch (e) {
              displayValue = String(value)
            }
          } else if (typeof value === 'number') {
            displayValue = value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
          } else if (typeof value === 'object' && value !== null) {
            displayValue = JSON.stringify(value)
          }
          
          doc.setFontSize(8)
          doc.setFont('helvetica', 'bold')
          doc.setTextColor(100, 100, 100)
          doc.text(`${label}:`, margin + 10, yPosition)
          doc.setFont('helvetica', 'normal')
          doc.setTextColor(0, 0, 0)
          const valueText = String(displayValue).substring(0, 60) // Limit length
          doc.text(valueText, margin + 50, yPosition)
          yPosition += 6
        })
        
        if (Object.keys(record).length > 5) {
          doc.setFontSize(7)
          doc.setTextColor(128, 128, 128)
          doc.text(`+ ${Object.keys(record).length - 5} campo(s) adicional(is)`, margin + 10, yPosition)
          yPosition += 5
        }
        
        yPosition += 3
      })

      if (data.length > 30) {
        yPosition += 3
        checkNewPage(10)
        doc.setFontSize(9)
        doc.setTextColor(128, 128, 128)
        doc.setFont('helvetica', 'italic')
        addText(`Nota: Exibindo apenas os primeiros 30 de ${data.length} registro(s). Consulte o arquivo JSON para todos os dados completos.`, 9, false, [128, 128, 128])
      }
    }

    // Footer on all pages
    const totalPages = (doc as any).internal.getNumberOfPages()
    for (let i = 1; i <= totalPages; i++) {
      doc.setPage(i)
      
      // Footer line
      doc.setDrawColor(200, 200, 200)
      doc.setLineWidth(0.5)
      doc.line(margin, pageHeight - 15, pageWidth - margin, pageHeight - 15)
      
      doc.setFontSize(8)
      doc.setTextColor(128, 128, 128)
      doc.setFont('helvetica', 'normal')
      doc.text(
        `Página ${i} de ${totalPages} | SADAE - Sistema de Análise de Dados`,
        pageWidth / 2,
        pageHeight - 10,
        { align: 'center' }
      )
    }

    // Save PDF
    doc.save(`relatorio-${generatedReport.report_id || 'report'}.pdf`)
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
                  generateBillingReport.isPending ||
                  generateSupportReport.isPending ||
                  !reportFilters.start_date ||
                  !reportFilters.end_date
                }
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {(generateMonitoringReport.isPending || 
                  generateMaintenanceReport.isPending ||
                  generateBillingReport.isPending ||
                  generateSupportReport.isPending) ? (
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
                <li>O relatório será exibido em um modal com resumo e dados completos</li>
                <li>Você pode baixar o relatório em formato PDF ou JSON</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Report Modal */}
      {showReportModal && generatedReport && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b">
              <div className="flex items-center space-x-3">
                <FileText className="w-6 h-6 text-blue-600" />
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Relatório Gerado</h2>
                  <p className="text-sm text-gray-600">ID: {generatedReport.report_id}</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={downloadReportPDF}
                  className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
                >
                  <FileText className="w-4 h-4" />
                  <span>Baixar PDF</span>
                </button>
                <button
                  onClick={downloadReport}
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                >
                  <Download className="w-4 h-4" />
                  <span>Baixar JSON</span>
                </button>
                <button
                  onClick={() => {
                    setShowReportModal(false)
                    setGeneratedReport(null)
                  }}
                  className="p-2 text-gray-400 hover:text-gray-600 transition"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {/* Summary */}
              {generatedReport.summary && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Resumo</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {Object.entries(generatedReport.summary).map(([key, value]: [string, any]) => {
                      // Skip period object, it will be shown separately
                      if (key === 'period' && typeof value === 'object') return null
                      // Skip complex objects (statistics, breakdowns, etc.)
                      if (typeof value === 'object' && value !== null && !Array.isArray(value)) return null
                      // Skip arrays
                      if (Array.isArray(value)) return null
                      
                      // Translate labels to Portuguese
                      const labelMap: { [key: string]: string } = {
                        'total_readings': 'Total de Leituras',
                        'average_value': 'Valor Médio',
                        'min_value': 'Valor Mínimo',
                        'max_value': 'Valor Máximo',
                        'total_interventions': 'Total de Intervenções',
                        'total_cost': 'Custo Total',
                        'average_repair_time': 'Tempo Médio de Reparo',
                        'period': 'Período',
                        'team_statistics': 'Estatísticas por Equipe',
                        'total_bills': 'Total de Faturas',
                        'total_amount': 'Valor Total',
                        'total_consumption': 'Consumo Total',
                        'average_amount': 'Valor Médio',
                        'average_consumption': 'Consumo Médio',
                        'paid_bills': 'Faturas Pagas',
                        'paid_amount': 'Valor Pago',
                        'unpaid_bills': 'Faturas Não Pagas',
                        'unpaid_amount': 'Valor Não Pago',
                        'payment_rate': 'Taxa de Pagamento (%)',
                        'overdue_bills': 'Faturas Vencidas',
                        'overdue_amount': 'Valor Vencido',
                        'total_tickets': 'Total de Tickets',
                        'resolved_tickets': 'Tickets Resolvidos',
                        'resolution_rate': 'Taxa de Resolução (%)',
                        'average_response_time_hours': 'Tempo Médio de Resposta (h)',
                        'average_resolution_time_hours': 'Tempo Médio de Resolução (h)',
                        'average_satisfaction': 'Satisfação Média',
                        'completed_interventions': 'Intervenções Concluídas',
                        'completion_rate': 'Taxa de Conclusão (%)',
                        'average_cost': 'Custo Médio',
                        'average_duration_hours': 'Duração Média (h)',
                        'average_response_hours': 'Tempo Médio de Resposta (h)'
                      }
                      const label = labelMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
                      
                      let displayValue = value
                      
                      // Format numbers
                      if (typeof value === 'number') {
                        if (key.includes('value') || key.includes('average') || key.includes('min') || key.includes('max') || key.includes('amount') || key.includes('cost') || key.includes('consumption')) {
                          displayValue = value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                        } else if (key.includes('rate') || key.includes('satisfaction')) {
                          displayValue = value.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 2 })
                        } else {
                          displayValue = value.toLocaleString('pt-BR')
                        }
                      } else if (value === null || value === undefined) {
                        displayValue = 'N/A'
                      }
                      
                      return (
                        <div key={key} className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
                          <p className="text-xs font-medium text-blue-700 uppercase tracking-wide mb-1">{label}</p>
                          <p className="text-2xl font-bold text-blue-900">
                            {String(displayValue)}
                          </p>
                        </div>
                      )
                    })}
                  </div>
                  
                  {/* Period display */}
                  {generatedReport.summary.period && (
                    <div className="mt-4 bg-gray-50 p-4 rounded-lg border border-gray-200">
                      <p className="text-sm font-medium text-gray-700 mb-2">Período de Análise</p>
                      <div className="flex items-center space-x-4 text-sm text-gray-600">
                        <div className="flex items-center space-x-2">
                          <Calendar className="w-4 h-4" />
                          <span>
                            <strong>Início:</strong> {
                              generatedReport.summary.period.start 
                                ? new Date(generatedReport.summary.period.start).toLocaleDateString('pt-BR', {
                                    day: '2-digit',
                                    month: 'long',
                                    year: 'numeric'
                                  })
                                : 'N/A'
                            }
                          </span>
                        </div>
                        <span className="text-gray-400">→</span>
                        <div className="flex items-center space-x-2">
                          <Calendar className="w-4 h-4" />
                          <span>
                            <strong>Fim:</strong> {
                              generatedReport.summary.period.end 
                                ? new Date(generatedReport.summary.period.end).toLocaleDateString('pt-BR', {
                                    day: '2-digit',
                                    month: 'long',
                                    year: 'numeric'
                                  })
                                : 'N/A'
                            }
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* Statistics breakdowns */}
                  {generatedReport.summary.statistics && (
                    <div className="mt-6">
                      <h4 className="text-md font-semibold text-gray-900 mb-3">Estatísticas Detalhadas</h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {Object.entries(generatedReport.summary.statistics).map(([key, value]: [string, any]) => {
                          if (typeof value === 'object' && value !== null) return null
                          const statLabelMap: { [key: string]: string } = {
                            'average_value': 'Média',
                            'min_value': 'Mínimo',
                            'max_value': 'Máximo',
                            'standard_deviation': 'Desvio Padrão'
                          }
                          const label = statLabelMap[key] || key.replace(/_/g, ' ')
                          return (
                            <div key={key} className="bg-gray-50 p-3 rounded border border-gray-200">
                              <p className="text-xs font-medium text-gray-600 mb-1">{label}</p>
                              <p className="text-lg font-bold text-gray-900">
                                {typeof value === 'number' ? value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : String(value)}
                              </p>
                            </div>
                          )
                        })}
                      </div>
                      {generatedReport.summary.statistics.percentiles && (
                        <div className="mt-4">
                          <h5 className="text-sm font-semibold text-gray-700 mb-2">Percentis</h5>
                          <div className="grid grid-cols-4 gap-2">
                            {Object.entries(generatedReport.summary.statistics.percentiles).map(([key, value]: [string, any]) => (
                              <div key={key} className="bg-gray-50 p-2 rounded text-center">
                                <p className="text-xs text-gray-600">{key.toUpperCase()}</p>
                                <p className="text-sm font-bold">{typeof value === 'number' ? value.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) : String(value)}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                  
                  {/* Status/Category breakdowns */}
                  {(generatedReport.summary.status_breakdown || generatedReport.summary.category_breakdown || generatedReport.summary.priority_breakdown) && (
                    <div className="mt-6">
                      <h4 className="text-md font-semibold text-gray-900 mb-3">Distribuições</h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {generatedReport.summary.status_breakdown && (
                          <div className="bg-gray-50 p-4 rounded border border-gray-200">
                            <h5 className="text-sm font-semibold text-gray-700 mb-2">Por Status</h5>
                            {Object.entries(generatedReport.summary.status_breakdown).map(([status, data]: [string, any]) => (
                              <div key={status} className="flex justify-between text-sm py-1">
                                <span className="text-gray-600">{status === 'open' ? 'Aberto' : status === 'in_progress' ? 'Em Andamento' : status === 'resolved' ? 'Resolvido' : status === 'closed' ? 'Fechado' : status === 'paid' ? 'Pago' : status === 'pending' ? 'Pendente' : status === 'overdue' ? 'Vencido' : status}:</span>
                                <span className="font-medium">{data.count || data}</span>
                              </div>
                            ))}
                          </div>
                        )}
                        {generatedReport.summary.category_breakdown && (
                          <div className="bg-gray-50 p-4 rounded border border-gray-200">
                            <h5 className="text-sm font-semibold text-gray-700 mb-2">Por Categoria</h5>
                            {Object.entries(generatedReport.summary.category_breakdown).map(([category, count]: [string, any]) => (
                              <div key={category} className="flex justify-between text-sm py-1">
                                <span className="text-gray-600">{category === 'billing' ? 'Faturamento' : category === 'technical' ? 'Técnico' : category === 'complaint' ? 'Reclamação' : category === 'request' ? 'Solicitação' : category === 'information' ? 'Informação' : category === 'emergency' ? 'Emergência' : category}:</span>
                                <span className="font-medium">{typeof count === 'object' ? count.count : count}</span>
                              </div>
                            ))}
                          </div>
                        )}
                        {generatedReport.summary.priority_breakdown && (
                          <div className="bg-gray-50 p-4 rounded border border-gray-200">
                            <h5 className="text-sm font-semibold text-gray-700 mb-2">Por Prioridade</h5>
                            {Object.entries(generatedReport.summary.priority_breakdown).map(([priority, count]: [string, any]) => (
                              <div key={priority} className="flex justify-between text-sm py-1">
                                <span className="text-gray-600">{priority === 'low' ? 'Baixa' : priority === 'medium' ? 'Média' : priority === 'high' ? 'Alta' : priority === 'urgent' ? 'Urgente' : priority}:</span>
                                <span className="font-medium">{typeof count === 'object' ? count.count : count}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {/* Team statistics */}
                  {generatedReport.team_statistics && Object.keys(generatedReport.team_statistics).length > 0 && (
                    <div className="mt-6">
                      <h4 className="text-md font-semibold text-gray-900 mb-3">Estatísticas por Equipe</h4>
                      <div className="space-y-3">
                        {Object.entries(generatedReport.team_statistics).map(([team, stats]: [string, any]) => (
                          <div key={team} className="bg-gray-50 p-4 rounded border border-gray-200">
                            <h5 className="text-sm font-semibold text-gray-700 mb-2">{team}</h5>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                              <div>
                                <span className="text-gray-600">Total: </span>
                                <span className="font-medium">{stats.total_interventions || 0}</span>
                              </div>
                              <div>
                                <span className="text-gray-600">Concluídas: </span>
                                <span className="font-medium">{stats.completed_interventions || 0}</span>
                              </div>
                              <div>
                                <span className="text-gray-600">Taxa: </span>
                                <span className="font-medium">{typeof stats.completion_rate === 'number' ? stats.completion_rate.toFixed(1) : stats.completion_rate || 0}%</span>
                              </div>
                              <div>
                                <span className="text-gray-600">Custo Médio: </span>
                                <span className="font-medium">R$ {typeof stats.avg_cost === 'number' ? stats.avg_cost.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) : stats.avg_cost || '0,00'}</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Filters */}
              {generatedReport.filters && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Filtros Aplicados</h3>
                  <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {Object.entries(generatedReport.filters).map(([key, value]: [string, any]) => {
                        if (value === null || value === undefined || value === '') return null
                        
                        // Translate filter labels to Portuguese
                        const filterLabelMap: { [key: string]: string } = {
                          'start_date': 'Data Inicial',
                          'end_date': 'Data Final',
                          'sensor_type': 'Tipo de Sensor',
                          'sensor_id': 'ID do Sensor',
                          'location': 'Localização',
                          'status': 'Status',
                          'team_name': 'Equipe',
                          'category': 'Categoria',
                          'customer_id': 'ID do Cliente'
                        }
                        const label = filterLabelMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
                        let displayValue = value
                        
                        // Format dates
                        if (key.includes('date') || (typeof value === 'string' && value.includes('T'))) {
                          try {
                            displayValue = new Date(value).toLocaleDateString('pt-BR', {
                              day: '2-digit',
                              month: 'short',
                              year: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit'
                            })
                          } catch (e) {
                            displayValue = String(value)
                          }
                        } else if (typeof value === 'object') {
                          displayValue = JSON.stringify(value)
                        }
                        
                        return (
                          <div key={key} className="flex items-start space-x-2 py-2 border-b border-gray-200 last:border-0">
                            <span className="text-sm font-medium text-gray-700 min-w-[120px]">{label}:</span>
                            <span className="text-sm text-gray-900 flex-1">{String(displayValue)}</span>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                </div>
              )}

              {/* Data Preview */}
              {(generatedReport.readings || generatedReport.interventions || generatedReport.bills || generatedReport.tickets) && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Dados ({generatedReport.readings?.length || generatedReport.interventions?.length || generatedReport.bills?.length || generatedReport.tickets?.length || 0} registros)
                  </h3>
                  <div className="bg-gray-50 p-4 rounded-lg max-h-96 overflow-y-auto border border-gray-200">
                    <div className="space-y-3">
                      {(generatedReport.readings || generatedReport.interventions || generatedReport.bills || generatedReport.tickets).slice(0, 20).map((item: any, index: number) => (
                        <div key={index} className="bg-white p-3 rounded border border-gray-200 hover:shadow-sm transition">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                            {Object.entries(item).slice(0, 6).map(([key, value]: [string, any]) => {
                              // Translate field labels to Portuguese
                              const fieldLabelMap: { [key: string]: string } = {
                                'sensor_id': 'ID do Sensor',
                                'sensor_type': 'Tipo de Sensor',
                                'value': 'Valor',
                                'unit': 'Unidade',
                                'location': 'Localização',
                                'timestamp': 'Data/Hora',
                                'id': 'ID',
                                'service_order_id': 'ID da Ordem de Serviço',
                                'team_name': 'Equipe',
                                'completed_at': 'Concluído em',
                                'cost': 'Custo',
                                'description': 'Descrição',
                                'reading_id': 'ID da Leitura',
                                'operator_id': 'ID do Operador',
                                'operator_name': 'Nome do Operador',
                                'observation_type': 'Tipo de Observação',
                                'text': 'Texto',
                                'created_at': 'Criado em',
                                'updated_at': 'Atualizado em',
                                'status': 'Status',
                                'priority': 'Prioridade',
                                'assigned_team': 'Equipe Atribuída',
                                'repair_time': 'Tempo de Reparo',
                                'material_cost': 'Custo de Material',
                                'labor_cost': 'Custo de Mão de Obra',
                                'customer_id': 'ID do Cliente',
                                'meter_id': 'ID do Medidor',
                                'amount': 'Valor',
                                'consumption': 'Consumo',
                                'billing_period_start': 'Início do Período',
                                'billing_period_end': 'Fim do Período',
                                'due_date': 'Data de Vencimento',
                                'paid_at': 'Pago em',
                                'ticket_number': 'Número do Ticket',
                                'title': 'Título',
                                'category': 'Categoria',
                                'resolved_at': 'Resolvido em',
                                'satisfaction_rating': 'Avaliação de Satisfação',
                                'assigned_agent_id': 'ID do Agente Atribuído',
                                'client_name': 'Nome do Cliente'
                              }
                              const label = fieldLabelMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
                              let displayValue = value
                              
                              // Translate category values to Portuguese
                              if (key === 'category' && typeof value === 'string') {
                                const categoryMap: { [key: string]: string } = {
                                  'billing': 'Faturamento',
                                  'technical': 'Técnico',
                                  'complaint': 'Reclamação',
                                  'request': 'Solicitação',
                                  'information': 'Informação',
                                  'emergency': 'Emergência'
                                }
                                displayValue = categoryMap[value.toLowerCase()] || value
                              }
                              // Translate status values to Portuguese
                              else if (key === 'status' && typeof value === 'string') {
                                const statusMap: { [key: string]: string } = {
                                  'open': 'Aberto',
                                  'in_progress': 'Em Andamento',
                                  'waiting_client': 'Aguardando Cliente',
                                  'resolved': 'Resolvido',
                                  'closed': 'Fechado',
                                  'reopened': 'Reaberto',
                                  'escalated': 'Escalado'
                                }
                                displayValue = statusMap[value.toLowerCase()] || value
                              }
                              // Translate priority values to Portuguese
                              else if (key === 'priority' && typeof value === 'string') {
                                const priorityMap: { [key: string]: string } = {
                                  'low': 'Baixa',
                                  'medium': 'Média',
                                  'high': 'Alta',
                                  'urgent': 'Urgente'
                                }
                                displayValue = priorityMap[value.toLowerCase()] || value
                              }
                              // Ensure ticket_number is displayed as string
                              else if (key === 'ticket_number') {
                                displayValue = String(value || 'N/A')
                              }
                              // Format dates - only for fields that end with '_at', '_date', or contain 'timestamp'
                              else if ((key.endsWith('_at') || key.endsWith('_date') || key.includes('timestamp')) && 
                                       typeof value === 'string' && value.includes('T')) {
                                try {
                                  displayValue = new Date(value).toLocaleString('pt-BR', {
                                    day: '2-digit',
                                    month: '2-digit',
                                    year: 'numeric',
                                    hour: '2-digit',
                                    minute: '2-digit'
                                  })
                                } catch (e) {
                                  displayValue = String(value)
                                }
                              }
                              // Format numbers
                              else if (typeof value === 'number') {
                                if (key.includes('rating') || key.includes('rate')) {
                                  displayValue = value.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 2 })
                                } else if (key.includes('amount') || key.includes('cost') || key.includes('value') || key.includes('consumption')) {
                                  displayValue = value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                                } else {
                                  displayValue = value.toLocaleString('pt-BR')
                                }
                              }
                              // Handle null/undefined
                              else if (value === null || value === undefined) {
                                displayValue = 'N/A'
                              }
                              
                              return (
                                <div key={key} className="flex items-start">
                                  <span className="font-medium text-gray-600 min-w-[100px]">{label}:</span>
                                  <span className="text-gray-900 break-words">{String(displayValue)}</span>
                                </div>
                              )
                            })}
                          </div>
                          {Object.keys(item).length > 6 && (
                            <p className="text-xs text-gray-500 mt-2 italic">
                              + {Object.keys(item).length - 6} campos adicionais
                            </p>
                          )}
                        </div>
                      ))}
                      {(generatedReport.readings?.length || generatedReport.interventions?.length || generatedReport.bills?.length || generatedReport.tickets?.length || 0) > 20 && (
                        <div className="text-center py-4 text-sm text-gray-500 bg-blue-50 rounded border border-blue-200">
                          <p className="font-medium">... e mais {(generatedReport.readings?.length || generatedReport.interventions?.length || generatedReport.bills?.length || generatedReport.tickets?.length || 0) - 20} registros</p>
                          <p className="text-xs mt-1">Use o download JSON para ver todos os dados completos</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Metadata */}
              <div className="mt-6 pt-6 border-t border-gray-200">
                <div className="flex flex-wrap items-center gap-4 text-sm">
                  <div className="flex items-center space-x-2 text-gray-600">
                    <Calendar className="w-4 h-4 text-gray-400" />
                    <span>
                      <strong className="text-gray-700">Gerado em:</strong>{' '}
                      {new Date(generatedReport.generated_at || Date.now()).toLocaleString('pt-BR', {
                        day: '2-digit',
                        month: 'long',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </span>
                  </div>
                  {generatedReport.generated_by && (
                    <div className="flex items-center space-x-2 text-gray-600">
                      <span className="text-gray-400">•</span>
                      <span>
                        <strong className="text-gray-700">Gerado por:</strong> {generatedReport.generated_by}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

