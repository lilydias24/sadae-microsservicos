import appConfig from "../config/app.config"

export interface CheckoutItem {
  name: string
  price: number // in cents, e.g., 1000 = R$10,00
  quantity: number
}

export interface CustomerInfo {
  customer_name?: string
  customer_email?: string
  customer_cellphone?: string
  address_cep?: string
  address_complement?: string
  address_number?: string
}

function encodeValue(value: string) {
  // encode component but keep spaces as + as InfinitePay examples show
  return encodeURIComponent(value).replace(/%20/g, "+")
}

export function buildInfinitePayCheckoutUrl(params: {
  handle: string
  items: CheckoutItem[]
  order_nsu: string
  redirect_url: string
  customer?: CustomerInfo
}): string {
  const { handle, items, order_nsu, redirect_url, customer } = params
  if (!handle) throw new Error("InfinitePay handle não configurado")

  const base = `${appConfig.payments.checkoutBaseUrl}/${encodeValue(handle)}`

  // Items JSON must use name, price (or amount per doc variant), quantity
  // We'll use price consistently per doc primary example
  const itemsJson = JSON.stringify(items)
  const itemsParam = encodeURIComponent(itemsJson)

  const qs: string[] = []
  qs.push(`items=${itemsParam}`)
  qs.push(`order_nsu=${encodeValue(order_nsu)}`)
  qs.push(`redirect_url=${encodeURIComponent(redirect_url)}`)

  if (customer) {
    const {
      customer_name,
      customer_email,
      customer_cellphone,
      address_cep,
      address_complement,
      address_number,
    } = customer
    if (customer_name) qs.push(`customer_name=${encodeValue(customer_name)}`)
    if (customer_email) qs.push(`customer_email=${encodeValue(customer_email)}`)
    if (customer_cellphone) qs.push(`customer_cellphone=${encodeValue(customer_cellphone)}`)
    if (address_cep) qs.push(`address_cep=${encodeValue(address_cep)}`)
    if (address_complement) qs.push(`address_complement=${encodeValue(address_complement)}`)
    if (address_number) qs.push(`address_number=${encodeValue(address_number)}`)
  }

  return `${base}?${qs.join("&")}`
}

export async function checkInfinitePayPayment(params: {
  handle: string
  transaction_nsu: string
  external_order_nsu: string
  slug: string
}): Promise<{ success: boolean; paid: boolean }> {
  const url = `${appConfig.payments.paymentCheckBaseUrl}/${encodeURIComponent(params.handle)}`

  // The docs state GET or POST accepted; we'll use GET with query params
  const search = new URLSearchParams({
    transaction_nsu: params.transaction_nsu,
    external_order_nsu: params.external_order_nsu,
    slug: params.slug,
  })

  const res = await fetch(`${url}?${search.toString()}`)
  if (!res.ok) {
    // Attempt to parse detail
    let detail = await res.text()
    try {
      const j = JSON.parse(detail)
      detail = j.detail || detail
    } catch {}
    throw new Error(`Falha ao verificar pagamento: ${detail}`)
  }
  return res.json()
}
