"use client"

import { useState, useMemo } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "../services/api"
import { useAuth } from "../contexts/AuthContext"
import { 
  Card, 
  CardHeader, 
  CardContent, 
  Button, 
  Badge, 
  Modal, 
  Input, 
  Skeleton,
  TableSkeleton 
} from "../components/ui"
import { formatCurrency, formatDate, getStatusColor, getStatusText } from "../utils/cn"
import { BillListSkeleton, StatCardSkeleton } from "../components/billing/BillingSkeleton"
import dataService, { type Bill, type BillDispute, type DebtNegotiation } from "../services/dataService"

export function BillingPage() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState<"bills" | "disputes" | "negotiations">("bills")
  const [selectedBill, setSelectedBill] = useState<Bill | null>(null)
  const [selectedDispute, setSelectedDispute] = useState<BillDispute | null>(null)
  const [selectedNegotiation, setSelectedNegotiation] = useState<DebtNegotiation | null>(null)
  const [showDisputeForm, setShowDisputeForm] = useState(false)
  const [showBillDetails, setShowBillDetails] = useState(false)
  const [showDisputeDetails, setShowDisputeDetails] = useState(false)
  const [showNegotiationDetails, setShowNegotiationDetails] = useState(false)
  const [disputeReason, setDisputeReason] = useState("")
  
  // Novos modais melhorados
  const [showResolveDispute, setShowResolveDispute] = useState(false)
  const [showCreateNegotiation, setShowCreateNegotiation] = useState(false)
  const [resolutionText, setResolutionText] = useState("")
  const [resolutionType, setResolutionType] = useState<"approve" | "reject" | null>(null)
  
  // Estados para nova negociação
  const [newNegotiation, setNewNegotiation] = useState({
    customerId: "",
    totalDebt: "",
    installments: "",
    discountPercentage: "",
    interestRate: "",
    description: ""
  })
  
  // Filtros
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [sortBy, setSortBy] = useState<"date" | "amount" | "status">("date")
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc")
  const [dateFilter, setDateFilter] = useState<string>("all")
  const [amountFilter, setAmountFilter] = useState<string>("all")
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false)

  const queryClient = useQueryClient()

  // Data queries using dataService (handles mock/real data automatically)
  const { data: bills = [], isLoading: billsLoading } = useQuery({
    queryKey: ["bills"],
    queryFn: () => dataService.getBills(),
  })

  const { data: disputes = [], isLoading: disputesLoading } = useQuery({
    queryKey: ["disputes"],
    queryFn: () => dataService.getBillDisputes(),
  })

  const { data: negotiations = [], isLoading: negotiationsLoading } = useQuery({
    queryKey: ["negotiations"],
    queryFn: () => dataService.getDebtNegotiations(),
  })

  const isLoading = billsLoading || disputesLoading || negotiationsLoading

  // Memoized filtered and sorted bills
  const filteredBills = useMemo(() => {
    if (!bills) return []
    
    let filtered = bills.filter((bill: Bill) => {
      const matchesSearch = bill.id.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesStatus = statusFilter === "all" || bill.status === statusFilter
      
      // Date filter
      let matchesDate = true
      if (dateFilter !== "all") {
        const billDate = new Date(bill.due_date)
        const now = new Date()
        
        switch (dateFilter) {
          case "thisMonth":
            matchesDate = billDate.getMonth() === now.getMonth() && billDate.getFullYear() === now.getFullYear()
            break
          case "lastMonth":
            const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1)
            matchesDate = billDate.getMonth() === lastMonth.getMonth() && billDate.getFullYear() === lastMonth.getFullYear()
            break
          case "last3Months":
            const threeMonthsAgo = new Date(now.getFullYear(), now.getMonth() - 3)
            matchesDate = billDate >= threeMonthsAgo
            break
          case "overdue":
            matchesDate = billDate < now && bill.status !== "paid"
            break
        }
      }
      
      // Amount filter
      let matchesAmount = true
      if (amountFilter !== "all") {
        switch (amountFilter) {
          case "low":
            matchesAmount = bill.amount < 50
            break
          case "medium":
            matchesAmount = bill.amount >= 50 && bill.amount < 150
            break
          case "high":
            matchesAmount = bill.amount >= 150
            break
        }
      }
      
      return matchesSearch && matchesStatus && matchesDate && matchesAmount
    })
    
    // Sort bills
    filtered.sort((a: Bill, b: Bill) => {
      let comparison = 0
      
      switch (sortBy) {
        case "date":
          comparison = new Date(a.due_date).getTime() - new Date(b.due_date).getTime()
          break
        case "amount":
          comparison = a.amount - b.amount
          break
        case "status":
          comparison = a.status.localeCompare(b.status)
          break
      }
      
      return sortOrder === "asc" ? comparison : -comparison
    })
    
    return filtered
  }, [bills, searchTerm, statusFilter, sortBy, sortOrder, dateFilter, amountFilter])

  // Statistics
    const statistics = useMemo(() => {
    if (!bills) return { total: 0, pending: 0, overdue: 0, paid: 0, totalAmount: 0 }

    return bills.reduce((acc: any, bill: Bill) => {      acc.total++
      acc.totalAmount += bill.amount
      
      switch (bill.status) {
        case "pending":
          acc.pending++
          break
        case "overdue":
          acc.overdue++
          break
        case "paid":
          acc.paid++
          break
      }
      
      return acc
    }, { total: 0, pending: 0, overdue: 0, paid: 0, totalAmount: 0 })
  }, [bills])
    // Create dispute mutation
  const createDisputeMutation = useMutation({
    mutationFn: (disputeData: { bill_id: string; reason: string }) => api.post("/billing/disputes", disputeData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["disputes"] })
      setShowDisputeForm(false)
      setSelectedBill(null)
      setDisputeReason("")
    },
  })

  // Process payment mutation
  const processPaymentMutation = useMutation({
    mutationFn: (billId: string) => api.post(`/billing/bills/${billId}/pay`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bills"] })
    },
  })

  // Resolve dispute mutation (approve/reject)
  const resolveDisputeMutation = useMutation({
    mutationFn: ({ disputeId, approved, resolution }: { disputeId: string, approved: boolean, resolution: string }) => 
      api.put(`/billing/contests/${disputeId}/resolve?resolution=${encodeURIComponent(resolution)}&approved=${approved}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["disputes"] })
      queryClient.invalidateQueries({ queryKey: ["bills"] })
      setShowResolveDispute(false)
      setResolutionText("")
      setResolutionType(null)
      setSelectedDispute(null)
    },
  })

  // Create debt negotiation mutation
  const createNegotiationMutation = useMutation({
    mutationFn: (negotiationData: {
      customer_id: number,
      total_debt: number,
      installments: number,
      discount_percentage: number,
      interest_rate: number,
      description?: string
    }) => api.post("/billing/debt-negotiations", negotiationData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["negotiations"] })
      setShowCreateNegotiation(false)
      setNewNegotiation({
        customerId: "",
        totalDebt: "",
        installments: "",
        discountPercentage: "",
        interestRate: "",
        description: ""
      })
    },
  })

  // Resolve negotiation mutation (approve/reject)
  const resolveNegotiationMutation = useMutation({
    mutationFn: ({ negotiationId, approved }: { negotiationId: string, approved: boolean }) => 
      api.put(`/billing/debt-negotiations/${negotiationId}/resolve?approved=${approved}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["negotiations"] })
      setShowNegotiationDetails(false)
      setSelectedNegotiation(null)
    },
  })

  if (isLoading) {
    return (
      <div className="space-y-8">
        {/* Header Skeleton */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <Skeleton className="h-8 w-64 mb-2" />
            <Skeleton className="h-5 w-96" />
          </div>
          <div className="flex flex-col lg:flex-row gap-3">
            <Skeleton className="h-10 w-64" />
            <Skeleton className="h-10 w-40" />
          </div>
        </div>

        {/* Stats Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {Array.from({ length: 4 }).map((_, index) => (
            <StatCardSkeleton key={index} />
          ))}
        </div>

        {/* Content Skeleton */}
        <Card>
          <CardHeader>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <Skeleton className="h-6 w-32 mb-2" />
                <Skeleton className="h-4 w-48" />
              </div>
              <div className="flex items-center space-x-3">
                <Skeleton className="h-10 w-40" />
                <Skeleton className="h-10 w-8" />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <BillListSkeleton count={6} />
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header Section */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {user?.role === "citizen" ? "Minhas Faturas" : "Gestão de Faturamento"}
          </h1>
          <p className="text-gray-600 mt-1">
            {user?.role === "citizen"
              ? "Visualize e gerencie suas faturas de água"
              : "Gerencie faturas, contestações e negociações de débito"}
          </p>
        </div>
        
        {/* Search and Filters */}
        <div className="space-y-4">
          <div className="flex flex-col lg:flex-row gap-3">
            <Input
              placeholder="Buscar por ID da fatura..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="lg:w-64"
            />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Todos os status</option>
              <option value="pending">Pendente</option>
              <option value="paid">Pago</option>
              <option value="overdue">Em Atraso</option>
            </select>
            <Button
              variant="ghost"
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
              className="lg:w-auto"
            >
              {showAdvancedFilters ? "Menos filtros" : "Mais filtros"}
            </Button>
          </div>
          
          {showAdvancedFilters && (
            <Card className="p-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Período
                  </label>
                  <select
                    value={dateFilter}
                    onChange={(e) => setDateFilter(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">Todos os períodos</option>
                    <option value="thisMonth">Este mês</option>
                    <option value="lastMonth">Mês passado</option>
                    <option value="last3Months">Últimos 3 meses</option>
                    <option value="overdue">Vencidas</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Valor
                  </label>
                  <select
                    value={amountFilter}
                    onChange={(e) => setAmountFilter(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">Todos os valores</option>
                    <option value="low">Até R$ 50</option>
                    <option value="medium">R$ 50 - R$ 150</option>
                    <option value="high">Acima de R$ 150</option>
                  </select>
                </div>
                
                <div className="flex items-end">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                      setSearchTerm("")
                      setStatusFilter("all")
                      setDateFilter("all")
                      setAmountFilter("all")
                      setSortBy("date")
                      setSortOrder("desc")
                    }}
                    className="w-full"
                  >
                    Limpar filtros
                  </Button>
                </div>
              </div>
              
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex flex-wrap gap-2">
                  {searchTerm && (
                    <Badge variant="info" className="flex items-center gap-1">
                      Busca: "{searchTerm}"
                      <button
                        onClick={() => setSearchTerm("")}
                        className="ml-1 hover:text-blue-800"
                      >
                        ×
                      </button>
                    </Badge>
                  )}
                  {statusFilter !== "all" && (
                    <Badge variant="info" className="flex items-center gap-1">
                      Status: {getStatusText(statusFilter)}
                      <button
                        onClick={() => setStatusFilter("all")}
                        className="ml-1 hover:text-blue-800"
                      >
                        ×
                      </button>
                    </Badge>
                  )}
                  {dateFilter !== "all" && (
                    <Badge variant="info" className="flex items-center gap-1">
                      Período: {dateFilter === "thisMonth" ? "Este mês" : 
                               dateFilter === "lastMonth" ? "Mês passado" :
                               dateFilter === "last3Months" ? "Últimos 3 meses" :
                               dateFilter === "overdue" ? "Vencidas" : dateFilter}
                      <button
                        onClick={() => setDateFilter("all")}
                        className="ml-1 hover:text-blue-800"
                      >
                        ×
                      </button>
                    </Badge>
                  )}
                  {amountFilter !== "all" && (
                    <Badge variant="info" className="flex items-center gap-1">
                      Valor: {amountFilter === "low" ? "Até R$ 50" :
                              amountFilter === "medium" ? "R$ 50-150" :
                              amountFilter === "high" ? "Acima R$ 150" : amountFilter}
                      <button
                        onClick={() => setAmountFilter("all")}
                        className="ml-1 hover:text-blue-800"
                      >
                        ×
                      </button>
                    </Badge>
                  )}
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-3 bg-blue-100 rounded-lg">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total de Faturas</p>
              <p className="text-2xl font-bold text-gray-900">{statistics.total}</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-3 bg-amber-100 rounded-lg">
              <svg className="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Pendentes</p>
              <p className="text-2xl font-bold text-gray-900">{statistics.pending}</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-3 bg-red-100 rounded-lg">
              <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Em Atraso</p>
              <p className="text-2xl font-bold text-gray-900">{statistics.overdue}</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-3 bg-green-100 rounded-lg">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Pagas</p>
              <p className="text-2xl font-bold text-gray-900">{statistics.paid}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Navigation Tabs */}
      {user?.role !== "citizen" && (
        <Card padding="none">
          <nav className="flex space-x-8 px-6 py-4 border-b border-gray-100">
            {[
              { id: "bills", name: "Faturas", icon: "📄", count: statistics.total },
              { id: "disputes", name: "Contestações", icon: "⚖️", count: disputes?.length || 0 },
              { id: "negotiations", name: "Negociações", icon: "🤝", count: negotiations?.length || 0 },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                <span>{tab.icon}</span>
                <span>{tab.name}</span>
                <Badge variant="default" className="ml-1">{tab.count}</Badge>
              </button>
            ))}
          </nav>
        </Card>
      )}

      {/* Bills Content */}
      {(activeTab === "bills" || user?.role === "citizen") && (
        <Card>
          <CardHeader>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  {user?.role === "citizen" ? "Suas Faturas" : "Todas as Faturas"}
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  {filteredBills.length === bills?.length 
                    ? `${filteredBills.length} faturas encontradas`
                    : `${filteredBills.length} de ${bills?.length || 0} faturas (filtradas)`
                  }
                </p>
              </div>
              <div className="flex items-center space-x-3">
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="date">Ordenar por data</option>
                  <option value="amount">Ordenar por valor</option>
                  <option value="status">Ordenar por status</option>
                </select>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}
                >
                  {sortOrder === "asc" ? "↑" : "↓"}
                </Button>
              </div>
            </div>
          </CardHeader>
          
          <CardContent>
            {filteredBills.length === 0 ? (
              <div className="text-center py-16">
                <div className="mx-auto w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                  <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  {searchTerm || statusFilter !== "all" || dateFilter !== "all" || amountFilter !== "all"
                    ? "Nenhuma fatura encontrada"
                    : "Nenhuma fatura disponível"}
                </h3>
                <p className="text-gray-500 mb-4">
                  {searchTerm || statusFilter !== "all" || dateFilter !== "all" || amountFilter !== "all"
                    ? "Tente ajustar os filtros para encontrar mais resultados."
                    : "Não há faturas para exibir no momento."}
                </p>
                {(searchTerm || statusFilter !== "all" || dateFilter !== "all" || amountFilter !== "all") && (
                  <Button
                    variant="secondary"
                    onClick={() => {
                      setSearchTerm("")
                      setStatusFilter("all")
                      setDateFilter("all")
                      setAmountFilter("all")
                    }}
                  >
                    Limpar todos os filtros
                  </Button>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                {filteredBills.map((bill: Bill) => (
                  <div key={bill.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h4 className="text-sm font-medium text-gray-900">
                            Fatura #{bill.id.slice(-8)}
                          </h4>
                          <Badge className={getStatusColor(bill.status)}>
                            {getStatusText(bill.status)}
                          </Badge>
                        </div>
                        
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm text-gray-600">
                          <div className="flex items-center space-x-2">
                            <span>💰</span>
                            <span className="font-medium">{formatCurrency(bill.amount)}</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span>💧</span>
                            <span>{bill.consumption}m³</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span>📅</span>
                            <span>Vence em {formatDate(bill.due_date)}</span>
                          </div>
                        </div>
                        
                        <div className="mt-2 text-xs text-gray-500">
                          Período: {formatDate(bill.period_start)} - {formatDate(bill.period_end)}
                        </div>
                      </div>
                      
                      <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-2 sm:space-y-0 sm:space-x-2">
                        {user?.role === "citizen" && bill.status === "pending" && (
                          <>
                            <Button
                              onClick={() => processPaymentMutation.mutate(bill.id)}
                              variant="success"
                              size="sm"
                              isLoading={processPaymentMutation.isPending}
                              className="w-full sm:w-auto"
                            >
                              Pagar
                            </Button>
                            <Button
                              onClick={() => {
                                setSelectedBill(bill)
                                setShowDisputeForm(true)
                              }}
                              variant="warning"
                              size="sm"
                              className="w-full sm:w-auto"
                            >
                              Contestar
                            </Button>
                          </>
                        )}
                        <Button 
                          variant="ghost" 
                          size="sm"
                          className="w-full sm:w-auto"
                          onClick={() => {
                            setSelectedBill(bill)
                            setShowBillDetails(true)
                          }}
                        >
                          Ver Detalhes
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Disputes Content */}
      {activeTab === "disputes" && user?.role !== "citizen" && (
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-gray-900">Contestações de Faturas</h3>
            <p className="text-sm text-gray-600 mt-1">
              {disputes?.length || 0} contestações registradas
            </p>
          </CardHeader>
          <CardContent>
            {!disputes?.length ? (
              <div className="text-center py-12">
                <div className="mx-auto w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                  <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Nenhuma contestação</h3>
                <p className="text-gray-500">Não há contestações de faturas no momento.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {disputes.map((dispute: BillDispute) => (
                  <div key={dispute.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h4 className="text-sm font-medium text-gray-900">
                            Contestação #{dispute.id.slice(-8)}
                          </h4>
                          <Badge className={getStatusColor(dispute.status)}>
                            {getStatusText(dispute.status)}
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-600 mb-2">{dispute.reason}</p>
                        <div className="text-xs text-gray-500 mb-2">
                          Fatura: #{dispute.bill_id.slice(-8)} • {formatDate(dispute.created_at)}
                        </div>
                        {dispute.response && (
                          <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                            <p className="text-sm font-medium text-blue-900 mb-1">Resposta da administração:</p>
                            <p className="text-sm text-blue-800">{dispute.response}</p>
                          </div>
                        )}
                      </div>
                      {dispute.status === "pending" && user?.role !== "citizen" && (
                        <div className="flex items-center space-x-2 ml-4">
                          <Button 
                            variant="success" 
                            size="sm"
                            onClick={() => {
                              setSelectedDispute(dispute)
                              setResolutionType("approve")
                              setShowResolveDispute(true)
                            }}
                          >
                            Aprovar
                          </Button>
                          <Button 
                            variant="danger" 
                            size="sm"
                            onClick={() => {
                              setSelectedDispute(dispute)
                              setResolutionType("reject")
                              setShowResolveDispute(true)
                            }}
                          >
                            Rejeitar
                          </Button>
                        </div>
                      )}
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => {
                          setSelectedDispute(dispute)
                          setShowDisputeDetails(true)
                        }}
                      >
                        Ver Detalhes
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Negotiations Content */}
      {activeTab === "negotiations" && user?.role !== "citizen" && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Negociações de Débito</h3>
                <p className="text-sm text-gray-600 mt-1">
                  {negotiations?.length || 0} negociações registradas
                </p>
              </div>
              {user?.role !== "citizen" && (
                <Button 
                  onClick={() => setShowCreateNegotiation(true)}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  Nova Negociação
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {!negotiations?.length ? (
              <div className="text-center py-12">
                <div className="mx-auto w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                  <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Nenhuma negociação</h3>
                <p className="text-gray-500">Não há negociações de débito no momento.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {negotiations.map((negotiation: DebtNegotiation) => (
                  <div key={negotiation.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h4 className="text-sm font-medium text-gray-900">
                            Negociação #{negotiation.id.slice(-8)}
                          </h4>
                          <Badge className={getStatusColor(negotiation.status)}>
                            {getStatusText(negotiation.status)}
                          </Badge>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm text-gray-600">
                          <div className="flex items-center space-x-2">
                            <span>💰</span>
                            <span>Total: {formatCurrency(negotiation.total_debt)}</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span>📊</span>
                            <span>{negotiation.installments}x de {formatCurrency(negotiation.monthly_amount)}</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span>📅</span>
                            <span>{formatDate(negotiation.created_at)}</span>
                          </div>
                        </div>
                      </div>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => {
                          setSelectedNegotiation(negotiation)
                          setShowNegotiationDetails(true)
                        }}
                      >
                        Ver Detalhes
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Dispute Form Modal */}
      <Modal
        isOpen={showDisputeForm}
        onClose={() => {
          setShowDisputeForm(false)
          setSelectedBill(null)
          setDisputeReason("")
        }}
        title={`Contestar Fatura #${selectedBill?.id.slice(-8) || ''}`}
        size="md"
      >
        <div className="space-y-6">
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">Detalhes da Fatura</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Valor:</span>
                <span className="ml-2 font-medium">{selectedBill && formatCurrency(selectedBill.amount)}</span>
              </div>
              <div>
                <span className="text-gray-500">Consumo:</span>
                <span className="ml-2 font-medium">{selectedBill?.consumption}m³</span>
              </div>
              <div>
                <span className="text-gray-500">Vencimento:</span>
                <span className="ml-2 font-medium">{selectedBill && formatDate(selectedBill.due_date)}</span>
              </div>
              <div>
                <span className="text-gray-500">Status:</span>
                <Badge className={`ml-2 ${selectedBill && getStatusColor(selectedBill.status)}`}>
                  {selectedBill && getStatusText(selectedBill.status)}
                </Badge>
              </div>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Motivo da Contestação *
            </label>
            <textarea
              value={disputeReason}
              onChange={(e) => setDisputeReason(e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Descreva detalhadamente o motivo da sua contestação..."
              required
            />
            {disputeReason.length > 0 && disputeReason.length < 10 && (
              <p className="text-sm text-amber-600 mt-1">
                Por favor, forneça mais detalhes (mínimo 10 caracteres)
              </p>
            )}
          </div>

          <div className="flex flex-col sm:flex-row gap-3 sm:justify-end">
            <Button
              variant="secondary"
              onClick={() => {
                setShowDisputeForm(false)
                setSelectedBill(null)
                setDisputeReason("")
              }}
              className="w-full sm:w-auto"
            >
              Cancelar
            </Button>
            <Button
              onClick={() => selectedBill && createDisputeMutation.mutate({
                bill_id: selectedBill.id,
                reason: disputeReason,
              })}
              disabled={!disputeReason.trim() || disputeReason.length < 10}
              isLoading={createDisputeMutation.isPending}
              className="w-full sm:w-auto"
            >
              Enviar Contestação
            </Button>
          </div>
        </div>
      </Modal>

      {/* Bill Details Modal */}
      <Modal
        isOpen={showBillDetails}
        onClose={() => {
          setShowBillDetails(false)
          setSelectedBill(null)
        }}
        title={`Detalhes da Fatura #${selectedBill?.id.slice(-8) || ''}`}
        size="lg"
      >
        {selectedBill && (
          <div className="space-y-6">
            {/* Status Banner */}
            <div className={`p-4 rounded-lg border ${
              selectedBill.status === "paid" 
                ? "bg-green-50 border-green-200" 
                : selectedBill.status === "overdue"
                ? "bg-red-50 border-red-200"
                : "bg-amber-50 border-amber-200"
            }`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`w-3 h-3 rounded-full ${
                    selectedBill.status === "paid" 
                      ? "bg-green-500" 
                      : selectedBill.status === "overdue"
                      ? "bg-red-500"
                      : "bg-amber-500"
                  }`} />
                  <span className="font-medium text-gray-900">
                    Status: {getStatusText(selectedBill.status)}
                  </span>
                </div>
                <Badge className={getStatusColor(selectedBill.status)}>
                  {getStatusText(selectedBill.status)}
                </Badge>
              </div>
            </div>

            {/* Billing Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card className="p-4">
                <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                  <span className="mr-2">💰</span>
                  Informações de Cobrança
                </h4>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Valor Total:</span>
                    <span className="font-medium text-lg text-gray-900">
                      {formatCurrency(selectedBill.amount)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Data de Vencimento:</span>
                    <span className="font-medium">
                      {formatDate(selectedBill.due_date)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Data de Emissão:</span>
                    <span className="font-medium">
                      {formatDate(selectedBill.created_at)}
                    </span>
                  </div>
                </div>
              </Card>

              <Card className="p-4">
                <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                  <span className="mr-2">💧</span>
                  Consumo de Água
                </h4>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Consumo Total:</span>
                    <span className="font-medium text-lg text-blue-600">
                      {selectedBill.consumption} m³
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Período de Leitura:</span>
                    <span className="font-medium text-sm">
                      {formatDate(selectedBill.period_start)} - {formatDate(selectedBill.period_end)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Valor por m³:</span>
                    <span className="font-medium">
                      {formatCurrency(selectedBill.amount / selectedBill.consumption)}
                    </span>
                  </div>
                </div>
              </Card>
            </div>

            {/* Breakdown */}
            <Card className="p-4">
              <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                <span className="mr-2">📊</span>
                Detalhamento da Fatura
              </h4>
              <div className="space-y-3">
                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                  <span className="text-gray-600">Consumo de Água ({selectedBill.consumption} m³)</span>
                  <span className="font-medium">
                    {formatCurrency(selectedBill.amount * 0.75)}
                  </span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                  <span className="text-gray-600">Taxa de Esgoto</span>
                  <span className="font-medium">
                    {formatCurrency(selectedBill.amount * 0.20)}
                  </span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                  <span className="text-gray-600">Taxas Municipais</span>
                  <span className="font-medium">
                    {formatCurrency(selectedBill.amount * 0.05)}
                  </span>
                </div>
                <div className="flex justify-between items-center py-2 border-t-2 border-gray-300 font-semibold text-lg">
                  <span className="text-gray-900">Total a Pagar</span>
                  <span className="text-gray-900">
                    {formatCurrency(selectedBill.amount)}
                  </span>
                </div>
              </div>
            </Card>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-gray-200">
              {selectedBill.status === "pending" && user?.role === "citizen" && (
                <>
                  <Button
                    onClick={() => {
                      processPaymentMutation.mutate(selectedBill.id)
                      setShowBillDetails(false)
                    }}
                    variant="success"
                    className="flex-1"
                    isLoading={processPaymentMutation.isPending}
                  >
                    💳 Pagar Fatura
                  </Button>
                  <Button
                    onClick={() => {
                      setShowBillDetails(false)
                      setShowDisputeForm(true)
                    }}
                    variant="warning"
                    className="flex-1"
                  >
                    ⚖️ Contestar
                  </Button>
                </>
              )}
              <Button
                variant="secondary"
                onClick={() => {
                  // Simular download do PDF
                  alert(`Download da fatura #${selectedBill.id.slice(-8)} iniciado!`)
                }}
                className="flex-1"
              >
                📄 Baixar PDF
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Dispute Details Modal */}
      <Modal
        isOpen={showDisputeDetails}
        onClose={() => {
          setShowDisputeDetails(false)
          setSelectedDispute(null)
        }}
        title={`Detalhes da Contestação #${selectedDispute?.id.slice(-8) || ''}`}
        size="lg"
      >
        {selectedDispute && (
          <div className="space-y-6">
            {/* Status */}
            <div className={`p-4 rounded-lg border ${
              selectedDispute.status === "approved" 
                ? "bg-green-50 border-green-200" 
                : selectedDispute.status === "rejected"
                ? "bg-red-50 border-red-200"
                : "bg-amber-50 border-amber-200"
            }`}>
              <div className="flex items-center justify-between">
                <span className="font-medium text-gray-900">
                  Status da Contestação
                </span>
                <Badge className={getStatusColor(selectedDispute.status)}>
                  {getStatusText(selectedDispute.status)}
                </Badge>
              </div>
            </div>

            {/* Dispute Information */}
            <Card className="p-4">
              <h4 className="font-semibold text-gray-900 mb-3">Informações da Contestação</h4>
              <div className="space-y-3">
                <div>
                  <span className="text-sm font-medium text-gray-700">Fatura Contestada:</span>
                  <p className="text-gray-900">#{selectedDispute.bill_id.slice(-8)}</p>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-700">Data da Contestação:</span>
                  <p className="text-gray-900">{formatDate(selectedDispute.created_at)}</p>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-700">Motivo:</span>
                  <p className="text-gray-900 mt-1 p-3 bg-gray-50 rounded-lg">
                    {selectedDispute.reason}
                  </p>
                </div>
                {selectedDispute.response && (
                  <div>
                    <span className="text-sm font-medium text-gray-700">Resposta da Administração:</span>
                    <p className="text-gray-900 mt-1 p-3 bg-blue-50 rounded-lg border border-blue-200">
                      {selectedDispute.response}
                    </p>
                  </div>
                )}
              </div>
            </Card>

            {/* Actions for pending disputes */}
            {selectedDispute.status === "pending" && user?.role !== "citizen" && (
              <div className="flex gap-3 pt-4 border-t border-gray-200">
                <Button variant="success" className="flex-1">
                  ✅ Aprovar Contestação
                </Button>
                <Button variant="danger" className="flex-1">
                  ❌ Rejeitar Contestação
                </Button>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* Negotiation Details Modal */}
      <Modal
        isOpen={showNegotiationDetails}
        onClose={() => {
          setShowNegotiationDetails(false)
          setSelectedNegotiation(null)
        }}
        title={`Detalhes da Negociação #${selectedNegotiation?.id.slice(-8) || ''}`}
        size="lg"
      >
        {selectedNegotiation && (
          <div className="space-y-6">
            {/* Status */}
            <div className={`p-4 rounded-lg border ${
              selectedNegotiation.status === "completed" 
                ? "bg-green-50 border-green-200" 
                : selectedNegotiation.status === "active"
                ? "bg-blue-50 border-blue-200"
                : "bg-purple-50 border-purple-200"
            }`}>
              <div className="flex items-center justify-between">
                <span className="font-medium text-gray-900">
                  Status da Negociação
                </span>
                <Badge className={getStatusColor(selectedNegotiation.status)}>
                  {getStatusText(selectedNegotiation.status)}
                </Badge>
              </div>
            </div>

            {/* Negotiation Summary */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card className="p-4">
                <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                  <span className="mr-2">💰</span>
                  Resumo Financeiro
                </h4>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Valor Total da Dívida:</span>
                    <span className="font-medium text-lg text-red-600">
                      {formatCurrency(selectedNegotiation.total_debt)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Número de Parcelas:</span>
                    <span className="font-medium">
                      {selectedNegotiation.installments}x
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Valor Mensal:</span>
                    <span className="font-medium text-lg text-green-600">
                      {formatCurrency(selectedNegotiation.monthly_amount)}
                    </span>
                  </div>
                </div>
              </Card>

              <Card className="p-4">
                <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                  <span className="mr-2">📅</span>
                  Informações da Negociação
                </h4>
                <div className="space-y-3">
                  <div>
                    <span className="text-gray-600">Data de Criação:</span>
                    <p className="font-medium">{formatDate(selectedNegotiation.created_at)}</p>
                  </div>
                  <div>
                    <span className="text-gray-600">Cliente:</span>
                    <p className="font-medium">#{selectedNegotiation.customer_id.slice(-8)}</p>
                  </div>
                  <div>
                    <span className="text-gray-600">Taxa de Desconto:</span>
                    <p className="font-medium text-green-600">
                      {((1 - (selectedNegotiation.monthly_amount * selectedNegotiation.installments) / selectedNegotiation.total_debt) * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>
              </Card>
            </div>

            {/* Payment Schedule */}
            <Card className="p-4">
              <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                <span className="mr-2">📊</span>
                Cronograma de Pagamento
              </h4>
              <div className="space-y-2">
                {Array.from({ length: selectedNegotiation.installments }, (_, index) => {
                  const dueDate = new Date()
                  dueDate.setMonth(dueDate.getMonth() + index + 1)
                  
                  return (
                    <div key={index} className="flex justify-between items-center py-2 border-b border-gray-100">
                      <span className="text-gray-600">
                        {index + 1}ª Parcela - {formatDate(dueDate.toISOString())}
                      </span>
                      <span className="font-medium">
                        {formatCurrency(selectedNegotiation.monthly_amount)}
                      </span>
                    </div>
                  )
                })}
                <div className="flex justify-between items-center py-2 border-t-2 border-gray-300 font-semibold">
                  <span className="text-gray-900">Total a Pagar</span>
                  <span className="text-gray-900">
                    {formatCurrency(selectedNegotiation.monthly_amount * selectedNegotiation.installments)}
                  </span>
                </div>
              </div>
            </Card>

            {/* Actions */}
            {selectedNegotiation.status === "proposed" && user?.role !== "citizen" && (
              <div className="flex gap-3 pt-4 border-t border-gray-200">
                <Button 
                  variant="success" 
                  className="flex-1"
                  onClick={() => {
                    resolveNegotiationMutation.mutate({
                      negotiationId: selectedNegotiation.id,
                      approved: true
                    })
                  }}
                  isLoading={resolveNegotiationMutation.isPending}
                >
                  ✅ Aprovar Negociação
                </Button>
                <Button 
                  variant="danger" 
                  className="flex-1"
                  onClick={() => {
                    resolveNegotiationMutation.mutate({
                      negotiationId: selectedNegotiation.id,
                      approved: false
                    })
                  }}
                  isLoading={resolveNegotiationMutation.isPending}
                >
                  ❌ Rejeitar Negociação
                </Button>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* Modal para Resolver Contestação */}
      <Modal 
        isOpen={showResolveDispute} 
        onClose={() => {
          setShowResolveDispute(false)
          setResolutionText("")
          setResolutionType(null)
          setSelectedDispute(null)
        }}
        title={`${resolutionType === "approve" ? "Aprovar" : "Rejeitar"} Contestação`}
      >
        {selectedDispute && (
          <div className="space-y-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Detalhes da Contestação</h4>
              <p className="text-sm text-gray-600 mb-2">
                <span className="font-medium">Protocolo:</span> #{selectedDispute.id.slice(-8)}
              </p>
              <p className="text-sm text-gray-600 mb-2">
                <span className="font-medium">Motivo:</span> {selectedDispute.reason}
              </p>
              {selectedDispute.description && (
                <p className="text-sm text-gray-600">
                  <span className="font-medium">Descrição:</span> {selectedDispute.description}
                </p>
              )}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {resolutionType === "approve" ? "Motivo da Aprovação" : "Motivo da Rejeição"}
              </label>
              <textarea
                value={resolutionText}
                onChange={(e) => setResolutionText(e.target.value)}
                placeholder={`Digite aqui o motivo da ${resolutionType === "approve" ? "aprovação" : "rejeição"}...`}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                rows={4}
                required
              />
            </div>
            
            <div className="flex gap-3 pt-4 border-t border-gray-200">
              <Button 
                variant="ghost" 
                className="flex-1"
                onClick={() => {
                  setShowResolveDispute(false)
                  setResolutionText("")
                  setResolutionType(null)
                  setSelectedDispute(null)
                }}
              >
                Cancelar
              </Button>
              <Button 
                variant={resolutionType === "approve" ? "success" : "danger"}
                className="flex-1"
                onClick={() => {
                  if (resolutionText.trim()) {
                    resolveDisputeMutation.mutate({
                      disputeId: selectedDispute.id,
                      approved: resolutionType === "approve",
                      resolution: resolutionText
                    })
                  }
                }}
                isLoading={resolveDisputeMutation.isPending}
                disabled={!resolutionText.trim()}
              >
                {resolutionType === "approve" ? "Aprovar" : "Rejeitar"} Contestação
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Modal para Criar Nova Negociação */}
      <Modal 
        isOpen={showCreateNegotiation} 
        onClose={() => {
          setShowCreateNegotiation(false)
          setNewNegotiation({
            customerId: "",
            totalDebt: "",
            installments: "",
            discountPercentage: "",
            interestRate: "",
            description: ""
          })
        }}
        title="Nova Negociação de Débito"
      >
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                ID do Cliente
              </label>
              <Input
                value={newNegotiation.customerId}
                onChange={(e) => setNewNegotiation(prev => ({ ...prev, customerId: e.target.value }))}
                placeholder="Digite o ID do cliente"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Valor Total da Dívida (R$)
              </label>
              <Input
                type="number"
                step="0.01"
                value={newNegotiation.totalDebt}
                onChange={(e) => setNewNegotiation(prev => ({ ...prev, totalDebt: e.target.value }))}
                placeholder="0,00"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Número de Parcelas
              </label>
              <Input
                type="number"
                min="1"
                value={newNegotiation.installments}
                onChange={(e) => setNewNegotiation(prev => ({ ...prev, installments: e.target.value }))}
                placeholder="Ex: 12"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Desconto (%)
              </label>
              <Input
                type="number"
                step="0.01"
                min="0"
                max="100"
                value={newNegotiation.discountPercentage}
                onChange={(e) => setNewNegotiation(prev => ({ ...prev, discountPercentage: e.target.value }))}
                placeholder="0,00"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Taxa de Juros (% ao mês)
              </label>
              <Input
                type="number"
                step="0.01"
                min="0"
                value={newNegotiation.interestRate}
                onChange={(e) => setNewNegotiation(prev => ({ ...prev, interestRate: e.target.value }))}
                placeholder="0,00"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Observações (Opcional)
            </label>
            <textarea
              value={newNegotiation.description}
              onChange={(e) => setNewNegotiation(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Digite observações sobre a negociação..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              rows={3}
            />
          </div>
          
          <div className="bg-blue-50 p-4 rounded-lg">
            <h4 className="font-medium text-blue-900 mb-2">Resumo da Negociação</h4>
            <div className="text-sm text-blue-800 space-y-1">
              <p><span className="font-medium">Valor Original:</span> R$ {parseFloat(newNegotiation.totalDebt || "0").toFixed(2)}</p>
              <p><span className="font-medium">Desconto:</span> {parseFloat(newNegotiation.discountPercentage || "0").toFixed(2)}%</p>
              <p><span className="font-medium">Valor com Desconto:</span> R$ {(parseFloat(newNegotiation.totalDebt || "0") * (1 - parseFloat(newNegotiation.discountPercentage || "0") / 100)).toFixed(2)}</p>
              <p><span className="font-medium">Parcelas:</span> {newNegotiation.installments || "0"}x</p>
              <p><span className="font-medium">Valor por Parcela:</span> R$ {newNegotiation.installments ? ((parseFloat(newNegotiation.totalDebt || "0") * (1 - parseFloat(newNegotiation.discountPercentage || "0") / 100)) / parseInt(newNegotiation.installments)).toFixed(2) : "0,00"}</p>
            </div>
          </div>
          
          <div className="flex gap-3 pt-4 border-t border-gray-200">
            <Button 
              variant="ghost" 
              className="flex-1"
              onClick={() => {
                setShowCreateNegotiation(false)
                setNewNegotiation({
                  customerId: "",
                  totalDebt: "",
                  installments: "",
                  discountPercentage: "",
                  interestRate: "",
                  description: ""
                })
              }}
            >
              Cancelar
            </Button>
            <Button 
              className="flex-1 bg-blue-600 hover:bg-blue-700"
              onClick={() => {
                if (newNegotiation.customerId && newNegotiation.totalDebt && newNegotiation.installments) {
                  createNegotiationMutation.mutate({
                    customer_id: parseInt(newNegotiation.customerId),
                    total_debt: parseFloat(newNegotiation.totalDebt),
                    installments: parseInt(newNegotiation.installments),
                    discount_percentage: parseFloat(newNegotiation.discountPercentage || "0"),
                    interest_rate: parseFloat(newNegotiation.interestRate || "0"),
                    description: newNegotiation.description || undefined
                  })
                }
              }}
              isLoading={createNegotiationMutation.isPending}
              disabled={!newNegotiation.customerId || !newNegotiation.totalDebt || !newNegotiation.installments}
            >
              Criar Negociação
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
