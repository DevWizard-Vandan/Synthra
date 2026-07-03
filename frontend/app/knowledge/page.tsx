"use client";

import { SectionHeader } from "@/components/ui/headers";
import { BookOpen } from "lucide-react";

// AWAITING_BACKEND: GET /knowledge not yet implemented

export default function KnowledgePage() {
  return (
    <div className="max-w-screen-2xl mx-auto">
      <SectionHeader
        title="Knowledge"
        description="Datasets, operators, learned rules, failures, and successful mutations"
      />

      <div className="card p-5 border-amber-500/30 bg-amber-500/5 mb-6">
        <div className="flex items-start gap-3">
          <BookOpen className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <p className="text-sm font-semibold text-amber-400">
              Awaiting Backend Implementation
            </p>
            <p className="text-xs text-muted mt-1">
              The knowledge base REST API endpoint has not yet been implemented.
              This view will display dataset catalog contents, operator catalog,
              learned rules from the LearningRepository, known failures, and
              successful mutation patterns.
            </p>
            <div className="mt-3 space-y-1.5 text-xs font-mono text-muted">
              <p>• <code>GET /knowledge</code> — full knowledge base snapshot</p>
              <p>• <code>GET /knowledge/datasets</code> — dataset catalog</p>
              <p>• <code>GET /knowledge/operators</code> — operator catalog</p>
              <p>• <code>GET /knowledge/rules</code> — learned rules</p>
              <p>• <code>GET /knowledge/failures</code> — failure patterns</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {["Datasets", "Operators", "Learned Rules", "Failures", "Successful Mutations", "Knowledge Confidence"].map(
          (section) => (
            <div key={section} className="card p-5">
              <h2 className="text-sm font-semibold text-foreground mb-3">{section}</h2>
              <div className="h-24 flex items-center justify-center border border-dashed border-default rounded-lg">
                <p className="text-xs text-muted">
                  Awaiting backend endpoint
                </p>
              </div>
            </div>
          )
        )}
      </div>
    </div>
  );
}
