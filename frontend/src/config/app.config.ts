// Configuration for data source
export const appConfig = {
  // Set to true to use real API data, false to use mock data
  useRealData: true, // Change to true when ready to use real backend data

  // API endpoints
  apiEndpoints: {
    auth: "/auth",
    billing: "/billing",
    monitoring: "/monitoring",
    maintenance: "/maintenance",
    support: "/support"
  },

  // InfinitePay integration
  payments: {
    infinitePayHandle: "eriicmoraes", // TODO: set your InfinitePay handle (e.g., "cloudwalker")
    checkoutBaseUrl: "https://checkout.infinitepay.io",
    paymentCheckBaseUrl: "https://api.infinitepay.io/invoices/public/checkout/payment_check",
    successRedirectPath: "/payment/success",
  },

  // Mock data fallback
  useMockFallback: true, // If real API fails, fallback to mock data
}

// Helper function to determine data source
export const shouldUseRealData = () => {
  return appConfig.useRealData
}

export default appConfig