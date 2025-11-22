import { useState, useEffect, useRef, useCallback } from 'react'
import { useAuth } from '../contexts/AuthContext'

interface ChatMessage {
  id: number
  ticket_id: number
  message_type: 'client' | 'agent' | 'system'
  content: string
  author_user_id: number | null
  author_name: string
  author_email: string | null
  is_internal: boolean
  created_at: string
}

interface UseChatWebSocketReturn {
  messages: ChatMessage[]
  isConnected: boolean
  sendMessage: (content: string) => void
  sendTyping: (isTyping: boolean) => void
  error: string | null
}

export function useChatWebSocket(ticketId: number | null): UseChatWebSocketReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const { token } = useAuth()

  const connect = useCallback(() => {
    if (!ticketId || !token) {
      return
    }

    try {
      // Construir URL do WebSocket
      const wsUrl = `ws://localhost:8002/support/tickets/${ticketId}/ws?token=${encodeURIComponent(token)}`
      console.log('🔌 Conectando WebSocket do chat:', wsUrl)

      const websocket = new WebSocket(wsUrl)
      wsRef.current = websocket

      websocket.onopen = () => {
        console.log('✅ WebSocket do chat conectado!')
        setIsConnected(true)
        setError(null)

        // Enviar ping a cada 30 segundos para manter conexão viva
        pingIntervalRef.current = setInterval(() => {
          if (websocket.readyState === WebSocket.OPEN) {
            websocket.send(JSON.stringify({ type: 'ping' }))
          }
        }, 30000)
      }

      websocket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          console.log('📨 Mensagem WebSocket recebida:', message)

          switch (message.type) {
            case 'connected':
              console.log('✅ Conectado ao chat do ticket:', message.data.ticket_id)
              break

            case 'pong':
              // Resposta ao ping - conexão está viva
              break

            case 'new_message':
              // Nova mensagem recebida
              setMessages((prev) => {
                // Evitar duplicatas
                const exists = prev.some((m) => m.id === message.data.id)
                if (exists) {
                  return prev
                }
                return [...prev, message.data]
              })
              break

            case 'typing':
              // Indicador de digitação (pode ser usado no futuro)
              console.log('⌨️ Usuário digitando:', message.data)
              break

            case 'error':
              console.error('❌ Erro do WebSocket:', message.data)
              setError(message.data.message || 'Erro desconhecido')
              break

            default:
              console.log('📨 Mensagem desconhecida:', message)
          }
        } catch (error) {
          console.error('❌ Erro ao processar mensagem WebSocket:', error)
        }
      }

      websocket.onerror = (error) => {
        console.error('❌ Erro no WebSocket do chat:', error)
        setError('Erro na conexão WebSocket')
        setIsConnected(false)
      }

      websocket.onclose = () => {
        console.log('🔌 WebSocket do chat desconectado')
        setIsConnected(false)
        wsRef.current = null

        // Limpar interval de ping
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current)
          pingIntervalRef.current = null
        }

        // Tentar reconectar após 3 segundos
        if (ticketId && token) {
          console.log('🔄 Tentando reconectar em 3s...')
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, 3000)
        }
      }
    } catch (error) {
      console.error('❌ Erro ao criar WebSocket:', error)
      setError('Erro ao criar conexão WebSocket')
    }
  }, [ticketId, token])

  const sendMessage = useCallback((content: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('❌ WebSocket não está conectado')
      setError('WebSocket não está conectado')
      return
    }

    try {
      wsRef.current.send(
        JSON.stringify({
          type: 'message',
          content: content,
        })
      )
    } catch (error) {
      console.error('❌ Erro ao enviar mensagem:', error)
      setError('Erro ao enviar mensagem')
    }
  }, [])

  const sendTyping = useCallback((isTyping: boolean) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return
    }

    try {
      wsRef.current.send(
        JSON.stringify({
          type: 'typing',
          is_typing: isTyping,
        })
      )
    } catch (error) {
      console.error('❌ Erro ao enviar indicador de digitação:', error)
    }
  }, [])

  useEffect(() => {
    connect()

    // Cleanup
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current)
      }
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close()
      }
    }
  }, [connect])

  return {
    messages,
    isConnected,
    sendMessage,
    sendTyping,
    error,
  }
}

