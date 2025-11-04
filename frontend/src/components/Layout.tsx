import type React from "react"
import type { ReactNode } from "react"
import { Sidebar } from "./Sidebar"
import { Header } from "./Header"
import { ChatWidget } from "./ChatWidget"

interface LayoutProps {
  children: ReactNode
  showChatWidget?: boolean
}

export const Layout: React.FC<LayoutProps> = ({ children, showChatWidget = true }) => {
  return (
    <div className="flex h-screen bg-slate-50">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>
      {showChatWidget && <ChatWidget />}
    </div>
  )
}
