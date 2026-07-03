"use client";

import { MapContainer, TileLayer, Circle, Marker, Popup, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";
import { LoppisSummary } from "@loppis/shared";
import { formatDateCompact, formatDateLong } from "@/lib/format";
import { useI18n } from "@/lib/i18n/context";
import { useEffect, useRef } from "react";

function loppisIcon(dateLabel: string) {
  return L.divIcon({
    className: "loppis-marker",
    html: `<div style="display:flex;flex-direction:column;align-items:center;gap:2px">
      <div style="background:#2563eb;color:#fff;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-size:14px;border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.3)">L</div>
      <div style="background:#fff;color:#1e40af;font-size:10px;font-weight:600;padding:1px 4px;border-radius:4px;border:1px solid #bfdbfe;white-space:nowrap;box-shadow:0 1px 3px rgba(0,0,0,.15)">${dateLabel}</div>
    </div>`,
    iconSize: [72, 48],
    iconAnchor: [36, 14],
  });
}

const centerIcon = L.divIcon({
  className: "search-center-marker",
  html: `<div style="background:#dc2626;color:#fff;border-radius:50%;width:18px;height:18px;border:3px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,.4);cursor:grab"></div>`,
  iconSize: [18, 18],
  iconAnchor: [9, 9],
});

function MapController({
  center,
  panToCenter,
  onPanComplete,
}: {
  center: { lat: number; lng: number };
  panToCenter: boolean;
  onPanComplete: () => void;
}) {
  const map = useMap();
  useEffect(() => {
    map.setView([center.lat, center.lng], panToCenter ? 11 : map.getZoom(), { animate: true });
    if (panToCenter) onPanComplete();
  }, [center.lat, center.lng, panToCenter, map, onPanComplete]);
  return null;
}

function MapClickHandler({ onCenterChange }: { onCenterChange: (lat: number, lng: number) => void }) {
  useMapEvents({
    click(e) {
      onCenterChange(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

interface Props {
  center: { lat: number; lng: number };
  loppis: LoppisSummary[];
  selectedId?: string;
  onSelect: (l: LoppisSummary) => void;
  radiusKm: number;
  onCenterChange: (lat: number, lng: number) => void;
  panToCenter: boolean;
  onPanComplete: () => void;
}

export default function MapView({
  center,
  loppis,
  selectedId,
  onSelect,
  radiusKm,
  onCenterChange,
  panToCenter,
  onPanComplete,
}: Props) {
  const dragRef = useRef(false);
  const { locale, reliabilityLabel } = useI18n();

  return (
    <MapContainer
      center={[center.lat, center.lng]}
      zoom={10}
      style={{ height: "100%", width: "100%" }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <MapController center={center} panToCenter={panToCenter} onPanComplete={onPanComplete} />
      <MapClickHandler onCenterChange={onCenterChange} />
      <Circle
        center={[center.lat, center.lng]}
        radius={radiusKm * 1000}
        pathOptions={{ color: "#2563eb", fillColor: "#2563eb", fillOpacity: 0.08, weight: 2, dashArray: "6 4" }}
      />
      <Marker
        position={[center.lat, center.lng]}
        icon={centerIcon}
        draggable
        eventHandlers={{
          dragstart: () => {
            dragRef.current = true;
          },
          dragend: (e) => {
            const { lat, lng } = e.target.getLatLng();
            onCenterChange(lat, lng);
            dragRef.current = false;
          },
        }}
      />
      {loppis.map((item) => (
        <Marker
          key={item.id}
          position={[item.lat, item.lng]}
          icon={loppisIcon(formatDateCompact(item.start_at))}
          eventHandlers={{ click: () => onSelect(item) }}
          opacity={selectedId && selectedId !== item.id ? 0.6 : 1}
        >
          <Popup>
            <strong>{item.title}</strong>
            <br />
            <span style={{ fontWeight: 600 }}>{formatDateLong(item.start_at, locale)}</span>
            <br />
            {reliabilityLabel(item.reliability_score, item.status)} ({Math.round(item.reliability_score)})
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
