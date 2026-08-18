import { useState } from "react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Complaint } from "@/data/mockData";
import { formatCurrency, relativeTime } from "@/lib/utils";
import { ChevronDown, ChevronUp, Search } from "lucide-react";

interface ComplaintTableProps {
  complaints: Complaint[];
}

function riskLevel(amount: number): "critical" | "high" | "medium" {
  if (amount > 100000) return "critical";
  if (amount > 50000) return "high";
  return "medium";
}

export function ComplaintTable({ complaints }: ComplaintTableProps) {
  const [sortKey, setSortKey] = useState<"amount_inr" | "incident_time" | "complaint_id">("incident_time");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [search, setSearch] = useState("");

  const toggleSort = (key: typeof sortKey) => {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  const filtered = complaints
    .filter((c) => {
      if (!search) return true;
      const q = search.toLowerCase();
      return (
        c.complaint_id.toLowerCase().includes(q) ||
        c.fraud_type.toLowerCase().includes(q) ||
        c.bank.toLowerCase().includes(q)
      );
    })
    .sort((a, b) => {
      const mult = sortDir === "asc" ? 1 : -1;
      if (sortKey === "incident_time")
        return mult * (new Date(a.incident_time).getTime() - new Date(b.incident_time).getTime());
      return mult * ((a[sortKey] as number) - (b[sortKey] as number));
    });

  const SortIcon = ({ field }: { field: typeof sortKey }) => {
    if (sortKey !== field) return null;
    return sortDir === "asc" ? (
      <ChevronUp className="inline h-3 w-3" />
    ) : (
      <ChevronDown className="inline h-3 w-3" />
    );
  };

  return (
    <Card className="flex flex-col h-full">
      <CardHeader className="flex flex-row items-center justify-between gap-2 pb-2">
        <CardTitle className="flex items-center gap-2">
          <span className="inline-block h-2 w-2 rounded-full bg-brand animate-pulse" />
          Live Complaints ({filtered.length})
        </CardTitle>
        <div className="relative">
          <Search className="absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted" />
          <input
            type="text"
            placeholder="Filter..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-8 w-36 rounded-md border border-border bg-surface pl-7 pr-2 text-xs text-gray-200 placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-brand"
          />
        </div>
      </CardHeader>
      <div className="flex-1 overflow-auto">
        <table className="w-full text-xs">
          <thead className="sticky top-0 bg-surface-raised">
            <tr className="border-b border-border text-left text-muted">
              <th className="px-4 py-2 font-medium">
                <button onClick={() => toggleSort("complaint_id")} className="cursor-pointer">
                  ID <SortIcon field="complaint_id" />
                </button>
              </th>
              <th className="px-4 py-2 font-medium">Type</th>
              <th className="px-4 py-2 font-medium">Bank</th>
              <th className="px-4 py-2 font-medium">
                <button onClick={() => toggleSort("amount_inr")} className="cursor-pointer">
                  Amount <SortIcon field="amount_inr" />
                </button>
              </th>
              <th className="px-4 py-2 font-medium">ATM</th>
              <th className="px-4 py-2 font-medium">
                <button onClick={() => toggleSort("incident_time")} className="cursor-pointer">
                  Time <SortIcon field="incident_time" />
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((c) => (
              <tr
                key={c.complaint_id}
                className="border-b border-border/50 transition-colors hover:bg-surface-overlay/50"
              >
                <td className="px-4 py-2.5 font-mono text-gray-300">{c.complaint_id}</td>
                <td className="px-4 py-2.5">
                  <Badge variant={riskLevel(c.amount_inr)}>{c.fraud_type}</Badge>
                </td>
                <td className="px-4 py-2.5 text-gray-300">{c.bank}</td>
                <td className="px-4 py-2.5 font-mono text-gray-200">
                  {formatCurrency(c.amount_inr)}
                </td>
                <td className="px-4 py-2.5 text-gray-400 truncate max-w-[140px]">
                  {c.withdrawal_atm_name}
                </td>
                <td className="px-4 py-2.5 text-muted">{relativeTime(c.incident_time)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
