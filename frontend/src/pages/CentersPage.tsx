import { Building2, Info, MapPin, RefreshCw } from "lucide-react";
import { useDispatchData } from "../features/dispatch/DispatchDataContext";
import type { ApiOrder, ApiRoute } from "../shared/api";
import { Button } from "../shared/ui/Button";
import { PageIntro } from "../shared/ui/PageIntro";
import { RouteMap } from "./RouteMap";
import "leaflet/dist/leaflet.css";

const colors = ["#7C3AED", "#2563EB", "#FF6B00", "#DC2626", "#0891B2", "#16A34A"];

export default function CentersPage() {
  const { centers, staff, orders, plan, loading, error, refresh } = useDispatchData();
  const noOrders: ApiOrder[] = [];
  const noRoutes: ApiRoute[] = [];
  const noOrderIds = new Set<string>();
  const routesByCenter = new Map<string, ApiRoute[]>();
  for (const route of plan?.routes ?? []) {
    routesByCenter.set(
      route.service_center_id,
      [...(routesByCenter.get(route.service_center_id) ?? []), route],
    );
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
          <RouteMap
            orders={noOrders}
            centers={centers}
            routes={noRoutes}
            routeColors={colors}
            selectedStaffId={null}
            pgpOrderIds={noOrderIds}
            riskyOrderIds={noOrderIds}
            hideCompleted={false}
            openOrder={() => undefined}
          />
          <div className="coverage-head">
            <b>Сервисные центры</b>
            <span>Координаты из API · нажмите на точку для подробностей</span>
          </div>
          <div className="coverage-legend">
            <Info size={14} />
            Положение и карточки СЦ соответствуют основной карте маршрутов
          </div>
        </div>
      </div>
    </div>
  );
}
