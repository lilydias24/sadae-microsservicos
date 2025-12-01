import React, { useEffect, useState } from "react"
import { monitoringDev } from "../services/monitoringService"
import { useWebSocket } from "../contexts/WebSocketContext"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { api } from "../services/api"
import { useAuth } from "../contexts/AuthContext"
import { Modal } from "../components/ui"
import { MessageSquare, Map as MapIcon, List, Wifi, WifiOff, AlertCircle, CheckCircle2, Clock, Settings, Inbox, Bell, Save, X } from "lucide-react"
import { DigitalTwinMap } from "../components/DigitalTwinMap"
import { generateSmartMeters } from "../utils/generateSmartMeters"

// --- INTERFACES (mantidas para estrutura) ---
interface SensorReading {
  id: string
  sensor_id: string
  sensor_type: string
  value: number
  unit: string
  timestamp: string
  location: string
  latitude?: number
  longitude?: number
  status: "normal" | "warning" | "critical"
}

interface Anomaly {
  id: string
  sensor_id: string
  description: string
  severity: "low" | "medium" | "high"
  status: "pending" | "confirmed" | "resolved"
  created_at: string
}

// --- DADOS MOCADOS ---
const mockSensors: SensorReading[] = [
  // Zona Central
  { id: "s1", sensor_id: "P-101", sensor_type: "pressure", value: 3.5, unit: "bar", timestamp: new Date().toISOString(), location: "Estação Central - Sé", latitude: -23.5505, longitude: -46.6333, status: "normal" },
  { id: "s2", sensor_id: "F-102", sensor_type: "flow", value: 150.2, unit: "m³/h", timestamp: new Date().toISOString(), location: "República", latitude: -23.5443, longitude: -46.6431, status: "normal" },
  { id: "s3", sensor_id: "Q-103", sensor_type: "quality", value: 0.5, unit: "mg/L", timestamp: new Date().toISOString(), location: "Consolação", latitude: -23.5537, longitude: -46.6602, status: "normal" },

  // Zona Norte
  { id: "s4", sensor_id: "P-201", sensor_type: "pressure", value: 3.8, unit: "bar", timestamp: new Date().toISOString(), location: "Santana", latitude: -23.5089, longitude: -46.6289, status: "normal" },
  { id: "s5", sensor_id: "F-202", sensor_type: "flow", value: 180.5, unit: "m³/h", timestamp: new Date().toISOString(), location: "Tucuruvi", latitude: -23.4801, longitude: -46.6025, status: "normal" },
  { id: "s6", sensor_id: "L-203", sensor_type: "level", value: 92, unit: "%", timestamp: new Date().toISOString(), location: "Reservatório Cantareira", latitude: -23.4489, longitude: -46.6388, status: "normal" },
  { id: "s7", sensor_id: "P-204", sensor_type: "pressure", value: 3.2, unit: "bar", timestamp: new Date().toISOString(), location: "Casa Verde", latitude: -23.5178, longitude: -46.6567, status: "normal" },

  // Zona Sul
  { id: "s8", sensor_id: "P-301", sensor_type: "pressure", value: 3.6, unit: "bar", timestamp: new Date().toISOString(), location: "Vila Mariana", latitude: -23.5881, longitude: -46.6386, status: "normal" },
  { id: "s9", sensor_id: "L-302", sensor_type: "level", value: 85, unit: "%", timestamp: new Date().toISOString(), location: "Reservatório Guarapiranga", latitude: -23.6558, longitude: -46.6396, status: "warning" },
  { id: "s10", sensor_id: "F-303", sensor_type: "flow", value: 165.3, unit: "m³/h", timestamp: new Date().toISOString(), location: "Santo Amaro", latitude: -23.6528, longitude: -46.7056, status: "normal" },
  { id: "s11", sensor_id: "Q-304", sensor_type: "quality", value: 0.4, unit: "mg/L", timestamp: new Date().toISOString(), location: "Interlagos", latitude: -23.6806, longitude: -46.6750, status: "normal" },
  { id: "s12", sensor_id: "P-305", sensor_type: "pressure", value: 3.9, unit: "bar", timestamp: new Date().toISOString(), location: "Jabaquara", latitude: -23.6178, longitude: -46.6428, status: "normal" },

  // Zona Leste
  { id: "s13", sensor_id: "P-401", sensor_type: "pressure", value: 3.3, unit: "bar", timestamp: new Date().toISOString(), location: "Tatuapé", latitude: -23.5408, longitude: -46.5767, status: "normal" },
  { id: "s14", sensor_id: "F-402", sensor_type: "flow", value: 142.8, unit: "m³/h", timestamp: new Date().toISOString(), location: "Penha", latitude: -23.5289, longitude: -46.5411, status: "normal" },
  { id: "s15", sensor_id: "Q-403", sensor_type: "quality", value: 0.6, unit: "mg/L", timestamp: new Date().toISOString(), location: "São Miguel", latitude: -23.4975, longitude: -46.4361, status: "normal" },
  { id: "s16", sensor_id: "L-404", sensor_type: "level", value: 78, unit: "%", timestamp: new Date().toISOString(), location: "Reservatório Aricanduva", latitude: -23.5625, longitude: -46.5178, status: "warning" },

  // Zona Oeste
  { id: "s17", sensor_id: "P-501", sensor_type: "pressure", value: 4.1, unit: "bar", timestamp: new Date().toISOString(), location: "Pinheiros", latitude: -23.5617, longitude: -46.6822, status: "normal" },
  { id: "s18", sensor_id: "F-502", sensor_type: "flow", value: 195.7, unit: "m³/h", timestamp: new Date().toISOString(), location: "Lapa", latitude: -23.5283, longitude: -46.7056, status: "normal" },
  { id: "s19", sensor_id: "Q-503", sensor_type: "quality", value: 0.3, unit: "mg/L", timestamp: new Date().toISOString(), location: "Butantã", latitude: -23.5736, longitude: -46.7286, status: "normal" },
  { id: "s20", sensor_id: "P-504", sensor_type: "pressure", value: 4.8, unit: "bar", timestamp: new Date().toISOString(), location: "Zona Industrial - Jaguaré", latitude: -23.5520, longitude: -46.7420, status: "critical" },

  // Estações de Tratamento
  { id: "s21", sensor_id: "Q-601", sensor_type: "quality", value: 0.2, unit: "mg/L", timestamp: new Date().toISOString(), location: "ETA Guaraú", latitude: -23.4650, longitude: -46.6150, status: "normal" },
  { id: "s22", sensor_id: "Q-602", sensor_type: "quality", value: 0.3, unit: "mg/L", timestamp: new Date().toISOString(), location: "ETA Alto da Boa Vista", latitude: -23.6350, longitude: -46.6850, status: "normal" },

  // Monitoramento Meteorológico
  { id: "s23", sensor_id: "PC-701", sensor_type: "precipitation", value: 2.1, unit: "mm", timestamp: new Date().toISOString(), location: "Estação Meteorológica - Ibirapuera", latitude: -23.5875, longitude: -46.6575, status: "normal" },
  { id: "s24", sensor_id: "PC-702", sensor_type: "precipitation", value: 0.0, unit: "mm", timestamp: new Date().toISOString(), location: "Estação Norte", latitude: -23.4900, longitude: -46.6200, status: "normal" },
  { id: "s25", sensor_id: "PC-703", sensor_type: "precipitation", value: 1.5, unit: "mm", timestamp: new Date().toISOString(), location: "Estação Sul", latitude: -23.6500, longitude: -46.6800, status: "normal" },

  // Pontos Críticos
  { id: "s26", sensor_id: "P-801", sensor_type: "pressure", value: 2.1, unit: "bar", timestamp: new Date().toISOString(), location: "Zona Crítica - Capão Redondo", latitude: -23.6689, longitude: -46.7789, status: "warning" },
  { id: "s27", sensor_id: "F-802", sensor_type: "flow", value: 95.3, unit: "m³/h", timestamp: new Date().toISOString(), location: "Brasilândia", latitude: -23.4650, longitude: -46.6850, status: "warning" },
];

