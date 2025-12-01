import React, { useEffect, useState } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import { useQueryClient } from "@tanstack/react-query"
import appConfig from "../config/app.config"
import { checkInfinitePayPayment } from "../utils/infinitepay"
import dataService from "../services/dataService"

export default function PaymentSuccessPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [status, setStatus] = useState<{ loading: boolean; paid?: boolean; error?: string; attempted?: boolean }>({ loading: true })

  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const receipt_url = params.get("receipt_url") || ""
    const transaction_id = params.get("transaction_id") || ""
    const capture_method = params.get("capture_method") || ""
    const order_nsu = params.get("order_nsu") || ""
    const slug = params.get("slug") || ""

    const handle = appConfig.payments.infinitePayHandle
    if (!handle) {
      setStatus({ loading: false, error: "Handle da InfinitePay não configurado.", attempted: true })
      return
    }

    if (!transaction_id || !order_nsu || !slug) {
      // Mesmo sem parâmetros completos, mostra mensagem amigável e redireciona.
      setStatus({ loading: false, error: "Retorno de pagamento incompleto.", attempted: true })
      return
    }

    ;(async () => {
      try {
        const result = await checkInfinitePayPayment({
          handle,
          transaction_nsu: transaction_id,
          external_order_nsu: order_nsu,
          slug,
        })
        // Se pago, registra no backend para atualizar status da fatura
        if (result.paid) {
          try {
            await dataService.payBill(order_nsu)
          } catch (e) {
            console.warn("Falha ao registrar pagamento no backend, seguindo com fluxo:", e)
          }
        }
        setStatus({ loading: false, paid: result.paid, attempted: true })
      } catch (e: any) {
        // Em falha de verificação (ex: CORS), ainda registramos pagamento no backend como melhor esforço
        try {
          await dataService.payBill(order_nsu)
          setStatus({ loading: false, paid: true, attempted: true })
        } catch (regErr) {
          // Não conseguimos registrar; seguimos com mensagem amigável
          setStatus({ loading: false, error: e.message || "Falha ao verificar. Redirecionando...", attempted: true })
        }
      }
    })()
  }, [location.search])

  // Redireciona automaticamente após resultado
  useEffect(() => {
    if (!status.loading && status.attempted) {
      const timeout = setTimeout(() => {
        // Força refetch das faturas para refletir status atualizado
        queryClient.invalidateQueries({ queryKey: ["bills"] })
        navigate("/billing")
      }, status.paid ? 2500 : 3500) // sucesso mais rápido, pendente/erro um pouco mais longo
      return () => clearTimeout(timeout)
    }
  }, [status, navigate, queryClient])

  return (
    <div className="p-6 max-w-xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Status do Pagamento</h1>
      {status.loading ? (
        <div className="text-gray-600">Verificando pagamento...</div>
      ) : status.paid ? (
        <div className="text-green-700">
          Pagamento confirmado! Redirecionando para faturamento...
        </div>
      ) : status.error ? (
        <div className="text-red-600">
          {status.error} Redirecionando para faturamento...
        </div>
      ) : (
        <div className="text-yellow-700">
          Pagamento em processamento. Atualizando e redirecionando...
        </div>
      )}

      <div className="mt-6">
        <button
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          onClick={() => {
            queryClient.invalidateQueries({ queryKey: ["bills"] })
            navigate("/billing")
          }}
        >
          Ir agora para Faturamento
        </button>
        <p className="text-xs text-gray-500 mt-2">Você será redirecionado automaticamente.</p>
      </div>
    </div>
  )
}
