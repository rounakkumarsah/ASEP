"use client"

import * as React from "react"
import { useRouter, usePathname } from "next/navigation"

type User = {
  id: string
  username: string
  role: string
}

type AuthContextType = {
  user: User | null
  isLoading: boolean
  login: (token: string, user: User) => void
  logout: () => void
}

const AuthContext = React.createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<User | null>(null)
  const [isLoading, setIsLoading] = React.useState(true)
  const router = useRouter()
  const pathname = usePathname()

  React.useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem("asep_access_token")
      if (token) {
        try {
          // For now, we mock the /me endpoint if the backend is not fully integrated yet.
          // In the future:
          // const response = await apiClient.get("/me")
          // setUser(response.data)
          
          // MOCK:
          setUser({ id: "1", username: "admin", role: "supervisor" })
        } catch {
          localStorage.removeItem("asep_access_token")
          setUser(null)
        }
      }
      setIsLoading(false)
    }
    initAuth()
  }, [])

  React.useEffect(() => {
    if (!isLoading) {
      const isAuthRoute = pathname?.startsWith("/login")
      if (!user && !isAuthRoute) {
        router.push("/login")
      } else if (user && isAuthRoute) {
        router.push("/")
      }
    }
  }, [user, isLoading, pathname, router])

  const login = (token: string, user: User) => {
    localStorage.setItem("asep_access_token", token)
    setUser(user)
    router.push("/")
  }

  const logout = () => {
    localStorage.removeItem("asep_access_token")
    setUser(null)
    router.push("/login")
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = React.useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
