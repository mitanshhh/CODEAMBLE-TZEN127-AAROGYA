"use client";

import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { RouteGuard } from "@/components/layout/RouteGuard";
import { FloatingChatbot } from "@/components/chat/FloatingChatbot";
import { usePathname } from 'next/navigation';
import { useState } from 'react';

export function ClientLayout({ children }: { children: React.ReactNode }) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const pathname = usePathname();

  if (pathname === '/login') {
    return <>{children}</>;
  }

  return (
    <>
      <Sidebar 
        isCollapsed={isCollapsed} 
        setIsCollapsed={setIsCollapsed} 
        isMobileOpen={isMobileOpen} 
        setIsMobileOpen={setIsMobileOpen} 
      />
      
      {/* Mobile overlay */}
      {isMobileOpen && (
        <div 
          className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40 md:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      <div className={`flex-1 flex flex-col h-screen overflow-hidden transition-all duration-300 ${isCollapsed ? 'md:ml-20' : 'md:ml-64'}`}>
        <Header setIsMobileOpen={setIsMobileOpen} />
        <main className="flex-1 overflow-y-auto p-4 md:p-6 relative">
          <RouteGuard>
            {children}
          </RouteGuard>
        </main>
        <FloatingChatbot />
      </div>
    </>
  );
}
