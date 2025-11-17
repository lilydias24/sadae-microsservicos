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
    if (user) {
      initializeChat()
      loadChatHistory()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user])

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
      // Garantir que tickets seja sempre um array
      if (Array.isArray(tickets)) {
        setChatHistory(tickets)
      } else {
        setChatHistory([])
      }
    } catch (error) {
      console.error('Erro ao carregar histórico:', error)
      setChatHistory([]) // Garantir array vazio em caso de erro
    }
  }

  const waitForAIResponse = async (ticketId: number, afterTimestamp: Date): Promise<string | null> => {
    // Aguardar e verificar resposta da IA
    for (let i = 0; i < 5; i++) {
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      try {
        const { data: ticketMessages } = await api.get(`/support/tickets/${ticketId}/messages`)
        
        if (Array.isArray(ticketMessages)) {
          const aiMessage = ticketMessages
            .filter((msg: any) => 
              msg.message_type === 'agent' && 
              msg.author_name === 'Assistente Virtual' &&
              new Date(msg.created_at) > afterTimestamp
            )
            .pop()
          
          if (aiMessage) {
            return aiMessage.content
          }
        }
      } catch (error) {
        console.error('Erro ao buscar resposta da IA:', error)
      }
    }
    
    return null
  }

  const checkChitChat = (message: string): string | null => {
    // Normalizar: remover acentos e caracteres especiais, converter para minúsculas
    let normalized = message.toLowerCase().trim()
    // Remover pontuação mas manter espaços
    normalized = normalized.replace(/[^\w\s]/g, ' ').replace(/\s+/g, ' ').trim()
    
    console.log('🔍 Verificando chit chat para:', message, '→ normalizado:', normalized)
    
    // Saudações - lista completa
    const greetings = ['oi', 'olá', 'ola', 'oie', 'eai', 'hey', 'hi', 'hello', 'bom dia', 'boa tarde', 'boa noite', 'e aí', 'eai']
    
    // Verificar se a mensagem é APENAS uma saudação ou começa com saudação
    for (const greeting of greetings) {
      // Verificar se é exatamente a saudação
      if (normalized === greeting) {
        console.log('✅ Detectado saudação exata:', greeting)
        const responses = [
          'Olá! 👋 Bem-vindo ao atendimento do SADAE. Como posso ajudá-lo hoje?',
          'Oi! 😊 Estou aqui para ajudar. Em que posso ser útil?',
          'Olá! 👋 Fico feliz em ajudar. O que você precisa?',
          'Oi! 😊 Como posso ajudar você hoje?'
        ]
        return responses[Math.floor(Math.random() * responses.length)]
      }
      // Verificar se começa com a saudação seguida de espaço ou fim
      if (normalized.startsWith(greeting + ' ') || normalized === greeting) {
        console.log('✅ Detectado saudação no início:', greeting)
        const responses = [
          'Olá! 👋 Bem-vindo ao atendimento do SADAE. Como posso ajudá-lo hoje?',
          'Oi! 😊 Estou aqui para ajudar. Em que posso ser útil?',
          'Olá! 👋 Fico feliz em ajudar. O que você precisa?',
          'Oi! 😊 Como posso ajudar você hoje?'
        ]
        return responses[Math.floor(Math.random() * responses.length)]
      }
    }
    
    // Agradecimentos
    const thanks = ['obrigado', 'obrigada', 'valeu', 'grato', 'grata', 'thanks', 'thank you']
    if (thanks.some(t => normalized.includes(t))) {
      const responses = [
        'De nada! 😊 Fico feliz em ajudar. Precisa de mais alguma coisa?',
        'Por nada! 😊 Estou sempre aqui para ajudar. Mais alguma dúvida?',
        'Imagina! 😊 Fico feliz em poder ajudar. Precisa de mais informações?'
      ]
      return responses[Math.floor(Math.random() * responses.length)]
    }
    
    // Despedidas
    const goodbyes = ['tchau', 'até', 'até logo', 'até mais', 'bye', 'falou', 'flw']
    if (goodbyes.some(g => normalized.includes(g))) {
      const responses = [
        'Tchau! 👋 Foi um prazer ajudar. Volte sempre que precisar!',
        'Até logo! 😊 Qualquer dúvida, estou aqui!',
        'Tchau! 👋 Tenha um ótimo dia!'
      ]
      return responses[Math.floor(Math.random() * responses.length)]
    }
    
    // Status
    const status = ['tudo bem', 'tudo bom', 'como vai', 'como está', 'beleza', 'tranquilo']
    if (status.some(s => normalized.includes(s))) {
      const responses = [
        'Tudo ótimo! 😊 Pronto para ajudar você. E você, como está?',
        'Estou bem, obrigado! 😊 Como posso ajudar você hoje?',
        'Tudo certo! 😊 Em que posso ser útil?'
      ]
      return responses[Math.floor(Math.random() * responses.length)]
    }
    
    return null
  }

  const checkCommonQuestions = (message: string): string | null => {
    const normalized = message.toLowerCase()
    
    // Consulta de conta
    if (normalized.includes('como consultar') || normalized.includes('ver conta') || 
        normalized.includes('minha conta') || normalized.includes('consulta conta')) {
      return `💳 **Consulta de Conta de Água**

Para consultar sua conta, você pode:

1. **Acessar o Dashboard**
   - Vá em Dashboard > Faturamento
   - Informe seu CPF/CNPJ e número de cliente

2. **Visualizar Informações**
   - Faturas abertas e pagas
   - Histórico de consumo
   - Detalhes de cada fatura

3. **Baixar 2ª Via**
   - Clique em "Baixar 2ª Via" na fatura desejada
   - O documento será gerado em PDF

Precisa de ajuda com algum passo específico?`
    }
    
    // Segunda via
    if (normalized.includes('segunda via') || normalized.includes('2ª via') || 
        normalized.includes('baixar fatura') || normalized.includes('imprimir fatura')) {
      return `📄 **2ª Via de Fatura**

Para baixar a 2ª via da sua fatura:

1. Acesse **Dashboard > Faturamento**
2. Localize a fatura desejada
3. Clique no botão **"Baixar 2ª Via"**
4. O PDF será gerado automaticamente

A 2ª via pode ser usada para:
- Pagamento em bancos e lotéricas
- Comprovação de pagamento
- Declaração de imposto de renda

Conseguiu baixar? Precisa de mais ajuda?`
    }
    
    // Vazamento
    if (normalized.includes('vazamento') || normalized.includes('vazando') || 
        normalized.includes('água vazando') || normalized.includes('vazou')) {
      return `🚨 **Reportar Vazamento**

Se você identificou um vazamento, siga estes passos:

1. **Ações Imediatas**
   - Feche o registro principal da água
   - Sinalize a área para evitar acidentes
   - Evite contato com a água vazada

2. **Reportar o Vazamento**
   - Acesse **Serviços Públicos > Reportar Vazamento**
   - Informe a localização exata
   - Descreva a intensidade do vazamento
   - Adicione fotos se possível

3. **Urgência**
   - Vazamentos grandes são tratados como emergência
   - Nossa equipe será acionada imediatamente

É um vazamento urgente? Posso criar um ticket de emergência agora!`
    }
    
    // Religação
    if (normalized.includes('religação') || normalized.includes('religar') || 
        normalized.includes('religar água') || normalized.includes('ligar água')) {
      return `🔧 **Solicitar Religação de Água**

Para solicitar a religação, você precisa:

1. **Regularizar Pendências**
   - Quitar todas as faturas em atraso
   - Pagar taxas de corte (se houver)
   - Verificar se não há débitos pendentes

2. **Documentos Necessários**
   - Número do imóvel/cliente
   - Comprovante de pagamento das pendências
   - CPF/CNPJ do titular
   - Endereço completo

3. **Solicitar**
   - Acesse **Atendimento > Novo Ticket**
   - Categoria: "Solicitação"
   - Assunto: "Religação de Água"

Deseja que eu crie um ticket para sua solicitação agora?`
    }
    
    // Tarifas
    if (normalized.includes('tarifa') || normalized.includes('preço') || 
        normalized.includes('valor') || normalized.includes('quanto custa')) {
      return `💰 **Tarifas de Água e Esgoto**

As tarifas variam conforme:

1. **Faixa de Consumo**
   - Até 10m³: Tarifa social
   - 11-20m³: Tarifa residencial básica
   - 21-30m³: Tarifa residencial média
   - Acima de 30m³: Tarifa residencial alta

2. **Categoria**
   - Residencial
   - Comercial
   - Industrial
   - Pública

**Para consultar sua tarifa:**
- Acesse **Serviços Públicos > Informações**
- Use a calculadora de tarifas no app
- Consulte sua última fatura

Quer simular o valor da sua próxima fatura?`
    }
    
    return null
  }

  const getBotResponse = async (userMessage: string): Promise<string | null> => {
    // 1. Verificar Chit Chat primeiro
    const chitChatResponse = checkChitChat(userMessage)
    if (chitChatResponse) {
      return chitChatResponse
    }
    
    // 2. Verificar perguntas comuns
    const commonQuestionResponse = checkCommonQuestions(userMessage)
    if (commonQuestionResponse) {
      return commonQuestionResponse
    }

    // 3. Fallback: buscar na base de conhecimento
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

    // 4. Respostas padrão como último fallback
    const message = userMessage.toLowerCase()
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

    return `Entendi. Para ajudá-lo melhor:\n\n1. 📚 Buscar na base de conhecimento\n2. 🎫 Criar ticket para atendimento\n3. 👤 Conectar com atendente\n\nO que você prefere?`
  }

  const createTicketFromChat = async (content: string): Promise<number | null> => {
    try {
      console.log('📝 Criando ticket do chat com dados:', { content })
      
      const response = await api.post('/support/tickets', {
        title: `Chat: ${content.substring(0, 50)}`,
        description: content,
        category: 'information',
        priority: 'medium',
        client_phone: user?.phone || ''
      })

      console.log('✅ Ticket criado do chat:', response.data)
      return response.data.id
    } catch (error: any) {
      console.error('❌ Erro ao criar ticket do chat:', error)
      console.error('❌ Detalhes do erro:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status
      })
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
    const messageToSend = inputMessage
    setInputMessage('')
    setIsTyping(true)

    try {
      // Verificar se é chit chat ou pergunta comum ANTES de criar ticket
      const chitChatResponse = checkChitChat(messageToSend)
      const commonQuestionResponse = checkCommonQuestions(messageToSend)
      
      // Se for chit chat ou pergunta comum, responder imediatamente sem criar ticket
      if (chitChatResponse || commonQuestionResponse) {
        const botMessage: ChatMessage = {
          id: `bot-${Date.now()}`,
          content: chitChatResponse || commonQuestionResponse || '',
          sender: 'bot',
          timestamp: new Date(),
          author_name: 'Assistente Virtual'
        }
        setMessages(prev => [...prev, botMessage])
        setIsTyping(false)
        return
      }
      
      // Se não temos ticket e não é chit chat, criar um ticket
      let ticketId = currentTicketId
      if (!ticketId) {
        ticketId = await createTicketFromChat(messageToSend)
        if (ticketId) {
          setCurrentTicketId(ticketId)
          const ticketMessage: ChatMessage = {
            id: `ticket-${Date.now()}`,
            content: `✅ **Ticket Criado!**\n\nNúmero: #${ticketId}\n\nAguarde enquanto processamos sua mensagem...`,
            sender: 'bot',
            timestamp: new Date(),
            ticket_id: ticketId
          }
          setMessages(prev => [...prev, ticketMessage])
          loadChatHistory()
        }
      }

      // Se temos ticket, enviar mensagem e aguardar resposta da IA
      if (ticketId) {
        // Enviar mensagem para o ticket (isso dispara a resposta automática da IA)
        await api.post(`/support/tickets/${ticketId}/messages`, {
          content: messageToSend
        })
        
        // Aguardar resposta da IA
        const aiResponse = await waitForAIResponse(ticketId, userMessage.timestamp)
        
        if (aiResponse) {
          const botMessage: ChatMessage = {
            id: `bot-${Date.now()}`,
            content: aiResponse,
            sender: 'bot',
            timestamp: new Date(),
            ticket_id: ticketId,
            author_name: 'Assistente Virtual'
          }
          setMessages(prev => [...prev, botMessage])
        } else {
          // Fallback: usar chit chat e perguntas comuns primeiro
          const fallbackResponse = await getBotResponse(messageToSend)
          if (fallbackResponse) {
            const botMessage: ChatMessage = {
              id: `bot-${Date.now()}`,
              content: fallbackResponse,
              sender: 'bot',
              timestamp: new Date(),
              ticket_id: ticketId,
              author_name: 'Assistente Virtual'
            }
            setMessages(prev => [...prev, botMessage])
          }
        }
      } else {
        // Sem ticket: usar respostas diretas (chit chat já foi verificado acima)
        const botResponse = await getBotResponse(messageToSend)
        if (botResponse) {
          const botMessage: ChatMessage = {
            id: `bot-${Date.now()}`,
            content: botResponse,
            sender: 'bot',
            timestamp: new Date(),
            author_name: 'Assistente Virtual'
          }
          setMessages(prev => [...prev, botMessage])
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
      
      // Garantir que ticketMessages seja sempre um array
      if (Array.isArray(ticketMessages)) {
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
      } else {
        setMessages([])
        console.warn('Resposta da API não é um array:', ticketMessages)
      }
    } catch (error) {
      console.error('Erro ao carregar mensagens do ticket:', error)
      setMessages([])
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
          {Array.isArray(chatHistory) && chatHistory.map((ticket) => (
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

