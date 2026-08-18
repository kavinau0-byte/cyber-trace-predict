import { Badge } from "@/components/ui/badge";
import type { Prediction } from "@/data/mockData";
import { TrendingUp, TrendingDown, Minus, MapPin } from "lucide-react";

interface PredictionCardsProps {
  predictions: Prediction[];
  selectedPrediction: string | null;
  onSelectPrediction: (id: string | null) => void;
}

function TrendIcon({ trend }: { trend: Prediction["trend"] }) {
  switch (trend) {
    case "rising":
      return <TrendingUp className="h-3.5 w-3.5 text-critical" />;
    case "declining":
      return <TrendingDown className="h-3.5 w-3.5 text-success" />;
    default:
      return <Minus className="h-3.5 w-3.5 text-muted" />;
  }
}

export function PredictionCards({
  predictions,
  selectedPrediction,
  onSelectPrediction,
}: PredictionCardsProps) {
  return (
    <div className="flex flex-col gap-2">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-muted px-1">
        AI Hotspot Predictions
      </h3>
      {predictions.map((pred) => {
        const isSelected = pred.id === selectedPrediction;
        const confPct = (pred.confidence * 100).toFixed(0);

        return (
          <button
            key={pred.id}
            onClick={() => onSelectPrediction(isSelected ? null : pred.id)}
            className={`w-full text-left rounded-lg border p-3 transition-all cursor-pointer ${
              isSelected
                ? "border-brand bg-brand/5 ring-1 ring-brand/30"
                : "border-border bg-surface-raised hover:border-border hover:bg-surface-overlay/50"
            }`}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <MapPin className="h-3 w-3 text-muted shrink-0" />
                  <span className="text-xs font-semibold text-gray-200 truncate">
                    {pred.zone_name}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-[10px] text-muted">
                  <span>{pred.complaint_count} complaints</span>
                  <span>·</span>
                  <span>{pred.radius_km} km radius</span>
                </div>
              </div>
              <div className="flex flex-col items-end gap-1 shrink-0">
                <div className="flex items-center gap-1.5">
                  <TrendIcon trend={pred.trend} />
                  <span
                    className={`text-lg font-bold ${
                      pred.risk_level === "critical"
                        ? "text-critical"
                        : pred.risk_level === "high"
                          ? "text-high"
                          : "text-brand"
                    }`}
                  >
                    {confPct}%
                  </span>
                </div>
                <Badge variant={pred.risk_level}>{pred.risk_level}</Badge>
              </div>
            </div>
            {isSelected && (
              <div className="mt-2 pt-2 border-t border-border/50">
                <div className="flex flex-wrap gap-1">
                  {pred.fraud_types.map((ft) => (
                    <Badge key={ft} variant="outline" className="text-[10px]">
                      {ft}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </button>
        );
      })}
    </div>
  );
}
