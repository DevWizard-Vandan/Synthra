import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function formatNumber(n: number): string {
  return new Intl.NumberFormat().format(n);
}

export function getStateColor(state: string): string {
  const s = state.toLowerCase();
  if (s === "running") return "text-emerald-400";
  if (s === "completed") return "text-sky-400";
  if (s === "failed") return "text-rose-400";
  if (s === "queued") return "text-amber-400";
  if (s === "paused") return "text-slate-400";
  if (s === "draft") return "text-purple-400";
  return "text-slate-400";
}

export function getStateBg(state: string): string {
  const s = state.toLowerCase();
  if (s === "running") return "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
  if (s === "completed") return "bg-sky-500/15 text-sky-400 border-sky-500/30";
  if (s === "failed") return "bg-rose-500/15 text-rose-400 border-rose-500/30";
  if (s === "queued") return "bg-amber-500/15 text-amber-400 border-amber-500/30";
  if (s === "paused") return "bg-slate-500/15 text-slate-400 border-slate-500/30";
  if (s === "stopped") return "bg-rose-500/15 text-rose-400 border-rose-500/30";
  return "bg-slate-500/15 text-slate-400 border-slate-500/30";
}
