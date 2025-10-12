export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ')
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(amount)
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('pt-BR')
}

export function getStatusColor(status: string): string {
  const statusColors: Record<string, string> = {
    pending: 'text-amber-700 bg-amber-50 border-amber-200',
    paid: 'text-green-700 bg-green-50 border-green-200',
    overdue: 'text-red-700 bg-red-50 border-red-200',
    approved: 'text-green-700 bg-green-50 border-green-200',
    rejected: 'text-red-700 bg-red-50 border-red-200',
    active: 'text-blue-700 bg-blue-50 border-blue-200',
    completed: 'text-green-700 bg-green-50 border-green-200',
    proposed: 'text-purple-700 bg-purple-50 border-purple-200'
  }
  
  return statusColors[status] || 'text-gray-700 bg-gray-50 border-gray-200'
}

export function getStatusText(status: string): string {
  const statusTexts: Record<string, string> = {
    pending: 'Pendente',
    paid: 'Pago',
    overdue: 'Em Atraso',
    approved: 'Aprovado',
    rejected: 'Rejeitado',
    active: 'Ativo',
    completed: 'Concluído',
    proposed: 'Proposto'
  }
  
  return statusTexts[status] || status
}