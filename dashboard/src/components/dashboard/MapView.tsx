import { useEffect, useRef, useMemo } from "react";
import L from "leaflet";
import type { Complaint, Prediction } from "@/data/mockData";

interface MapViewProps {
  complaints: Complaint[];
  predictions: Prediction[];
  selectedPrediction: string | null;
  onSelectPrediction: (id: string | null) => void;
}

function getRiskColor(level: string): string {
  switch (level) {
    case "critical":
      return "#ef4444";
    case "high":
      return "#f59e0b";
    default:
      return "#3b82f6";
  }
}

export function MapView({
  complaints,
  predictions,
  selectedPrediction,
  onSelectPrediction,
}: MapViewProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<L.Map | null>(null);
  const markersRef = useRef<L.LayerGroup>(null);
  const circlesRef = useRef<L.LayerGroup>(null);

  const center = useMemo(() => L.latLng(12.95, 77.62), []);

  useEffect(() => {
    if (!mapRef.current || mapInstance.current) return;

    const map = L.map(mapRef.current, {
      center,
      zoom: 12,
      zoomControl: false,
      attributionControl: false,
    });

    L.control.zoom({ position: "bottomright" }).addTo(map);

    L.tileLayer(
      "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
      { maxZoom: 19 }
    ).addTo(map);

    markersRef.current = L.layerGroup().addTo(map);
    circlesRef.current = L.layerGroup().addTo(map);
    mapInstance.current = map;

    return () => {
      map.remove();
      mapInstance.current = null;
    };
  }, [center]);

  // Draw prediction zones
  useEffect(() => {
    const circles = circlesRef.current;
    if (!circles) return;
    circles.clearLayers();

    predictions.forEach((pred) => {
      const color = getRiskColor(pred.risk_level);
      const isSelected = pred.id === selectedPrediction;
      const radius = pred.radius_km * 1000;

      const circle = L.circle([pred.center_lat, pred.center_lon], {
        radius,
        color,
        fillColor: color,
        fillOpacity: isSelected ? 0.25 : 0.12,
        weight: isSelected ? 3 : 1.5,
        dashArray: isSelected ? undefined : "6 4",
      });

      circle.on("click", () => {
        onSelectPrediction(pred.id === selectedPrediction ? null : pred.id);
      });

      circle.bindTooltip(
        `<div style="font-family:Inter,sans-serif;font-size:12px;padding:2px 0">
          <strong>${pred.zone_name}</strong><br/>
          Confidence: ${(pred.confidence * 100).toFixed(0)}%<br/>
          Complaints: ${pred.complaint_count}
        </div>`,
        { className: "bg-surface-overlay border-border text-gray-200 text-xs" }
      );

      circles.addLayer(circle);

      // Zone label
      const label = L.marker([pred.center_lat, pred.center_lon], {
        icon: L.divIcon({
          className: "",
          html: `<div style="
            font-family:Inter,sans-serif;
            font-size:10px;
            font-weight:600;
            color:${color};
            text-shadow:0 0 8px ${color}40;
            white-space:nowrap;
            text-align:center;
            transform:translate(-50%,-50%);
          ">${pred.zone_name.split(" ")[0]}</div>`,
          iconSize: [0, 0],
        }),
      });
      circles.addLayer(label);
    });
  }, [predictions, selectedPrediction, onSelectPrediction]);

  // Draw complaint markers
  useEffect(() => {
    const markers = markersRef.current;
    if (!markers) return;
    markers.clearLayers();

    const filtered = selectedPrediction
      ? complaints.filter((c) => {
          const pred = predictions.find((p) => p.id === selectedPrediction);
          if (!pred) return false;
          const dist =
            Math.sqrt(
              Math.pow((c.victim_lat - pred.center_lat) * 111, 2) +
                Math.pow((c.victim_lon - pred.center_lon) * 111, 2)
            );
          return dist <= pred.radius_km;
        })
      : complaints;

    filtered.forEach((c) => {
      const marker = L.circleMarker([c.victim_lat, c.victim_lon], {
        radius: 4,
        fillColor: getRiskColor(
          c.amount_inr > 100000 ? "critical" : c.amount_inr > 50000 ? "high" : "medium"
        ),
        fillOpacity: 0.8,
        weight: 0,
      });

      marker.bindTooltip(
        `<div style="font-family:Inter,sans-serif;font-size:11px;padding:2px 0">
          <strong>${c.complaint_id}</strong> — ${c.fraud_type}<br/>
          ₹${c.amount_inr.toLocaleString("en-IN")} — ${c.bank}
        </div>`,
        { className: "bg-surface-overlay border-border text-gray-200 text-xs" }
      );

      markers.addLayer(marker);
    });
  }, [complaints, selectedPrediction, predictions]);

  return (
    <div ref={mapRef} className="h-full w-full rounded-lg" />
  );
}
