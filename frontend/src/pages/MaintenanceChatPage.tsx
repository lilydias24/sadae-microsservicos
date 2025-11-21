"use client"

import React, { useState, useEffect, useRef } from 'react'
import { Bot, User, Send, Loader2, MessageSquare, Wrench, Search, X, Wifi, WifiOff, AlertTriangle, CheckCircle2 } from 'lucide-react'
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

interface MaintenanceSummary {
  totalOrders: number
  openOrders: number
  inProgressOrders: number
  completedOrders: number
  availableTeams: number
}

export function MaintenanceChatPage() {
  const { user } = useAuth()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [currentTicketId, setCurrentTicketId] = useState<number | null>(null)
  const [chatHistory, setChatHistory] = useState<Array<{ id: number; title: string; created_at: string }>>([])
  const [showHistory, setShowHistory] = useState(false)
  const [maintenanceSummary, setMaintenanceSummary] = useState<MaintenanceSummary | null>(null)
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
      loadMaintenanceSummary()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadMaintenanceSummary = async () => {
    try {
      const [ordersRes, teamsRes] = await Promise.allSettled([
        api.get('/maintenance/orders'),
        api.get('/maintenance/teams')
      ])

      const orders = ordersRes.status === 'fulfilled' ? ordersRes.value.data : []
      const teams = teamsRes.status === 'fulfilled' ? teamsRes.value.data : []

      const openOrders = Array.isArray(orders) ? orders.filter((o: any) => o.status === 'open') : []
      const inProgressOrders = Array.isArray(orders) ? orders.filter((o: any) => o.status === 'in_progress') : []
      const completedOrders = Array.isArray(orders) ? orders.filter((o: any) => o.status === 'completed') : []
      const availableTeams = Array.isArray(teams) ? teams.filter((t: any) => t.status === 'available' || t.is_active) : []

      setMaintenanceSummary({
        totalOrders: Array.isArray(orders) ? orders.length : 0,
        openOrders: openOrders.length,
        inProgressOrders: inProgressOrders.length,
        completedOrders: completedOrders.length,
        availableTeams: availableTeams.length
      })
    } catch (error) {
      console.error('Erro ao carregar resumo de manutenção:', error)
    }
  }

  const initializeChat = async () => {
    setIsLoading(true)
    try {
      const welcomeMessage: ChatMessage = {
        id: `welcome-${Date.now()}`,
        content: `Olá${user?.full_name ? `, ${user.full_name}` : ''}! 🔧\n\nBem-vindo ao atendimento de Manutenção do SADAE.\n\nComo posso ajudá-lo com serviços de manutenção?\n\n• 🔧 Solicitar serviço de manutenção\n• 📋 Acompanhar ordens de serviço\n• 🚰 Reportar vazamentos\n• ⚠️ Emergências\n• 👥 Informações sobre equipes\n• 📍 Manutenção por localização\n\nEstou aqui para resolver suas solicitações de manutenção!`,
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
        params: { category: 'technical', limit: 10 }
      })
      if (Array.isArray(tickets)) {
        setChatHistory(tickets)
      } else {
        setChatHistory([])
      }
    } catch (error) {
      console.error('Erro ao carregar histórico:', error)
      setChatHistory([])
    }
  }

  const loadConversation = async (ticketId: number) => {
    try {
      setIsLoading(true)
      const { data: ticket } = await api.get(`/support/tickets/${ticketId}`)
      const { data: ticketMessages } = await api.get(`/support/tickets/${ticketId}/messages`)
      
      setCurrentTicketId(ticketId)
      
      const convertedMessages: ChatMessage[] = ticketMessages.map((msg: any) => ({
        id: `msg-${msg.id}`,
        content: msg.content,
        sender: msg.message_type === 'client' ? 'user' : msg.message_type === 'agent' ? 'bot' : 'bot',
        timestamp: new Date(msg.created_at),
        ticket_id: msg.ticket_id,
        author_name: msg.author_name
      }))
      
      setMessages(convertedMessages)
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
        // Criar novo ticket de manutenção
        const { data: newTicket } = await api.post('/support/tickets', {
          title: inputMessage.substring(0, 50),
          description: inputMessage,
          category: 'technical',
          priority: 'medium'
        })

        setCurrentTicketId(newTicket.id)
        
        // Simular resposta do bot
        setTimeout(() => {
          const botMessage: ChatMessage = {
            id: `bot-${Date.now()}`,
            content: `Entendi sua solicitação de manutenção. Criei o ticket #${newTicket.ticket_number} para acompanhar seu caso.\n\nUm de nossos técnicos irá analisar e responder em breve. Você pode acompanhar o status pela página de Suporte.`,
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
    <div className="flex h-[calc(100vh-120px)] bg-gradient-to-br from-orange-50 to-yellow-50">
      {/* Sidebar - Histórico de conversas */}
      <div className={`${showHistory ? 'w-80' : 'w-0'} bg-white border-r border-gray-200 overflow-hidden transition-all duration-300`}>
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="font-semibold text-gray-900">Histórico de Manutenção</h2>
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
              Nenhuma conversa anterior sobre manutenção
            </div>
          ) : (
            chatHistory.map((chat) => (
              <button
                key={chat.id}
                onClick={() => loadConversation(chat.id)}
                className="w-full p-4 text-left hover:bg-gray-50 border-b border-gray-100 transition-colors"
              >
                <div className="flex items-start space-x-3">
                  <Wrench className="w-5 h-5 text-orange-600 mt-1 flex-shrink-0" />
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
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-orange-500 to-yellow-500 flex items-center justify-center">
                  <Wrench className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Atendimento de Manutenção</h3>
                  <div className="flex items-center space-x-2">
                    <p className="text-xs text-gray-500">Assistente Técnico</p>
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
              {maintenanceSummary && (
                <div className="flex items-center space-x-4 text-sm">
                  <div className="flex items-center space-x-2">
                    <Wrench className="w-4 h-4 text-gray-500" />
                    <span className="text-gray-600">{maintenanceSummary.totalOrders} ordens</span>
                  </div>
                  {maintenanceSummary.openOrders > 0 && (
                    <div className="flex items-center space-x-2">
                      <AlertTriangle className="w-4 h-4 text-orange-500" />
                      <span className="text-gray-600">{maintenanceSummary.openOrders} abertas</span>
                    </div>
                  )}
                  {maintenanceSummary.availableTeams > 0 && (
                    <div className="flex items-center space-x-2">
                      <CheckCircle2 className="w-4 h-4 text-green-500" />
                      <span className="text-gray-600">{maintenanceSummary.availableTeams} equipes disponíveis</span>
                    </div>
                  )}
                </div>
              )}
              
              <button
                onClick={startNewChat}
                className="px-4 py-2 bg-gradient-to-r from-orange-500 to-yellow-500 text-white rounded-lg hover:from-orange-600 hover:to-yellow-600 transition-all duration-200 text-sm font-medium"
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
              <Loader2 className="w-8 h-8 text-orange-500 animate-spin" />
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
                        : 'bg-gradient-to-br from-orange-500 to-yellow-500'
                    }`}>
                      {message.sender === 'user' ? (
                        <User className="w-5 h-5 text-white" />
                      ) : (
                        <Wrench className="w-5 h-5 text-white" />
                      )}
                    </div>
                    
                    <div className={`rounded-2xl px-4 py-3 ${
                      message.sender === 'user'
                        ? 'bg-blue-500 text-white'
                        : 'bg-white text-gray-900 shadow-sm border border-gray-200'
                    }`}>
                      {message.author_name && message.sender !== 'user' && (
                        <p className="text-xs font-medium text-orange-600 mb-1">
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
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-500 to-yellow-500 flex items-center justify-center">
                    <Wrench className="w-5 h-5 text-white" />
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
                placeholder="Digite sua mensagem sobre manutenção..."
                rows={3}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              />
            </div>
            
            <button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim()}
              className="px-6 py-3 bg-gradient-to-r from-orange-500 to-yellow-500 text-white rounded-xl hover:from-orange-600 hover:to-yellow-600 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <Send className="w-5 h-5" />
              <span className="font-medium">Enviar</span>
            </button>
          </div>

          {wsError && (
            <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-2">
              <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
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
