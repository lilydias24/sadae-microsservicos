"use client"

import React, { useState, useEffect, useRef } from 'react'
import { Bot, User, Send, Loader2, MessageSquare, DollarSign, Search, X, Wifi, WifiOff, Receipt, AlertCircle, Users } from 'lucide-react'
import { api } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import { useChatWebSocket } from '../hooks/useChatWebSocket'

interface ChatMessage {
  id: string
  content: string
  sender: 'user' | 'agent' | 'bot'
  timestamp: Date
  ticket_id?: number
  author_name?: string
}

interface BillingSummary {
  totalBills: number
  overdueAmount: number
  contestedBills: number
  activeNegotiations: number
}

export function BillingChatPage() {
  const { user } = useAuth()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [currentTicketId, setCurrentTicketId] = useState<number | null>(null)
  const [chatHistory, setChatHistory] = useState<Array<{ id: number; title: string; created_at: string }>>([])
  const [showHistory, setShowHistory] = useState(false)
  const [billingSummary, setBillingSummary] = useState<BillingSummary | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  // WebSocket hook
  const { 
    messages: wsMessages, 
    isConnected: wsConnected, 
    sendMessage: wsSendMessage,
    sendTyping: wsSendTyping,
    error: wsError 
  } = useChatWebSocket(currentTicketId)
  
  // Sincronizar mensagens do WebSocket
  useEffect(() => {
    if (currentTicketId && wsMessages.length > 0) {
      const convertedMessages: ChatMessage[] = wsMessages.map((msg) => ({
        id: `msg-${msg.id}`,
        content: msg.content,
        sender: msg.message_type === 'client' ? 'user' : msg.message_type === 'agent' ? 'bot' : 'bot',
        timestamp: new Date(msg.created_at),
        ticket_id: msg.ticket_id,
        author_name: msg.author_name
      }))
      setMessages(convertedMessages)
    }
  }, [wsMessages, currentTicketId])

  useEffect(() => {
    if (user) {
      initializeChat()
      loadChatHistory()
      loadBillingSummary()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadBillingSummary = async () => {
    try {
      const [billsRes, contestsRes, negotiationsRes] = await Promise.allSettled([
        api.get('/billing/bills'),
        api.get('/billing/contests'),
        api.get('/billing/negotiations')
      ])

      const bills = billsRes.status === 'fulfilled' ? billsRes.value.data : []
      const contests = contestsRes.status === 'fulfilled' ? contestsRes.value.data : []
      const negotiations = negotiationsRes.status === 'fulfilled' ? negotiationsRes.value.data : []

      const overdueBills = Array.isArray(bills) ? bills.filter((b: any) => b.status === 'overdue') : []
      const overdueAmount = overdueBills.reduce((sum: number, b: any) => sum + (b.amount || 0), 0)

      setBillingSummary({
        totalBills: Array.isArray(bills) ? bills.length : 0,
        overdueAmount,
        contestedBills: Array.isArray(contests) ? contests.length : 0,
        activeNegotiations: Array.isArray(negotiations) ? negotiations.filter((n: any) => n.status === 'pending').length : 0
      })
    } catch (error) {
      console.error('Erro ao carregar resumo de faturamento:', error)
    }
  }

  const initializeChat = async () => {
    setIsLoading(true)
    try {
      const welcomeMessage: ChatMessage = {
        id: `welcome-${Date.now()}`,
        content: `Olá${user?.full_name ? `, ${user.full_name}` : ''}! 💰\n\nBem-vindo ao atendimento de Faturamento do SADAE.\n\nComo posso ajudá-lo com suas questões financeiras?\n\n• 📄 Consultar faturas\n• ⚖️ Contestar valores\n• 🤝 Negociar débitos\n• 💳 Informações sobre pagamento\n• 📊 Histórico de consumo\n• 📝 Segunda via de conta\n\nEstou aqui para resolver suas dúvidas sobre faturamento!`,
        sender: 'bot',
        timestamp: new Date()
      }
      setMessages([welcomeMessage])
    } catch (error) {
      console.error('Erro ao inicializar chat:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const loadChatHistory = async () => {
    try {
      const { data: tickets } = await api.get('/support/tickets', {
        params: { category: 'billing', limit: 10 }
      })
      if (Array.isArray(tickets)) {
        // Filter out closed tickets for operators and support agents
        const isOperator = user?.role === 'operator' || user?.role === 'support_agent'
        const filteredTickets = isOperator 
          ? tickets.filter((t: any) => t.status !== 'closed' && t.status?.value !== 'closed')
          : tickets
        setChatHistory(filteredTickets)
      } else {
        setChatHistory([])
      }
    } catch (error) {
      console.error('Erro ao carregar histórico:', error)
      setChatHistory([])
    }
  }

  const createTicketContextSummary = (ticket: any): ChatMessage => {
    const statusText = ticket.status?.value || ticket.status || 'Aberto'
    const categoryText = ticket.category?.value || ticket.category || 'Não especificada'
    const priorityText = ticket.priority?.value || ticket.priority || 'Média'
    const createdAt = ticket.created_at ? new Date(ticket.created_at).toLocaleDateString('pt-BR') : 'Data não disponível'
    
    const contextSummary = `📋 **Resumo do Ticket ${ticket.ticket_number}**\n\n` +
      `**Título:** ${ticket.title || 'Sem título'}\n` +
      `**Descrição:** ${ticket.description ? (ticket.description.length > 200 ? ticket.description.substring(0, 200) + '...' : ticket.description) : 'Sem descrição'}\n` +
      `**Status:** ${statusText}\n` +
      `**Categoria:** ${categoryText}\n` +
      `**Prioridade:** ${priorityText}\n` +
      `**Criado em:** ${createdAt}\n` +
      (ticket.assigned_agent_name ? `**Atendente:** ${ticket.assigned_agent_name}\n` : '') +
      `\n---\n`
    
    return {
      id: `context-${ticket.id}-${Date.now()}`,
      content: contextSummary,
      sender: 'bot',
      timestamp: new Date(ticket.created_at || Date.now()),
      ticket_id: ticket.id,
      author_name: 'Sistema'
    }
  }

  const loadConversation = async (ticketId: number) => {
    try {
      setIsLoading(true)
      const { data: ticket } = await api.get(`/support/tickets/${ticketId}`)
      const { data: ticketMessages } = await api.get(`/support/tickets/${ticketId}/messages`)
      
      setCurrentTicketId(ticketId)
      
      // Verificar se o ticket está aberto (open ou in_progress)
      const ticketStatus = ticket.status?.value || ticket.status || 'open'
      const isOpenTicket = ticketStatus === 'open' || ticketStatus === 'in_progress'
      
      const convertedMessages: ChatMessage[] = Array.isArray(ticketMessages) && ticketMessages.length > 0
        ? ticketMessages.map((msg: any) => ({
            id: `msg-${msg.id}`,
            content: msg.content,
            sender: msg.message_type === 'client' ? 'user' : msg.message_type === 'agent' ? 'bot' : 'bot',
            timestamp: new Date(msg.created_at),
            ticket_id: msg.ticket_id,
            author_name: msg.author_name
          }))
        : []
      
      // Se o ticket está aberto, adicionar o resumo do contexto no início
      if (isOpenTicket) {
        const contextMessage = createTicketContextSummary(ticket)
        // Verificar se já existe uma mensagem de contexto para evitar duplicatas
        const hasContextMessage = convertedMessages.some(msg => msg.id.startsWith('context-'))
        if (!hasContextMessage) {
          setMessages([contextMessage, ...convertedMessages])
        } else {
          setMessages(convertedMessages)
        }
      } else {
        setMessages(convertedMessages)
      }
      
      setShowHistory(false)
    } catch (error) {
      console.error('Erro ao carregar conversa:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      content: inputMessage,
      sender: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsTyping(true)

    try {
      if (currentTicketId) {
        // Enviar mensagem via WebSocket se conectado
        if (wsConnected) {
          wsSendMessage(inputMessage)
        } else {
          // Fallback para API REST
          await api.post(`/support/tickets/${currentTicketId}/messages`, {
            content: inputMessage
          })
        }
      } else {
        // Criar novo ticket de faturamento
        const { data: newTicket } = await api.post('/support/tickets', {
          title: inputMessage.substring(0, 50),
          description: inputMessage,
          category: 'billing',
          priority: 'medium'
        })

        setCurrentTicketId(newTicket.id)
        
        // Simular resposta do bot
        setTimeout(() => {
          const botMessage: ChatMessage = {
            id: `bot-${Date.now()}`,
            content: `Entendi sua solicitação sobre faturamento. Criei o ticket #${newTicket.ticket_number} para acompanhar seu caso.\n\nUm de nossos especialistas em faturamento irá analisar e responder em breve. Você pode acompanhar o status pela página de Suporte.`,
            sender: 'bot',
            timestamp: new Date(),
            ticket_id: newTicket.id
          }
          setMessages(prev => [...prev, botMessage])
          setIsTyping(false)
        }, 1500)
      }
    } catch (error) {
      console.error('Erro ao enviar mensagem:', error)
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        content: 'Desculpe, ocorreu um erro ao enviar sua mensagem. Tente novamente.',
        sender: 'bot',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsTyping(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const startNewChat = () => {
    setCurrentTicketId(null)
    initializeChat()
  }

  return (
    <div className="flex h-[calc(100vh-120px)] bg-gradient-to-br from-green-50 to-blue-50">
      {/* Sidebar - Histórico de conversas */}
      <div className={`${showHistory ? 'w-80' : 'w-0'} bg-white border-r border-gray-200 overflow-hidden transition-all duration-300`}>
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="font-semibold text-gray-900">Histórico de Faturamento</h2>
          <button
            onClick={() => setShowHistory(false)}
            className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <div className="overflow-y-auto h-[calc(100%-60px)]">
          {chatHistory.length === 0 ? (
            <div className="p-4 text-center text-gray-500 text-sm">
              Nenhuma conversa anterior sobre faturamento
            </div>
          ) : (
            chatHistory.map((chat) => (
              <button
                key={chat.id}
                onClick={() => loadConversation(chat.id)}
                className="w-full p-4 text-left hover:bg-gray-50 border-b border-gray-100 transition-colors"
              >
                <div className="flex items-start space-x-3">
                  <Receipt className="w-5 h-5 text-green-600 mt-1 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {chat.title}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(chat.created_at).toLocaleDateString('pt-BR')}
                    </p>
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <MessageSquare className="w-5 h-5 text-gray-600" />
              </button>
              
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-green-500 to-blue-500 flex items-center justify-center">
                  <DollarSign className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Atendimento de Faturamento</h3>
                  <div className="flex items-center space-x-2">
                    <p className="text-xs text-gray-500">Assistente Financeiro</p>
                    {currentTicketId && (
                      <>
                        {wsConnected ? (
                          <Wifi className="w-3 h-3 text-green-500" aria-label="Conectado" />
                        ) : (
                          <WifiOff className="w-3 h-3 text-yellow-500" aria-label="Desconectado" />
                        )}
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              {billingSummary && (
                <div className="flex items-center space-x-4 text-sm">
                  <div className="flex items-center space-x-2">
                    <Receipt className="w-4 h-4 text-gray-500" />
                    <span className="text-gray-600">{billingSummary.totalBills} faturas</span>
                  </div>
                  {billingSummary.contestedBills > 0 && (
                    <div className="flex items-center space-x-2">
                      <AlertCircle className="w-4 h-4 text-orange-500" />
                      <span className="text-gray-600">{billingSummary.contestedBills} contestações</span>
                    </div>
                  )}
                  {billingSummary.activeNegotiations > 0 && (
                    <div className="flex items-center space-x-2">
                      <Users className="w-4 h-4 text-blue-500" />
                      <span className="text-gray-600">{billingSummary.activeNegotiations} negociações</span>
                    </div>
                  )}
                </div>
              )}
              
              <button
                onClick={startNewChat}
                className="px-4 py-2 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-lg hover:from-green-600 hover:to-blue-600 transition-all duration-200 text-sm font-medium"
              >
                Nova Conversa
              </button>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <Loader2 className="w-8 h-8 text-green-500 animate-spin" />
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}
                >
                  <div className={`flex items-start space-x-3 max-w-2xl ${message.sender === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                      message.sender === 'user' 
                        ? 'bg-blue-500' 
                        : 'bg-gradient-to-br from-green-500 to-blue-500'
                    }`}>
                      {message.sender === 'user' ? (
                        <User className="w-5 h-5 text-white" />
                      ) : (
                        <DollarSign className="w-5 h-5 text-white" />
                      )}
                    </div>
                    
                    <div className={`rounded-2xl px-4 py-3 ${
                      message.sender === 'user'
                        ? 'bg-blue-500 text-white'
                        : 'bg-white text-gray-900 shadow-sm border border-gray-200'
                    }`}>
                      {message.author_name && message.sender !== 'user' && (
                        <p className="text-xs font-medium text-green-600 mb-1">
                          {message.author_name}
                        </p>
                      )}
                      <p className="text-sm whitespace-pre-wrap leading-relaxed">
                        {message.content}
                      </p>
                      <p className={`text-xs mt-2 ${
                        message.sender === 'user' ? 'text-blue-100' : 'text-gray-400'
                      }`}>
                        {message.timestamp.toLocaleTimeString('pt-BR', {
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </p>
                    </div>
                  </div>
                </div>
              ))}

              {isTyping && (
                <div className="flex items-start space-x-3 max-w-2xl animate-fade-in">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-blue-500 flex items-center justify-center">
                    <DollarSign className="w-5 h-5 text-white" />
                  </div>
                  <div className="bg-white rounded-2xl px-4 py-3 shadow-sm border border-gray-200">
                    <div className="flex space-x-2">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input Area */}
        <div className="bg-white border-t border-gray-200 px-6 py-4">
          <div className="flex items-end space-x-4">
            <div className="flex-1">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Digite sua mensagem sobre faturamento..."
                rows={3}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>
            
            <button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim()}
              className="px-6 py-3 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-xl hover:from-green-600 hover:to-blue-600 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <Send className="w-5 h-5" />
              <span className="font-medium">Enviar</span>
            </button>
          </div>

          {wsError && (
            <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-2">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">
                Erro na conexão em tempo real. Suas mensagens serão enviadas normalmente.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
