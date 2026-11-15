import { useState } from "react";
import {
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Layers3,
  Plus,
  RefreshCw,
} from "lucide-react";
import { Button } from "../shared/ui/Button";
import { Tooltip } from "../shared/ui/Tooltip";
import { PageIntro } from "../shared/ui/PageIntro";
import { Chips } from "../shared/ui/Chips";
import { useToast } from "../features/toast/ToastProvider";
import { useDispatchData } from "../features/dispatch/DispatchDataContext";
import { RouteMap } from "./RouteMap";
import "leaflet/dist/leaflet.css";

interface MapPageProps {
  openOrder: (orderId: string) => void;
  openCreate: () => void;
}

export default function MapPage({ openOrder, openCreate }: MapPageProps) {
  const [activeStaffId, setActiveStaffId] = useState<string | null>(null);
  const [filter, setFilter] = useState("Все");
  const [hideCompleted, setHideCompleted] = useState(false);
  const { toast } = useToast();
  const { date, plan, orders, staff, centers, loading, replanning, error, refresh } =
    useDispatchData();
  const staffById = new Map(staff.map((person) => [person.staff_id, person]));
  const colors = ["#7C3AED", "#2563EB", "#FF6B00", "#DC2626", "#0891B2", "#16A34A"];

  const routes = plan?.routes ?? [];
  const visibleRoutes = routes.filter((route) => {
    const person = staffById.get(route.staff_id);
    if (filter === "3ЛТП") return person?.profiles.includes("LTP3");
    if (filter === "Инсталляция") return person?.profiles.includes("INSTALL");
    if (filter === "Высокий риск") {
      return route.stops.some((stop) =>
        plan?.alerts.some((alert) => alert.type === "LATE_RISK" && alert.order_id === stop.order_id),
      );
    }
    if (filter === "ПГП") {
      return plan?.pgp_groups.some((group) =>
        group.order_ids.some((id) => route.stops.some((stop) => stop.order_id === id)),
      );
    }
    return true;
  });
  const pgpOrderIds = new Set(
    (plan?.pgp_groups ?? []).flatMap((group) => group.order_ids),
  );
  const riskyOrderIds = new Set(
    (plan?.alerts ?? [])
      .filter((alert) => alert.type === "LATE_RISK" && alert.status === "ACTIVE")
      .flatMap((alert) => (alert.order_id ? [alert.order_id] : [])),
  );

  async function handleRefresh() {
    if (await refresh()) toast("Данные диспетчерского плана обновлены");
  }

  return (
    <div className="screen map-screen">
      <PageIntro
        eyebrow={`ОПЕРАТИВНЫЙ КОНТРОЛЬ · ${date}`}
        title="Карта маршрутов"
        subtitle={`${routes.length} маршрутов · ${plan?.summary?.visits_planned ?? 0} визитов`}
        live
      />
      <div className="map-layout">
        <div className="map-canvas">
          <div className="map-toolbar">
            <Button variant="secondary" icon={<Layers3 size={16} />} onClick={() => setFilter("Все")}>
              Все маршруты
            </Button>
            <Button
              variant={hideCompleted ? "secondary" : "ghost"}
              onClick={() => setHideCompleted((hidden) => !hidden)}
            >
              {hideCompleted ? "Показать выполненные" : "Скрыть выполненные"}
            </Button>
            <Button variant="ghost" icon={<AlertTriangle size={15} />} onClick={() => setFilter("Высокий риск")}>
              Только риски
            </Button>
            <span className="toolbar-divider" />
            <Button
              variant="ghost"
              disabled={loading || replanning}
              onClick={() => void handleRefresh()}
              icon={<RefreshCw className={loading ? "spin" : ""} size={16} />}
            >
              Обновить
            </Button>
          </div>
          {error && <div className="card" role="alert">{error}</div>}
          {loading && <div className="card" role="status">Загружаем маршруты…</div>}
          <RouteMap
            orders={orders}
            centers={centers}
            routes={visibleRoutes}
            routeColors={colors}
            selectedStaffId={activeStaffId}
            pgpOrderIds={pgpOrderIds}
            riskyOrderIds={riskyOrderIds}
            hideCompleted={hideCompleted}
            openOrder={openOrder}
          />
          <Tooltip text="Создать наряд вручную">
            <button className="fab" onClick={openCreate}>
              <Plus size={24} />
            </button>
          </Tooltip>
        </div>
        <aside className="route-panel">
          <Chips
            items={["Все", "3ЛТП", "Инсталляция", "Высокий риск", "ПГП"]}
            selected={filter}
            onSelect={setFilter}
          />
          <div className="panel-heading">
            <b>Маршруты сотрудников</b>
            <span>{visibleRoutes.length} на линии</span>
          </div>
          <div className="employee-list">
            {visibleRoutes.map((route, i) => {
              const person = staffById.get(route.staff_id);
              const visitCount = route.stops.filter((stop) => stop.type === "VISIT").length;
              return (
              <button
                className={`employee-card ${activeStaffId === route.staff_id ? "active" : ""}`}
                key={route.staff_id}
                onClick={() => setActiveStaffId(route.staff_id)}
              >
                <span
                  className="avatar"
                  style={{ background: `${colors[i % colors.length]}18`, color: colors[i % colors.length] }}
                >
                  {(person?.display_name ?? route.staff_id).slice(0, 2)}
                </span>
                <span className="employee-info">
                  <b>{person?.display_name ?? route.staff_id}</b>
                  <small>
                    {route.service_center_id} · {person?.shift.start}–{person?.shift.end}
                  </small>
                  <span className="progress">
                    <i
                      style={{
                        width: `${Math.min(100, visitCount * 12)}%`,
                        background: colors[i % colors.length],
                      }}
                    />
                  </span>
                </span>
                <span className="visits">
                  <b>{visitCount}</b>
                  <small>визитов</small>
                </span>
                <ChevronRight size={16} />
              </button>
              );
            })}
          </div>
          <details className="legend">
            <summary>
              Условные обозначения <ChevronDown size={15} />
            </summary>
            <div>
              <span>
                <i className="green-dot" />
                Сотрудник
              </span>
              <span>
                <i className="yellow-dot" />
                Риск
              </span>
              <span>
                <i className="purple-dot" />
                ПГП
              </span>
              <span>
                <i className="square-dot" />
                СЦ
              </span>
            </div>
          </details>
        </aside>
      </div>
    </div>
  );
}