const mockAnomalies: Anomaly[] = [
  { id: "a1", sensor_id: "P-102", description: "Pressão 20% acima do limite superior.", severity: "high", status: "pending", created_at: new Date(Date.now() - 5 * 60 * 1000).toISOString() },
  { id: "a2", sensor_id: "L-301", description: "Nível do reservatório abaixo do limite de segurança.", severity: "medium", status: "pending", created_at: new Date(Date.now() - 30 * 60 * 1000).toISOString() },
  { id: "a3", sensor_id: "F-208", description: "Fluxo inconsistente detectado durante a madrugada.", severity: "low", status: "pending", created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString() },
];

const mockRealtimeChartData = Array.from({ length: 50 }, (_, i) => ({
  value: 3.5 + Math.sin(i / 5) * 0.5 + (Math.random() - 0.5) * 0.2,
  timestamp: new Date(Date.now() - (50 - i) * 60 * 1000).toISOString(),
}));


export function MonitoringPage() {
  const { user } = useAuth()
  const [selectedSensorType, setSelectedSensorType] = useState<string>("all")
  const [statusKey, setStatusKey] = useState(0) // Forçar re-render quando status mudar
  const { 
    sensorData, 
    alerts, 
    isConnected, 
    lastMessage,
    connectionStatus,
    reconnectCount,
    lastMessageTime,
    latency,
    connectionUptime
  } = useWebSocket()

  // Debug: Log quando status ou reconnectCount mudarem
  useEffect(() => {
    console.log("[MonitoringPage] Status ou reconnectCount mudaram", {
      connectionStatus,
      reconnectCount,
      timestamp: new Date().toISOString(),
      statusType: typeof connectionStatus,
      statusValue: connectionStatus,
      isValidStatus: ['disconnected', 'connecting', 'connected', 'reconnecting'].includes(connectionStatus),
      willShowReconnecting: connectionStatus === 'reconnecting' && reconnectCount > 0,
      willShowConnecting: connectionStatus === 'connecting'
    })
    // Forçar atualização da key para garantir re-render
    setStatusKey(prev => prev + 1)
    
    // FORÇAR ATUALIZAÇÃO DO DOM DIRETAMENTE
    const updateStatusText = () => {
      const statusElement = document.querySelector('[data-testid="status-text"]') as HTMLElement | null
      if (statusElement) {
        let displayText = ''
        if (connectionStatus === 'connected') {
          displayText = 'Conectado'
        } else if (connectionStatus === 'connecting') {
          displayText = 'Conectando...'
        } else if (connectionStatus === 'reconnecting') {
          displayText = reconnectCount > 0 ? `Reconectando... (${reconnectCount})` : 'Reconectando...'
        } else if (connectionStatus === 'disconnected') {
          displayText = reconnectCount > 0 ? `Desconectado (tentativa ${reconnectCount})` : 'Desconectado'
        } else {
          displayText = 'Desconhecido'
        }
        
        // Atualizar diretamente no DOM - FORÇAR
        statusElement.textContent = displayText
        statusElement.innerText = displayText
        statusElement.setAttribute('data-status', connectionStatus)
        statusElement.setAttribute('data-reconnect-count', String(reconnectCount))
        
        // Forçar reflow para garantir atualização visual
        void statusElement.offsetHeight
        
        console.log("[MonitoringPage] DOM atualizado FORÇADAMENTE:", {
          displayText,
          connectionStatus,
          reconnectCount,
          elementTextContent: statusElement.textContent,
          elementInnerText: statusElement.innerText,
          timestamp: new Date().toISOString()
        })
      } else {
        console.warn("[MonitoringPage] Elemento status-text não encontrado no DOM")
      }
    }
    
    // Atualizar imediatamente
    updateStatusText()
    
    // Atualizar novamente após delays para garantir
    const timeout1 = setTimeout(updateStatusText, 50)
    const timeout2 = setTimeout(updateStatusText, 200)
    
    return () => {
      clearTimeout(timeout1)
      clearTimeout(timeout2)
    }
  }, [connectionStatus, reconnectCount])
  
  // Código antigo de verificação (mantido para debug)
  useEffect(() => {
    setTimeout(() => {
      const statusElement = document.querySelector('[data-testid="status-text"]') as HTMLElement | null
      if (statusElement) {
        // Obter valores atuais do estado através dos atributos data do elemento pai
        const parentDiv = statusElement.closest('[data-status]') as HTMLElement | null
        const currentStatus = parentDiv?.getAttribute('data-status') || connectionStatus
        const currentReconnectCount = parseInt(parentDiv?.getAttribute('data-reconnect-count') || '0', 10) || reconnectCount
        
        const computedStyle = window.getComputedStyle(statusElement)
        const parentElement = statusElement.parentElement
        const parentComputedStyle = parentElement ? window.getComputedStyle(parentElement) : null
        
        // Calcular texto esperado
        let expectedText = ''
        if (currentStatus === 'connected') {
          expectedText = 'Conectado'
        } else if (currentStatus === 'connecting') {
          expectedText = 'Conectando...'
        } else if (currentStatus === 'reconnecting') {
          expectedText = currentReconnectCount > 0 ? `Reconectando... (${currentReconnectCount})` : 'Reconectando...'
        } else if (currentStatus === 'disconnected') {
          expectedText = currentReconnectCount > 0 ? `Desconectado (tentativa ${currentReconnectCount})` : 'Desconectado'
        } else {
          expectedText = 'Desconhecido'
        }
        
        console.log("[MonitoringPage] Elemento DOM encontrado:", {
          textContent: statusElement.textContent,
          innerText: statusElement.innerText || statusElement.textContent,
          expectedText,
          currentStatus,
          currentReconnectCount,
          connectionStatus,
          reconnectCount,
          isVisible: computedStyle.display !== 'none' && computedStyle.visibility !== 'hidden' && computedStyle.opacity !== '0',
          display: computedStyle.display,
          visibility: computedStyle.visibility,
          opacity: computedStyle.opacity,
          parentDisplay: parentComputedStyle?.display,
          parentVisibility: parentComputedStyle?.visibility,
          timestamp: new Date().toISOString()
        })
        
        // Forçar atualização visual se não corresponder
        if (statusElement.textContent !== expectedText) {
          console.warn("[MonitoringPage] Texto no DOM não corresponde! Atualizando forçadamente...", {
            atual: statusElement.textContent,
            esperado: expectedText
          })
          statusElement.textContent = expectedText
        }
      } else {
        console.warn("[MonitoringPage] Elemento DOM não encontrado!")
      }
    }, 100)
  }, [connectionStatus, reconnectCount])

  // Debug: Log no render para verificar se está re-renderizando
  console.log("[MonitoringPage] RENDER - Status atual", {
    connectionStatus,
    reconnectCount,
    timestamp: new Date().toISOString(),
    renderCount: Date.now()
  })

  // Estado vindo do backend, com fallback para mocks
  const [realtimeData, setRealtimeData] = useState<any[]>([])
  const [anomalies, setAnomalies] = useState<{ data: Anomaly[] }>({ data: [] })
  const [anomaliesLimit, setAnomaliesLimit] = useState<number>(20)
  const [isUpdating, setIsUpdating] = useState<number | null>(null)

  // Estados para observações (RF004)
  const [showObservationModal, setShowObservationModal] = useState(false)
  const [selectedReading, setSelectedReading] = useState<{ sensor_id: string; reading_id?: number; timestamp: string } | null>(null)
  const [observationText, setObservationText] = useState("")
  const [observationType, setObservationType] = useState<string>("general")
  const [isSubmittingObservation, setIsSubmittingObservation] = useState(false)
  const [observations, setObservations] = useState<any[]>([])
  const [viewMode, setViewMode] = useState<'list' | 'map'>('list')

  // Estados para configuração de alertas
  const [showAlertConfigModal, setShowAlertConfigModal] = useState(false)
  const [thresholds, setThresholds] = useState<Record<string, { min: number; max: number; deviation_factor: number }>>({})
  const [editingThresholds, setEditingThresholds] = useState<Record<string, { min: number; max: number }>>({})
  const [isLoadingThresholds, setIsLoadingThresholds] = useState(false)
  const [isSavingThresholds, setIsSavingThresholds] = useState(false)

  // Debug: Log quando modal mudar
  useEffect(() => {
    console.log("[MonitoringPage] Estado do modal de alertas mudou", {
      showAlertConfigModal,
      timestamp: new Date().toISOString()
    })
  }, [showAlertConfigModal])

  // Debug: Verificar se botão está no DOM e adicionar listener direto
  useEffect(() => {
    let foundButton: HTMLButtonElement | null = null
    let directHandler: ((e: Event) => void) | null = null
    
    const checkButton = () => {
      // Procurar por qualquer botão que contenha "Configurar Alertas"
      const buttons = document.querySelectorAll('button')
      
      buttons.forEach(btn => {
        if (btn.textContent?.includes('Configurar Alertas') && btn instanceof HTMLButtonElement) {
          foundButton = btn
        }
      })
      
      if (foundButton) {
        // Adicionar listener direto no DOM (fallback caso o onClick do React não funcione)
        directHandler = (e: Event) => {
          e.preventDefault()
          e.stopPropagation()
          handleOpenAlertConfig()
        }
        
        foundButton.addEventListener('click', directHandler, true) // useCapture = true
      }
    }
    
    // Verificar após um pequeno delay para garantir que o DOM foi renderizado
    const timeout = setTimeout(checkButton, 1000)
    
    return () => {
      clearTimeout(timeout)
      if (foundButton && directHandler) {
        foundButton.removeEventListener('click', directHandler, true)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Generate smart meters based on network sensors
  const [smartMeters] = useState(() => generateSmartMeters(mockSensors))

  // Carregar dados iniciais (apenas uma vez)
  useEffect(() => {
    const loadInitialData = async () => {
      console.log("[MonitoringPage] Iniciando carregamento de dados iniciais", {
        timestamp: new Date().toISOString()
      })
      try {
        const [hist, an] = await Promise.all([
          monitoringDev.getHistory({ sensor_id: "PRESS_001", limit: 50 }),
          monitoringDev.getAnomalies({ status: "pending", limit: anomaliesLimit }),
        ])
        const readings = Array.isArray(hist.data.readings) ? hist.data.readings : []
        const series = readings
          .filter((r: any) => r.sensor_id === "PRESS_001")
          .sort((a: any, b: any) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
          .map((r: any) => ({ value: Number(r.value), timestamp: r.timestamp }))
        setRealtimeData(series)
        setAnomalies({
          data: an.data?.map((a: any) => ({
            id: String(a.id),
            sensor_id: a.sensor_id,
            description: a.description,
            severity: a.severity,
            status: a.status,
            created_at: a.created_at,
          })) ?? []
        })
        console.log("[MonitoringPage] Dados iniciais carregados com sucesso", {
          readingsCount: series.length,
          anomaliesCount: an.data?.length || 0,
          timestamp: new Date().toISOString()
        })
      } catch (error) {
        console.error("[MonitoringPage] Erro ao carregar dados iniciais", {
          error: error instanceof Error ? error.message : String(error),
          stack: error instanceof Error ? error.stack : undefined,
          timestamp: new Date().toISOString()
        })
      }
    }
    loadInitialData()
  }, [])

  // Carregar limiares quando abrir o modal
  const loadThresholds = async () => {
    console.log("[MonitoringPage] Carregando limiares de alerta", {
      timestamp: new Date().toISOString()
    })
    setIsLoadingThresholds(true)
    try {
      const sensorTypes = ['pressure', 'flow', 'water_quality', 'precipitation', 'river_level']
      const thresholdsData: Record<string, { min: number; max: number; deviation_factor: number }> = {}
      const errors: string[] = []
      
      for (const type of sensorTypes) {
        try {
          console.log("[MonitoringPage] Carregando limiares para tipo", { sensorType: type })
          const response = await monitoringDev.getThresholds(type)
          thresholdsData[type] = response.data
          console.log("[MonitoringPage] Limiares carregados com sucesso", {
            sensorType: type,
            thresholds: response.data
          })
        } catch (error) {
          const errorMsg = error instanceof Error ? error.message : String(error)
          errors.push(`${type}: ${errorMsg}`)
          console.error("[MonitoringPage] Erro ao carregar limiares para tipo", {
            sensorType: type,
            error: errorMsg,
            stack: error instanceof Error ? error.stack : undefined,
            timestamp: new Date().toISOString()
          })
        }
      }
      
      if (errors.length > 0) {
        console.warn("[MonitoringPage] Alguns limiares não foram carregados", {
          errors,
          loadedTypes: Object.keys(thresholdsData),
          timestamp: new Date().toISOString()
        })
      }
      
      setThresholds(thresholdsData)
      setEditingThresholds(thresholdsData)
      console.log("[MonitoringPage] Limiares carregados com sucesso", {
        totalTypes: Object.keys(thresholdsData).length,
        timestamp: new Date().toISOString()
      })
    } catch (error) {
      console.error("[MonitoringPage] Erro crítico ao carregar limiares", {
        error: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
        timestamp: new Date().toISOString()
      })
      alert("Erro ao carregar configurações de alerta. Tente novamente.")
    } finally {
      setIsLoadingThresholds(false)
    }
  }

  // Salvar limiares
  const saveThresholds = async () => {
    console.log("[MonitoringPage] Iniciando salvamento de limiares", {
      thresholds: editingThresholds,
      timestamp: new Date().toISOString()
    })
    setIsSavingThresholds(true)
    try {
      const savedTypes: string[] = []
      const failedTypes: Array<{ type: string; error: string }> = []
      
      for (const [sensorType, values] of Object.entries(editingThresholds)) {
        const thresholdValues = values as { min: number; max: number }
        if (thresholdValues.min >= thresholdValues.max) {
          const errorMsg = `Valor mínimo (${thresholdValues.min}) deve ser menor que máximo (${thresholdValues.max})`
          console.error("[MonitoringPage] Validação de limiares falhou", {
            sensorType,
            min: thresholdValues.min,
            max: thresholdValues.max,
            error: errorMsg,
            timestamp: new Date().toISOString()
          })
          alert(`Erro: O valor mínimo deve ser menor que o máximo para ${translateSensorType(sensorType)}`)
          setIsSavingThresholds(false)
          return
        }
        
        try {
          console.log("[MonitoringPage] Salvando limiares para tipo", {
            sensorType,
            min: thresholdValues.min,
            max: thresholdValues.max
          })
          await monitoringDev.updateThresholds(sensorType, thresholdValues.min, thresholdValues.max)
          savedTypes.push(sensorType)
          console.log("[MonitoringPage] Limiares salvos com sucesso", {
            sensorType,
            timestamp: new Date().toISOString()
          })
        } catch (error) {
          const errorMsg = error instanceof Error ? error.message : String(error)
          failedTypes.push({ type: sensorType, error: errorMsg })
          console.error("[MonitoringPage] Erro ao salvar limiares para tipo", {
            sensorType,
            min: thresholdValues.min,
            max: thresholdValues.max,
            error: errorMsg,
            stack: error instanceof Error ? error.stack : undefined,
            timestamp: new Date().toISOString()
          })
          alert(`Erro ao salvar limiares para ${translateSensorType(sensorType)}. Tente novamente.`)
          setIsSavingThresholds(false)
          return
        }
      }
      
      console.log("[MonitoringPage] Todos os limiares salvos com sucesso", {
        savedTypes,
        total: savedTypes.length,
        timestamp: new Date().toISOString()
      })
      
      // Recarregar limiares atualizados
      await loadThresholds()
      alert("Limiares de alerta atualizados com sucesso!")
      setShowAlertConfigModal(false)
    } catch (error) {
      console.error("[MonitoringPage] Erro crítico ao salvar limiares", {
        error: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
        timestamp: new Date().toISOString()
      })
      alert("Erro ao salvar configurações. Tente novamente.")
    } finally {
      setIsSavingThresholds(false)
    }
  }

  // Abrir modal de configuração
  const handleOpenAlertConfig = () => {
    setShowAlertConfigModal(true)
    loadThresholds()
  }

  // Processar dados do WebSocket em tempo real
  useEffect(() => {
    if (lastMessage && lastMessage.type === "sensor_reading") {
      const reading = lastMessage.data
      console.log("[MonitoringPage] Processando nova leitura do WebSocket", {
        sensorId: reading?.sensor_id,
        value: reading?.value,
        timestamp: reading?.timestamp,
        receivedAt: new Date().toISOString()
      })

      // Atualizar gráfico em tempo real
      setRealtimeData((prev: Array<{ value: number; timestamp: string }>) => {
        const newData = [...prev, { value: Number(reading.value), timestamp: reading.timestamp }]
        // Manter apenas as últimas 50 leituras
        const trimmed = newData.slice(-50)
        console.log("[MonitoringPage] Gráfico atualizado", {
          previousCount: prev.length,
          newCount: trimmed.length,
          removedCount: newData.length - trimmed.length
        })
        return trimmed
      })
    }

    if (lastMessage && lastMessage.type === "anomaly_detected") {
      console.log("[MonitoringPage] Nova anomalia detectada via WebSocket", {
        sensorId: lastMessage.data?.sensor_id,
        severity: lastMessage.data?.severity,
        description: lastMessage.data?.description,
        timestamp: new Date().toISOString()
      })
      // Adicionar anomalia à lista
      setAnomalies((prev: { data: Anomaly[] }) => ({
        data: [lastMessage.data, ...prev.data]
      }))
    }
  }, [lastMessage])

  const handleAnomalyAction = async (id: number, action: "confirm" | "resolve") => {
    try {
      setIsUpdating(id)
      const newStatus = action === "confirm" ? "confirmed" : "resolved"
      await monitoringDev.updateAnomalyStatus(id, newStatus as any)
      // refresh list
      const an = await monitoringDev.getAnomalies({ status: "pending", limit: anomaliesLimit })
      setAnomalies({
        data: an.data?.map((a: any) => ({
          id: String(a.id),
          sensor_id: a.sensor_id,
          description: a.description,
          severity: a.severity,
          status: a.status,
          created_at: a.created_at,
        })) ?? []
      })
    } catch (e) {
      // noop
    } finally {
      setIsUpdating(null)
    }
  }

  // Função para abrir modal de observação (RF004)
  const handleOpenObservationModal = (sensorId: string, readingId?: number, timestamp?: string) => {
    setSelectedReading({ sensor_id: sensorId, reading_id: readingId, timestamp: timestamp || new Date().toISOString() })
    setShowObservationModal(true)
    setObservationText("")
  }

  // Função para submeter observação (RF004)
  const handleSubmitObservation = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    if (!selectedReading) return

    // Validação: 10-500 caracteres
    if (observationText.length < 10) {
      alert("A observação deve ter no mínimo 10 caracteres")
      return
    }
    if (observationText.length > 500) {
      alert("A observação deve ter no máximo 500 caracteres")
      return
    }

    try {
      setIsSubmittingObservation(true)
      await api.post("/monitoring/observations", {
        sensor_id: selectedReading.sensor_id,
        reading_id: selectedReading.reading_id,
        text: observationText,
        observation_type: observationType,
        timestamp: selectedReading.timestamp
      })

      alert("Observação registrada com sucesso!")
      setShowObservationModal(false)
      setObservationText("")
      setSelectedReading(null)

      // Recarregar observações se necessário
      // loadObservations()
    } catch (error: any) {
      console.error("Erro ao registrar observação:", error)
      alert(`Erro ao registrar observação: ${error.response?.data?.detail || error.message}`)
    } finally {
      setIsSubmittingObservation(false)
    }
  }

  // Filtrando os sensores mocados com base no seletor
  const filteredSensors = selectedSensorType === "all"
    ? mockSensors
    : mockSensors.filter(s => s.sensor_type === selectedSensorType);
  const sensors = { data: filteredSensors };

  const sensorsLoading = false;
  const anomaliesLoading = false;

  const sensorTypes = [
    { value: "all", label: "Todos os Sensores" },
    { value: "pressure", label: "Pressão" },
    { value: "flow", label: "Fluxo" },
    { value: "level", label: "Nível" },
    { value: "quality", label: "Qualidade" },
    { value: "precipitation", label: "Precipitação" },
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case "normal": return "text-green-600 bg-green-100"
      case "warning": return "text-yellow-600 bg-yellow-100"
      case "critical": return "text-white bg-red-600"
      default: return "text-gray-600 bg-gray-100"
    }
  }

  const getSeverityColor = (severity: string | undefined) => {
    if (!severity) return "text-gray-600 bg-gray-100"
    const normalizedSeverity = severity.toLowerCase()
    switch (normalizedSeverity) {
      case "low": return "text-blue-600 bg-blue-100"
      case "medium": return "text-yellow-600 bg-yellow-100"
      case "high": return "text-white bg-red-500"
      case "critical": return "text-white bg-red-700"
      default: return "text-gray-600 bg-gray-100"
    }
  }

  const translateSensorType = (type: string): string => {
    const typeMap: { [key: string]: string } = {
      pressure: "Pressão",
      flow: "Fluxo",
      level: "Nível",
      quality: "Qualidade",
      precipitation: "Precipitação",
      water_quality: "Qualidade da Água",
      river_level: "Nível do Rio"
    }
    const normalizedType = type.toLowerCase().replace(/-/g, '_')
    return typeMap[normalizedType] || type.charAt(0).toUpperCase() + type.slice(1)
  }

  const translateStatus = (status: string): string => {
    const statusMap: { [key: string]: string } = {
      normal: "Normal",
      warning: "Aviso",
      critical: "Crítico"
    }
    return statusMap[status.toLowerCase()] || status
  }

  const translateSeverity = (severity: string | undefined): string => {
    if (!severity) return "Médio"
    const severityMap: { [key: string]: string } = {
      low: "Baixo",
      medium: "Médio",
      high: "Alto",
      critical: "Crítico"
    }
    return severityMap[severity.toLowerCase()] || severity
  }

  const translateAnomalyDescription = (description: string): string => {
    if (!description) return ""

    // Traduzir descrições automáticas em inglês
    if (description.toLowerCase().includes("automatic anomaly detection")) {
      // Padrão 1: "Automatic anomaly detection: river_level value 2.21 exceeds threshold"
      // Padrão 2: "Automatic anomaly detection: precipitation value 9.28 exceeds threshold"
      const typeMatch = description.match(/(river_level|precipitation|flow|water_quality|pressure|level|quality)\s+value\s+([0-9.]+)/i)
      const thresholdMatch = description.match(/exceeds\s+threshold/i)

      if (typeMatch && thresholdMatch) {
        const sensorType = translateSensorType(typeMatch[1])
        const value = typeMatch[2]
        return `Detecção automática de anomalia: ${sensorType} com valor ${value} excede o limiar`
      }

      // Tradução genérica com substituições
      return description
        .replace(/Automatic anomaly detection:/i, "Detecção automática de anomalia:")
        .replace(/automatic anomaly detection:/i, "detecção automática de anomalia:")
        .replace(/exceeds threshold/i, "excede o limiar")
        .replace(/exceeded threshold/i, "excedeu o limiar")
        .replace(/river_level/gi, "nível do rio")
        .replace(/precipitation/gi, "precipitação")
        .replace(/water_quality/gi, "qualidade da água")
        .replace(/\bflow\b/gi, "fluxo")
        .replace(/\bpressure\b/gi, "pressão")
        .replace(/\blevel\b/gi, "nível")
        .replace(/\bquality\b/gi, "qualidade")
        .replace(/\bvalue\b/gi, "valor")
    }
    return description
  }

  if (sensorsLoading || anomaliesLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  // Função para formatar tempo
  const formatUptime = (seconds: number | null): string => {
    if (!seconds) return "0s"
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    if (hours > 0) return `${hours}h ${minutes}m ${secs}s`
    if (minutes > 0) return `${minutes}m ${secs}s`
    return `${secs}s`
  }

  // Função para formatar tempo desde última mensagem
  const getTimeSinceLastMessage = (): string => {
    if (!lastMessageTime) return "Nunca"
    const seconds = Math.floor((Date.now() - lastMessageTime.getTime()) / 1000)
    if (seconds < 60) return `${seconds}s atrás`
    const minutes = Math.floor(seconds / 60)
    if (minutes < 60) return `${minutes}min atrás`
    const hours = Math.floor(minutes / 60)
    return `${hours}h ${minutes % 60}min atrás`
  }

  // Função para obter cor do status de conexão WebSocket
  const getConnectionStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'text-green-600 bg-green-50 border-green-200'
      case 'connecting': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'reconnecting': return 'text-orange-600 bg-orange-50 border-orange-200'
      case 'disconnected': return 'text-red-600 bg-red-50 border-red-200'
      default: return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  // Função para obter ícone do status
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected': return <CheckCircle2 className="w-4 h-4" />
      case 'connecting': return <Clock className="w-4 h-4 animate-spin" />
      case 'reconnecting': return <AlertCircle className="w-4 h-4 animate-pulse" />
      case 'disconnected': return <WifiOff className="w-4 h-4" />
      default: return <WifiOff className="w-4 h-4" />
    }
  }

  // Função para obter texto do status
  const getStatusText = (status: string) => {
    let text = ''
    
    switch (status) {
      case 'connected': 
        text = 'Conectado'
        break
      case 'connecting': 
        text = 'Conectando...'
        break
      case 'reconnecting': 
        text = reconnectCount > 0 ? `Reconectando... (${reconnectCount})` : 'Reconectando...'
        break
      case 'disconnected': 
        text = reconnectCount > 0 ? `Desconectado (tentativa ${reconnectCount})` : 'Desconectado'
        break
      default: 
        text = 'Desconhecido'
    }
    
    // Debug: log para verificar valores
    if (status === 'reconnecting' || reconnectCount > 0) {
      console.log("[MonitoringPage] getStatusText retornando", {
        status,
        reconnectCount,
        text,
        timestamp: new Date().toISOString()
      })
    }
    
    return text
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Monitoramento em Tempo Real</h1>
          <p className="text-gray-600">Acompanhe os dados dos sensores da rede de abastecimento</p>
        </div>

        <div className="flex items-center space-x-4">
          {/* Botão de Configuração de Alertas */}
          <button
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              handleOpenAlertConfig()
            }}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer"
            title="Configurar Limiares de Alerta"
            type="button"
          >
            <Bell className="w-4 h-4" />
            <span className="text-sm font-medium">Configurar Alertas</span>
          </button>

          {/* Indicador de Status WebSocket */}
          <div 
            className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${getConnectionStatusColor(connectionStatus)}`} 
            key={`status-${connectionStatus}-${reconnectCount}`}
            data-status={connectionStatus}
            data-reconnect-count={reconnectCount}
          >
            {(() => {
              const icon = getStatusIcon(connectionStatus)
              console.log("[MonitoringPage] Renderizando ícone:", connectionStatus)
              return icon
            })()}
            <div className="flex flex-col">
              <span 
                key={`status-text-${connectionStatus}-${reconnectCount}-${statusKey}`}
                className="text-xs font-semibold" 
                data-testid="status-text"
                data-status={connectionStatus}
                data-reconnect-count={reconnectCount}
              >
                {(() => {
                  let displayText = ''
                  if (connectionStatus === 'connected') {
                    displayText = 'Conectado'
                  } else if (connectionStatus === 'connecting') {
                    displayText = 'Conectando...'
                  } else if (connectionStatus === 'reconnecting') {
                    displayText = reconnectCount > 0 ? `Reconectando... (${reconnectCount})` : 'Reconectando...'
                  } else if (connectionStatus === 'disconnected') {
                    displayText = reconnectCount > 0 ? `Desconectado (tentativa ${reconnectCount})` : 'Desconectado'
                  } else {
                    displayText = 'Desconhecido'
                  }
                  
                  console.log("[MonitoringPage] Renderizando texto no span:", {
                    displayText,
                    connectionStatus,
                    reconnectCount,
                    timestamp: new Date().toISOString(),
                    elementKey: `text-${connectionStatus}-${reconnectCount}`,
                    spanKey: `status-text-${connectionStatus}-${reconnectCount}-${statusKey}`
                  })
                  
                  return displayText
                })()}
              </span>
              {connectionStatus === 'connected' && (
                <div className="flex items-center gap-3 text-xs mt-1">
                  {latency !== null && (
                    <span className="text-gray-600">
                      Latência: <span className="font-medium">{latency}ms</span>
                    </span>
                  )}
                  {connectionUptime !== null && (
                    <span className="text-gray-600">
                      Uptime: <span className="font-medium">{formatUptime(connectionUptime)}</span>
                    </span>
                  )}
                  {lastMessageTime && (
                    <span className="text-gray-600">
                      Última msg: <span className="font-medium">{getTimeSinceLastMessage()}</span>
                    </span>
                  )}
                </div>
              )}
              {(connectionStatus === 'reconnecting' || (reconnectCount > 0 && connectionStatus !== 'connected')) && (
                <span className="text-xs text-gray-600 mt-1">
                  Tentativas: {reconnectCount}
                </span>
              )}
            </div>
          </div>
          {/* View Mode Toggle */}
          <div className="flex items-center bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('list')}
              className={`flex items-center gap-2 px-3 py-2 rounded-md transition-colors ${viewMode === 'list'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
                }`}
            >
              <List className="w-4 h-4" />
              <span className="text-sm font-medium">Lista</span>
            </button>
            <button
              onClick={() => setViewMode('map')}
              className={`flex items-center gap-2 px-3 py-2 rounded-md transition-colors ${viewMode === 'map'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
                }`}
            >
              <MapIcon className="w-4 h-4" />
              <span className="text-sm font-medium">Mapa</span>
            </button>
          </div>

          <select
            value={selectedSensorType}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSelectedSensorType(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {sensorTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>

          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-600">Ao vivo</span>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Sensores Ativos</p>
              <p className="text-2xl font-bold text-gray-900">{mockSensors.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Status Normal</p>
              <p className="text-2xl font-bold text-gray-900">
                {mockSensors.filter((s: SensorReading) => s.status === "normal").length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Alertas</p>
              <p className="text-2xl font-bold text-gray-900">
                {mockSensors.filter((s: SensorReading) => s.status === "warning").length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-red-100 rounded-lg">
              <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Críticos</p>
              <p className="text-2xl font-bold text-gray-900">
                {mockSensors.filter((s: SensorReading) => s.status === "critical").length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Real-time Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Dados em Tempo Real (Sensor de Pressão P-101)</h3>
          {user?.role === "operator" && (
            <button
              onClick={() => handleOpenObservationModal("PRESS_001", undefined, new Date().toISOString())}
              className="flex items-center space-x-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
            >
              <MessageSquare className="w-4 h-4" />
              <span>Registrar Observação</span>
            </button>
          )}
        </div>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={realtimeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" tickFormatter={(value: string) => new Date(value).toLocaleTimeString()} />
              <YAxis domain={[2, 5]} />
              <Tooltip
                labelFormatter={(value: string) => new Date(value).toLocaleString()}
                formatter={(value: number) => [`${value.toFixed(2)} bar`, "Pressão"]}
              />
              <Line type="monotone" dataKey="value" stroke="#2563eb" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Digital Twin Map or List View */}
      {viewMode === 'map' ? (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Mapa Digital Twin - Rede de Abastecimento</h3>
            <p className="text-sm text-gray-600">Visualização em tempo real dos sensores na rede</p>
          </div>
          {!filteredSensors || filteredSensors.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-[600px] text-center px-6">
              <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                <Inbox className="w-10 h-10 text-gray-400" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Nenhum sensor para exibir no mapa
              </h3>
              <p className="text-sm text-gray-600 mb-4 max-w-md">
                Configure sensores com localização (latitude e longitude) para visualizá-los no mapa de monitoramento.
              </p>
              <button
                onClick={() => {
                  // TODO: Implementar navegação para página de configuração de sensores
                  alert("Funcionalidade de configuração de sensores será implementada em breve.")
                }}
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Settings className="w-4 h-4" />
                <span>Configurar Sensores</span>
              </button>
            </div>
          ) : (
            <div className="h-[600px]">
              <DigitalTwinMap sensors={filteredSensors} smartMeters={smartMeters} />
            </div>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Sensors List */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Sensores Ativos</h3>
            </div>
            {!sensors?.data || sensors.data.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                  <Inbox className="w-8 h-8 text-gray-400" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Nenhum sensor configurado
                </h3>
                <p className="text-sm text-gray-600 mb-4 max-w-sm">
                  Não há sensores configurados no sistema no momento. Configure sensores para começar a monitorar a rede de abastecimento.
                </p>
                <button
                  onClick={() => {
                    // TODO: Implementar navegação para página de configuração de sensores
                    alert("Funcionalidade de configuração de sensores será implementada em breve.")
                  }}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <Settings className="w-4 h-4" />
                  <span>Configurar Sensores</span>
                </button>
              </div>
            ) : (
              <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
                {sensors?.data?.map((sensor: SensorReading) => (
                  <div key={sensor.id} className="px-6 py-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {translateSensorType(sensor.sensor_type)} - {sensor.sensor_id}
                        </p>
                        <p className="text-sm text-gray-600">{sensor.location}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-gray-900">
                          {sensor.value} {sensor.unit}
                        </p>
                        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(sensor.status)}`}>
                          {translateStatus(sensor.status)}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Anomalies */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Anomalias Pendentes</h3>
            </div>
            <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
              {!anomalies?.data || anomalies.data.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                    <CheckCircle2 className="w-8 h-8 text-green-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    Nenhuma anomalia pendente
                  </h3>
                  <p className="text-sm text-gray-600 max-w-sm">
                    Ótimo! Todos os sensores estão operando normalmente.
                  </p>
                </div>
              ) : (
                anomalies?.data?.map((anomaly: Anomaly) => (
                <div key={anomaly.id} className="px-6 py-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">Sensor {anomaly.sensor_id}</p>
                      <p className="text-sm text-gray-600 mt-1">{translateAnomalyDescription(anomaly.description)}</p>
                      <p className="text-xs text-gray-500 mt-1">{new Date(anomaly.created_at).toLocaleString("pt-BR")}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getSeverityColor(anomaly.severity)}`}>
                        {translateSeverity(anomaly.severity)}
                      </span>
                      <button
                        onClick={() => handleAnomalyAction(Number(anomaly.id), "confirm")}
                        disabled={isUpdating === Number(anomaly.id)}
                        className="px-2 py-1 text-xs rounded-md bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
                      >
                        {isUpdating === Number(anomaly.id) ? "..." : "Confirmar"}
                      </button>
                      <button
                        onClick={() => handleAnomalyAction(Number(anomaly.id), "resolve")}
                        disabled={isUpdating === Number(anomaly.id)}
                        className="px-2 py-1 text-xs rounded-md bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
                      >
                        {isUpdating === Number(anomaly.id) ? "..." : "Fechar"}
                      </button>
                    </div>
                  </div>
                </div>
              ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal de Observação (RF004) */}
      {showObservationModal && (
        <Modal
          isOpen={showObservationModal}
          onClose={() => {
            setShowObservationModal(false)
            setObservationText("")
            setSelectedReading(null)
          }}
          title="Registrar Observação"
        >
          <form onSubmit={handleSubmitObservation} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sensor
              </label>
              <input
                type="text"
                value={selectedReading?.sensor_id || ""}
                disabled
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tipo de Observação
              </label>
              <select
                value={observationType}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setObservationType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="general">Geral</option>
                <option value="maintenance">Manutenção</option>
                <option value="inspection">Inspeção</option>
                <option value="issue">Problema</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Observação <span className="text-gray-500">(10-500 caracteres)</span>
              </label>
              <textarea
                value={observationText}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setObservationText(e.target.value)}
                rows={5}
                minLength={10}
                maxLength={500}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Descreva a observação sobre este dado do sensor..."
              />
              <div className="mt-1 text-sm text-gray-500">
                {observationText.length}/500 caracteres
                {observationText.length > 0 && observationText.length < 10 && (
                  <span className="text-red-500 ml-2">Mínimo de 10 caracteres</span>
                )}
              </div>
            </div>

            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={() => {
                  setShowObservationModal(false)
                  setObservationText("")
                  setSelectedReading(null)
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={isSubmittingObservation || observationText.length < 10 || observationText.length > 500}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmittingObservation ? "Salvando..." : "Registrar Observação"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal de Configuração de Alertas */}
      {showAlertConfigModal && (
        <Modal
          isOpen={showAlertConfigModal}
          onClose={() => {
            setShowAlertConfigModal(false)
            setEditingThresholds({})
          }}
          title="Configurar Limiares de Alerta"
        >
          <div className="space-y-6">
            {isLoadingThresholds ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-3 text-gray-600">Carregando configurações...</span>
              </div>
            ) : (
              <>
                <p className="text-sm text-gray-600">
                  Configure os limiares mínimo e máximo para cada tipo de sensor. Valores fora desses limites serão considerados anomalias.
                </p>

                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {['pressure', 'flow', 'water_quality', 'precipitation', 'river_level'].map((sensorType) => {
                    const current = editingThresholds[sensorType] || thresholds[sensorType] || { min: 0, max: 100 }
                    const deviationFactor = thresholds[sensorType]?.deviation_factor || 2.0

                    return (
                      <div key={sensorType} className="border border-gray-200 rounded-lg p-4">
                        <h4 className="font-semibold text-gray-900 mb-3">
                          {translateSensorType(sensorType)}
                        </h4>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Limiar Mínimo
                            </label>
                            <input
                              type="number"
                              step="0.1"
                              value={current.min}
                              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                                const newValue = parseFloat(e.target.value) || 0
                                setEditingThresholds({
                                  ...editingThresholds,
                                  [sensorType]: { ...current, min: newValue }
                                })
                              }}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Limiar Máximo
                            </label>
                            <input
                              type="number"
                              step="0.1"
                              value={current.max}
                              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                                const newValue = parseFloat(e.target.value) || 0
                                setEditingThresholds({
                                  ...editingThresholds,
                                  [sensorType]: { ...current, max: newValue }
                                })
                              }}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                          </div>
                        </div>
                        <div className="mt-2 text-xs text-gray-500">
                          Fator de desvio: {deviationFactor.toFixed(1)} (usado para detecção estatística)
                        </div>
                        {current.min >= current.max && (
                          <div className="mt-2 text-xs text-red-600">
                            ⚠️ O valor mínimo deve ser menor que o máximo
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>

                <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
                  <button
                    type="button"
                    onClick={() => {
                      setShowAlertConfigModal(false)
                      setEditingThresholds({})
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors flex items-center gap-2"
                    disabled={isSavingThresholds}
                  >
                    <X className="w-4 h-4" />
                    Cancelar
                  </button>
                  <button
                    type="button"
                    onClick={saveThresholds}
                    disabled={isSavingThresholds}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                  >
                    {isSavingThresholds ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        Salvando...
                      </>
                    ) : (
                      <>
                        <Save className="w-4 h-4" />
                        Salvar Configurações
                      </>
                    )}
                  </button>
                </div>
              </>
            )}
          </div>
        </Modal>
      )}
    </div>
  )
}
