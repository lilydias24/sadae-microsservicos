import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { AuthProvider } from "./contexts/AuthContext"
import { WebSocketProvider } from "./contexts/WebSocketContext"
import { ProtectedRoute } from "./components/ProtectedRoute"
import { Layout } from "./components/Layout"

// Pages
import { LoginPage } from "./pages/LoginPage"

import { DashboardPage } from "./pages/DashboardPage"

import { MaintenancePage } from "./pages/MaintenancePage"



import "./index.css"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <WebSocketProvider>
          <Router>
            <div className="min-h-screen bg-slate-50">
              <Routes>
                {/* Public routes */}
                <Route path="/login" element={<LoginPage />} />
                
                {/* Protected routes */}
                <Route
                  path="/"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <Navigate to="/dashboard" replace />
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/dashboard"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <DashboardPage />
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                
                <Route
                  path="/maintenance/*"
                  element={
                    <ProtectedRoute allowedRoles={["maintenance_manager", "operator"]}>
                      <Layout>
                        <MaintenancePage />
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                
                
                
                
                
              </Routes>
            </div>
          </Router>
        </WebSocketProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App
