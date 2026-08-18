import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ArrowRight, Shield, MapPin, Brain } from "lucide-react";
import { Globe } from "@/components/landing/Globe";

export function Landing() {
  const navigate = useNavigate();

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#06080f]">
      {/* Globe background */}
      <div className="absolute inset-0 flex items-center justify-center opacity-60">
        <Globe />
      </div>

      {/* Top gradient fade */}
      <div className="absolute inset-x-0 top-0 h-32 bg-gradient-to-b from-[#06080f] to-transparent z-10" />

      {/* Content */}
      <div className="relative z-20 flex flex-col items-center justify-center min-h-screen px-4">
        <div className="text-center max-w-2xl animate-[fadeUp_1s_ease-out]">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 rounded-full border border-brand/20 bg-brand/5 px-4 py-1.5 mb-8 animate-[fadeIn_0.8s_ease-out_0.2s_both]">
            <span className="h-1.5 w-1.5 rounded-full bg-brand animate-pulse" />
            <span className="text-xs text-brand font-medium">
              SIH 2026 — Cybercrime Intelligence
            </span>
          </div>

          {/* Title */}
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-white leading-[1.1] mb-4">
            <span className="text-brand">Cyber</span>Trace
          </h1>
          <p className="text-base md:text-lg text-gray-400 max-w-lg mx-auto mb-10 leading-relaxed">
            Predicting cash-withdrawal hotspots for cybercrime fraud using
            GNN-based mule account tracing, geospatial clustering, and NLP —
            with a blockchain-backed audit trail.
          </p>

          {/* CTA */}
          <div className="animate-[fadeIn_0.8s_ease-out_0.6s_both]">
            <Button
              size="lg"
              onClick={() => navigate("/dashboard")}
              className="group text-sm px-6 h-11"
            >
              Enter Dashboard
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Button>
          </div>

          {/* Feature pills */}
          <div className="flex flex-wrap items-center justify-center gap-4 mt-12 animate-[fadeIn_1s_ease-out_1s_both]">
            {[
              { icon: Brain, label: "NLP Entity Extraction" },
              { icon: MapPin, label: "Geospatial Hotspots" },
              { icon: Shield, label: "Blockchain Audit" },
            ].map((feat) => (
              <div
                key={feat.label}
                className="flex items-center gap-2 rounded-md border border-border bg-surface/60 backdrop-blur-sm px-3 py-2"
              >
                <feat.icon className="h-3.5 w-3.5 text-brand" />
                <span className="text-xs text-gray-400">{feat.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom gradient fade */}
      <div className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-[#06080f] to-transparent z-10" />
    </div>
  );
}
