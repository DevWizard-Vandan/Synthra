"use client";

import { SectionHeader } from "@/components/ui/headers";
import { Beaker } from "lucide-react";

// AWAITING_BACKEND: GET /research/history, GET /research/hypotheses not yet implemented

export default function ResearchPage() {
  return (
    <div className="max-w-screen-2xl mx-auto">
      <SectionHeader
        title="Research"
        description="Prompt history, reasoning, hypotheses, and mutation lineage"
      />

      <div className="card p-5 border-amber-500/30 bg-amber-500/5 mb-6">
        <div className="flex items-start gap-3">
          <Beaker className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <p className="text-sm font-semibold text-amber-400">
              Awaiting Backend Implementation
            </p>
            <p className="text-xs text-muted mt-1">
              The research history endpoints have not yet been exposed via the REST API.
              This view will display prompt history, LLM reasoning, generated hypotheses,
              mutation lineage, novelty scores, and selection scores once available.
            </p>
            <div className="mt-3 space-y-1.5 text-xs font-mono text-muted">
              <p>• <code>GET /research/history</code> — prompt history with reasoning</p>
              <p>• <code>GET /research/hypotheses</code> — generated hypotheses per campaign</p>
              <p>• <code>GET /research/mutations</code> — mutation history and novelty scores</p>
              <p>• <code>GET /research/lineage</code> — expression lineage tree</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {["Prompt History", "Generated Hypotheses", "Mutation Lineage"].map((section) => (
          <div key={section} className="card p-5 h-64 flex flex-col">
            <h2 className="text-sm font-semibold text-foreground mb-3">{section}</h2>
            <div className="flex-1 flex items-center justify-center">
              <p className="text-xs text-muted text-center">
                Data available after backend endpoint implementation
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
