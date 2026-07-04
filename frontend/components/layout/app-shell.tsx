"use client";

import { TopNav } from "./top-nav";
import { Sidebar } from "./sidebar";
import { motion } from "framer-motion";

import { usePathname } from "next/navigation";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  if (pathname === "/login") {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-background">
      <TopNav />
      <Sidebar />
      <motion.main
        className="ml-56 pt-14 min-h-screen"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        <div className="p-6">{children}</div>
      </motion.main>
    </div>
  );
}
