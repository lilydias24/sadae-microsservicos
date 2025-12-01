import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { AuthProvider } from "./contexts/AuthContext"
import { WebSocketProvider } from "./contexts/WebSocketContext"
import { ProtectedRoute } from "./components/ProtectedRoute"
import { Layout } from "./components/Layout"

// Pages
import { LoginPage } from "./pages/LoginPage"
import { ResetPasswordPage } from "./pages/ResetPasswordPage"
import { DashboardPage } from "./pages/DashboardPage"
import { BillingPage } from "./pages/BillingPage"
import { BillingChatPage } from "./pages/BillingChatPage"
import { MaintenancePage } from "./pages/MaintenancePage"
import { MaintenanceChatPage } from "./pages/MaintenanceChatPage"
import { MonitoringPage } from "./pages/MonitoringPage"
import { SupportPage } from "./pages/SupportPage"
import { ChatPage } from "./pages/ChatPage"
import { ProfilePage } from "./pages/ProfilePage"
import { ReportsPage } from "./pages/ReportsPage"
import PaymentSuccessPage from "./pages/PaymentSuccess"

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
                <Route path="/forgot-password" element={<ResetPasswordPage />} />
                <Route path="/reset-password/:token" element={<ResetPasswordPage />} />
                <Route path="/payment/success" element={<PaymentSuccessPage />} />

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
                  path="/billing/*"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <BillingPage />
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/maintenance"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <MaintenancePage />
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/monitoring"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <MonitoringPage />
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/support"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <SupportPage />
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/chat"
                  element={
                    <ProtectedRoute>
                      <Layout showChatWidget={false}>
                        <ChatPage />
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/billing-chat"
                  element={
                    <ProtectedRoute>
                      <Layout showChatWidget={false}>
                        <BillingChatPage />
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/maintenance-chat"
                  element={
                    <ProtectedRoute>
                      <Layout showChatWidget={false}>
                        <MaintenanceChatPage />
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/profile"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <ProfilePage />
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/reports"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <ReportsPage />
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
