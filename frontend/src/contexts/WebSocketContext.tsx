import React, { createContext, useContext, useEffect, useState, useRef, type ReactNode } from "react"
import { useAuth } from "./AuthContext"

interface WebSocketContextType {
  ws: WebSocket | null
  isConnected: boolean
  sensorData: any[]
  alerts: any[]
  lastMessage: any
  connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'reconnecting'
  reconnectCount: number
  lastMessageTime: Date | null
  latency: number | null
  connectionUptime: number | null
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined)

export const useWebSocket = () => {
  const context = useContext(WebSocketContext)
  if (context === undefined) {
    throw new Error("useWebSocket must be used within a WebSocketProvider")
  }
  return context
}

interface WebSocketProviderProps {
  children: ReactNode
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }: WebSocketProviderProps) => {
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [sensorData, setSensorData] = useState<any[]>([])
  const [alerts, setAlerts] = useState<any[]>([])
  const [lastMessage, setLastMessage] = useState<any>(null)
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'reconnecting'>('disconnected')
  const [reconnectCount, setReconnectCount] = useState(0)
  const [lastMessageTime, setLastMessageTime] = useState<Date | null>(null)
  const [latency, setLatency] = useState<number | null>(null)
  const [connectionUptime, setConnectionUptime] = useState<number | null>(null)
  const { token, user } = useAuth()
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const pingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const pongTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const connectionStartTimeRef = useRef<number | null>(null)
  const uptimeIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const reconnectCountRef = useRef<number>(0) // Ref para manter contador atualizado

  useEffect(() => {
    if (!token || !user) {
      // Silenciar mensagem quando não há autenticação (usuário não logado)
      return
    }

    const connectWebSocket = () => {
      try {
        // Conectar ao monitoring-service via WebSocket nativo
        // URL: ws://localhost:8003/ws (porta 8003 mapeada para 8002 do container)
        const wsUrl = "ws://localhost:8003/ws"
        
        // Usar ref para obter valor atualizado do contador
        const currentReconnectCount = reconnectCountRef.current
        
        // Se já tem tentativas, está reconectando - manter status visível
        if (currentReconnectCount > 0) {
          setConnectionStatus('reconnecting')
          console.log("[WebSocket] Tentando reconectar - Estado: 'reconnecting'", {
            url: wsUrl,
            timestamp: new Date().toISOString(),
            reconnectCount: currentReconnectCount,
            status: 'reconnecting',
            stateSet: true
          })
        } else {
          setConnectionStatus('connecting')
          console.log("[WebSocket] Iniciando conexão - Estado: 'connecting'", {
            url: wsUrl,
            timestamp: new Date().toISOString(),
            reconnectCount: 0,
            status: 'connecting',
            stateSet: true
          })
        }
        
        const websocket = new WebSocket(wsUrl)
        wsRef.current = websocket

        websocket.onopen = () => {
          const connectionTime = Date.now()
          console.log("[WebSocket] Conexão estabelecida com sucesso", {
            timestamp: new Date().toISOString(),
            readyState: websocket.readyState,
            reconnectCount: reconnectCount
          })
          setWs(websocket)
          setIsConnected(true)
          setConnectionStatus('connected')
          console.log("[WebSocket] Estado setado para 'connected' após conexão bem-sucedida", {
            timestamp: new Date().toISOString()
          })
          setReconnectCount(0) // Reset contador ao conectar com sucesso
          reconnectCountRef.current = 0 // Reset ref também
          connectionStartTimeRef.current = connectionTime
          setConnectionUptime(0)
          
          // Atualizar uptime a cada segundo
          if (uptimeIntervalRef.current) {
            clearInterval(uptimeIntervalRef.current)
          }
          uptimeIntervalRef.current = setInterval(() => {
            if (connectionStartTimeRef.current) {
              setConnectionUptime(Math.floor((Date.now() - connectionStartTimeRef.current) / 1000))
            }
          }, 1000)
          
          // Enviar ping para manter conexão viva e medir latência
          if (pingIntervalRef.current) {
            clearInterval(pingIntervalRef.current)
          }
          pingIntervalRef.current = setInterval(() => {
            if (websocket.readyState === WebSocket.OPEN) {
              const pingTime = Date.now()
              websocket.send(JSON.stringify({ type: "ping", timestamp: pingTime }))
              
              // Timeout para detectar se não recebeu pong
              if (pongTimeoutRef.current) {
                clearTimeout(pongTimeoutRef.current)
              }
              pongTimeoutRef.current = setTimeout(() => {
                console.warn("[WebSocket] Pong não recebido - possível problema de conexão", {
                  timestamp: new Date().toISOString(),
                  pingTime,
                  timeout: 5000
                })
                setLatency(null)
              }, 5000) // 5 segundos de timeout
            }
          }, 30000) // 30 segundos

          // Limpar interval quando desconectar
          websocket.addEventListener('close', () => {
            if (pingIntervalRef.current) {
              clearInterval(pingIntervalRef.current)
              pingIntervalRef.current = null
            }
            if (pongTimeoutRef.current) {
              clearTimeout(pongTimeoutRef.current)
              pongTimeoutRef.current = null
            }
            if (uptimeIntervalRef.current) {
              clearInterval(uptimeIntervalRef.current)
              uptimeIntervalRef.current = null
            }
            connectionStartTimeRef.current = null
            setConnectionUptime(null)
          })
        }

        websocket.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data)
            const messageTime = new Date()
            console.log("[WebSocket] Mensagem recebida", {
              type: message.type,
              timestamp: messageTime.toISOString(),
              dataSize: event.data.length
            })
            setLastMessage(message)
            setLastMessageTime(messageTime)

            // Processar pong para calcular latência
            if (message.type === "pong" && message.timestamp) {
              const latencyMs = Date.now() - message.timestamp
              setLatency(latencyMs)
              if (pongTimeoutRef.current) {
                clearTimeout(pongTimeoutRef.current)
                pongTimeoutRef.current = null
              }
              console.log("[WebSocket] Latência medida", {
                latency: `${latencyMs}ms`,
                timestamp: new Date().toISOString()
              })
            }

            // Processar diferentes tipos de mensagem
            if (message.type === "sensor_reading") {
              setSensorData((prev: any[]) => {
                const newData = [message.data, ...prev.slice(0, 99)] // Manter últimas 100 leituras
                console.log("[WebSocket] Nova leitura de sensor processada", {
                  sensorId: message.data?.sensor_id,
                  value: message.data?.value,
                  totalReadings: newData.length
                })
                return newData
              })
            } else if (message.type === "anomaly_detected") {
              setAlerts((prev: any[]) => [message.data, ...prev])
              console.log("[WebSocket] Nova anomalia detectada", {
                sensorId: message.data?.sensor_id,
                severity: message.data?.severity,
                description: message.data?.description,
                timestamp: new Date().toISOString()
              })
            }
          } catch (error) {
            console.error("[WebSocket] Erro ao processar mensagem", {
              error: error instanceof Error ? error.message : String(error),
              stack: error instanceof Error ? error.stack : undefined,
              rawData: event.data,
              timestamp: new Date().toISOString()
            })
          }
        }

        websocket.onerror = (error) => {
          console.error("[WebSocket] Erro na conexão", {
            error: error instanceof Error ? error.message : String(error),
            readyState: websocket.readyState,
            url: wsUrl,
            timestamp: new Date().toISOString()
          })
          setConnectionStatus('reconnecting')
        }

        websocket.onclose = (event) => {
          // Não reconectar se foi fechamento intencional (código 1000)
          if (event.code === 1000) {
            console.log("[WebSocket] Conexão fechada intencionalmente", {
              code: event.code,
              timestamp: new Date().toISOString()
            })
            setConnectionStatus('disconnected')
            setReconnectCount(0)
            reconnectCountRef.current = 0
            setWs(null)
            setIsConnected(false)
            wsRef.current = null
            return
          }

          // Incrementar contador de reconexões (tanto no estado quanto na ref)
          setReconnectCount((prev: number) => {
            const newCount = prev + 1
            reconnectCountRef.current = newCount // Atualizar ref também
            console.log("[WebSocket] Contador de reconexão incrementado", {
              previous: prev,
              new: newCount,
              timestamp: new Date().toISOString()
            })
            return newCount
          })
          
          // Marcar como reconectando FORA do callback para garantir atualização
          setConnectionStatus('reconnecting')
          console.log("[WebSocket] Estado setado para 'reconnecting'", {
            timestamp: new Date().toISOString(),
            reconnectCount: reconnectCountRef.current
          })
          
          // Obter o novo contador da ref para usar no timeout
          const currentCount = reconnectCountRef.current
          
          console.log("[WebSocket] Conexão fechada - iniciando reconexão", {
            code: event.code,
            reason: event.reason || "Sem motivo especificado",
            wasClean: event.wasClean,
            timestamp: new Date().toISOString(),
            reconnectCount: currentCount
          })
          
          // Tentar reconectar após 5 segundos
          console.log("[WebSocket] Agendando reconexão", {
            attempt: currentCount,
            delay: "5s",
            timestamp: new Date().toISOString()
          })
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log("[WebSocket] Executando tentativa de reconexão", {
              attempt: reconnectCountRef.current,
              timestamp: new Date().toISOString()
            })
            connectWebSocket()
          }, 5000)
          
          setWs(null)
          setIsConnected(false)
          wsRef.current = null
          
          // Limpar intervalos
          if (pingIntervalRef.current) {
            clearInterval(pingIntervalRef.current)
            pingIntervalRef.current = null
          }
          if (pongTimeoutRef.current) {
            clearTimeout(pongTimeoutRef.current)
            pongTimeoutRef.current = null
          }
          if (uptimeIntervalRef.current) {
            clearInterval(uptimeIntervalRef.current)
            uptimeIntervalRef.current = null
          }
          connectionStartTimeRef.current = null
          setConnectionUptime(null)
        }
      } catch (error) {
        console.error("[WebSocket] Erro ao criar conexão WebSocket", {
          error: error instanceof Error ? error.message : String(error),
          stack: error instanceof Error ? error.stack : undefined,
          url: "ws://localhost:8003/ws",
          timestamp: new Date().toISOString()
        })
        setConnectionStatus('reconnecting')
        setReconnectCount((prev: number) => {
          const newCount = prev + 1
          reconnectCountRef.current = newCount // Atualizar ref também
          // Tentar reconectar após 5 segundos
          reconnectTimeoutRef.current = setTimeout(connectWebSocket, 5000)
          return newCount
        })
      }
    }

    connectWebSocket()

    // Cleanup
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
        reconnectTimeoutRef.current = null
      }
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current)
        pingIntervalRef.current = null
      }
      if (pongTimeoutRef.current) {
        clearTimeout(pongTimeoutRef.current)
        pongTimeoutRef.current = null
      }
      if (uptimeIntervalRef.current) {
        clearInterval(uptimeIntervalRef.current)
        uptimeIntervalRef.current = null
      }
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        console.log("[WebSocket] Fechando conexão (cleanup)", {
          reason: "Component unmounting",
          timestamp: new Date().toISOString()
        })
        wsRef.current.close(1000, "Component unmounting")
      }
      connectionStartTimeRef.current = null
    }
  }, [token, user])

  const value = {
    ws,
    isConnected,
    sensorData,
    alerts,
    lastMessage,
    connectionStatus,
    reconnectCount,
    lastMessageTime,
    latency,
    connectionUptime,
  }

  return <WebSocketContext.Provider value={value}>{children}</WebSocketContext.Provider>
}
