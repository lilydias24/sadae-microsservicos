// Mock data for demonstration purposes
export const mockBills = [
  {
    id: "bill-001-2024",
    customer_id: "customer-123",
    amount: 85.50,
    consumption: 15.2,
    due_date: "2024-10-15",
    status: "pending" as const,
    created_at: "2024-09-15T10:00:00Z",
    period_start: "2024-08-15",
    period_end: "2024-09-15"
  },
  {
    id: "bill-002-2024",
    customer_id: "customer-123",
    amount: 125.30,
    consumption: 22.1,
    due_date: "2024-09-10",
    status: "overdue" as const,
    created_at: "2024-08-15T10:00:00Z",
    period_start: "2024-07-15",
    period_end: "2024-08-15"
  },
  {
    id: "bill-003-2024",
    customer_id: "customer-123",
    amount: 67.80,
    consumption: 12.5,
    due_date: "2024-08-15",
    status: "paid" as const,
    created_at: "2024-07-15T10:00:00Z",
    period_start: "2024-06-15",
    period_end: "2024-07-15"
  },
  {
    id: "bill-004-2024",
    customer_id: "customer-456",
    amount: 198.75,
    consumption: 35.8,
    due_date: "2024-10-20",
    status: "pending" as const,
    created_at: "2024-09-20T10:00:00Z",
    period_start: "2024-08-20",
    period_end: "2024-09-20"
  },
  {
    id: "bill-005-2024",
    customer_id: "customer-789",
    amount: 45.60,
    consumption: 8.9,
    due_date: "2024-10-12",
    status: "pending" as const,
    created_at: "2024-09-12T10:00:00Z",
    period_start: "2024-08-12",
    period_end: "2024-09-12"
  },
  {
    id: "bill-006-2024",
    customer_id: "customer-456",
    amount: 156.40,
    consumption: 28.3,
    due_date: "2024-09-05",
    status: "overdue" as const,
    created_at: "2024-08-05T10:00:00Z",
    period_start: "2024-07-05",
    period_end: "2024-08-05"
  }
]

export const mockDisputes = [
  {
    id: "dispute-001",
    bill_id: "bill-002-2024",
    reason: "Consumo muito alto para o período. Suspeito de vazamento não detectado ou erro na leitura do hidrômetro.",
    status: "pending" as const,
    created_at: "2024-09-11T14:30:00Z",
    response: undefined
  },
  {
    id: "dispute-002",
    bill_id: "bill-006-2024",
    reason: "Fatura cobrada mesmo com imóvel desocupado durante todo o mês de julho.",
    status: "approved" as const,
    created_at: "2024-09-06T09:15:00Z",
    response: "Após verificação, confirmamos que o imóvel estava desocupado. Valor será ajustado na próxima fatura."
  },
  {
    id: "dispute-003",
    bill_id: "bill-004-2024",
    reason: "Cobrança de taxa de esgoto incorreta.",
    status: "rejected" as const,
    created_at: "2024-09-21T16:45:00Z",
    response: "A taxa de esgoto está correta conforme regulamentação municipal vigente."
  }
]

export const mockNegotiations = [
  {
    id: "negotiation-001",
    customer_id: "customer-456",
    total_debt: 1250.80,
    installments: 6,
    monthly_amount: 208.47,
    status: "active" as const,
    created_at: "2024-08-15T11:00:00Z"
  },
  {
    id: "negotiation-002",
    customer_id: "customer-789",
    total_debt: 650.40,
    installments: 4,
    monthly_amount: 162.60,
    status: "proposed" as const,
    created_at: "2024-09-10T13:20:00Z"
  },
  {
    id: "negotiation-003",
    customer_id: "customer-101",
    total_debt: 890.30,
    installments: 12,
    monthly_amount: 74.19,
    status: "completed" as const,
    created_at: "2024-01-15T10:30:00Z"
  }
]