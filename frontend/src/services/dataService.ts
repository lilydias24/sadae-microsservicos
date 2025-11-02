import { api } from './api'
import { mockBills, mockDisputes, mockNegotiations } from '../data/mockData'
import appConfig from '../config/app.config'

// Types
export interface Bill {
  id: string
  customer_id: string
  amount: number
  consumption: number
  due_date: string
  status: 'pending' | 'overdue' | 'paid' | 'contested'
  created_at: string
  period_start: string
  period_end: string
}

export interface BillDispute {
  id: string
  bill_id: string
  reason: string
  description?: string
  status: 'pending' | 'approved' | 'rejected'
  created_at: string
  response?: string
  originalId?: number  // Add original numeric ID
}

export interface DebtNegotiation {
  id: string
  customer_id: string
  total_debt: number
  installments: number
  monthly_amount: number
  status: 'proposed' | 'active' | 'completed'
  created_at: string
}

class DataService {
  // Bills
  async getBills(): Promise<Bill[]> {
    if (appConfig.useRealData) {
      try {
        const response = await api.get('/billing/bills')
        
        if (!Array.isArray(response.data)) {
          console.warn('Response data is not an array, using mock data')
          if (appConfig.useMockFallback) {
            return mockBills
          }
          throw new Error('Invalid response format')
        }
        
        console.log('✅ Using real data from API:', response.data.length, 'bills')
        return response.data.map(this.transformBillFromAPI)
      } catch (error: any) {
        console.error('❌ Error fetching bills:', error.message)
        console.warn('Using mock data as fallback')
        if (appConfig.useMockFallback) {
          return mockBills
        }
        throw error
      }
    }
    return mockBills
  }

  async getBillsByCustomer(customerId: string): Promise<Bill[]> {
    if (appConfig.useRealData) {
      try {
        const response = await api.get(`/billing/bills?customer_id=${customerId}`)
        return response.data.map(this.transformBillFromAPI)
      } catch (error) {
        console.warn('Failed to fetch real bills data, using mock data:', error)
        if (appConfig.useMockFallback) {
          return mockBills.filter(bill => bill.customer_id === customerId)
        }
        throw error
      }
    }
    return mockBills.filter(bill => bill.customer_id === customerId)
  }

  // Transform API bill data to frontend format
  private transformBillFromAPI(apiBill: any): Bill {
    return {
      id: `bill-${apiBill.id.toString().padStart(3, '0')}-2024`,
      customer_id: `customer-${apiBill.customer_id}`,
      amount: parseFloat(apiBill.amount),
      consumption: apiBill.consumption,
      due_date: apiBill.due_date.split('T')[0],
      status: apiBill.status,
      created_at: apiBill.created_at,
      period_start: apiBill.billing_period_start.split('T')[0],
      period_end: apiBill.billing_period_end.split('T')[0]
    }
  }

  // Bill Disputes
  async getBillDisputes(): Promise<BillDispute[]> {
    if (appConfig.useRealData) {
      try {
        const response = await api.get('/billing/contests')
        if (!Array.isArray(response.data)) {
          console.warn('Contests response data is not an array, using mock data')
          if (appConfig.useMockFallback) {
            return mockDisputes
          }
          throw new Error('Invalid response format')
        }
        console.log('✅ Using real contest data from API:', response.data.length, 'contests')
        return response.data.map(this.transformDisputeFromAPI)
      } catch (error) {
        console.warn('Failed to fetch real disputes data, using mock data:', error)
        if (appConfig.useMockFallback) {
          return mockDisputes
        }
        throw error
      }
    }
    return mockDisputes
  }

  async createBillDispute(billId: string, reason: string): Promise<BillDispute> {
    if (appConfig.useRealData) {
      try {
        const response = await api.post('/billing/contests', {
          bill_id: parseInt(billId.split('-')[1]),
          reason: reason,
          description: reason
        })
        return this.transformDisputeFromAPI(response.data)
      } catch (error) {
        console.error('Failed to create real dispute:', error)
        throw error
      }
    }
    
    // Mock implementation
    const newDispute: BillDispute = {
      id: `dispute-${Date.now()}`,
      bill_id: billId,
      reason: reason,
      status: 'pending',
      created_at: new Date().toISOString()
    }
    return newDispute
  }

  private transformDisputeFromAPI(apiDispute: any): BillDispute {
    return {
      id: `dispute-${apiDispute.id.toString().padStart(3, '0')}`,
      bill_id: `bill-${apiDispute.bill_id.toString().padStart(3, '0')}-2024`,
      reason: apiDispute.reason,
      status: apiDispute.status,
      created_at: apiDispute.created_at,
      response: apiDispute.resolution,
      originalId: apiDispute.id  // Keep original numeric ID
    }
  }

  // Debt Negotiations
  async getDebtNegotiations(): Promise<DebtNegotiation[]> {
    if (appConfig.useRealData) {
      try {
        const response = await api.get('/billing/negotiations')
        if (!Array.isArray(response.data)) {
          console.warn('Negotiations response data is not an array, using mock data')
          if (appConfig.useMockFallback) {
            return mockNegotiations
          }
          throw new Error('Invalid response format')
        }
        console.log('✅ Using real negotiation data from API:', response.data.length, 'negotiations')
        return response.data.map(this.transformNegotiationFromAPI)
      } catch (error) {
        console.warn('Failed to fetch real negotiations data, using mock data:', error)
        if (appConfig.useMockFallback) {
          return mockNegotiations
        }
        throw error
      }
    }
    return mockNegotiations
  }

  async createDebtNegotiation(
    customerId: string, 
    totalDebt: number, 
    installments: number
  ): Promise<DebtNegotiation> {
    if (appConfig.useRealData) {
      try {
        const monthlyAmount = totalDebt / installments
        const response = await api.post('/billing/negotiations', {
          customer_id: parseInt(customerId.split('-')[1]),
          installments: installments,
          installment_amount: monthlyAmount,
          discount_percentage: 0.0,
          interest_rate: 0.0
        })
        return this.transformNegotiationFromAPI(response.data)
      } catch (error) {
        console.error('Failed to create real negotiation:', error)
        throw error
      }
    }

    // Mock implementation
    const monthlyAmount = totalDebt / installments
    const newNegotiation: DebtNegotiation = {
      id: `negotiation-${Date.now()}`,
      customer_id: customerId,
      total_debt: totalDebt,
      installments: installments,
      monthly_amount: monthlyAmount,
      status: 'proposed',
      created_at: new Date().toISOString()
    }
    return newNegotiation
  }

  private transformNegotiationFromAPI(apiNegotiation: any): DebtNegotiation {
    return {
      id: `negotiation-${apiNegotiation.id.toString().padStart(3, '0')}`,
      customer_id: `customer-${apiNegotiation.customer_id}`,
      total_debt: parseFloat(apiNegotiation.total_debt),
      installments: apiNegotiation.installments,
      monthly_amount: parseFloat(apiNegotiation.installment_amount),
      status: apiNegotiation.status,
      created_at: apiNegotiation.created_at
    }
  }

  // Test connection to real API
  async testConnection(): Promise<boolean> {
    try {
      await api.get('/health')
      return true
    } catch (error) {
      return false
    }
  }
}

export const dataService = new DataService()
export default dataService