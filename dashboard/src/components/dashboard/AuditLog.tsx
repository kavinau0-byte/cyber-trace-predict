import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { AuditEntry } from "@/data/mockData";
import { formatTime } from "@/lib/utils";
import { Shield, Link2 } from "lucide-react";

interface AuditLogProps {
  entries: AuditEntry[];
}

function actionColor(action: string): "critical" | "high" | "medium" | "success" | "default" {
  if (action.includes("flagged") || action.includes("escalated")) return "critical";
  if (action.includes("dispatched")) return "high";
  if (action.includes("generated") || action.includes("linked")) return "medium";
  if (action.includes("ingested") || action.includes("marked")) return "success";
  return "default";
}

export function AuditLog({ entries }: AuditLogProps) {
  return (
    <Card className="flex flex-col h-full">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-xs">
          <Shield className="h-3.5 w-3.5 text-brand" />
          Blockchain Audit Trail
          <Badge variant="outline" className="ml-auto text-[10px]">
            {entries.length} entries
          </Badge>
        </CardTitle>
      </CardHeader>
      <div className="flex-1 overflow-auto px-4 pb-4">
        <div className="relative">
          {/* Vertical timeline line */}
          <div className="absolute left-[7px] top-2 bottom-2 w-px bg-border" />

          <div className="space-y-3">
            {entries.map((entry) => (
              <div key={entry.id} className="relative flex gap-3 group">
                {/* Timeline dot */}
                <div className="relative z-10 mt-1.5 flex h-[15px] w-[15px] shrink-0 items-center justify-center">
                  <div
                    className={`h-2 w-2 rounded-full ${
                      actionColor(entry.action) === "critical"
                        ? "bg-critical animate-pulse-glow"
                        : actionColor(entry.action) === "high"
                          ? "bg-high"
                          : actionColor(entry.action) === "medium"
                            ? "bg-brand"
                            : "bg-success"
                    }`}
                  />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[11px] font-medium text-gray-200 truncate">
                      {entry.action.replace(".", " → ")}
                    </span>
                    <span className="text-[10px] text-muted shrink-0">
                      {formatTime(entry.timestamp)}
                    </span>
                  </div>
                  <p className="text-[10px] text-muted mt-0.5 truncate">
                    {entry.entity_id} · {entry.actor}
                  </p>
                  <div className="flex items-center gap-1 mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <Link2 className="h-2.5 w-2.5 text-muted" />
                    <span className="font-mono text-[9px] text-muted/70 truncate">
                      {entry.block_hash}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Card>
  );
}
