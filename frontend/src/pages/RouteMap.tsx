import { useEffect, useMemo } from "react";
import {
  CircleMarker,
  MapContainer,
  Polyline,
  Popup,
  TileLayer,
  useMap,
} from "react-leaflet";
import type { LatLngBoundsExpression, LatLngExpression, LatLngTuple } from "leaflet";
import type { ApiOrder, ApiRoute, ApiServiceCenter } from "../shared/api";

interface RouteMapProps {
  orders: ApiOrder[];
  centers: ApiServiceCenter[];
  routes: ApiRoute[];
  routeColors: string[];
  selectedStaffId: string | null;
  pgpOrderIds: Set<string>;
  riskyOrderIds: Set<string>;
  hideCompleted: boolean;
  openOrder: (orderId: string) => void;
}

function FitMapToBounds({ bounds }: { bounds: LatLngBoundsExpression | null }) {
  const map = useMap();

  useEffect(() => {
    if (bounds) map.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });
  }, [bounds, map]);

  return null;
}

export function RouteMap({
  orders,
  centers,
  routes,
  routeColors,
  selectedStaffId,
  pgpOrderIds,
  riskyOrderIds,
  hideCompleted,
  openOrder,
}: RouteMapProps) {
  const ordersById = new Map(orders.map((order) => [order.order_id, order]));
  const centersById = new Map(
    centers.map((center) => [center.service_center_id, center]),
  );
  const coordinates = useMemo<LatLngTuple[]>(
    () => {
      const points: LatLngTuple[] = [];
      for (const order of orders) points.push([order.lat, order.lon]);
      for (const center of centers) points.push([center.lat, center.lon]);
      return points;
    },
    [orders, centers],
  );
  const bounds = useMemo<LatLngBoundsExpression | null>(
    () => {
      if (!coordinates.length) return null;
      const southWest: LatLngTuple = [
        Math.min(...coordinates.map(([lat]) => lat)),
        Math.min(...coordinates.map(([, lon]) => lon)),
      ];
      const northEast: LatLngTuple = [
        Math.max(...coordinates.map(([lat]) => lat)),
        Math.max(...coordinates.map(([, lon]) => lon)),
      ];
      return [southWest, northEast];
    },
    [coordinates],
  );
  const defaultCenter: LatLngExpression = coordinates[0] ?? [56.8389, 60.6057];

  return (
    <MapContainer
      center={defaultCenter}
      zoom={12}
      scrollWheelZoom
      className="route-leaflet-map"
      aria-label="Карта маршрутов и сервисных центров"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FitMapToBounds bounds={bounds} />
      {routes.map((route, routeIndex) => {
        const routePoints = route.stops
          .filter(
            (stop) =>
              ["DEPOT_START", "VISIT", "RESTOCK", "DEPOT_END"].includes(stop.type) &&
              (!hideCompleted || stop.status !== "DONE"),
          )
          .flatMap((stop) => {
            if (stop.type === "VISIT") {
              const order = ordersById.get(stop.order_id ?? "");
              return order ? [[order.lat, order.lon] as LatLngExpression] : [];
            }
            const center = centersById.get(stop.location_id);
            return center ? [[center.lat, center.lon] as LatLngExpression] : [];
          });
        if (routePoints.length < 2) return null;
        const color = routeColors[routeIndex % routeColors.length];
        const selected = route.staff_id === selectedStaffId;
        return (
          <Polyline
            key={route.staff_id}
            positions={routePoints}
            pathOptions={{
              color,
              weight: selected ? 6 : 3,
              opacity: selected ? 0.95 : 0.55,
            }}
          />
        );
      })}
      {orders.map((order) => {
        const route = routes.find((candidate) =>
          candidate.stops.some(
            (stop) => stop.type === "VISIT" && stop.order_id === order.order_id,
          ),
        );
        const routeIndex = route ? routes.indexOf(route) : -1;
        const color = pgpOrderIds.has(order.order_id)
          ? "#7C3AED"
          : riskyOrderIds.has(order.order_id) || order.status === "UNASSIGNED"
            ? "#F97316"
            : routeIndex >= 0
              ? routeColors[routeIndex % routeColors.length]
              : "#64748B";
        if (hideCompleted && order.status === "DONE") return null;
        return (
          <CircleMarker
            key={order.order_id}
            center={[order.lat, order.lon]}
            radius={route?.staff_id === selectedStaffId ? 8 : 6}
            pathOptions={{ color: "#fff", weight: 2, fillColor: color, fillOpacity: 0.95 }}
          >
            <Popup>
              <strong>{order.order_id}</strong>
              <br />
              {order.address}
              <br />
              {order.work_type_code} · {order.technology}
              <br />
              <button
                type="button"
                className="map-popup-action"
                onClick={() => openOrder(order.order_id)}
              >
                Открыть наряд
              </button>
            </Popup>
          </CircleMarker>
        );
      })}
      {centers.map((center, index) => (
        <CircleMarker
          key={center.service_center_id}
          center={[center.lat, center.lon]}
          radius={10}
          pathOptions={{
            color: "#fff",
            weight: 2,
            fillColor: routeColors[index % routeColors.length],
            fillOpacity: 1,
          }}
        >
          <Popup>
            <strong>{center.name}</strong>
            <br />
            {center.address}
            <br />
            {center.service_center_id}
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
