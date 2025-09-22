"use client"

import type React from "react"
import { createContext, useContext, useEffect, useState, type ReactNode } from "react"
import { io, type Socket } from "socket.io-client"
import { useAuth } from "./AuthContext"

interface WebSocketContextType {
  socket: Socket | null
  isConnected: boolean
  sensorData: any[]
  alerts: any[]
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
  const [socket, setSocket] = useState<Socket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [sensorData, setSensorData] = useState<any[]>([])
  const [alerts, setAlerts] = useState<any[]>([])
  const { token, user } = useAuth()

  useEffect(() => {
    if (token && user) {
      // WebSocket temporarily disabled - no service provides WebSocket yet
      // const newSocket = io("ws://localhost:8001", {
      //   auth: {
      //     token: token,
      //   },
      // })

      // newSocket.on("connect", () => {
      //   console.log("Connected to WebSocket")
      //   setSocket(newSocket)
      // })

      // newSocket.on("disconnect", () => {
      //   console.log("Disconnected from WebSocket")
      //   setSocket(null)
      // })

      // newSocket.on("notification", (data) => {
      //   console.log("Received notification:", data)
      // })

      // newSocket.on("alert", (data) => {
      //   console.log("Received alert:", data)
      // })

      console.log("WebSocket connection temporarily disabled")
    }

    // return () => {
    //   if (socket) {
    //     socket.disconnect()
    //   }
    // }
  }, [token, user])

  const value = {
    socket,
    isConnected,
    sensorData,
    alerts,
  }

  return <WebSocketContext.Provider value={value}>{children}</WebSocketContext.Provider>
}
