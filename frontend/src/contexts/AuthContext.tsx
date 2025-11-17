"use client"

import type React from "react"
import { createContext, useContext, useState, useEffect, type ReactNode } from "react"
import { api } from "../services/api"

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
  login: (username: string, password: string) => Promise<void>
  register: (userData: RegisterData) => Promise<void>
  logout: () => void
  updateUser: (userData: Partial<User>) => void
  isLoading: boolean
}

interface RegisterData {
  username: string
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
      try {
        // Validar se storedUser não é "undefined" ou string vazia
        if (storedUser && storedUser !== "undefined" && storedUser.trim() !== "") {
          const parsedUser = JSON.parse(storedUser)
          setToken(storedToken)
          setUser(parsedUser)
          // Let the axios interceptor handle the Authorization header
        } else {
          // Limpar valores inválidos
          localStorage.removeItem("token")
          localStorage.removeItem("user")
        }
      } catch (error) {
        console.error("Erro ao parsear usuário do localStorage:", error)
        // Limpar valores corrompidos
        localStorage.removeItem("token")
        localStorage.removeItem("user")
      }
    }

    setIsLoading(false)
  }, [])

  const login = async (username: string, password: string) => {
    try {
      // Call the real auth service API
      const response = await api.post("/auth/login", {
        email: username, // LoginPage sends email as username
        password: password
      })

      const { access_token, user } = response.data
      
      // Update user structure to match frontend interface
      const frontendUser: User = {
        user_id: user.id,
        username: user.email,
        email: user.email,
        full_name: user.name,
        role: user.role,
        is_active: user.is_active,
        phone: undefined,
        address: undefined
      }

      setToken(access_token)
      setUser(frontendUser)

      localStorage.setItem("token", access_token)
      localStorage.setItem("user", JSON.stringify(frontendUser))
      
      // Let the axios interceptor handle the Authorization header automatically
    } catch (error: any) {
      console.error("Login error:", error)
      throw error
    }
  }

  const register = async (userData: RegisterData) => {
    try {
      // Call the real auth service API
      const response = await api.post("/auth/register", {
        email: userData.email,
        name: userData.full_name,
        password: userData.password,
        role: userData.role
      })

      const { access_token, user } = response.data
      
      // Update user structure to match frontend interface
      const frontendUser: User = {
        user_id: user.id,
        username: user.email,
        email: user.email,
        full_name: user.name,
        role: user.role,
        is_active: user.is_active,
        phone: undefined,
        address: undefined
      }

      setToken(access_token)
      setUser(frontendUser)

      localStorage.setItem("token", access_token)
      localStorage.setItem("user", JSON.stringify(frontendUser))
      
      // Let the axios interceptor handle the Authorization header automatically
      
      console.log("User registered successfully:", frontendUser)
    } catch (error: any) {
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
