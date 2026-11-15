import { useMemo } from "react";
import { Building2, Info, MapPin, RefreshCw } from "lucide-react";
import { useDispatchData } from "../features/dispatch/DispatchDataContext";
import type { ApiRoute } from "../shared/api";
import { Button } from "../shared/ui/Button";
import { PageIntro } from "../shared/ui/PageIntro";

const colors = ["#7C3AED", "#2563EB", "#FF6B00", "#DC2626", "#0891B2", "#16A34A"];

export default function CentersPage() {
  const { centers, staff, orders, plan, loading, error, refresh } = useDispatchData();
  const routesByCenter = new Map<string, ApiRoute[]>();
  for (const route of plan?.routes ?? []) {
    routesByCenter.set(
      route.service_center_id,
      [...(routesByCenter.get(route.service_center_id) ?? []), route],
    );
  }
  const bounds = useMemo(() => {
    if (!centers.length) return { minLat: 56.7, maxLat: 57, minLon: 60.4, maxLon: 60.8 };
    return {
      minLat: Math.min(...centers.map((center) => center.lat)),
      maxLat: Math.max(...centers.map((center) => center.lat)),
      minLon: Math.min(...centers.map((center) => center.lon)),
      maxLon: Math.max(...centers.map((center) => center.lon)),
    };
  }, [centers]);

  function centerPosition(lat: number, lon: number) {
    const latRange = Math.max(bounds.maxLat - bounds.minLat, 0.001);
    const lonRange = Math.max(bounds.maxLon - bounds.minLon, 0.001);
    return {
      left: `${10 + ((lon - bounds.minLon) / lonRange) * 80}%`,
      top: `${18 + ((bounds.maxLat - lat) / latRange) * 65}%`,
    };
  }

  return (
    <div className="screen">
      <PageIntro
        eyebrow={`${centers.length} СЕРВИСНЫХ ЦЕНТРОВ`}
        title="Сервисные центры"
        subtitle="Справочник API, закреплённые сотрудники и маршруты на сегодня"
        actions={
          <Button
            variant="secondary"
            icon={<RefreshCw size={16} />}
            disabled={loading}
            onClick={() => void refresh()}
          >
            Обновить
          </Button>
        }
      />
      {error && <div className="card" role="alert">{error}</div>}
      {loading && <div className="card" role="status">Загружаем сервисные центры…</div>}
      <div className="centers-layout">
        <div className="centers-list">
          {centers.map((center, index) => {
            const centerStaff = staff.filter(
              (person) => person.service_center_id === center.service_center_id,
            );
            const routes = routesByCenter.get(center.service_center_id) ?? [];
            const staffIds = new Set(centerStaff.map((person) => person.staff_id));
            const assignedOrders = orders.filter(
              (order) => order.assigned_staff_id && staffIds.has(order.assigned_staff_id),
            ).length;
            const visits = routes.reduce(
              (count, route) => count + route.stops.filter((stop) => stop.type === "VISIT").length,
              0,
            );
            return (
              <article className="center-card card" key={center.service_center_id}>
                <div className="center-card-title">
                  <span style={{ background: colors[index % colors.length] }}>
                    <Building2 size={20} />
                  </span>
                  <div>
                    <h2>{center.name}</h2>
                    <p><MapPin size={12} /> {center.address}</p>
                  </div>
                </div>
                <div className="center-metrics">
                  <div><span>Сотрудники</span><b>{centerStaff.length}</b></div>
                  <div><span>Маршруты</span><b>{routes.length}</b></div>
                  <div><span>Назначено</span><b>{assignedOrders}</b></div>
                </div>
                <div className="stock">
                  <div>
                    <span>Рабочее окно</span>
                    <small>
                      {center.opening_hours
                        ? `${center.opening_hours.open}–${center.opening_hours.close}`
                        : "не указано"}
                      {center.restock_duration_min != null
                        ? ` · пополнение ${center.restock_duration_min} мин`
                        : ""}
                    </small>
                  </div>
                  <span>Визитов сегодня <b>{visits}</b></span>
                  <span className="muted">
                    <Info size={13} /> Остатки оборудования API не предоставляет
                  </span>
                </div>
              </article>
            );
          })}
        </div>
        <div className="coverage-map card">
          <div className="coverage-roads" />
          <div className="coverage-head">
            <b>Сервисные центры</b>
            <span>Координаты из справочника API</span>
          </div>
          {centers.map((center, index) => (
            <div
              className="coverage-zone"
              key={center.service_center_id}
              style={{
                ...centerPosition(center.lat, center.lon),
                borderColor: colors[index % colors.length],
                background: `${colors[index % colors.length]}18`,
              }}
            >
              <span style={{ background: colors[index % colors.length] }}>
                <Building2 size={14} />
              </span>
              <b>{center.name}</b>
            </div>
          ))}
          <div className="coverage-legend">
            <Info size={14} />
            Положение центров соответствует координатам API; зоны ответственности не заданы
          </div>
        </div>
      </div>
    </div>
  );
}
