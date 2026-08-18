import { useState } from "react";
import { MapView } from "./MapView";
import { ComplaintTable } from "./ComplaintTable";
import { PredictionCards } from "./PredictionCards";
import { AuditLog } from "./AuditLog";
import { StatsBar } from "./StatsBar";
import { complaints, predictions, auditLog } from "@/data/mockData";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Radio } from "lucide-react";

export function DashboardLayout() {
  const [selectedPrediction, setSelectedPrediction] = useState<string | null>(null);
  const [rightPanel, setRightPanel] = useState<"predictions" | "audit">("predictions");
  const navigate = useNavigate();

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-[#06080f]">
      {/* Top Bar */}
      <header className="flex items-center justify-between border-b border-border bg-surface/80 backdrop-blur-sm px-4 py-2.5 shrink-0">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate("/")}
            className="h-8 w-8"
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div className="flex items-center gap-2">
            <Radio className="h-4 w-4 text-critical animate-pulse" />
            <h1 className="text-sm font-bold tracking-tight text-gray-100">
              CYBERTRACE
            </h1>
          </div>
          <span className="text-[10px] text-muted hidden sm:inline">
            Fraud Intelligence Dashboard
          </span>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-success animate-pulse" />
            <span className="text-[10px] text-muted">LIVE</span>
          </div>
          <div className="text-[10px] text-muted font-mono">
            Bengaluru · {new Date().toLocaleString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: false })}
          </div>
        </div>
      </header>

      {/* Stats */}
      <div className="px-4 py-3 shrink-0">
        <StatsBar />
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden gap-0">
        {/* Left: Complaint Table */}
        <div className="w-[420px] shrink-0 border-r border-border overflow-hidden flex flex-col p-2 pl-4 pb-3">
          <ComplaintTable
            complaints={complaints}
          />
        </div>

        {/* Center: Map */}
        <div className="flex-1 relative p-2">
          <MapView
            complaints={complaints}
            predictions={predictions}
            selectedPrediction={selectedPrediction}
            onSelectPrediction={setSelectedPrediction}
          />
          {/* Map overlay gradient */}
          <div className="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-[#06080f] to-transparent pointer-events-none" />
        </div>

        {/* Right: Predictions / Audit */}
        <div className="w-[280px] shrink-0 border-l border-border overflow-hidden flex flex-col">
          {/* Panel Toggle */}
          <div className="flex border-b border-border shrink-0">
            <button
              onClick={() => setRightPanel("predictions")}
              className={`flex-1 py-2 text-[11px] font-medium transition-colors cursor-pointer ${
                rightPanel === "predictions"
                  ? "text-brand border-b-2 border-brand"
                  : "text-muted hover:text-gray-300"
              }`}
            >
              Predictions
            </button>
            <button
              onClick={() => setRightPanel("audit")}
              className={`flex-1 py-2 text-[11px] font-medium transition-colors cursor-pointer ${
                rightPanel === "audit"
                  ? "text-brand border-b-2 border-brand"
                  : "text-muted hover:text-gray-300"
              }`}
            >
              Audit Trail
            </button>
          </div>
          <div className="flex-1 overflow-auto p-3">
            {rightPanel === "predictions" ? (
              <PredictionCards
                predictions={predictions}
                selectedPrediction={selectedPrediction}
                onSelectPrediction={setSelectedPrediction}
              />
            ) : (
              <AuditLog entries={auditLog} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
