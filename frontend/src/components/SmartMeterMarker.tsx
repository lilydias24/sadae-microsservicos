import { Marker, Popup } from 'react-leaflet'
import L from 'leaflet'
import { SmartMeter, MeterCluster } from '../utils/generateSmartMeters'

interface SmartMeterClusterProps {
    cluster: MeterCluster
    onClick?: () => void
}

// Create cluster icon
const createClusterIcon = (count: number, status: string) => {
    const colors = {
        normal: '#10b981',
        warning: '#f59e0b',
        critical: '#ef4444'
    }

    const color = colors[status as keyof typeof colors] || colors.normal
    const size = Math.min(40 + Math.log(count) * 10, 60)

    return L.divIcon({
        className: 'smart-meter-cluster',
        html: `
      <div style="
        background-color: ${color};
        width: ${size}px;
        height: ${size}px;
        border-radius: 50%;
        border: 3px solid white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        color: white;
        font-size: ${Math.min(12 + Math.log(count) * 2, 18)}px;
      ">
        ${count}
      </div>
    `,
        iconSize: [size, size],
        iconAnchor: [size / 2, size / 2]
    })
}

// Create individual meter icon
const createMeterIcon = (status: string, type: string) => {
    const colors = {
        normal: '#10b981',
        warning: '#f59e0b',
        critical: '#ef4444'
    }

    const shapes = {
        residential: 'circle',
        commercial: 'square',
        industrial: 'triangle'
    }

    const color = colors[status as keyof typeof colors] || colors.normal
    const size = 10

    return L.divIcon({
        className: 'smart-meter-individual',
        html: `
      <div style="
        background-color: ${color};
        width: ${size}px;
        height: ${size}px;
        border-radius: ${type === 'residential' ? '50%' : type === 'commercial' ? '2px' : '0'};
        border: 2px solid white;
        box-shadow: 0 1px 4px rgba(0,0,0,0.3);
      "></div>
    `,
        iconSize: [size, size],
        iconAnchor: [size / 2, size / 2],
        popupAnchor: [0, -size / 2]
    })
}

const translateMeterType = (type: string): string => {
    const typeMap: { [key: string]: string } = {
        residential: 'Residencial',
        commercial: 'Comercial',
        industrial: 'Industrial'
    }
    return typeMap[type] || type
}

const translateStatus = (status: string): string => {
    const statusMap: { [key: string]: string } = {
        normal: 'Normal',
        warning: 'Aviso',
        critical: 'Crítico'
    }
    return statusMap[status] || status
}

const translateAlert = (alert: string): string => {
    const alertMap: { [key: string]: string } = {
        low_pressure: 'Pressão Baixa',
        continuous_flow: 'Fluxo Contínuo (Possível Vazamento)',
        high_consumption: 'Consumo Elevado',
        no_communication: 'Sem Comunicação'
    }
    return alertMap[alert] || alert
}

export function SmartMeterClusterMarker({ cluster, onClick }: SmartMeterClusterProps) {
    if (cluster.type === 'individual') {
        const meter = cluster.meters[0]

        return (
            <Marker
                position={[cluster.center.lat, cluster.center.lng]}
                icon={createMeterIcon(meter.status, meter.meter_type)}
            >
                <Popup>
                    <div className="p-2 min-w-[220px]">
                        <h3 className="font-bold text-sm mb-2">{meter.meter_id}</h3>
                        <div className="space-y-1 text-xs">
                            <p>
                                <span className="font-medium">Tipo:</span>{' '}
                                {translateMeterType(meter.meter_type)}
                            </p>
                            <p>
                                <span className="font-medium">Endereço:</span>{' '}
                                {meter.address}
                            </p>
                            <p>
                                <span className="font-medium">Bairro:</span>{' '}
                                {meter.neighborhood}
                            </p>
                            <hr className="my-2" />
                            <p>
                                <span className="font-medium">Vazão:</span>{' '}
                                <span className="font-bold text-blue-600">
                                    {meter.flow_rate_l_min.toFixed(1)} L/min
                                </span>
                            </p>
                            <p>
                                <span className="font-medium">Pressão:</span>{' '}
                                <span className="font-bold text-blue-600">
                                    {meter.pressure_bar.toFixed(2)} bar
                                </span>
                            </p>
                            <p>
                                <span className="font-medium">Consumo 24h:</span>{' '}
                                {meter.consumption_24h.toFixed(2)} m³
                            </p>
                            <p>
                                <span className="font-medium">Consumo 30d:</span>{' '}
                                {meter.consumption_30d.toFixed(1)} m³
                            </p>
                            <hr className="my-2" />
                            <p>
                                <span className="font-medium">Status:</span>{' '}
                                <span className={`font-semibold ${meter.status === 'critical' ? 'text-red-600' :
                                        meter.status === 'warning' ? 'text-yellow-600' :
                                            'text-green-600'
                                    }`}>
                                    {translateStatus(meter.status)}
                                </span>
                            </p>
                            {meter.alerts.length > 0 && (
                                <>
                                    <p className="font-medium mt-2">Alertas:</p>
                                    <ul className="list-disc list-inside text-xs">
                                        {meter.alerts.map((alert, idx) => (
                                            <li key={idx} className="text-red-600">
                                                {translateAlert(alert)}
                                            </li>
                                        ))}
                                    </ul>
                                </>
                            )}
                            <hr className="my-2" />
                            <p className="text-xs text-gray-500">
                                Sensor de rede: {meter.network_sensor_id}
                            </p>
                            <p className="text-xs text-gray-500">
                                Distância: {meter.distance_to_sensor_km.toFixed(2)} km
                            </p>
                        </div>
                    </div>
                </Popup>
            </Marker>
        )
    }

    // Cluster marker
    return (
        <Marker
            position={[cluster.center.lat, cluster.center.lng]}
            icon={createClusterIcon(cluster.count!, cluster.status)}
            eventHandlers={{
                click: onClick
            }}
        >
            <Popup>
                <div className="p-2">
                    <h3 className="font-bold text-sm mb-2">
                        Cluster de {cluster.count} Hidrômetros
                    </h3>
                    <div className="space-y-1 text-xs">
                        <p>
                            <span className="font-medium">Status:</span>{' '}
                            <span className={`font-semibold ${cluster.status === 'critical' ? 'text-red-600' :
                                    cluster.status === 'warning' ? 'text-yellow-600' :
                                        'text-green-600'
                                }`}>
                                {translateStatus(cluster.status)}
                            </span>
                        </p>
                        <p className="text-gray-600 mt-2">
                            Clique para aproximar e ver detalhes
                        </p>
                    </div>
                </div>
            </Popup>
        </Marker>
    )
}
