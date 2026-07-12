import { APIProvider, Map as GoogleMap, Marker, useMap } from "@vis.gl/react-google-maps";
import { Map as MapIcon } from "lucide-react";
import { useEffect, useMemo } from "react";
import { CircleMarker, MapContainer, Polyline, Popup, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";

// com uma chave do Google Maps o mapa usa o Google; sem ela, cai para
// Leaflet + OpenStreetMap (zero configuração)
const GMAPS_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

const ROUTE_COLORS = ["#2b6cb0", "#c05621", "#2f855a", "#6b46c1", "#b83280", "#975a16"];

const PRIORITY_COLORS = {
  critical: "#e53e3e",
  high: "#dd6b20",
  normal: "#3182ce",
};

const PRIORITY_LABELS = {
  critical: "Crítica",
  high: "Alta",
  normal: "Normal",
};

function buildRoutePaths(depot, points, solution) {
  if (!solution?.routes) return [];
  const pointsById = Object.fromEntries(points.map((p) => [p.id, p]));
  return solution.routes
    .filter((r) => r.stops.length)
    .map((route, i) => ({
      vehicleId: route.vehicle_id,
      color: ROUTE_COLORS[i % ROUTE_COLORS.length],
      path: [
        { lat: depot.lat, lng: depot.lon },
        ...route.stops.map((s) => ({ lat: pointsById[s].lat, lng: pointsById[s].lon })),
        { lat: depot.lat, lng: depot.lon },
      ],
    }));
}

/* ── Google Maps ────────────────────────────────────────── */

function GRoutePolyline({ path, color }) {
  const map = useMap();
  useEffect(() => {
    if (!map || !window.google) return undefined;
    const polyline = new window.google.maps.Polyline({
      path,
      strokeColor: color,
      strokeWeight: 3,
      strokeOpacity: 0.85,
      map,
    });
    return () => polyline.setMap(null);
  }, [map, path, color]);
  return null;
}

function circleIcon(color, scale = 7) {
  return {
    path: 0, // google.maps.SymbolPath.CIRCLE
    scale,
    fillColor: color,
    fillOpacity: 1,
    strokeColor: "#ffffff",
    strokeWeight: 1.5,
  };
}

function GoogleMapView({ depot, points, routePaths }) {
  return (
    <APIProvider apiKey={GMAPS_KEY}>
      <GoogleMap
        style={{ width: "100%", height: "100%" }}
        defaultCenter={{ lat: depot.lat, lng: depot.lon }}
        defaultZoom={12}
        gestureHandling="greedy"
        disableDefaultUI={false}
      >
        {routePaths.map((r) => (
          <GRoutePolyline key={r.vehicleId} path={r.path} color={r.color} />
        ))}

        <Marker
          position={{ lat: depot.lat, lng: depot.lon }}
          title={`${depot.name} (depósito)`}
          icon={circleIcon("#1a202c", 9)}
        />

        {points.map((p) => (
          <Marker
            key={p.id}
            position={{ lat: p.lat, lng: p.lon }}
            title={`${p.name} · ${PRIORITY_LABELS[p.priority]} · ${p.demand_kg} kg`}
            icon={circleIcon(PRIORITY_COLORS[p.priority])}
          />
        ))}
      </GoogleMap>
    </APIProvider>
  );
}

/* ── Leaflet / OpenStreetMap (fallback sem chave) ───────── */

function LeafletMapView({ depot, points, routePaths, vehiclesById, solution }) {
  return (
    <MapContainer center={[depot.lat, depot.lon]} zoom={12} style={{ height: "100%", width: "100%" }}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {routePaths.map((r) => {
        const route = solution.routes.find((x) => x.vehicle_id === r.vehicleId);
        return (
          <Polyline
            key={r.vehicleId}
            positions={r.path.map((p) => [p.lat, p.lng])}
            pathOptions={{ color: r.color, weight: 3, opacity: 0.85 }}
          >
            <Popup>
              <b>{vehiclesById[r.vehicleId]?.name}</b>
              <br />
              {route.stops.length} paradas · {route.distance_km.toFixed(1)} km ·{" "}
              {route.load_kg.toFixed(1)} kg
            </Popup>
          </Polyline>
        );
      })}

      <CircleMarker
        center={[depot.lat, depot.lon]}
        radius={10}
        pathOptions={{ color: "#1a202c", fillColor: "#1a202c", fillOpacity: 1 }}
      >
        <Popup><b>{depot.name}</b> (depósito)</Popup>
      </CircleMarker>

      {points.map((p) => (
        <CircleMarker
          key={p.id}
          center={[p.lat, p.lon]}
          radius={6}
          pathOptions={{
            color: PRIORITY_COLORS[p.priority],
            fillColor: PRIORITY_COLORS[p.priority],
            fillOpacity: 0.9,
          }}
        >
          <Popup>
            <b>{p.name}</b>
            <br />
            Prioridade: {PRIORITY_LABELS[p.priority]}
            <br />
            Demanda: {p.demand_kg} kg
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}

/* ── Ponto de entrada ──────────────────────────────────── */

export default function MapView({ scenario, solution }) {
  const routePaths = useMemo(
    () => (scenario ? buildRoutePaths(scenario.depot, scenario.points, solution) : []),
    [scenario, solution]
  );

  if (!scenario) {
    return (
      <div className="map-placeholder">
        <MapIcon size={32} />
        <span>Execute uma otimização para visualizar as rotas.</span>
      </div>
    );
  }

  const { depot, points, vehicles } = scenario;
  const vehiclesById = Object.fromEntries(vehicles.map((v) => [v.id, v]));

  if (GMAPS_KEY) {
    return <GoogleMapView depot={depot} points={points} routePaths={routePaths} />;
  }

  return (
    <LeafletMapView
      depot={depot}
      points={points}
      routePaths={routePaths}
      vehiclesById={vehiclesById}
      solution={solution}
    />
  );
}
