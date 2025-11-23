import React, { useState, useEffect, useRef } from 'react'
import { MessageSquare, X, Send, Bot, User, Loader2, Wifi, WifiOff } from 'lucide-react'
import { api } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import { useChatWebSocket } from '../hooks/useChatWebSocket'

interface ChatMessage {
  id: string
  content: string
  sender: 'user' | 'agent' | 'bot'
  timestamp: Date
  ticket_id?: number
}

interface ChatWidgetProps {
  initialTicketId?: number
}

export function ChatWidget({ initialTicketId }: ChatWidgetProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [currentTicketId, setCurrentTicketId] = useState<number | null>(initialTicketId || null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { user } = useAuth()
  
  // WebSocket hook - só conecta se tiver ticket
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
      // Converter mensagens do WebSocket para o formato do widget
      const convertedMessages: ChatMessage[] = wsMessages.map((msg) => ({
        id: `msg-${msg.id}`,
        content: msg.content,
        sender: msg.message_type === 'client' ? 'user' : msg.message_type === 'agent' ? 'bot' : 'bot',
        timestamp: new Date(msg.created_at),
        ticket_id: msg.ticket_id
      }))
      
      setMessages(convertedMessages)
    }
  }, [wsMessages, currentTicketId])

  useEffect(() => {
    if (isOpen && messages.length === 0 && !currentTicketId) {
      initializeChat()
    } else if (isOpen && currentTicketId && wsMessages.length === 0) {
      // Carregar mensagens existentes do ticket
      loadTicketMessages()
    }
  }, [isOpen, currentTicketId])

  useEffect(() => {
    scrollToBottom()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages.length])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const initializeChat = async () => {
    setIsLoading(true)
    try {
      // Mensagem de boas-vindas do bot
      const welcomeMessage: ChatMessage = {
        id: `welcome-${Date.now()}`,
        content: `Olá! 👋 Sou o assistente virtual do SADAE. Como posso ajudá-lo hoje? Posso ajudar com:\n\n• Consultas sobre sua conta\n• Reportar vazamentos\n• Solicitar serviços\n• Informações sobre tarifas\n• Resolver dúvidas gerais`,
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

  const getBotResponse = async (userMessage: string): Promise<string> => {
    // Respostas automáticas baseadas em palavras-chave
    const message = userMessage.toLowerCase()

    // Buscar na base de conhecimento
    try {
      const { data: knowledgeBase } = await api.get('/support/knowledge-base', {
        params: { search: userMessage, limit: 3 }
      })

      if (knowledgeBase && knowledgeBase.length > 0) {
        const article = knowledgeBase[0]
        return `📚 Baseado na nossa base de conhecimento:\n\n${article.title}\n\n${article.content.substring(0, 200)}${article.content.length > 200 ? '...' : ''}\n\nIsso ajuda? Se precisar de mais informações, posso criar um ticket para você.`
      }
    } catch (error) {
      console.error('Erro ao buscar base de conhecimento:', error)
    }

    // Respostas padrão baseadas em palavras-chave
    if (message.includes('conta') || message.includes('fatura') || message.includes('pagamento')) {
      return `💳 Para consultar sua conta de água, você pode:\n\n1. Acessar a área do cliente em Dashboard > Faturamento\n2. Informar seu CPF/CNPJ e número de cliente\n3. Visualizar faturas abertas e pagas\n4. Baixar 2ª via\n\nPrecisa de ajuda com algo específico sobre sua conta?`
    }

    if (message.includes('vazamento') || message.includes('vazando') || message.includes('vazou')) {
      return `🚨 Para reportar um vazamento:\n\n1. Feche o registro principal se possível\n2. Sinalize a área para evitar acidentes\n3. Informe a localização exata\n4. Descreva a intensidade\n\nPosso criar um ticket urgente para você. Deseja que eu crie?`
    }

    if (message.includes('religação') || message.includes('religar') || message.includes('corte')) {
      return `🔧 Para solicitar religação:\n\n1. Regularize pendências financeiras\n2. Tenha em mãos o número do imóvel\n3. Comprovante de pagamento\n4. Informe o endereço completo\n\nDeseja que eu crie um ticket para sua solicitação?`
    }

    if (message.includes('tarifa') || message.includes('preço') || message.includes('valor')) {
      return `💰 As tarifas variam por:\n\n• Faixa de consumo\n• Categoria (residencial, comercial, etc.)\n• Localização\n\nVocê pode consultar a tabela vigente em Serviços Públicos > Informações ou usar o simulador no app.\n\nQuer que eu crie um ticket para informações mais detalhadas?`
    }

    if (message.includes('sim') || message.includes('criar') || message.includes('ticket')) {
      return `🎫 Perfeito! Vou criar um ticket para você. Para isso, preciso de algumas informações:\n\n1. Qual é o assunto principal?\n2. Descrição detalhada do problema/solicitação\n3. Localização (se aplicável)\n\nPode me fornecer essas informações?`
    }

    // Resposta padrão
    return `Entendi. Para ajudá-lo melhor, posso:\n\n1. Buscar informações na nossa base de conhecimento\n2. Criar um ticket para atendimento especializado\n3. Conectar você com um atendente\n\nO que você prefere?`
  }

  const createTicketFromChat = async (content: string): Promise<number | null> => {
    try {
      console.log('📝 Criando ticket do widget com dados:', { content })
      
      const response = await api.post('/support/tickets', {
        title: `Chat: ${content.substring(0, 50)}`,
        description: content,
        category: 'information',
        priority: 'medium',
        client_phone: user?.phone || ''
      })

      console.log('✅ Ticket criado do widget:', response.data)
      return response.data.id
    } catch (error: any) {
      console.error('❌ Erro ao criar ticket do widget:', error)
      console.error('❌ Detalhes do erro:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status
      })
      return null
    }
  }

  const loadTicketMessages = async () => {
    if (!currentTicketId) return
    
    try {
      setIsLoading(true)
      const { data: ticketMessages } = await api.get(`/support/tickets/${currentTicketId}/messages`)
      
      if (Array.isArray(ticketMessages)) {
        const convertedMessages: ChatMessage[] = ticketMessages.map((msg: any) => ({
          id: `msg-${msg.id}`,
          content: msg.content,
          sender: msg.message_type === 'client' ? 'user' : msg.message_type === 'agent' ? 'bot' : 'bot',
          timestamp: new Date(msg.created_at),
          ticket_id: currentTicketId
        }))
        setMessages(convertedMessages)
      }
    } catch (error) {
      console.error('Erro ao carregar mensagens do ticket:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputMessage.trim() || isTyping) return

    const messageToSend = inputMessage
    setInputMessage('')

    // Se tiver ticket e WebSocket conectado, usar WebSocket
    if (currentTicketId && wsConnected) {
      setIsTyping(true)
      wsSendMessage(messageToSend)
      // WebSocket vai atualizar as mensagens automaticamente
      setIsTyping(false)
      return
    }

    // Se não tiver ticket, criar um primeiro
    if (!currentTicketId) {
      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        content: messageToSend,
        sender: 'user',
        timestamp: new Date()
      }

      setMessages(prev => [...prev, userMessage])
      setIsTyping(true)

      try {
        // Buscar resposta do bot
        const botResponse = await getBotResponse(messageToSend)

        // Aguardar um pouco para simular digitação
        await new Promise(resolve => setTimeout(resolve, 1000))

        const botMessage: ChatMessage = {
          id: `bot-${Date.now()}`,
          content: botResponse,
          sender: 'bot',
          timestamp: new Date()
        }

        setMessages(prev => [...prev, botMessage])

        // Se o usuário quer criar ticket, criar automaticamente
        if (messageToSend.toLowerCase().includes('criar') || messageToSend.toLowerCase().includes('ticket')) {
          const ticketId = await createTicketFromChat(messageToSend)
          if (ticketId) {
            setCurrentTicketId(ticketId)
            const ticketMessage: ChatMessage = {
              id: `ticket-${Date.now()}`,
              content: `✅ Ticket criado com sucesso! Número: #${ticketId}\n\nAgora você pode conversar em tempo real.`,
              sender: 'bot',
              timestamp: new Date(),
              ticket_id: ticketId
            }
            setMessages(prev => [...prev, ticketMessage])
          }
        }
      } catch (error) {
        console.error('Erro ao processar mensagem:', error)
        const errorMessage: ChatMessage = {
          id: `error-${Date.now()}`,
          content: 'Desculpe, ocorreu um erro. Por favor, tente novamente ou crie um ticket diretamente.',
          sender: 'bot',
          timestamp: new Date()
        }
        setMessages(prev => [...prev, errorMessage])
      } finally {
        setIsTyping(false)
      }
    } else {
      // Fallback: usar API REST se WebSocket não estiver conectado
      try {
        setIsTyping(true)
        await api.post(`/support/tickets/${currentTicketId}/messages`, {
          content: messageToSend
        })
        // Recarregar mensagens
        await loadTicketMessages()
      } catch (error) {
        console.error('Erro ao enviar mensagem:', error)
      } finally {
        setIsTyping(false)
      }
    }
  }

  return (
    <>
      {/* Botão flutuante */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 w-16 h-16 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 transition-all flex items-center justify-center z-50 hover:scale-110"
          aria-label="Abrir chat"
        >
          <MessageSquare className="w-6 h-6" />
          <span className="absolute top-0 right-0 w-3 h-3 bg-green-400 rounded-full border-2 border-white"></span>
        </button>
      )}

      {/* Janela de chat */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-96 h-[600px] bg-white rounded-lg shadow-2xl flex flex-col z-50 border border-gray-200">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-4 rounded-t-lg flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-white bg-opacity-20 rounded-full flex items-center justify-center">
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold">Atendimento SADAE</h3>
                <div className="flex items-center space-x-2">
                  <p className="text-xs text-blue-100">Assistente Virtual</p>
                  {currentTicketId && (
                    <>
                      {wsConnected ? (
                        <Wifi className="w-3 h-3 text-green-300" aria-label="Conectado" />
                      ) : (
                        <WifiOff className="w-3 h-3 text-yellow-300" aria-label="Desconectado" />
                      )}
                    </>
                  )}
                </div>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-white hover:text-gray-200 transition-colors"
              aria-label="Fechar chat"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Mensagens */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
            {isLoading ? (
              <div className="flex items-center justify-center h-full">
                <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
              </div>
            ) : (
              <>
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg px-4 py-2 ${
                        message.sender === 'user'
                          ? 'bg-blue-600 text-white'
                          : message.sender === 'bot'
                          ? 'bg-white text-gray-800 shadow border border-gray-200'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      <div className="flex items-start space-x-2">
                        {message.sender === 'bot' && (
                          <Bot className="w-4 h-4 mt-0.5 text-blue-600 flex-shrink-0" />
                        )}
                        {message.sender === 'user' && (
                          <User className="w-4 h-4 mt-0.5 text-white flex-shrink-0" />
                        )}
                        <div className="flex-1">
                          <p className="text-sm whitespace-pre-line">{message.content}</p>
                          <p className="text-xs opacity-75 mt-1">
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
                    <div className="bg-white text-gray-800 rounded-lg px-4 py-2 shadow border border-gray-200">
                      <div className="flex space-x-1">
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
          <form onSubmit={handleSendMessage} className="p-4 border-t border-gray-200 bg-white">
            <div className="flex space-x-2">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Digite sua mensagem..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                disabled={isTyping || isLoading}
              />
              <button
                type="submit"
                disabled={!inputMessage.trim() || isTyping || isLoading}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
            {currentTicketId && (
              <p className="text-xs text-gray-500 mt-2">
                Ticket #{currentTicketId} • <button className="text-blue-600 hover:underline">Ver detalhes</button>
              </p>
            )}
          </form>
        </div>
      )}
    </>
  )
}

