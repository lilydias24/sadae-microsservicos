"use client"

import type React from "react"
import { createContext, useContext, useEffect, useState, useRef, type ReactNode } from "react"
import { useAuth } from "./AuthContext"

interface WebSocketContextType {
  ws: WebSocket | null
  isConnected: boolean
  sensorData: any[]
  alerts: any[]
  lastMessage: any
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

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [sensorData, setSensorData] = useState<any[]>([])
  const [alerts, setAlerts] = useState<any[]>([])
  const [lastMessage, setLastMessage] = useState<any>(null)
  const { token, user } = useAuth()
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

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
        console.log("🔌 WebSocket: Conectando a", wsUrl)
        
        const websocket = new WebSocket(wsUrl)
        wsRef.current = websocket

        websocket.onopen = () => {
          console.log("✅ WebSocket: Conectado com sucesso!")
          setWs(websocket)
          setIsConnected(true)
          
          // Enviar ping para manter conexão viva
          const pingInterval = setInterval(() => {
            if (websocket.readyState === WebSocket.OPEN) {
              websocket.send(JSON.stringify({ type: "ping" }))
            }
          }, 30000) // 30 segundos

          // Limpar interval quando desconectar
          websocket.addEventListener('close', () => clearInterval(pingInterval))
        }

        websocket.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data)
            console.log("📨 WebSocket: Mensagem recebida:", message)
            setLastMessage(message)

            // Processar diferentes tipos de mensagem
            if (message.type === "sensor_reading") {
              setSensorData(prev => {
                const newData = [message.data, ...prev.slice(0, 99)] // Manter últimas 100 leituras
                return newData
              })
            } else if (message.type === "anomaly_detected") {
              setAlerts(prev => [message.data, ...prev])
              console.log("⚠️ WebSocket: Nova anomalia detectada!", message.data)
            }
          } catch (error) {
            console.error("❌ WebSocket: Erro ao processar mensagem:", error)
          }
        }

        websocket.onerror = (error) => {
          console.error("❌ WebSocket: Erro na conexão:", error)
        }

        websocket.onclose = () => {
          console.log("🔌 WebSocket: Conexão fechada")
          setWs(null)
          setIsConnected(false)
          wsRef.current = null

          // Tentar reconectar após 5 segundos
          console.log("🔄 WebSocket: Tentando reconectar em 5s...")
          reconnectTimeoutRef.current = setTimeout(connectWebSocket, 5000)
        }
      } catch (error) {
        console.error("❌ WebSocket: Erro ao criar conexão:", error)
        // Tentar reconectar após 5 segundos
        reconnectTimeoutRef.current = setTimeout(connectWebSocket, 5000)
      }
    }

    connectWebSocket()

    // Cleanup
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        console.log("🔌 WebSocket: Fechando conexão...")
        wsRef.current.close()
      }
    }
  }, [token, user])

  const value = {
    ws,
    isConnected,
    sensorData,
    alerts,
    lastMessage,
  }

  return <WebSocketContext.Provider value={value}>{children}</WebSocketContext.Provider>
}
