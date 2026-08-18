import { stats } from "@/data/mockData";
import { AlertTriangle, IndianRupee, Target, TrendingUp } from "lucide-react";

const items = [
  {
    label: "Total Complaints",
    value: stats.totalComplaints.toString(),
    icon: AlertTriangle,
    color: "text-brand",
  },
  {
    label: "Amount Lost",
    value: `₹${(stats.totalAmountLost / 100000).toFixed(1)}L`,
    icon: IndianRupee,
    color: "text-critical",
  },
  {
    label: "Critical Hotspots",
    value: stats.activeHotspots.toString(),
    icon: Target,
    color: "text-high",
  },
  {
    label: "Avg Confidence",
    value: `${(stats.avgConfidence * 100).toFixed(0)}%`,
    icon: TrendingUp,
    color: "text-success",
  },
];

export function StatsBar() {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {items.map((item) => (
        <div
          key={item.label}
          className="flex items-center gap-3 rounded-lg border border-border bg-surface-raised px-4 py-3"
        >
          <item.icon className={`h-5 w-5 ${item.color} shrink-0`} />
          <div>
            <p className="text-lg font-bold text-gray-100 leading-none">{item.value}</p>
            <p className="text-[10px] text-muted mt-1">{item.label}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
