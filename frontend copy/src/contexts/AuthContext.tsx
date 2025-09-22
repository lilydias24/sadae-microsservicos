"use client"

import type React from "react"
import { createContext, useContext, useState, useEffect, type ReactNode } from "react"
import { api, authService } from "../services/api"

interface User {
  user_id: number
  username: string
  email: string
  full_name: string
  role: string
  is_active: boolean
  phone?: string
  address?: string
}

interface AuthContextType {
  user: User | null
  token: string | null
    login: (name: string, password: string) => Promise<void>
  register: (userData: RegisterData) => Promise<void>
  logout: () => void
  updateUser: (userData: Partial<User>) => void
  isLoading: boolean
}

interface RegisterData {
  name: string
  email: string
  password: string
  full_name: string
  role: string
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const storedToken = localStorage.getItem("token")
    const storedUser = localStorage.getItem("user")

    if (storedToken && storedUser) {
      setToken(storedToken)
      setUser(JSON.parse(storedUser))
      api.defaults.headers.common["Authorization"] = `Bearer ${storedToken}`
    }

    setIsLoading(false)
  }, [])

  const login = async (name: string, password: string) => {
    try {
      const response = await authService.login(name, password)
      const { access_token, user } = response.data
      setToken(access_token)
      setUser({
        user_id: user.id,
        username: user.name,
        email: user.email,
        full_name: user.name,
        role: user.role,
        is_active: user.is_active,
      })
      localStorage.setItem("token", access_token)
      localStorage.setItem("user", JSON.stringify({
        user_id: user.id,
        username: user.name,
        email: user.email,
        full_name: user.name,
        role: user.role,
        is_active: user.is_active,
      }))
      api.defaults.headers.common["Authorization"] = `Bearer ${access_token}`
    } catch (error) {
      throw error
    }
  }

  const register = async (userData: RegisterData) => {
    try {
      // Simulação de registro - na implementação real, faria chamada para API
      console.log("Registering user:", userData)
      
      // Criar usuário mockado baseado nos dados fornecidos
      const mockUser: User = {
        user_id: Math.floor(Math.random() * 1000),
        username: userData.name,
        email: userData.email,
        full_name: userData.full_name,
        role: userData.role,
        is_active: true
      }
      
      const mockToken = `mock-jwt-token-${Date.now()}`

      setToken(mockToken)
      setUser(mockUser)

      localStorage.setItem("token", mockToken)
      localStorage.setItem("user", JSON.stringify(mockUser))
      
      console.log("User registered successfully:", mockUser)
    } catch (error) {
      console.error("Registration error:", error)
      throw error
    }
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem("token")
    localStorage.removeItem("user")
  }

  const updateUser = (userData: Partial<User>) => {
    if (user) {
      const updatedUser = { ...user, ...userData }
      setUser(updatedUser)
      localStorage.setItem("user", JSON.stringify(updatedUser))
    }
  }

  const value = {
    user,
    token,
    login,
    register,
    logout,
    updateUser,
    isLoading,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
