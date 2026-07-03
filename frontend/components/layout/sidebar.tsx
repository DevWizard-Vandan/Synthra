"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  LayoutDashboard,
  Beaker,
  FlaskConical,
  Users2,
  Dna,
  BookOpen,
  Activity,
  Settings,
  ChevronRight,
  Layers,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/campaigns", label: "Campaigns", icon: Layers },
  { href: "/research", label: "Research", icon: Beaker },
  { href: "/simulations", label: "Simulation Queue", icon: FlaskConical },
  { href: "/candidates", label: "Candidates", icon: Zap },
  { href: "/evolution", label: "Evolution", icon: Dna },
  { href: "/knowledge", label: "Knowledge", icon: BookOpen },
  { href: "/telemetry", label: "Telemetry", icon: Activity },
  { href: "/workers", label: "Workers", icon: Users2 },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { data: status } = useQuery({
    queryKey: ["status"],
    queryFn: api.status,
    refetchInterval: 5000,
  });

  return (
    <aside className="fixed left-0 top-14 bottom-0 w-56 bg-surface border-r border-default z-30 flex flex-col">
      {/* System pulse */}
      <div className="px-3 pt-4 pb-2">
        <div className="rounded-lg bg-surface-2 border border-default p-3 flex items-center gap-3">
          <span
            className={cn(
              "status-dot",
              status?.governor_state === "running" ? "running" : "stopped"
            )}
          />
          <div className="min-w-0">
            <p className="text-xs font-semibold text-foreground truncate">
              Governor
            </p>
            <p className="text-xs text-muted capitalize">
              {status?.governor_state ?? "—"}
            </p>
          </div>
          <div className="ml-auto text-right">
            <p className="text-xs font-semibold text-foreground">
              {status?.active_workers ?? 0}
            </p>
            <p className="text-xs text-muted">workers</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-2 py-2 space-y-0.5" aria-label="Main navigation">
        {navItems.map(({ href, label, icon: Icon }) => {
          const active =
            href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150 group relative",
                active
                  ? "bg-[hsl(245_80%_65%/0.15)] text-[hsl(245,80%,75%)]"
                  : "text-muted hover:text-foreground hover:bg-surface-2"
              )}
              aria-current={active ? "page" : undefined}
            >
              {active && (
                <motion.div
                  layoutId="sidebar-active"
                  className="absolute inset-0 rounded-lg bg-[hsl(245_80%_65%/0.12)] border border-[hsl(245_80%_65%/0.25)]"
                  transition={{ type: "spring", bounce: 0.15, duration: 0.4 }}
                />
              )}
              <Icon
                className={cn(
                  "w-4 h-4 shrink-0 relative z-10",
                  active ? "text-[hsl(245,80%,72%)]" : "text-muted group-hover:text-foreground"
                )}
                aria-hidden="true"
              />
              <span className="relative z-10">{label}</span>
              {active && (
                <ChevronRight
                  className="w-3 h-3 ml-auto relative z-10 text-[hsl(245,80%,72%)]"
                  aria-hidden="true"
                />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-3 py-3 border-t border-default">
        <p className="text-xs text-subtle text-center">
          SYNTHRA v{status?.version ?? "0.1.0"}
        </p>
      </div>
    </aside>
  );
}
