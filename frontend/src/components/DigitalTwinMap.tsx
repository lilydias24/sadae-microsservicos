import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useEffect } from 'react'

// Fix for default marker icons in Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

interface SensorData {
    sensor_id: string
    sensor_type: string
    value: number
    unit: string
    location: string
    latitude?: number
    longitude?: number
    status?: 'normal' | 'warning' | 'critical'
    timestamp?: string
}

interface DigitalTwinMapProps {
    sensors: SensorData[]
}

// Custom marker icons based on status
const createCustomIcon = (status: string = 'normal') => {
    const colors = {
        normal: '#10b981',   // green
        warning: '#f59e0b',  // yellow
        critical: '#ef4444'  // red
    }

    const color = colors[status as keyof typeof colors] || colors.normal

    return L.divIcon({
        className: 'custom-marker',
        html: `
      <div style="
        background-color: ${color};
        width: 24px;
        height: 24px;
        border-radius: 50%;
        border: 3px solid white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <div style="
          width: 8px;
          height: 8px;
          background-color: white;
          border-radius: 50%;
        "></div>
      </div>
    `,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
        popupAnchor: [0, -12]
    })
}

// Component to auto-fit bounds
function AutoFitBounds({ sensors }: { sensors: SensorData[] }) {
    const map = useMap()

    useEffect(() => {
        if (sensors.length > 0) {
            const validSensors = sensors.filter(s => s.latitude && s.longitude)
            if (validSensors.length > 0) {
                const bounds = L.latLngBounds(
                    validSensors.map(s => [s.latitude!, s.longitude!])
                )
                map.fitBounds(bounds, { padding: [50, 50] })
            }
        }
    }, [sensors, map])

    return null
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
    return typeMap[type.toLowerCase()] || type
}

const translateStatus = (status: string = 'normal'): string => {
    const statusMap: { [key: string]: string } = {
        normal: "Normal",
        warning: "Aviso",
        critical: "Crítico"
    }
    return statusMap[status.toLowerCase()] || status
}

export function DigitalTwinMap({ sensors }: DigitalTwinMapProps) {
    // Filter sensors that have coordinates
    const sensorsWithCoords = sensors.filter(s => s.latitude && s.longitude)

    // Default center (São Paulo)
    const defaultCenter: [number, number] = [-23.5505, -46.6333]

    return (
        <div className="relative w-full h-full">
            <MapContainer
                center={defaultCenter}
                zoom={13}
                style={{ height: '100%', width: '100%', borderRadius: '0.5rem' }}
                className="z-0"
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                <AutoFitBounds sensors={sensorsWithCoords} />

                {sensorsWithCoords.map((sensor) => (
                    <Marker
                        key={sensor.sensor_id}
                        position={[sensor.latitude!, sensor.longitude!]}
                        icon={createCustomIcon(sensor.status)}
                    >
                        <Popup>
                            <div className="p-2 min-w-[200px]">
                                <h3 className="font-bold text-lg mb-2">{sensor.sensor_id}</h3>
                                <div className="space-y-1 text-sm">
                                    <p>
                                        <span className="font-medium">Tipo:</span>{' '}
                                        {translateSensorType(sensor.sensor_type)}
                                    </p>
                                    <p>
                                        <span className="font-medium">Local:</span>{' '}
                                        {sensor.location}
                                    </p>
                                    <p>
                                        <span className="font-medium">Valor:</span>{' '}
                                        <span className="font-bold text-blue-600">
                                            {sensor.value} {sensor.unit}
                                        </span>
                                    </p>
                                    <p>
                                        <span className="font-medium">Status:</span>{' '}
                                        <span className={`font-semibold ${sensor.status === 'critical' ? 'text-red-600' :
                                                sensor.status === 'warning' ? 'text-yellow-600' :
                                                    'text-green-600'
                                            }`}>
                                            {translateStatus(sensor.status)}
                                        </span>
                                    </p>
                                    {sensor.timestamp && (
                                        <p className="text-xs text-gray-500 mt-2">
                                            {new Date(sensor.timestamp).toLocaleString('pt-BR')}
                                        </p>
                                    )}
                                </div>
                            </div>
                        </Popup>
                    </Marker>
                ))}
            </MapContainer>

            {/* Legend */}
            <div className="absolute bottom-4 right-4 bg-white p-3 rounded-lg shadow-lg z-[1000]">
                <h4 className="font-semibold text-sm mb-2">Legenda</h4>
                <div className="space-y-1 text-xs">
                    <div className="flex items-center gap-2">
                        <div className="w-4 h-4 rounded-full bg-green-500 border-2 border-white"></div>
                        <span>Normal</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-4 h-4 rounded-full bg-yellow-500 border-2 border-white"></div>
                        <span>Aviso</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-4 h-4 rounded-full bg-red-500 border-2 border-white"></div>
                        <span>Crítico</span>
                    </div>
                </div>
            </div>
        </div>
    )
}
