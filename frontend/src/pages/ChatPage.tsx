"use client"

import React, { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { Bot, User, Send, Loader2, MessageSquare, Ticket, Search, X } from 'lucide-react'
import { api } from '../services/api'
import { useAuth } from '../contexts/AuthContext'

interface ChatMessage {
  id: string
  content: string
  sender: 'user' | 'agent' | 'bot'
  timestamp: Date
  ticket_id?: number
  author_name?: string
}

export function ChatPage() {
  const { user } = useAuth()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [currentTicketId, setCurrentTicketId] = useState<number | null>(null)
  const [chatHistory, setChatHistory] = useState<Array<{ id: number; title: string; created_at: string }>>([])
  const [showHistory, setShowHistory] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    initializeChat()
    loadChatHistory()
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const initializeChat = async () => {
    setIsLoading(true)
    try {
      const welcomeMessage: ChatMessage = {
        id: `welcome-${Date.now()}`,
        content: `Olá${user?.full_name ? `, ${user.full_name}` : ''}! 👋\n\nBem-vindo ao atendimento do SADAE. Como posso ajudá-lo hoje?\n\n• Consultas sobre sua conta\n• Reportar vazamentos\n• Solicitar serviços\n• Informações sobre tarifas\n• Resolver dúvidas gerais\n\nPosso responder automaticamente ou criar um ticket para atendimento especializado.`,
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
        params: { limit: 10 }
      })
      setChatHistory(tickets || [])
    } catch (error) {
      console.error('Erro ao carregar histórico:', error)
    }
  }

  const getBotResponse = async (userMessage: string): Promise<string> => {
    const message = userMessage.toLowerCase()

    // Buscar na base de conhecimento
    try {
      const { data: knowledgeBase } = await api.get('/support/knowledge-base', {
        params: { search: userMessage, limit: 3 }
      })

      if (knowledgeBase && knowledgeBase.length > 0) {
        const article = knowledgeBase[0]
        return `📚 Encontrei uma informação relevante:\n\n**${article.title}**\n\n${article.content.substring(0, 300)}${article.content.length > 300 ? '...' : ''}\n\nIsso ajuda? Se precisar de mais informações, posso criar um ticket para você.`
      }
    } catch (error) {
      console.error('Erro ao buscar base de conhecimento:', error)
    }

    // Respostas inteligentes
    if (message.includes('conta') || message.includes('fatura') || message.includes('pagamento')) {
      return `💳 **Consulta de Conta**\n\nPara consultar sua conta:\n\n1. Acesse Dashboard > Faturamento\n2. Informe CPF/CNPJ e número de cliente\n3. Visualize faturas e histórico\n4. Baixe 2ª via\n\nPrecisa de ajuda específica?`
    }

    if (message.includes('vazamento') || message.includes('vazando')) {
      return `🚨 **Reportar Vazamento**\n\nPara reportar:\n\n1. Feche o registro principal\n2. Sinalize a área\n3. Informe localização exata\n4. Descreva a intensidade\n\nPosso criar um ticket urgente agora. Deseja continuar?`
    }

    if (message.includes('religação') || message.includes('religar')) {
      return `🔧 **Solicitar Religação**\n\nÉ necessário:\n\n1. Regularizar pendências\n2. Número do imóvel\n3. Comprovante de pagamento\n4. Endereço completo\n\nDeseja que eu crie um ticket para sua solicitação?`
    }

    if (message.includes('tarifa') || message.includes('preço')) {
      return `💰 **Tarifas**\n\nAs tarifas variam por:\n• Faixa de consumo\n• Categoria (residencial/comercial)\n• Localização\n\nConsulte em Serviços Públicos > Informações.\n\nQuer mais detalhes?`
    }

    if (message.includes('sim') || message.includes('criar') || message.includes('ticket')) {
      return `🎫 **Criar Ticket**\n\nPara criar, preciso:\n\n1. Assunto principal\n2. Descrição detalhada\n3. Localização (se aplicável)\n\nPode me fornecer essas informações?`
    }

    return `Entendi. Para ajudá-lo melhor:\n\n1. 📚 Buscar na base de conhecimento\n2. 🎫 Criar ticket para atendimento\n3. 👤 Conectar com atendente\n\nO que você prefere?`
  }

  const createTicketFromChat = async (content: string): Promise<number | null> => {
    try {
      const { data: ticket } = await api.post('/support/tickets', {
        title: `Chat: ${content.substring(0, 50)}`,
        description: content,
        category: 'information',
        priority: 'medium',
        client_phone: user?.phone || ''
      })

      return ticket.id
    } catch (error) {
      console.error('Erro ao criar ticket:', error)
      return null
    }
  }

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputMessage.trim() || isTyping) return

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      content: inputMessage,
      sender: 'user',
      timestamp: new Date(),
      ticket_id: currentTicketId || undefined,
      author_name: user?.full_name || 'Você'
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsTyping(true)

    try {
      const botResponse = await getBotResponse(inputMessage)
      await new Promise(resolve => setTimeout(resolve, 1000))

      const botMessage: ChatMessage = {
        id: `bot-${Date.now()}`,
        content: botResponse,
        sender: 'bot',
        timestamp: new Date(),
        ticket_id: currentTicketId || undefined
      }

      setMessages(prev => [...prev, botMessage])

      if (inputMessage.toLowerCase().includes('criar') || inputMessage.toLowerCase().includes('ticket')) {
        if (!currentTicketId) {
          const ticketId = await createTicketFromChat(inputMessage)
          if (ticketId) {
            setCurrentTicketId(ticketId)
            const ticketMessage: ChatMessage = {
              id: `ticket-${Date.now()}`,
              content: `✅ **Ticket Criado!**\n\nNúmero: #${ticketId}\n\nUm atendente entrará em contato em breve.\n\nVocê pode acompanhar na área de Suporte.`,
              sender: 'bot',
              timestamp: new Date(),
              ticket_id: ticketId
            }
            setMessages(prev => [...prev, ticketMessage])
            loadChatHistory()
          }
        }
      }
    } catch (error) {
      console.error('Erro ao processar mensagem:', error)
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        content: 'Desculpe, ocorreu um erro. Por favor, tente novamente.',
        sender: 'bot',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsTyping(false)
    }
  }

  const loadTicketMessages = async (ticketId: number) => {
    try {
      setIsLoading(true)
      const { data: ticketMessages } = await api.get(`/support/tickets/${ticketId}/messages`)
      
      const chatMessages: ChatMessage[] = ticketMessages.map((msg: any) => ({
        id: `msg-${msg.id}`,
        content: msg.content,
        sender: msg.message_type === 'client' ? 'user' : msg.message_type === 'agent' ? 'agent' : 'bot',
        timestamp: new Date(msg.created_at),
        ticket_id: ticketId,
        author_name: msg.author_name
      }))

      setMessages(chatMessages)
      setCurrentTicketId(ticketId)
      setShowHistory(false)
    } catch (error) {
      console.error('Erro ao carregar mensagens do ticket:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex h-[calc(100vh-10rem)] -m-6">
      {/* Sidebar - Histórico */}
      <div className={`w-80 bg-white border-r border-gray-200 transition-all ${showHistory ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 lg:static lg:relative absolute inset-y-0 z-10`}>
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="font-semibold text-gray-900">Histórico de Conversas</h2>
          <button
            onClick={() => setShowHistory(false)}
            className="lg:hidden text-gray-500 hover:text-gray-700"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-4 space-y-2 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 12rem)' }}>
          <button
            onClick={() => {
              initializeChat()
              setCurrentTicketId(null)
              setShowHistory(false)
            }}
            className="w-full p-3 text-left bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors flex items-center space-x-2"
          >
            <MessageSquare className="w-4 h-4" />
            <span className="font-medium">Nova Conversa</span>
          </button>
          {chatHistory.map((ticket) => (
            <button
              key={ticket.id}
              onClick={() => loadTicketMessages(ticket.id)}
              className={`w-full p-3 text-left rounded-lg hover:bg-gray-50 transition-colors ${
                currentTicketId === ticket.id ? 'bg-blue-50 border border-blue-200' : ''
              }`}
            >
              <div className="flex items-center space-x-2 mb-1">
                <Ticket className="w-4 h-4 text-gray-500" />
                <span className="text-xs font-mono text-gray-500">#{ticket.id}</span>
              </div>
              <p className="text-sm font-medium text-gray-900 truncate">{ticket.title}</p>
              <p className="text-xs text-gray-500 mt-1">
                {new Date(ticket.created_at).toLocaleDateString('pt-BR')}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Área principal do chat */}
      <div className="flex-1 flex flex-col bg-gray-50">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 p-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowHistory(true)}
              className="lg:hidden text-gray-500 hover:text-gray-700"
            >
              <Search className="w-5 h-5" />
            </button>
            <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Atendimento SADAE</h3>
              <p className="text-xs text-gray-500">Assistente Virtual</p>
            </div>
          </div>
          {currentTicketId && (
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Ticket className="w-4 h-4" />
              <span>Ticket #{currentTicketId}</span>
            </div>
          )}
        </div>

        {/* Mensagens */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[70%] rounded-lg px-4 py-3 ${
                      message.sender === 'user'
                        ? 'bg-blue-600 text-white'
                        : message.sender === 'bot'
                        ? 'bg-white text-gray-800 shadow border border-gray-200'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    <div className="flex items-start space-x-2">
                      {message.sender === 'bot' && (
                        <Bot className="w-5 h-5 mt-0.5 text-blue-600 flex-shrink-0" />
                      )}
                      {message.sender === 'user' && (
                        <User className="w-5 h-5 mt-0.5 text-white flex-shrink-0" />
                      )}
                      <div className="flex-1">
                        {message.author_name && message.sender !== 'user' && (
                          <p className="text-xs font-medium text-gray-600 mb-1">{message.author_name}</p>
                        )}
                        <p className="text-sm whitespace-pre-line">{message.content}</p>
                        <p className="text-xs opacity-75 mt-2">
                          {message.timestamp.toLocaleTimeString('pt-BR', {
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-white text-gray-800 rounded-lg px-4 py-3 shadow border border-gray-200">
                    <div className="flex space-x-2">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input */}
        <form onSubmit={handleSendMessage} className="bg-white border-t border-gray-200 p-4">
          <div className="flex space-x-3 max-w-4xl mx-auto">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Digite sua mensagem..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={isTyping || isLoading}
            />
            <button
              type="submit"
              disabled={!inputMessage.trim() || isTyping || isLoading}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
            >
              <Send className="w-5 h-5" />
              <span className="hidden sm:inline">Enviar</span>
            </button>
          </div>
          {currentTicketId && (
            <p className="text-xs text-gray-500 mt-2 text-center">
              Conectado ao ticket #{currentTicketId} • <Link to="/support" className="text-blue-600 hover:underline">Ver detalhes</Link>
            </p>
          )}
        </form>
      </div>
    </div>
  )
}

