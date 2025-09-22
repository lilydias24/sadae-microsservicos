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
      setToken(storedToken)
      setUser(JSON.parse(storedUser))
      api.defaults.headers.common["Authorization"] = `Bearer ${storedToken}`
    }

    setIsLoading(false)
  }, [])

  const login = async (username: string, password: string) => {
    try {
      const response = await api.post('/login', {
        username,
        password
      })
      
      const { access_token, user: userData } = response.data

      setToken(access_token)
      setUser(userData)

      localStorage.setItem("token", access_token)
      localStorage.setItem("user", JSON.stringify(userData))

      api.defaults.headers.common["Authorization"] = `Bearer ${access_token}`
    } catch (error: any) {
      console.error("Login error:", error.response?.data || error.message)
      throw error
    }
  }

  const register = async (userData: RegisterData) => {
    try {
      const response = await api.post('/auth/register', userData)
      const { access_token, user: registeredUser } = response.data
      
      setToken(access_token)
      setUser(registeredUser)

      localStorage.setItem("token", access_token)
      localStorage.setItem("user", JSON.stringify(registeredUser))

      api.defaults.headers.common["Authorization"] = `Bearer ${access_token}`
    } catch (error: any) {
      console.error("Register error:", error.response?.data || error.message)
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
