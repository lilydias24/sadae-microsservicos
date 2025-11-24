import React, { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import ReactQuill from 'react-quill'
import 'react-quill/dist/quill.snow.css'
import { 
  MessageSquare, 
  Plus, 
  Search, 
  Filter, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  User,
  Mail,
  Phone,
  Calendar,
  Star,
  BookOpen,
  BarChart3,
  Ticket,
  Send,
  Paperclip,
  Eye,
  EyeOff,
  MessageCircle
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'

interface SupportTicket {
  id: number
  ticket_number: string
  title: string
  description: string
  category: string
  priority: string
  status: string
  client_name: string
  client_email: string
  assigned_agent_name?: string
  created_at: string
  updated_at?: string
  satisfaction_rating?: number
  satisfaction_comment?: string
  evaluation?: {
    rating: number
    comment: string
    evaluated_at: string
  }
}

interface TicketMessage {
  id: number
  message_type: string
  content: string
  author_name: string
  created_at: string
  is_internal: boolean
}

interface KnowledgeArticle {
  id: number
  title: string
  content: string
  category: string
  tags: string[]
  slug: string
  meta_description: string
  keywords: string[]
  view_count: number
  helpful_count: number
  not_helpful_count: number
  is_published: boolean
  is_featured: boolean
  created_by_user_id: number
}

const categoryColors: Record<string, string> = {
  billing: 'bg-green-100 text-green-800',
  technical: 'bg-blue-100 text-blue-800',
  complaint: 'bg-red-100 text-red-800',
  request: 'bg-purple-100 text-purple-800',
  information: 'bg-yellow-100 text-yellow-800',
  emergency: 'bg-red-200 text-red-900'
}

const statusColors: Record<string, string> = {
  open: 'bg-blue-100 text-blue-800',
  in_progress: 'bg-yellow-100 text-yellow-800',
  waiting_client: 'bg-orange-100 text-orange-800',
  resolved: 'bg-green-100 text-green-800',
  closed: 'bg-gray-100 text-gray-800'
}

// Função para traduzir status para português
const translateStatus = (status: string): string => {
  const statusMap: Record<string, string> = {
    'open': 'Aberto',
    'in_progress': 'Em Andamento',
    'waiting_client': 'Aguardando Cliente',
    'resolved': 'Resolvido',
    'closed': 'Fechado'
  }
  return statusMap[status] || status.replace('_', ' ')
}

// Função para traduzir prioridade para português
const translatePriority = (priority: string): string => {
  const priorityMap: Record<string, string> = {
    'low': 'Baixa',
    'medium': 'Média',
    'high': 'Alta',
    'urgent': 'Urgente'
  }
  return priorityMap[priority] || priority
}

// Função para traduzir categoria para português
const translateCategory = (category: string): string => {
  const categoryMap: Record<string, string> = {
    'billing': 'Faturamento',
    'technical': 'Técnico',
    'complaint': 'Reclamação',
    'request': 'Solicitação',
    'information': 'Informação',
    'emergency': 'Emergência'
  }
  return categoryMap[category] || category
}

const priorityColors: Record<string, string> = {
  low: 'bg-gray-100 text-gray-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-orange-100 text-orange-800',
  urgent: 'bg-red-100 text-red-800'
}

export function SupportPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('tickets')
  const [tickets, setTickets] = useState<SupportTicket[]>([])
  const [knowledgeBase, setKnowledgeBase] = useState<KnowledgeArticle[]>([])
  const [kbSearch, setKbSearch] = useState('')
  const [kbCategory, setKbCategory] = useState('all')
  const [kbTag, setKbTag] = useState('')
  const [kbAnalytics, setKbAnalytics] = useState<{views: number; helpful: number; notHelpful: number}>({views: 0, helpful: 0, notHelpful: 0})
  const [selectedTicket, setSelectedTicket] = useState<SupportTicket | null>(null)
  const [ticketMessages, setTicketMessages] = useState<TicketMessage[]>([])
  const [showCreateTicket, setShowCreateTicket] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [filterCategory, setFilterCategory] = useState('all')
  const [loading, setLoading] = useState(false)

  // Dashboard state
  const [dashboardStats, setDashboardStats] = useState<{
    total_tickets: number
    open_tickets: number
    in_progress_tickets: number
    resolved_tickets: number
    average_resolution_time: number
    satisfaction_average: number
    tickets_by_category: Array<{ category: string; count: number }>
    tickets_by_priority: Array<any>
    recent_tickets: Array<any>
  }>({
    total_tickets: 0,
    open_tickets: 0,
    in_progress_tickets: 0,
    resolved_tickets: 0,
    average_resolution_time: 0,
    satisfaction_average: 0,
    tickets_by_category: [],
    tickets_by_priority: [],
    recent_tickets: []
  })

  // Agent dashboard state
  const [agentDashboardStats, setAgentDashboardStats] = useState({
    agent_info: {
      name: '',
      satisfaction_rating: 0,
      total_resolved: 0,
      average_response_time: 0
    },
    my_tickets: {
      total_assigned: 0,
      open: 0,
      in_progress: 0,
      resolved_today: 0
    },
    daily_stats: {
      new_tickets_today: 0,
      pending_assignment: 0
    },
    recent_assigned: [],
    pending_tickets: []
  })

  // New ticket form state
  const [newTicket, setNewTicket] = useState({
    title: '',
    description: '',
    category: 'request',
    priority: 'medium'
  })

  // New message form state
  const [newMessage, setNewMessage] = useState('')
  const [showInternalMessages, setShowInternalMessages] = useState(false)
  
  // AI suggestion state
  const [aiSuggestion, setAiSuggestion] = useState<{
    suggestion: string | null
    confidence: number
    relevant_articles: Array<{ id: number; title: string; score: number }>
    suggestions: string[]
    should_escalate: boolean
  } | null>(null)
  const [loadingAiSuggestion, setLoadingAiSuggestion] = useState(false)
  
  // Evaluation state
  const [showEvaluation, setShowEvaluation] = useState(false)
  const [evaluationForm, setEvaluationForm] = useState({
    rating: 5,
    comment: ''
  })

  useEffect(() => {
    fetchTickets()
    fetchKnowledgeBase()
    if (user?.role === 'support_agent') {
      fetchAgentDashboardStats()
    } else if (user?.role !== 'citizen') {
      fetchDashboardStats()
    }
  }, [])

  const fetchTickets = async () => {
    try {
      setLoading(true)
      console.log('🔍 Buscando tickets...')
      const response = await api.get('/support/tickets')
      console.log('📦 Resposta da API:', response)
      
      // Garantir que data seja sempre um array e mapear os campos corretamente
      const ticketsArray = Array.isArray(response.data) ? response.data : []
      console.log(`✅ Tickets encontrados: ${ticketsArray.length}`)
      
      // Mapear e normalizar os dados dos tickets
      const normalizedTickets = ticketsArray.map((ticket: any) => ({
        id: ticket.id,
        ticket_number: ticket.ticket_number || `TKT-${ticket.id}` || '--',
        title: ticket.title || 'Sem título',
        description: ticket.description || 'Sem descrição',
        category: ticket.category?.value || ticket.category || 'request',
        priority: ticket.priority?.value || ticket.priority || 'medium',
        status: ticket.status?.value || ticket.status || 'open',
        client_name: ticket.client_name || ticket.client_name || 'Cliente',
        client_email: ticket.client_email || '',
        assigned_agent_name: ticket.assigned_agent_name || ticket.assigned_agent?.name || null,
        created_at: ticket.created_at || new Date().toISOString(),
        updated_at: ticket.updated_at || null,
        satisfaction_rating: ticket.satisfaction_rating || null,
        satisfaction_comment: ticket.satisfaction_comment || null,
        evaluation: ticket.evaluation || (ticket.satisfaction_rating ? {
          rating: ticket.satisfaction_rating,
          comment: ticket.satisfaction_comment || '',
          evaluated_at: ticket.updated_at || ticket.created_at || new Date().toISOString()
        } : null)
      }))
      
      console.log('✅ Tickets normalizados:', normalizedTickets)
      setTickets(normalizedTickets)
    } catch (error: any) {
      console.error('❌ Erro ao buscar tickets:', error)
      console.error('❌ Detalhes do erro:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        statusText: error.response?.statusText
      })
      setTickets([]) // Definir array vazio em caso de erro
      alert(`Erro ao carregar tickets: ${error.response?.data?.detail || error.message || 'Erro desconhecido'}`)
    } finally {
      setLoading(false)
    }
  }

  const fetchKnowledgeBase = async () => {
    // Mocked knowledge base data aligned to user's context
    const mocked: KnowledgeArticle[] = [
      {
        id: 1,
        title: 'Como consultar minha conta de água?',
        content:
          'Você pode consultar sua conta acessando a área do cliente em Dashboard > Faturamento. Informe seu CPF/CNPJ e número de cliente para visualizar faturas abertas e pagas. Também é possível baixar 2ª via e verificar histórico de consumo.',
        category: 'billing',
        tags: ['conta','fatura','consulta'],
        slug: 'como-consultar-conta-de-agua',
        meta_description: 'Aprenda a consultar sua conta de água e baixar a 2ª via.',
        keywords: ['conta de água','2ª via','fatura','consulta'],
        view_count: 124,
        helpful_count: 37,
        not_helpful_count: 4,
        is_published: true,
        is_featured: true,
        created_by_user_id: 1001
      },
      {
        id: 2,
        title: 'O que fazer em caso de vazamento?',
        content:
          'Feche o registro principal, sinalize a área e registre um chamado em Serviços Públicos > Reportar Vazamento. Informe localização, intensidade e um contato. Nossa equipe avaliará a urgência.',
        category: 'emergency',
        tags: ['vazamento','emergência','reparo'],
        slug: 'o-que-fazer-em-caso-de-vazamento',
        meta_description: 'Passo a passo para agir em casos de vazamento de água.',
        keywords: ['vazamento','emergência','registro','suporte'],
        view_count: 209,
        helpful_count: 96,
        not_helpful_count: 6,
        is_published: true,
        is_featured: true,
        created_by_user_id: 1002
      },
      {
        id: 3,
        title: 'Como solicitar religação de água?',
        content:
          'Após a regularização de pendências, solicite religação em Atendimento > Novo Ticket, categoria “Solicitação” e assunto “Religação”. Tenha em mãos o número do imóvel e comprovante do pagamento.',
        category: 'request',
        tags: ['religação','corte','religamento'],
        slug: 'como-solicitar-religacao-de-agua',
        meta_description: 'Veja como solicitar religação de água após regularização.',
        keywords: ['religação','corte','ligação de água'],
        view_count: 88,
        helpful_count: 24,
        not_helpful_count: 5,
        is_published: true,
        is_featured: false,
        created_by_user_id: 1003
      },
      {
        id: 4,
        title: 'Valores das tarifas de água e esgoto',
        content:
          'As tarifas variam por faixa de consumo e categoria (residencial, comercial, etc.). Consulte a tabela vigente em Serviços Públicos > Informações. A simulação no app ajuda a estimar sua próxima fatura.',
        category: 'information',
        tags: ['tarifa','preço','valor'],
        slug: 'valores-das-tarifas-de-agua-e-esgoto',
        meta_description: 'Conheça os valores e faixas de tarifas de água e esgoto.',
        keywords: ['tarifa','preço','água','esgoto'],
        view_count: 140,
        helpful_count: 31,
        not_helpful_count: 7,
        is_published: true,
        is_featured: false,
        created_by_user_id: 1004
      }
    ]
    setKnowledgeBase(mocked)
  }

  const fetchDashboardStats = async () => {
    try {
      const { data } = await api.get('/support/dashboard')
      // Mapear a resposta da API para o formato esperado pelo frontend
      const categoryMetrics = data.category_metrics || {}
      const ticketsByCategory = [
        { category: 'billing', count: categoryMetrics.billing || 0 },
        { category: 'technical', count: categoryMetrics.technical || 0 },
        { category: 'complaint', count: categoryMetrics.complaint || 0 },
        { category: 'request', count: categoryMetrics.request || 0 },
        { category: 'information', count: categoryMetrics.information || 0 },
        { category: 'emergency', count: categoryMetrics.emergency || 0 }
      ].filter(item => item.count > 0) // Apenas categorias com tickets
      
      setDashboardStats({
        total_tickets: data.ticket_metrics?.total_tickets || 0,
        open_tickets: data.ticket_metrics?.open_tickets || 0,
        in_progress_tickets: data.ticket_metrics?.in_progress_tickets || 0,
        resolved_tickets: data.ticket_metrics?.resolved_tickets || 0,
        average_resolution_time: data.ticket_metrics?.average_resolution_time || 0,
        satisfaction_average: data.ticket_metrics?.satisfaction_average || 0,
        tickets_by_category: ticketsByCategory,
        tickets_by_priority: [], // Não disponível na API atual
        recent_tickets: Array.isArray(data.recent_tickets) ? data.recent_tickets : []
      })
    } catch (error) {
      console.error('Error fetching dashboard stats:', error)
      // Manter estado padrão em caso de erro
      setDashboardStats({
        total_tickets: 0,
        open_tickets: 0,
        in_progress_tickets: 0,
        resolved_tickets: 0,
        average_resolution_time: 0,
        satisfaction_average: 0,
        tickets_by_category: [],
        tickets_by_priority: [],
        recent_tickets: []
      })
    }
  }

  const fetchAgentDashboardStats = async () => {
    try {
      const { data } = await api.get('/support/agent-dashboard')
      // Garantir que todos os arrays sejam válidos
      setAgentDashboardStats({
        agent_info: data.agent_info || {
          name: '',
          satisfaction_rating: 0,
          total_resolved: 0,
          average_response_time: 0
        },
        my_tickets: data.my_tickets || {
          total_assigned: 0,
          open: 0,
          in_progress: 0,
          resolved_today: 0
        },
        daily_stats: data.daily_stats || {
          new_tickets_today: 0,
          pending_assignment: 0
        },
        recent_assigned: Array.isArray(data.recent_assigned) ? data.recent_assigned : [],
        pending_tickets: Array.isArray(data.pending_tickets) ? data.pending_tickets : []
      })
    } catch (error) {
      console.error('Error fetching agent dashboard stats:', error)
      // Manter estado padrão em caso de erro
      setAgentDashboardStats({
        agent_info: {
          name: '',
          satisfaction_rating: 0,
          total_resolved: 0,
          average_response_time: 0
        },
        my_tickets: {
          total_assigned: 0,
          open: 0,
          in_progress: 0,
          resolved_today: 0
        },
        daily_stats: {
          new_tickets_today: 0,
          pending_assignment: 0
        },
        recent_assigned: [],
        pending_tickets: []
      })
    }
  }

  const fetchTicketMessages = async (ticketId: number) => {
    try {
      const { data } = await api.get(`/support/tickets/${ticketId}/messages`, {
        params: { include_internal: showInternalMessages },
      })
      setTicketMessages(data)
      
      // Auto-scroll to bottom when new messages arrive
      setTimeout(() => {
        const messagesContainer = document.querySelector('.max-h-96.overflow-y-auto')
        if (messagesContainer) {
          messagesContainer.scrollTop = messagesContainer.scrollHeight
        }
      }, 100)
    } catch (error) {
      console.error('Error fetching ticket messages:', error)
    }
  }
  
  // Auto-refresh messages when ticket is selected (for AI responses)
  useEffect(() => {
    if (!selectedTicket?.id) return
    
    const interval = setInterval(() => {
      fetchTicketMessages(selectedTicket.id)
    }, 3000) // Check every 3 seconds
    
    return () => clearInterval(interval)
  }, [selectedTicket?.id])

  // Auto-refresh ticket status when ticket is selected (for immediate status updates)
  useEffect(() => {
    if (!selectedTicket?.id) return
    
    const interval = setInterval(async () => {
      try {
        const { data } = await api.get(`/support/tickets/${selectedTicket.id}`)
        // Update selected ticket if status changed
        if (data.status !== selectedTicket.status) {
          setSelectedTicket(prev => prev ? { ...prev, status: data.status } : null)
          // Also update in tickets list
          setTickets(prev => prev.map(ticket => 
            ticket.id === selectedTicket.id 
              ? { ...ticket, status: data.status }
              : ticket
          ))
        }
      } catch (error) {
        console.error('Error refreshing ticket status:', error)
      }
    }, 2000) // Check every 2 seconds for status updates
    
    return () => clearInterval(interval)
  }, [selectedTicket?.id, selectedTicket?.status])

  const createTicket = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setLoading(true)
      
      // Validação básica no frontend
      if (!newTicket.title || newTicket.title.trim().length < 5) {
        alert('O título deve ter pelo menos 5 caracteres')
        setLoading(false)
        return
      }
      
      if (!newTicket.description || newTicket.description.trim().length < 10) {
        alert('A descrição deve ter pelo menos 10 caracteres')
        setLoading(false)
        return
      }
      
      // Preparar dados para envio
      const ticketData = {
        title: newTicket.title.trim(),
        description: newTicket.description.trim(),
        category: newTicket.category,
        priority: newTicket.priority
      }
      
      console.log('📝 Criando ticket com dados:', ticketData)
      
      const response = await api.post('/support/tickets', ticketData)
      console.log('✅ Ticket criado com sucesso:', response.data)
      
      // Normalizar o ticket criado para o formato esperado
      const createdTicket = response.data
      const normalizedCreatedTicket = {
        id: createdTicket.id,
        ticket_number: createdTicket.ticket_number || `TKT-${createdTicket.id}` || '--',
        title: createdTicket.title || newTicket.title || 'Sem título',
        description: createdTicket.description || newTicket.description || 'Sem descrição',
        category: createdTicket.category?.value || createdTicket.category || newTicket.category || 'request',
        priority: createdTicket.priority?.value || createdTicket.priority || newTicket.priority || 'medium',
        status: createdTicket.status?.value || createdTicket.status || 'open',
        client_name: createdTicket.client_name || user?.full_name || 'Cliente',
        client_email: createdTicket.client_email || user?.email || '',
        assigned_agent_name: createdTicket.assigned_agent_name || createdTicket.assigned_agent?.name || null,
        created_at: createdTicket.created_at || new Date().toISOString(),
        updated_at: createdTicket.updated_at || null,
        satisfaction_rating: createdTicket.satisfaction_rating || null,
        evaluation: createdTicket.evaluation || null
      }
      
      // Adicionar o ticket recém-criado no início da lista (otimista)
      setTickets(prev => [normalizedCreatedTicket, ...prev])
      
      // Limpar formulário e fechar modal
      setNewTicket({ title: '', description: '', category: 'request', priority: 'medium' })
      setShowCreateTicket(false)
      
      // Limpar filtros que podem ocultar o novo ticket
      setSearchTerm('')
      setFilterStatus('all')
      setFilterCategory('all')
      
      // Garantir que estamos vendo a lista, não um ticket específico
      setSelectedTicket(null)
      
      // Recarregar a lista completa após um pequeno delay para garantir sincronização
      setTimeout(async () => {
        await fetchTickets()
      }, 500)
      
      alert('Ticket criado com sucesso!')
    } catch (error: any) {
      console.error('❌ Erro ao criar ticket:', error)
      console.error('❌ Detalhes do erro:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        statusText: error.response?.statusText,
        request: error.config
      })
      
      // Extrair mensagem de erro de forma mais detalhada
      let errorMessage = 'Erro desconhecido'
      
      if (error.response?.data) {
        const errorData = error.response.data
        
        // FastAPI retorna erros de validação em formato específico
        if (Array.isArray(errorData.detail)) {
          // Erro de validação do FastAPI
          const validationErrors = errorData.detail.map((err: any) => {
            const field = err.loc?.join('.') || 'campo'
            const msg = err.msg || 'erro de validação'
            return `${field}: ${msg}`
          }).join('\n')
          errorMessage = `Erro de validação:\n${validationErrors}`
        } else if (errorData.detail) {
          errorMessage = typeof errorData.detail === 'string' 
            ? errorData.detail 
            : JSON.stringify(errorData.detail)
        } else if (errorData.message) {
          errorMessage = errorData.message
        }
      } else if (error.message) {
        errorMessage = error.message
      }
      
      console.error('❌ Erro completo:', {
        status: error.response?.status,
        data: error.response?.data,
        message: errorMessage
      })
      
      alert(`Não foi possível criar o ticket:\n${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedTicket || !newMessage.trim()) return

    try {
      // Remove HTML tags for plain text version, but send HTML to backend
      const plainText = newMessage.replace(/<[^>]*>/g, '').trim()
      if (!plainText) return

      await api.post(`/support/tickets/${selectedTicket.id}/messages`, { 
        content: newMessage // Send HTML content
      })
      setNewMessage('')
      setAiSuggestion(null) // Limpar sugestão após enviar
      
      // Refresh messages immediately
      if (selectedTicket.id) {
        fetchTicketMessages(selectedTicket.id)
        
        // If message is from client, poll for AI response
        if (user?.role === 'citizen') {
          // Poll for AI response (check every 2 seconds for 10 seconds)
          let attempts = 0
          const maxAttempts = 5
          const pollInterval = setInterval(async () => {
            attempts++
            await fetchTicketMessages(selectedTicket.id)
            
            if (attempts >= maxAttempts) {
              clearInterval(pollInterval)
            }
          }, 2000)
        }
      }
    } catch (error) {
      console.error('Error sending message:', error)
    }
  }

  // Update ticket status
  const updateTicketStatus = async (ticketId: number, newStatus: string) => {
    try {
      await api.put(`/support/tickets/${ticketId}`, { status: newStatus })
      
      // Update local state immediately
      setTickets(prev => prev.map(ticket => 
        ticket.id === ticketId 
          ? { ...ticket, status: newStatus }
          : ticket
      ))
      
      // Update selected ticket if it's the one being updated
      if (selectedTicket?.id === ticketId) {
        setSelectedTicket(prev => prev ? { ...prev, status: newStatus } : null)
      }
      
      // Refresh tickets list to ensure consistency
      setTimeout(() => {
        fetchTickets()
      }, 500)
    } catch (error) {
      console.error('Error updating ticket status:', error)
      alert('Erro ao atualizar status do ticket')
    }
  }

  // Buscar sugestão da IA quando o usuário digitar uma mensagem
  const fetchAiSuggestion = async (message: string) => {
    if (!selectedTicket || !message.trim() || message.length < 10) {
      setAiSuggestion(null)
      return
    }

    try {
      setLoadingAiSuggestion(true)
      const response = await api.post(`/support/tickets/${selectedTicket.id}/ai-suggest`, {
        content: message
      })
      setAiSuggestion(response.data)
    } catch (error) {
      console.error('Error fetching AI suggestion:', error)
      setAiSuggestion(null)
    } finally {
      setLoadingAiSuggestion(false)
    }
  }

  // Debounce para buscar sugestão da IA
  useEffect(() => {
    const timer = setTimeout(() => {
      if (newMessage.trim() && selectedTicket) {
        fetchAiSuggestion(newMessage)
      } else {
        setAiSuggestion(null)
      }
    }, 1000) // Aguardar 1 segundo após parar de digitar

    return () => clearTimeout(timer)
  }, [newMessage, selectedTicket])

  const filteredTickets = Array.isArray(tickets) ? tickets.filter(ticket => {
    const matchesSearch = (ticket.title || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (ticket.description || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (ticket.ticket_number || '').toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = filterStatus === 'all' || ticket.status === filterStatus
    const matchesCategory = filterCategory === 'all' || ticket.category === filterCategory
    return matchesSearch && matchesStatus && matchesCategory
  }) : []

  // Debug: Log quando tickets ou filtros mudarem
  useEffect(() => {
    console.log('🔍 Debug de filtros:', {
      totalTickets: tickets.length,
      filteredTickets: filteredTickets.length,
      searchTerm,
      filterStatus,
      filterCategory,
      tickets: tickets.map(t => ({ id: t.id, title: t.title, status: t.status, category: t.category }))
    })
  }, [tickets, filteredTickets, searchTerm, filterStatus, filterCategory])

  // Knowledge Base filtering with text, category and tags
  const normalize = (s: string) => s.toLowerCase()
  const kbTagMap: Record<number, string[]> = {
    1: ['conta', 'fatura', 'consulta'],
    2: ['vazamento', 'emergência', 'reparo'],
    3: ['religação', 'corte', 'religamento'],
    4: ['tarifa', 'preço', 'valor']
  }
  const kbFiltered = knowledgeBase.filter((a) => {
    if (!a.is_published) return false
    const combined = `${a.title || ''} ${a.content || ''} ${(a.keywords || []).join(' ')} ${(a.tags || []).join(' ')}`
    const textMatch = !kbSearch || normalize(combined).includes(normalize(kbSearch))
    const categoryMatch = kbCategory === 'all' || a.category === kbCategory
    const tagMatch = !kbTag || (a.tags || []).some((t) => normalize(t || '').includes(normalize(kbTag))) || (kbTagMap[a.id] && kbTagMap[a.id].some((t) => normalize(t || '').includes(normalize(kbTag))))
    return textMatch && categoryMatch && tagMatch
  })

  // Auto suggestions while creating a ticket
  const suggestionPool = knowledgeBase.map((a) => ({ id: a.id, title: a.title || '', category: a.category || '' }))
  const suggestions = !newTicket.title && !newTicket.description
    ? []
    : suggestionPool.filter((s) => {
        const q = normalize(`${newTicket.title || ''} ${newTicket.description || ''}`)
        return normalize(s.title || '').includes(q) || q.split(' ').some((w) => normalize(s.title || '').includes(w))
      }).slice(0, 4)

  const markHelpful = (id: number, helpful: boolean) => {
    setKnowledgeBase((prev) => prev.map((a) => a.id === id
      ? {
          ...a,
          view_count: a.view_count + 1,
          helpful_count: helpful ? a.helpful_count + 1 : a.helpful_count,
          not_helpful_count: helpful ? a.not_helpful_count : a.not_helpful_count + 1
        }
      : a
    ))
    setKbAnalytics((p) => ({
      views: p.views + 1,
      helpful: helpful ? p.helpful + 1 : p.helpful,
      notHelpful: helpful ? p.notHelpful : p.notHelpful + 1
    }))
  }

  // Submit evaluation
  const submitEvaluation = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedTicket) return

    try {
      const response = await api.post(`/support/tickets/${selectedTicket.id}/evaluate`, evaluationForm)
      
      // Update local state with the evaluation
      const updatedEvaluation = {
        rating: evaluationForm.rating,
        comment: evaluationForm.comment,
        evaluated_at: new Date().toISOString()
      }
      
      setTickets(prev => prev.map(ticket => 
          ticket.id === selectedTicket.id 
            ? {
                ...ticket,
                satisfaction_rating: evaluationForm.rating,
                satisfaction_comment: evaluationForm.comment,
                evaluation: updatedEvaluation
              }
            : ticket
        ))
      
      // Update selected ticket
      setSelectedTicket(prev => prev ? {
        ...prev,
        satisfaction_rating: evaluationForm.rating,
        satisfaction_comment: evaluationForm.comment,
        evaluation: updatedEvaluation
      } : null)
      
      setShowEvaluation(false)
      setEvaluationForm({ rating: 5, comment: '' })
      alert('Avaliação enviada com sucesso! Obrigado pelo seu feedback.')
      
      // Refresh ticket data to ensure consistency
      setTimeout(() => {
        fetchTickets()
      }, 500)
    } catch (error: any) {
      console.error('Error submitting evaluation:', error)
      const errorMessage = error.response?.data?.detail || error.message || 'Erro ao enviar avaliação'
      alert(`Erro: ${errorMessage}`)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'open': return <Clock className="w-4 h-4" />
      case 'in_progress': return <AlertCircle className="w-4 h-4" />
      case 'resolved': case 'closed': return <CheckCircle className="w-4 h-4" />
      default: return <Clock className="w-4 h-4" />
    }
  }

  const formatDate = (dateString: string) => {
    if (!dateString || dateString === 'Invalid Date') {
      return 'Data não disponível'
    }
    try {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) {
        return 'Data não disponível'
      }
      return date.toLocaleString('pt-BR')
    } catch (error) {
      return 'Data não disponível'
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Atendimento ao Cliente</h1>
        <div className="flex items-center space-x-3">
          <Link
            to="/chat"
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center space-x-2 transition-colors"
          >
            <MessageCircle className="w-4 h-4" />
            <span>Chat em Tempo Real</span>
          </Link>
          {activeTab === 'tickets' && (
            <button
              onClick={() => setShowCreateTicket(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2"
            >
              <Plus className="w-4 h-4" />
              <span>Novo Ticket</span>
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'tickets', name: 'Meus Tickets', icon: Ticket },
            { id: 'knowledge', name: 'Base de Conhecimento', icon: BookOpen },
            ...(user?.role !== 'citizen' ? [{ id: 'dashboard', name: user?.role === 'support_agent' ? 'Painel do Atendente' : 'Dashboard', icon: BarChart3 }] : [])
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              <span>{tab.name}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tickets Tab */}
      {activeTab === 'tickets' && (
        <div className="space-y-6">
          {!selectedTicket ? (
            <>
              {/* Search and Filters */}
              <div className="bg-white p-4 rounded-lg shadow border space-y-4">
                <div className="flex flex-col sm:flex-row gap-4">
                  <div className="flex-1 relative">
                    <Search className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Buscar tickets..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <select
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="all">Todos os Status</option>
                    <option value="open">Aberto</option>
                    <option value="in_progress">Em Andamento</option>
                    <option value="waiting_client">Aguardando Cliente</option>
                    <option value="resolved">Resolvido</option>
                    <option value="closed">Fechado</option>
                  </select>
                  <select
                    value={filterCategory}
                    onChange={(e) => setFilterCategory(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="all">Todas as Categorias</option>
                    <option value="billing">Faturamento</option>
                    <option value="technical">Técnico</option>
                    <option value="complaint">Reclamação</option>
                    <option value="request">Solicitação</option>
                    <option value="information">Informação</option>
                    <option value="emergency">Emergência</option>
                  </select>
                </div>
              </div>

              {/* Tickets List */}
              <div className="space-y-3">
                {loading ? (
                  <div className="flex justify-center items-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <span className="ml-3 text-gray-600">Carregando tickets...</span>
                  </div>
                ) : filteredTickets.length === 0 ? (
                  <div className="bg-white p-12 rounded-lg shadow border text-center">
                    <Ticket className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Nenhum ticket encontrado</h3>
                    <p className="text-gray-500 mb-4">
                      {searchTerm || filterStatus !== 'all' || filterCategory !== 'all'
                        ? 'Tente ajustar os filtros de busca'
                        : 'Comece criando seu primeiro ticket'}
                    </p>
                    {!searchTerm && filterStatus === 'all' && filterCategory === 'all' && (
                      <button
                        onClick={() => setShowCreateTicket(true)}
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2 mx-auto"
                      >
                        <Plus className="w-4 h-4" />
                        <span>Criar Primeiro Ticket</span>
                      </button>
                    )}
                  </div>
                ) : (
                  filteredTickets.map((ticket) => (
                    <div
                      key={ticket.id}
                      onClick={() => {
                        if (ticket.id) {
                          setSelectedTicket(ticket)
                          fetchTicketMessages(ticket.id)
                        }
                      }}
                      className="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md hover:border-blue-300 transition-all duration-200 cursor-pointer group"
                    >
                      <div className="p-5">
                        {/* Header com número e badges */}
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center space-x-3 flex-1 min-w-0">
                            <div className="flex-shrink-0">
                              <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center group-hover:bg-blue-100 transition-colors">
                                <Ticket className="w-5 h-5 text-blue-600" />
                              </div>
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center space-x-2 mb-1">
                                <span className="font-mono text-sm font-semibold text-gray-700">
                                  #{ticket.ticket_number || ticket.id}
                                </span>
                                <span className={`px-2 py-0.5 rounded-md text-xs font-medium ${categoryColors[ticket.category] || 'bg-gray-100 text-gray-800'}`}>
                                  {translateCategory(ticket.category)}
                                </span>
                                <span className={`px-2 py-0.5 rounded-md text-xs font-medium ${priorityColors[ticket.priority] || 'bg-gray-100 text-gray-800'}`}>
                                  {translatePriority(ticket.priority)}
                                </span>
                              </div>
                              <h3 className="text-base font-semibold text-gray-900 group-hover:text-blue-600 transition-colors truncate">
                                {ticket.title}
                              </h3>
                            </div>
                          </div>
                          <div className="flex-shrink-0 ml-4">
                            <div className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium ${statusColors[ticket.status] || 'bg-gray-100 text-gray-800'}`}>
                              {getStatusIcon(ticket.status)}
                              <span>{translateStatus(ticket.status || '')}</span>
                            </div>
                          </div>
                        </div>

                        {/* Descrição */}
                        <p className="text-gray-600 text-sm line-clamp-2 mb-4 pl-[58px]">
                          {ticket.description}
                        </p>

                        {/* Footer com informações adicionais */}
                        <div className="flex items-center justify-between pt-3 border-t border-gray-100 pl-[58px]">
                          <div className="flex items-center space-x-4 text-xs text-gray-500">
                            <div className="flex items-center space-x-1.5">
                              <Calendar className="w-3.5 h-3.5" />
                              <span>
                                {ticket.created_at && ticket.created_at !== 'Invalid Date' && !isNaN(new Date(ticket.created_at).getTime())
                                  ? new Date(ticket.created_at).toLocaleDateString('pt-BR', {
                                      day: '2-digit',
                                      month: 'short',
                                      year: 'numeric'
                                    })
                                  : ticket.created_at || 'Data não disponível'}
                              </span>
                            </div>
                            {ticket.assigned_agent_name && (
                              <div className="flex items-center space-x-1.5">
                                <User className="w-3.5 h-3.5" />
                                <span className="truncate max-w-[120px]">{ticket.assigned_agent_name}</span>
                              </div>
                            )}
                            {ticket.client_name && (
                              <div className="flex items-center space-x-1.5">
                                <Mail className="w-3.5 h-3.5" />
                                <span className="truncate max-w-[150px]">{ticket.client_name}</span>
                              </div>
                            )}
                          </div>
                          {ticket.satisfaction_rating && (
                            <div className="flex items-center space-x-1">
                              {[...Array(5)].map((_, i) => (
                                <Star
                                  key={i}
                                  className={`w-3.5 h-3.5 ${i < ticket.satisfaction_rating! ? 'text-yellow-400 fill-current' : 'text-gray-300'}`}
                                />
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </>
          ) : (
            /* Ticket Detail View */
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <button
                    onClick={() => setSelectedTicket(null)}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    ← Voltar
                  </button>
                  <h2 className="text-xl font-semibold">Ticket #{selectedTicket.ticket_number}</h2>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[selectedTicket.status]}`}>
                    {translateStatus(selectedTicket.status || '')}
                  </span>
                </div>
                {user?.role === 'citizen' && (
                  <button
                    onClick={() => navigate(`/chat?ticketId=${selectedTicket.id}`)}
                    className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium transition-colors"
                  >
                    <MessageCircle className="w-4 h-4" />
                    <span>Conversar sobre este ticket</span>
                  </button>
                )}
              </div>

              {/* Ticket Info */}
              <div className="bg-white p-6 rounded-lg shadow border">
                <h3 className="text-lg font-semibold mb-4">{selectedTicket.title}</h3>
                <p className="text-gray-700 mb-4">{selectedTicket.description}</p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Categoria:</span>
                    <p className="font-medium">{translateCategory(selectedTicket.category)}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">Prioridade:</span>
                    <p className="font-medium">{translatePriority(selectedTicket.priority)}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">Criado em:</span>
                    <p className="font-medium">{formatDate(selectedTicket.created_at)}</p>
                  </div>
                  {selectedTicket.assigned_agent_name && (
                    <div>
                      <span className="text-gray-500">Atribuído para:</span>
                      <p className="font-medium">{selectedTicket.assigned_agent_name}</p>
                    </div>
                  )}
                </div>
                
                {/* Status Update Section - Only for agents/managers */}
                {user?.role !== 'citizen' && (
                  <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <h4 className="font-semibold text-blue-800 mb-3">Atualizar Status</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedTicket.status !== 'open' && (
                        <button
                          onClick={() => updateTicketStatus(selectedTicket.id, 'open')}
                          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium transition-colors"
                        >
                          Abrir
                        </button>
                      )}
                      {selectedTicket.status !== 'in_progress' && (
                        <button
                          onClick={() => updateTicketStatus(selectedTicket.id, 'in_progress')}
                          className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 text-sm font-medium transition-colors"
                        >
                          Em Andamento
                        </button>
                      )}
                      {selectedTicket.status !== 'waiting_client' && (
                        <button
                          onClick={() => updateTicketStatus(selectedTicket.id, 'waiting_client')}
                          className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 text-sm font-medium transition-colors"
                        >
                          Aguardando Cliente
                        </button>
                      )}
                      {selectedTicket.status !== 'resolved' && (
                        <button
                          onClick={() => updateTicketStatus(selectedTicket.id, 'resolved')}
                          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-medium transition-colors"
                        >
                          Resolver
                        </button>
                      )}
                      {selectedTicket.status !== 'closed' && (
                        <button
                          onClick={() => updateTicketStatus(selectedTicket.id, 'closed')}
                          className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 text-sm font-medium transition-colors"
                        >
                          Fechar
                        </button>
                      )}
                    </div>
                    <p className="text-xs text-blue-600 mt-2">
                      Status atual: <span className="font-medium">{translateStatus(selectedTicket.status || '')}</span>
                    </p>
                  </div>
                )}
                
                {/* Evaluation Section for Resolved/Closed Tickets */}
                {(selectedTicket.status === 'resolved' || selectedTicket.status === 'closed') && (
                  <div className="mt-6 p-4 bg-green-50 rounded-lg border border-green-200">
                    {selectedTicket.satisfaction_rating || selectedTicket.evaluation ? (
                      <div>
                        <h4 className="font-semibold text-green-800 mb-2">Avaliação do Atendimento</h4>
                        <div className="flex items-center space-x-2 mb-2">
                          <span className="text-sm text-green-700">Nota:</span>
                          <div className="flex items-center space-x-1">
                            {[...Array(5)].map((_, i) => {
                              const rating = selectedTicket.satisfaction_rating || selectedTicket.evaluation?.rating || 0
                              return (
                                <Star
                                  key={i}
                                  className={`w-4 h-4 ${i < rating ? 'text-yellow-400 fill-current' : 'text-gray-300'}`}
                                />
                              )
                            })}
                          </div>
                          <span className="text-sm text-green-700">
                            ({(selectedTicket.satisfaction_rating || selectedTicket.evaluation?.rating || 0)}/5)
                          </span>
                        </div>
                        {(selectedTicket.evaluation?.comment || selectedTicket.satisfaction_comment) && (
                          <p className="text-sm text-green-700 italic mt-2">
                            "{(selectedTicket.evaluation?.comment || selectedTicket.satisfaction_comment)}"
                          </p>
                        )}
                        {selectedTicket.evaluation?.evaluated_at && (
                          <p className="text-xs text-green-600 mt-2">
                            Avaliado em: {formatDate(selectedTicket.evaluation.evaluated_at)}
                          </p>
                        )}
                      </div>
                    ) : (
                      <div>
                        <h4 className="font-semibold text-green-800 mb-2">Avalie nosso atendimento</h4>
                        <p className="text-sm text-green-700 mb-3">
                          Seu feedback é importante para melhorarmos nossos serviços.
                        </p>
                        <button
                          onClick={() => setShowEvaluation(true)}
                          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm font-medium"
                        >
                          Avaliar Atendimento
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Messages */}
              <div className="bg-white rounded-lg shadow border">
                <div className="p-4 border-b flex justify-between items-center">
                  <h4 className="font-semibold">Conversas</h4>
                  {user?.role !== 'citizen' && (
                    <button
                      onClick={() => setShowInternalMessages(!showInternalMessages)}
                      className="flex items-center space-x-2 text-sm text-gray-600 hover:text-gray-800"
                    >
                      {showInternalMessages ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      <span>{showInternalMessages ? 'Ocultar' : 'Mostrar'} Internas</span>
                    </button>
                  )}
                </div>
                <div className="p-4 space-y-4 max-h-96 overflow-y-auto">
                  {ticketMessages.map((message) => {
                    const isAIAssistant = message.author_name === 'Assistente Virtual'
                    const isClient = message.message_type === 'client'
                    const isSystem = message.message_type === 'system'
                    
                    return (
                      <div key={message.id} className={`flex ${isClient ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                          isClient
                            ? 'bg-blue-600 text-white'
                            : isAIAssistant
                            ? 'bg-gradient-to-r from-purple-100 to-blue-100 text-gray-800 border-2 border-purple-300'
                            : message.is_internal
                            ? 'bg-yellow-100 text-yellow-800 border border-yellow-300'
                            : isSystem
                            ? 'bg-gray-50 text-gray-600 border border-gray-200'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          <div className="flex items-center space-x-2 mb-1">
                            {isAIAssistant && (
                              <MessageSquare className="w-3 h-3 text-purple-600" />
                            )}
                            <span className={`text-xs font-medium ${isAIAssistant ? 'text-purple-700' : ''}`}>
                              {message.author_name}
                            </span>
                            {message.is_internal && <span className="text-xs">(Interno)</span>}
                            {isAIAssistant && (
                              <span className="text-xs bg-purple-200 text-purple-700 px-1.5 py-0.5 rounded-full">
                                IA
                              </span>
                            )}
                            <span className="text-xs opacity-75">{formatDate(message.created_at)}</span>
                          </div>
                          <div 
                            className="text-sm prose prose-sm max-w-none"
                            dangerouslySetInnerHTML={{ __html: message.content }}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
                
                {/* AI Suggestion */}
                {aiSuggestion && aiSuggestion.suggestion && (
                  <div className="p-4 border-t bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center">
                          <MessageSquare className="w-4 h-4 text-white" />
                        </div>
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            <span className="text-sm font-semibold text-purple-900">Sugestão da IA</span>
                            <span className="text-xs text-purple-600 bg-purple-100 px-2 py-0.5 rounded-full">
                              {Math.round(aiSuggestion.confidence * 100)}% de confiança
                            </span>
                          </div>
                          <button
                            onClick={() => setAiSuggestion(null)}
                            className="text-purple-600 hover:text-purple-800"
                          >
                            <span className="text-xs">✕</span>
                          </button>
                        </div>
                        <p className="text-sm text-gray-700 mb-3 bg-white p-3 rounded-lg border border-purple-200">
                          {aiSuggestion.suggestion}
                        </p>
                        {aiSuggestion.relevant_articles && aiSuggestion.relevant_articles.length > 0 && (
                          <div className="mb-3">
                            <p className="text-xs text-purple-700 mb-1 font-medium">Artigos relacionados:</p>
                            <div className="flex flex-wrap gap-2">
                              {aiSuggestion.relevant_articles.slice(0, 3).map((article) => (
                                <span
                                  key={article.id}
                                  className="text-xs bg-white text-purple-700 px-2 py-1 rounded border border-purple-200"
                                >
                                  {article.title}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => {
                              setNewMessage(aiSuggestion.suggestion || '')
                              setAiSuggestion(null)
                            }}
                            className="text-xs bg-purple-600 text-white px-3 py-1.5 rounded-lg hover:bg-purple-700 font-medium"
                          >
                            Usar Sugestão
                          </button>
                          {aiSuggestion.suggestions && aiSuggestion.suggestions.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {aiSuggestion.suggestions.slice(0, 2).map((suggestion, idx) => (
                                <button
                                  key={idx}
                                  onClick={() => {
                                    setNewMessage(suggestion)
                                    fetchAiSuggestion(suggestion)
                                  }}
                                  className="text-xs bg-white text-purple-700 px-2 py-1 rounded border border-purple-200 hover:bg-purple-50"
                                >
                                  {suggestion}
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                        {aiSuggestion.should_escalate && (
                          <div className="mt-2 text-xs text-orange-600 bg-orange-50 px-2 py-1 rounded border border-orange-200">
                            ⚠️ Recomendamos escalar para um agente humano
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
                {loadingAiSuggestion && (
                  <div className="p-4 border-t bg-purple-50">
                    <div className="flex items-center space-x-2 text-sm text-purple-600">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-600"></div>
                      <span>Analisando sua mensagem...</span>
                    </div>
                  </div>
                )}
                {/* Message Form with Rich Text Editor */}
                <form onSubmit={sendMessage} className="p-4 border-t">
                  <div className="space-y-2">
                    <div className="border border-gray-300 rounded-lg overflow-hidden focus-within:ring-2 focus-within:ring-blue-500">
                      <ReactQuill
                        theme="snow"
                        value={newMessage}
                        onChange={setNewMessage}
                        placeholder="Digite sua mensagem..."
                        modules={{
                          toolbar: [
                            [{ 'header': [1, 2, 3, false] }],
                            ['bold', 'italic', 'underline', 'strike'],
                            [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                            [{ 'color': [] }, { 'background': [] }],
                            ['link'],
                            ['clean']
                          ]
                        }}
                        formats={[
                          'header',
                          'bold', 'italic', 'underline', 'strike',
                          'list', 'bullet',
                          'color', 'background',
                          'link'
                        ]}
                        style={{ 
                          minHeight: '120px',
                          maxHeight: '200px'
                        }}
                        className="bg-white"
                      />
                    </div>
                    <div className="flex justify-end">
                      <button
                        type="submit"
                        disabled={!newMessage.replace(/<[^>]*>/g, '').trim()}
                        className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                      >
                        <Send className="w-4 h-4" />
                        <span>Enviar</span>
                      </button>
                    </div>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Knowledge Base Tab */}
      {activeTab === 'knowledge' && (
        <div className="space-y-6">
          {/* Search controls */}
          <div className="bg-white p-4 rounded-lg shadow border space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="md:col-span-2 relative">
                <Search className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Buscar por texto..."
                  value={kbSearch}
                  onChange={(e) => setKbSearch(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <select
                value={kbCategory}
                onChange={(e) => setKbCategory(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">Todas as Categorias</option>
                <option value="billing">Faturamento</option>
                <option value="request">Solicitação</option>
                <option value="information">Informação</option>
                <option value="emergency">Emergência</option>
              </select>
              <input
                type="text"
                placeholder="Filtrar por tag (ex: vazamento, tarifa)"
                value={kbTag}
                onChange={(e) => setKbTag(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Results */}
          <div className="grid gap-6">
            {kbFiltered.map((article) => (
              <div key={article.id} className="bg-white p-6 rounded-lg shadow border">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{article.title}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${categoryColors[article.category]}`}>
                      {article.category}
                    </span>
                    {article.tags?.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-2">
                        {article.tags.map((t) => (
                          <span key={t} className="px-2 py-0.5 rounded-full bg-gray-100 text-gray-700 text-xs">#{t}</span>
                        ))}
                      </div>
                    )}
                  </div>
                  {article.is_featured && (
                    <Star className="w-5 h-5 text-yellow-400 fill-current" />
                  )}
                </div>
                <p className="text-gray-700 text-sm mb-4">{article.content}</p>
                <div className="flex flex-wrap justify-between items-center text-sm text-gray-500 gap-2">
                  <div className="flex items-center space-x-4">
                    <span>{article.view_count} visualizações</span>
                    <span>{article.helpful_count} útil</span>
                    <span>{article.not_helpful_count} não útil</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button onClick={() => markHelpful(article.id, true)} className="px-3 py-1 rounded bg-green-50 text-green-700 hover:bg-green-100">Útil</button>
                    <button onClick={() => markHelpful(article.id, false)} className="px-3 py-1 rounded bg-red-50 text-red-700 hover:bg-red-100">Não útil</button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Simple Analytics */}
          <div className="bg-white p-4 rounded-lg shadow border text-sm text-gray-600">
            <div className="flex gap-6">
              <div>Total de visualizações: <span className="font-medium text-gray-900">{kbAnalytics.views}</span></div>
              <div>Úteis: <span className="font-medium text-gray-900">{kbAnalytics.helpful}</span></div>
              <div>Não úteis: <span className="font-medium text-gray-900">{kbAnalytics.notHelpful}</span></div>
            </div>
          </div>
        </div>
      )}

      {/* Dashboard Tab */}
      {activeTab === 'dashboard' && user?.role !== 'citizen' && (
        <div className="space-y-6">
          {user?.role === 'support_agent' ? (
            /* Agent Dashboard */
            <>
              {/* Agent Info Card */}
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-6 rounded-lg shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-semibold">Bem-vindo, {agentDashboardStats.agent_info?.name || 'Agente'}</h2>
                    <p className="text-blue-100">Atendente de Suporte</p>
                  </div>
                  <div className="text-center">
                    <div className="flex items-center space-x-1 mb-1">
                      {[...Array(5)].map((_, i) => (
                        <Star
                          key={i}
                          className={`w-4 h-4 ${i < Math.floor(agentDashboardStats.agent_info?.satisfaction_rating || 0) ? 'text-yellow-300 fill-current' : 'text-blue-300'}`}
                        />
                      ))}
                    </div>
                    <p className="text-sm text-blue-100">Avaliação: {(agentDashboardStats.agent_info?.satisfaction_rating || 0).toFixed(1)}</p>
                  </div>
                </div>
              </div>

              {/* Agent Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="bg-white p-6 rounded-lg shadow border">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <Ticket className="h-8 w-8 text-blue-600" />
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">Tickets Atribuídos</dt>
                        <dd className="text-lg font-medium text-gray-900">{agentDashboardStats.my_tickets?.total_assigned || 0}</dd>
                      </dl>
                    </div>
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow border">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <Clock className="h-8 w-8 text-yellow-600" />
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">Em Aberto</dt>
                        <dd className="text-lg font-medium text-gray-900">{agentDashboardStats.my_tickets?.open || 0}</dd>
                      </dl>
                    </div>
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow border">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <AlertCircle className="h-8 w-8 text-orange-600" />
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">Em Andamento</dt>
                        <dd className="text-lg font-medium text-gray-900">{agentDashboardStats.my_tickets?.in_progress || 0}</dd>
                      </dl>
                    </div>
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow border">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <CheckCircle className="h-8 w-8 text-green-600" />
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">Resolvidos Hoje</dt>
                        <dd className="text-lg font-medium text-gray-900">{agentDashboardStats.my_tickets?.resolved_today || 0}</dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              {/* Performance and Pending Tickets */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white p-6 rounded-lg shadow border">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Estatísticas do Dia</h3>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Novos Tickets Hoje</span>
                      <span className="text-sm font-medium text-gray-900">
                        {agentDashboardStats.daily_stats?.new_tickets_today || 0}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Aguardando Atribuição</span>
                      <span className="text-sm font-medium text-gray-900">
                        {agentDashboardStats.daily_stats?.pending_assignment || 0}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Total Resolvidos</span>
                      <span className="text-sm font-medium text-gray-900">
                        {agentDashboardStats.agent_info?.total_resolved || 0}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Tempo Médio de Resposta</span>
                      <span className="text-sm font-medium text-gray-900">
                        {(agentDashboardStats.agent_info?.average_response_time || 0).toFixed(1)}h
                      </span>
                    </div>
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow border">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Tickets Pendentes</h3>
                  <div className="space-y-3 max-h-64 overflow-y-auto">
                    {Array.isArray(agentDashboardStats.pending_tickets) && agentDashboardStats.pending_tickets.slice(0, 5).map((ticket: any) => (
                      <div key={ticket.id} className="flex justify-between items-center p-3 bg-yellow-50 rounded border border-yellow-200">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">#{ticket.ticket_number}</p>
                          <p className="text-xs text-gray-500 truncate">{ticket.title}</p>
                          <div className="flex items-center space-x-2 mt-1">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${priorityColors[ticket.priority]}`}>
                              {ticket.priority}
                            </span>
                            {!ticket.assigned_agent_id && (
                              <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                Não Atribuído
                              </span>
                            )}
                          </div>
                        </div>
                        <button
                          onClick={() => {
                            if (ticket.id) {
                              setSelectedTicket(ticket)
                              setActiveTab('tickets')
                              fetchTicketMessages(ticket.id)
                            }
                          }}
                          className="ml-2 text-blue-600 hover:text-blue-800 text-sm font-medium"
                        >
                          Assumir
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Recent Assigned Tickets */}
              <div className="bg-white rounded-lg shadow border">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Meus Tickets Recentes</h3>
                </div>
                <div className="divide-y divide-gray-200">
                  {Array.isArray(agentDashboardStats.recent_assigned) && agentDashboardStats.recent_assigned.map((ticket: any) => (
                    <div key={ticket.id} className="px-6 py-4 hover:bg-gray-50">
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-3">
                            <span className="font-mono text-sm text-gray-500">#{ticket.ticket_number}</span>
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[ticket.status]}`}>
                              {translateStatus(ticket.status || '')}
                            </span>
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${priorityColors[ticket.priority]}`}>
                              {ticket.priority}
                            </span>
                          </div>
                          <p className="text-sm text-gray-900 mt-1 truncate">{ticket.title}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            {ticket.client_name} • {formatDate(ticket.created_at)}
                          </p>
                        </div>
                        <button
                          onClick={() => {
                            if (ticket.id) {
                              setSelectedTicket(ticket)
                              setActiveTab('tickets')
                              fetchTicketMessages(ticket.id)
                            }
                          }}
                          className="ml-4 text-blue-600 hover:text-blue-800 text-sm font-medium"
                        >
                          Ver
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            /* Manager Dashboard */
            <>
              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="bg-white p-6 rounded-lg shadow border">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <Ticket className="h-8 w-8 text-blue-600" />
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">Total de Tickets</dt>
                        <dd className="text-lg font-medium text-gray-900">{dashboardStats.total_tickets}</dd>
                      </dl>
                    </div>
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow border">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <Clock className="h-8 w-8 text-yellow-600" />
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">Tickets Abertos</dt>
                        <dd className="text-lg font-medium text-gray-900">{dashboardStats.open_tickets}</dd>
                      </dl>
                    </div>
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow border">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <AlertCircle className="h-8 w-8 text-orange-600" />
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">Em Andamento</dt>
                        <dd className="text-lg font-medium text-gray-900">{dashboardStats.in_progress_tickets}</dd>
                      </dl>
                    </div>
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow border">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <CheckCircle className="h-8 w-8 text-green-600" />
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">Resolvidos</dt>
                        <dd className="text-lg font-medium text-gray-900">{dashboardStats.resolved_tickets}</dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              {/* Performance Metrics */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white p-6 rounded-lg shadow border">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Métricas de Performance</h3>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Tempo Médio de Resolução</span>
                      <span className="text-sm font-medium text-gray-900">
                        {(dashboardStats.average_resolution_time || 0).toFixed(1)} horas
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Satisfação Média</span>
                      <div className="flex items-center space-x-2">
                        <div className="flex items-center">
                          {[...Array(5)].map((_, i) => (
                            <Star
                              key={i}
                              className={`w-4 h-4 ${i < Math.floor(dashboardStats.satisfaction_average || 0) ? 'text-yellow-400 fill-current' : 'text-gray-300'}`}
                            />
                          ))}
                        </div>
                        <span className="text-sm font-medium text-gray-900">
                          {(dashboardStats.satisfaction_average || 0).toFixed(1)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow border">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Distribuição por Categoria</h3>
                  <div className="space-y-3">
                    {Array.isArray(dashboardStats.tickets_by_category) && dashboardStats.tickets_by_category.length > 0 ? (
                      dashboardStats.tickets_by_category.map((item: any) => (
                        <div key={item.category} className="flex justify-between items-center">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${categoryColors[item.category] || 'bg-gray-100 text-gray-800'}`}>
                            {item.category}
                          </span>
                          <span className="text-sm font-medium text-gray-900">{item.count}</span>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-gray-500">Nenhuma categoria com tickets registrada</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Recent Tickets */}
              <div className="bg-white rounded-lg shadow border">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Tickets Recentes</h3>
                </div>
                <div className="divide-y divide-gray-200">
                  {Array.isArray(dashboardStats.recent_tickets) && dashboardStats.recent_tickets.length > 0 ? (
                    dashboardStats.recent_tickets.slice(0, 5).map((ticket: any) => (
                      <div key={ticket.id} className="px-6 py-4 hover:bg-gray-50">
                        <div className="flex items-center justify-between">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-3">
                              <span className="font-mono text-sm text-gray-500">#{ticket.ticket_number}</span>
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[ticket.status] || 'bg-gray-100 text-gray-800'}`}>
                                {translateStatus(ticket.status || '')}
                              </span>
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${priorityColors[ticket.priority] || 'bg-gray-100 text-gray-800'}`}>
                                {ticket.priority}
                              </span>
                            </div>
                            <p className="text-sm text-gray-900 mt-1 truncate">{ticket.title}</p>
                            <p className="text-xs text-gray-500 mt-1">
                              {ticket.client_name} • {formatDate(ticket.created_at)}
                            </p>
                          </div>
                          <button
                            onClick={() => {
                              if (ticket.id) {
                                setSelectedTicket(ticket)
                                setActiveTab('tickets')
                                fetchTicketMessages(ticket.id)
                              }
                            }}
                            className="ml-4 text-blue-600 hover:text-blue-800 text-sm font-medium"
                          >
                            Ver
                          </button>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="px-6 py-8 text-center text-gray-500">
                      <p>Nenhum ticket recente encontrado</p>
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* Create Ticket Modal with auto-suggestions */}
      {showCreateTicket && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-semibold mb-4">Criar Novo Ticket</h3>
            <form onSubmit={createTicket} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Título</label>
                <input
                  type="text"
                  value={newTicket.title}
                  onChange={(e) => setNewTicket({ ...newTicket, title: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Descrição</label>
                <textarea
                  value={newTicket.description}
                  onChange={(e) => setNewTicket({ ...newTicket, description: e.target.value })}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Categoria</label>
                  <select
                    value={newTicket.category}
                    onChange={(e) => setNewTicket({ ...newTicket, category: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="request">Solicitação</option>
                    <option value="complaint">Reclamação</option>
                    <option value="technical">Técnico</option>
                    <option value="billing">Faturamento</option>
                    <option value="information">Informação</option>
                    <option value="emergency">Emergência</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Prioridade</label>
                  <select
                    value={newTicket.priority}
                    onChange={(e) => setNewTicket({ ...newTicket, priority: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="low">Baixa</option>
                    <option value="medium">Média</option>
                    <option value="high">Alta</option>
                    <option value="urgent">Urgente</option>
                  </select>
                </div>
              </div>
              {/* Suggestions */}
              {suggestions.length > 0 && (
                <div className="p-3 bg-blue-50 rounded border border-blue-200">
                  <div className="text-xs text-blue-800 mb-2">Sugestões com base no que você digitou:</div>
                  <ul className="list-disc list-inside space-y-1 text-sm text-blue-900">
                    {suggestions.map((s) => (
                      <li key={s.id} className="flex items-center justify-between">
                        <span>
                          {s.title}
                          <span className={`ml-2 px-2 py-0.5 rounded-full text-[10px] ${categoryColors[s.category]}`}>{s.category}</span>
                        </span>
                        <button
                          type="button"
                          onClick={() => {
                            setActiveTab('knowledge')
                            setKbSearch(s.title)
                            setShowCreateTicket(false)
                          }}
                          className="text-blue-700 hover:text-blue-900 text-xs"
                        >
                          Ver artigo
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateTicket(false)}
                  className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Criando...' : 'Criar Ticket'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Evaluation Modal */}
      {showEvaluation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-semibold mb-4">Avaliar Atendimento</h3>
            <form onSubmit={submitEvaluation} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Nota (1-5)</label>
                <div className="flex items-center space-x-2">
                  {[1, 2, 3, 4, 5].map((rating) => (
                    <button
                      key={rating}
                      type="button"
                      onClick={() => setEvaluationForm(prev => ({ ...prev, rating }))}
                      className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        evaluationForm.rating >= rating
                          ? 'bg-yellow-400 text-white'
                          : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                      }`}
                    >
                      <Star className="w-4 h-4" />
                    </button>
                  ))}
                  <span className="text-sm text-gray-600 ml-2">
                    {evaluationForm.rating === 1 && 'Muito Ruim'}
                    {evaluationForm.rating === 2 && 'Ruim'}
                    {evaluationForm.rating === 3 && 'Regular'}
                    {evaluationForm.rating === 4 && 'Bom'}
                    {evaluationForm.rating === 5 && 'Excelente'}
                  </span>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Comentário (opcional)</label>
                <textarea
                  value={evaluationForm.comment}
                  onChange={(e) => setEvaluationForm(prev => ({ ...prev, comment: e.target.value }))}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Deixe um comentário sobre o atendimento..."
                />
              </div>
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowEvaluation(false)}
                  className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  Enviar Avaliação
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}