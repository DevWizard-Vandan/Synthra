"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { motion } from "framer-motion";
import { Lock, User, Check, ExternalLink } from "lucide-react";

export function LoginForm() {
  const { login, state, verificationUrl } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) return;

    setIsSubmitting(true);
    try {
      await login(username, password, remember);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-[#05070f] p-4 text-slate-100">
      {/* Background ambient glow */}
      <div className="absolute top-1/4 left-1/4 h-96 w-96 rounded-full bg-indigo-600/10 blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 h-96 w-96 rounded-full bg-purple-600/10 blur-3xl" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 w-full max-w-md overflow-hidden rounded-2xl border border-slate-800 bg-[#0a0e1a]/80 p-8 backdrop-blur-xl shadow-2xl"
      >
        <div className="mb-8 text-center">
          <motion.div
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-400 mb-4"
          >
            <Lock className="h-6 w-6" />
          </motion.div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Welcome to SYNTHRA
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Sign in to access the Operations Center
          </p>
        </div>

        {state === "Waiting for Biometric Verification" && verificationUrl ? (
          <div className="flex flex-col items-center justify-center gap-4 text-center py-6">
            <div className="relative flex h-12 w-12 items-center justify-center rounded-full bg-indigo-500/10 text-indigo-400">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-indigo-500/10 opacity-75" />
              <ExternalLink className="h-6 w-6" />
            </div>
            <h2 className="text-lg font-semibold text-white">
              Biometric/MFA Verification Required
            </h2>
            <p className="text-sm text-slate-400">
              Please complete verification in the opened browser tab to continue.
            </p>
            <a
              href={verificationUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-all"
            >
              Open Verification Page <ExternalLink className="h-4 w-4" />
            </a>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label
                htmlFor="username"
                className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2"
              >
                Username
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
                  <User className="h-4 w-4" />
                </span>
                <input
                  id="username"
                  type="text"
                  required
                  disabled={isSubmitting}
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="name@worldquant.com"
                  className="block w-full rounded-lg border border-slate-800 bg-[#0d1224] py-2.5 pl-10 pr-4 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50 transition-colors"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2"
              >
                Password
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
                  <Lock className="h-4 w-4" />
                </span>
                <input
                  id="password"
                  type="password"
                  required
                  disabled={isSubmitting}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="block w-full rounded-lg border border-slate-800 bg-[#0d1224] py-2.5 pl-10 pr-4 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50 transition-colors"
                />
              </div>
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={remember}
                  disabled={isSubmitting}
                  onChange={() => setRemember(!remember)}
                  className="sr-only"
                />
                <div
                  className={`flex h-4 w-4 items-center justify-center rounded border transition-colors ${
                    remember
                      ? "border-indigo-500 bg-indigo-500"
                      : "border-slate-800 bg-[#0d1224]"
                  }`}
                >
                  {remember && <Check className="h-3 w-3 text-white" />}
                </div>
                <span className="ml-2 text-xs text-slate-400">Remember Me</span>
              </label>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="flex w-full items-center justify-center rounded-lg bg-indigo-600 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 transition-all cursor-pointer"
            >
              {isSubmitting
                ? "Connecting to WorldQuant..."
                : state === "Authenticating"
                ? "Authenticating..."
                : "Sign In"}
            </button>
          </form>
        )}
      </motion.div>
    </div>
  );
}
