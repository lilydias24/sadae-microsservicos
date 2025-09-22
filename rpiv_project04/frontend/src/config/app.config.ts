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
    crisis: "/crisis"
  },
  
  // Mock data fallback
  useMockFallback: true, // If real API fails, fallback to mock data
}

// Helper function to determine data source
export const shouldUseRealData = () => {
  return appConfig.useRealData && process.env.NODE_ENV !== 'development'
}

export default appConfig