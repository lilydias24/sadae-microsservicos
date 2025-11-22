export interface SmartMeter {
    meter_id: string
    customer_id: string
    meter_type: 'residential' | 'commercial' | 'industrial'
    address: string
    neighborhood: string
    coordinates: { lat: number, lng: number }

    // Current readings
    flow_rate_l_min: number
    pressure_bar: number
    consumption_24h: number
    consumption_30d: number

    // Status
    status: 'normal' | 'warning' | 'critical'
    alerts: string[]

    // Correlation
    network_sensor_id: string
    distance_to_sensor_km: number
}

interface SensorReading {
    sensor_id: string
    sensor_type: string
    value: number
    unit: string
    location: string
    latitude?: number
    longitude?: number
    status?: 'normal' | 'warning' | 'critical'
}

// Helper to calculate distance between two coordinates (Haversine formula)
function calculateDistance(
    coord1: { lat: number, lng: number },
    coord2: { lat: number, lng: number }
): number {
    const R = 6371 // Earth's radius in km
    const dLat = (coord2.lat - coord1.lat) * Math.PI / 180
    const dLng = (coord2.lng - coord1.lng) * Math.PI / 180
    const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(coord1.lat * Math.PI / 180) * Math.cos(coord2.lat * Math.PI / 180) *
        Math.sin(dLng / 2) * Math.sin(dLng / 2)
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
    return R * c
}

// Generate random coordinates within a radius
function randomCoordinatesNear(
    center: { lat: number, lng: number },
    radiusKm: number
): { lat: number, lng: number } {
    const radiusInDegrees = radiusKm / 111 // rough conversion
    const angle = Math.random() * 2 * Math.PI
    const distance = Math.random() * radiusInDegrees

    return {
        lat: center.lat + distance * Math.cos(angle),
        lng: center.lng + distance * Math.sin(angle)
    }
}

// Generate smart meters around network sensors
export function generateSmartMeters(networkSensors: SensorReading[]): SmartMeter[] {
    const meters: SmartMeter[] = []
    let meterCounter = 1

    networkSensors.forEach(sensor => {
        if (!sensor.latitude || !sensor.longitude) return

        // Generate 50-150 meters per sensor zone
        const meterCount = Math.floor(Math.random() * 100) + 50

        for (let i = 0; i < meterCount; i++) {
            // Random coordinates within 1-2km radius
            const coords = randomCoordinatesNear(
                { lat: sensor.latitude, lng: sensor.longitude },
                Math.random() * 1 + 1 // 1-2km
            )

            const distance = calculateDistance(
                { lat: sensor.latitude, lng: sensor.longitude },
                coords
            )

            // Determine meter type (80% residential, 15% commercial, 5% industrial)
            const rand = Math.random()
            const meterType: 'residential' | 'commercial' | 'industrial' =
                rand < 0.80 ? 'residential' :
                    rand < 0.95 ? 'commercial' : 'industrial'

            // Base consumption by type
            const baseConsumption = {
                residential: { daily: 0.6, monthly: 18 },
                commercial: { daily: 4.0, monthly: 120 },
                industrial: { daily: 30.0, monthly: 900 }
            }[meterType]

            // Base flow rate (L/min)
            const baseFlow = {
                residential: 5,
                commercial: 15,
                industrial: 50
            }[meterType]

            // Calculate pressure based on sensor and distance
            let pressure = sensor.value || 3.0

            // If sensor is critical/warning, affect nearby meters
            if (sensor.status === 'critical' && distance < 2) {
                const impactFactor = 1 - (distance / 2)
                pressure *= (1 - impactFactor * 0.5) // up to 50% reduction
            } else if (sensor.status === 'warning' && distance < 1.5) {
                const impactFactor = 1 - (distance / 1.5)
                pressure *= (1 - impactFactor * 0.25) // up to 25% reduction
            }

            // Add some randomness
            pressure += (Math.random() - 0.5) * 0.3

            // Determine status
            let status: 'normal' | 'warning' | 'critical' = 'normal'
            const alerts: string[] = []

            if (pressure < 1.5) {
                status = 'critical'
                alerts.push('low_pressure')
            } else if (pressure < 2.0) {
                status = 'warning'
                alerts.push('low_pressure')
            }

            // Random leak detection (5% chance)
            if (Math.random() < 0.05) {
                status = status === 'normal' ? 'warning' : status
                alerts.push('continuous_flow')
            }

            // Random high consumption (3% chance)
            if (Math.random() < 0.03) {
                status = status === 'normal' ? 'warning' : status
                alerts.push('high_consumption')
            }

            const meter: SmartMeter = {
                meter_id: `HM-${String(meterCounter).padStart(6, '0')}`,
                customer_id: `CUST-${String(meterCounter * 7).padStart(6, '0')}`,
                meter_type: meterType,
                address: `${sensor.location} - ${i + 1}`,
                neighborhood: sensor.location,
                coordinates: coords,

                flow_rate_l_min: baseFlow + (Math.random() - 0.5) * baseFlow * 0.3,
                pressure_bar: Math.max(0.5, pressure),
                consumption_24h: baseConsumption.daily + (Math.random() - 0.5) * baseConsumption.daily * 0.2,
                consumption_30d: baseConsumption.monthly + (Math.random() - 0.5) * baseConsumption.monthly * 0.2,

                status,
                alerts,

                network_sensor_id: sensor.sensor_id,
                distance_to_sensor_km: distance
            }

            meters.push(meter)
            meterCounter++
        }
    })

    return meters
}

// Cluster smart meters for visualization
export interface MeterCluster {
    type: 'cluster' | 'individual'
    count?: number
    center: { lat: number, lng: number }
    status: 'normal' | 'warning' | 'critical'
    meters: SmartMeter[]
}

export function clusterSmartMeters(
    meters: SmartMeter[],
    zoom: number
): MeterCluster[] {
    // At high zoom, show individual meters
    if (zoom >= 14) {
        return meters.map(m => ({
            type: 'individual' as const,
            center: m.coordinates,
            status: m.status,
            meters: [m]
        }))
    }

    // Grid-based clustering
    const gridSize = zoom >= 12 ? 0.005 : 0.01 // smaller grid at higher zoom
    const clusters = new Map<string, SmartMeter[]>()

    meters.forEach(meter => {
        const key = `${Math.floor(meter.coordinates.lat / gridSize)}_${Math.floor(meter.coordinates.lng / gridSize)}`
        if (!clusters.has(key)) clusters.set(key, [])
        clusters.get(key)!.push(meter)
    })

    return Array.from(clusters.values()).map(group => {
        // Calculate center
        const center = {
            lat: group.reduce((sum, m) => sum + m.coordinates.lat, 0) / group.length,
            lng: group.reduce((sum, m) => sum + m.coordinates.lng, 0) / group.length
        }

        // Calculate cluster status (worst status wins)
        const hasCritical = group.some(m => m.status === 'critical')
        const hasWarning = group.some(m => m.status === 'warning')
        const status = hasCritical ? 'critical' : hasWarning ? 'warning' : 'normal'

        return {
            type: 'cluster' as const,
            count: group.length,
            center,
            status,
            meters: group
        }
    })
}
