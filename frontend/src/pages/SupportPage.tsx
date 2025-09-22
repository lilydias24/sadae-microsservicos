import React, { useState, useEffect } from 'react'
import { api } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
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
  EyeOff
} from 'lucide-react'

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

const priorityColors: Record<string, string> = {
  low: 'bg-gray-100 text-gray-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-orange-100 text-orange-800',
  urgent: 'bg-red-100 text-red-800'
}

export function SupportPage() {
  const { user } = useAuth()
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
  const [dashboardStats, setDashboardStats] = useState({
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
      const { data } = await api.get('/support/tickets')
      setTickets(data)
    } catch (error) {
      console.error('Error fetching tickets:', error)
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
      setDashboardStats(data)
    } catch (error) {
      console.error('Error fetching dashboard stats:', error)
    }
  }

  const fetchAgentDashboardStats = async () => {
    try {
      const { data } = await api.get('/support/agent-dashboard')
      setAgentDashboardStats(data)
    } catch (error) {
      console.error('Error fetching agent dashboard stats:', error)
    }
  }

  const fetchTicketMessages = async (ticketId: number) => {
    try {
      const { data } = await api.get(`/support/tickets/${ticketId}/messages`, {
        params: { include_internal: showInternalMessages },
      })
      setTicketMessages(data)
    } catch (error) {
      console.error('Error fetching ticket messages:', error)
    }
  }

  const createTicket = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setLoading(true)
      const { data } = await api.post('/support/tickets', newTicket)
      setTickets([data, ...tickets])
      setNewTicket({ title: '', description: '', category: 'request', priority: 'medium' })
      setShowCreateTicket(false)
    } catch (error) {
      console.error('Error creating ticket:', error)
      alert('Não foi possível criar o ticket. Verifique os dados e tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedTicket || !newMessage.trim()) return

    try {
      await api.post(`/support/tickets/${selectedTicket.id}/messages`, { content: newMessage })
      setNewMessage('')
      fetchTicketMessages(selectedTicket.id)
    } catch (error) {
      console.error('Error sending message:', error)
    }
  }

  const filteredTickets = tickets.filter(ticket => {
    const matchesSearch = ticket.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         ticket.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         ticket.ticket_number.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = filterStatus === 'all' || ticket.status === filterStatus
    const matchesCategory = filterCategory === 'all' || ticket.category === filterCategory
    return matchesSearch && matchesStatus && matchesCategory
  })

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
    const combined = `${a.title} ${a.content} ${a.keywords.join(' ')} ${a.tags.join(' ')}`
    const textMatch = !kbSearch || normalize(combined).includes(normalize(kbSearch))
    const categoryMatch = kbCategory === 'all' || a.category === kbCategory
    const tagMatch = !kbTag || a.tags.some((t) => normalize(t).includes(normalize(kbTag))) || (kbTagMap[a.id] && kbTagMap[a.id].some((t) => normalize(t).includes(normalize(kbTag))))
    return textMatch && categoryMatch && tagMatch
  })

  // Auto suggestions while creating a ticket
  const suggestionPool = knowledgeBase.map((a) => ({ id: a.id, title: a.title, category: a.category }))
  const suggestions = !newTicket.title && !newTicket.description
    ? []
    : suggestionPool.filter((s) => {
        const q = normalize(`${newTicket.title} ${newTicket.description}`)
        return normalize(s.title).includes(q) || q.split(' ').some((w) => normalize(s.title).includes(w))
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
      await api.post(`/support/tickets/${selectedTicket.id}/evaluate`, evaluationForm)
      setTickets(prev => prev.map(ticket => 
          ticket.id === selectedTicket.id 
            ? {
                ...ticket,
                evaluation: {
                  rating: evaluationForm.rating,
                  comment: evaluationForm.comment,
                  evaluated_at: new Date().toISOString()
                }
              }
            : ticket
        ))
      setShowEvaluation(false)
      setEvaluationForm({ rating: 5, comment: '' })
      alert('Avaliação enviada com sucesso! Obrigado pelo seu feedback.')
    } catch (error) {
      console.error('Error submitting evaluation:', error)
      alert('Erro ao enviar avaliação. Tente novamente.')
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
    return new Date(dateString).toLocaleString('pt-BR')
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Atendimento ao Cliente</h1>
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
              <div className="space-y-4">
                {filteredTickets.map((ticket) => (
                  <div
                    key={ticket.id}
                    onClick={() => {
                      setSelectedTicket(ticket)
                      fetchTicketMessages(ticket.id)
                    }}
                    className="bg-white p-6 rounded-lg shadow border hover:shadow-md transition-shadow cursor-pointer"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <span className="font-mono text-sm text-gray-500">#{ticket.ticket_number}</span>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${categoryColors[ticket.category]}`}>
                            {ticket.category}
                          </span>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${priorityColors[ticket.priority]}`}>
                            {ticket.priority}
                          </span>
                        </div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">{ticket.title}</h3>
                        <p className="text-gray-600 text-sm line-clamp-2">{ticket.description}</p>
                        <div className="flex items-center space-x-4 mt-3 text-sm text-gray-500">
                          <div className="flex items-center space-x-1">
                            <Calendar className="w-4 h-4" />
                            <span>{formatDate(ticket.created_at)}</span>
                          </div>
                          {ticket.assigned_agent_name && (
                            <div className="flex items-center space-x-1">
                              <User className="w-4 h-4" />
                              <span>{ticket.assigned_agent_name}</span>
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="flex flex-col items-end space-y-2">
                        <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm font-medium ${statusColors[ticket.status]}`}>
                          {getStatusIcon(ticket.status)}
                          <span>{ticket.status.replace('_', ' ')}</span>
                        </div>
                        {ticket.satisfaction_rating && (
                          <div className="flex items-center space-x-1">
                            {[...Array(5)].map((_, i) => (
                              <Star
                                key={i}
                                className={`w-4 h-4 ${i < ticket.satisfaction_rating! ? 'text-yellow-400 fill-current' : 'text-gray-300'}`}
                              />
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            /* Ticket Detail View */
            <div className="space-y-6">
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => setSelectedTicket(null)}
                  className="text-blue-600 hover:text-blue-800"
                >
                  ← Voltar
                </button>
                <h2 className="text-xl font-semibold">Ticket #{selectedTicket.ticket_number}</h2>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[selectedTicket.status]}`}>
                  {selectedTicket.status.replace('_', ' ')}
                </span>
              </div>

              {/* Ticket Info */}
              <div className="bg-white p-6 rounded-lg shadow border">
                <h3 className="text-lg font-semibold mb-4">{selectedTicket.title}</h3>
                <p className="text-gray-700 mb-4">{selectedTicket.description}</p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Categoria:</span>
                    <p className="font-medium">{selectedTicket.category}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">Prioridade:</span>
                    <p className="font-medium">{selectedTicket.priority}</p>
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
                
                {/* Evaluation Section for Resolved Tickets */}
                {selectedTicket.status === 'resolved' && (
                  <div className="mt-6 p-4 bg-green-50 rounded-lg border border-green-200">
                    {selectedTicket.evaluation ? (
                      <div>
                        <h4 className="font-semibold text-green-800 mb-2">Avaliação do Atendimento</h4>
                        <div className="flex items-center space-x-2 mb-2">
                          <span className="text-sm text-green-700">Nota:</span>
                          <div className="flex items-center space-x-1">
                            {[...Array(5)].map((_, i) => (
                              <Star
                                key={i}
                                className={`w-4 h-4 ${i < selectedTicket.evaluation!.rating ? 'text-yellow-400 fill-current' : 'text-gray-300'}`}
                              />
                            ))}
                          </div>
                          <span className="text-sm text-green-700">({selectedTicket.evaluation.rating}/5)</span>
                        </div>
                        {selectedTicket.evaluation.comment && (
                          <p className="text-sm text-green-700 italic">"{selectedTicket.evaluation.comment}"</p>
                        )}
                        <p className="text-xs text-green-600 mt-2">
                          Avaliado em: {formatDate(selectedTicket.evaluation.evaluated_at)}
                        </p>
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
                  {ticketMessages.map((message) => (
                    <div key={message.id} className={`flex ${message.message_type === 'client' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        message.message_type === 'client' 
                          ? 'bg-blue-600 text-white'
                          : message.is_internal
                          ? 'bg-yellow-100 text-yellow-800 border border-yellow-300'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        <div className="flex items-center space-x-2 mb-1">
                          <span className="text-xs font-medium">{message.author_name}</span>
                          {message.is_internal && <span className="text-xs">(Interno)</span>}
                          <span className="text-xs opacity-75">{formatDate(message.created_at)}</span>
                        </div>
                        <p className="text-sm">{message.content}</p>
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Message Form */}
                <form onSubmit={sendMessage} className="p-4 border-t">
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      placeholder="Digite sua mensagem..."
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <button
                      type="submit"
                      disabled={!newMessage.trim()}
                      className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Send className="w-4 h-4" />
                    </button>
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
                    <h2 className="text-xl font-semibold">Bem-vindo, {agentDashboardStats.agent_info.name}</h2>
                    <p className="text-blue-100">Atendente de Suporte</p>
                  </div>
                  <div className="text-center">
                    <div className="flex items-center space-x-1 mb-1">
                      {[...Array(5)].map((_, i) => (
                        <Star
                          key={i}
                          className={`w-4 h-4 ${i < Math.floor(agentDashboardStats.agent_info.satisfaction_rating) ? 'text-yellow-300 fill-current' : 'text-blue-300'}`}
                        />
                      ))}
                    </div>
                    <p className="text-sm text-blue-100">Avaliação: {agentDashboardStats.agent_info.satisfaction_rating.toFixed(1)}</p>
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
                        <dd className="text-lg font-medium text-gray-900">{agentDashboardStats.my_tickets.total_assigned}</dd>
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
                        <dd className="text-lg font-medium text-gray-900">{agentDashboardStats.my_tickets.open}</dd>
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
                        <dd className="text-lg font-medium text-gray-900">{agentDashboardStats.my_tickets.in_progress}</dd>
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
                        <dd className="text-lg font-medium text-gray-900">{agentDashboardStats.my_tickets.resolved_today}</dd>
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
                        {agentDashboardStats.daily_stats.new_tickets_today}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Aguardando Atribuição</span>
                      <span className="text-sm font-medium text-gray-900">
                        {agentDashboardStats.daily_stats.pending_assignment}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Total Resolvidos</span>
                      <span className="text-sm font-medium text-gray-900">
                        {agentDashboardStats.agent_info.total_resolved}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Tempo Médio de Resposta</span>
                      <span className="text-sm font-medium text-gray-900">
                        {agentDashboardStats.agent_info.average_response_time.toFixed(1)}h
                      </span>
                    </div>
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow border">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Tickets Pendentes</h3>
                  <div className="space-y-3 max-h-64 overflow-y-auto">
                    {agentDashboardStats.pending_tickets.slice(0, 5).map((ticket: any) => (
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
                            setSelectedTicket(ticket)
                            setActiveTab('tickets')
                            fetchTicketMessages(ticket.id)
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
                  {agentDashboardStats.recent_assigned.map((ticket: any) => (
                    <div key={ticket.id} className="px-6 py-4 hover:bg-gray-50">
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-3">
                            <span className="font-mono text-sm text-gray-500">#{ticket.ticket_number}</span>
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[ticket.status]}`}>
                              {ticket.status.replace('_', ' ')}
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
                            setSelectedTicket(ticket)
                            setActiveTab('tickets')
                            fetchTicketMessages(ticket.id)
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
                        {dashboardStats.average_resolution_time.toFixed(1)} horas
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Satisfação Média</span>
                      <div className="flex items-center space-x-2">
                        <div className="flex items-center">
                          {[...Array(5)].map((_, i) => (
                            <Star
                              key={i}
                              className={`w-4 h-4 ${i < Math.floor(dashboardStats.satisfaction_average) ? 'text-yellow-400 fill-current' : 'text-gray-300'}`}
                            />
                          ))}
                        </div>
                        <span className="text-sm font-medium text-gray-900">
                          {dashboardStats.satisfaction_average.toFixed(1)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow border">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Distribuição por Categoria</h3>
                  <div className="space-y-3">
                    {dashboardStats.tickets_by_category.map((item: any) => (
                      <div key={item.category} className="flex justify-between items-center">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${categoryColors[item.category]}`}>
                          {item.category}
                        </span>
                        <span className="text-sm font-medium text-gray-900">{item.count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Recent Tickets */}
              <div className="bg-white rounded-lg shadow border">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Tickets Recentes</h3>
                </div>
                <div className="divide-y divide-gray-200">
                  {dashboardStats.recent_tickets.slice(0, 5).map((ticket: any) => (
                    <div key={ticket.id} className="px-6 py-4 hover:bg-gray-50">
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-3">
                            <span className="font-mono text-sm text-gray-500">#{ticket.ticket_number}</span>
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[ticket.status]}`}>
                              {ticket.status.replace('_', ' ')}
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
                            setSelectedTicket(ticket)
                            setActiveTab('tickets')
                            fetchTicketMessages(ticket.id)
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