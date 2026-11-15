import { useState } from "react";
import { ChevronDown, ChevronRight, RefreshCw, SlidersHorizontal } from "lucide-react";
import type { ModalType } from "../shared/types/domain";
import { useDispatchData } from "../features/dispatch/DispatchDataContext";
import { Button } from "../shared/ui/Button";
import { Tooltip } from "../shared/ui/Tooltip";
import { PageIntro } from "../shared/ui/PageIntro";
import { Chips } from "../shared/ui/Chips";
import { KPIs } from "../shared/ui/KPIs";

interface PlanPageProps {
  setModal: (m: ModalType) => void;
  openOrder: (orderId: string) => void;
}

export default function PlanPage({ setModal, openOrder }: PlanPageProps) {
  const [filter, setFilter] = useState("Все");
  const { date, plan, orders, staff, loading, replanning, error, rebuildPlan } =
    useDispatchData();
  const staffById = new Map(staff.map((person) => [person.staff_id, person]));
  const orderById = new Map(orders.map((order) => [order.order_id, order]));
  const routes = (plan?.routes ?? []).filter((route) => {
    const employee = staffById.get(route.staff_id);
    if (filter === "3ЛТП") return employee?.profiles.includes("LTP3");
    if (filter === "Инсталляция") return employee?.profiles.includes("INSTALL");
    if (filter === "Высокий риск") {
      return route.stops.some((stop) =>
        plan?.alerts.some(
          (alert) => alert.type === "LATE_RISK" && alert.order_id === stop.order_id,
        ),
      );
    }
    return true;
  });

  function timelinePosition(value: string) {
    const time = (value.includes("T") ? value.slice(11, 16) : value)
      .split(":")
      .map(Number);
    if (time.length < 2 || time.some(Number.isNaN)) return 0;
    const minutes = time[0] * 60 + time[1] - 8 * 60;
    return Math.max(0, Math.min(100, (minutes / (13 * 60)) * 100));
  }

  return (
    <div className="screen">
      <PageIntro
        eyebrow={`ПЛАН НА ${date}`}
        title="План и загрузка"
        subtitle={plan ? `Версия ${plan.plan_version} · актуально на ${plan.as_of.slice(11, 16)}` : "План смены"}
        actions={
          <>
            <Button
              variant="secondary"
              icon={<SlidersHorizontal size={16} />}
              onClick={() => setModal("scenario")}
            >
              Сценарный анализ
            </Button>
            <Button
              variant="secondary"
              icon={<RefreshCw size={16} className={replanning ? "spin" : ""} />}
              disabled={loading || replanning}
              onClick={() => void rebuildPlan()}
            >
              {replanning ? "Перестраиваем…" : "Перестроить план"}
            </Button>
          </>
        }
      />
      {error && <div className="card" role="alert">{error}</div>}
      {loading && <div className="card" role="status">Загружаем план…</div>}
      <KPIs plan={plan} />
      <div className="section-toolbar">
        <Chips
          items={["Все", "3ЛТП", "Инсталляция", "Высокий риск"]}
          selected={filter}
          onSelect={setFilter}
        />
        <span>{plan ? `План версии ${plan.plan_version}` : "План пока не построен"}</span>
      </div>
      <div className="gantt card">
        <div className="gantt-head">
          <div>Сотрудник / СЦ</div>
          {["08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21"].map(
            (h) => (
              <span key={h}>{h}:00</span>
            ),
          )}
        </div>
        <div className="group-row">
          <ChevronDown size={15} /> Маршруты <span>{routes.length} сотрудников</span>
        </div>
        {routes.map((route) => {
          const employee = staffById.get(route.staff_id);
          return (
          <div className="gantt-row" key={route.staff_id}>
            <div className="gantt-person">
              <span className="avatar">{(employee?.display_name ?? route.staff_id).slice(0, 2)}</span>
              <span>
                <b>{employee?.display_name ?? route.staff_id}</b>
                <small>
                  {route.service_center_id}
                  {route.team_staff_ids?.length
                    ? ` · бригада ${route.team_staff_ids.join(" + ")}`
                    : ""}
                </small>
              </span>
            </div>
            <div className="timeline">
              {plan && (
                <div className="now-line" style={{ left: `${timelinePosition(plan.as_of)}%` }} />
              )}
              {route.stops.filter((stop) => stop.type === "VISIT" || stop.type === "BREAK" || stop.type === "RESTOCK").map((stop) => {
                if (stop.type === "BREAK") {
                  return (
                    <span
                      key={`${route.staff_id}-${stop.seq}`}
                      className="bar gray"
                      style={{
                        left: `${timelinePosition(stop.start)}%`,
                        width: `${Math.max(2, timelinePosition(stop.end) - timelinePosition(stop.start))}%`,
                      }}
                    >
                      Перерыв
                    </span>
                  );
                }
                if (stop.type === "RESTOCK") {
                  return (
                    <Tooltip
                      key={`${route.staff_id}-${stop.seq}`}
                      text={`Пополнение оборудования · ${stop.location_id}`}
                    >
                      <span
                        className="bar blue"
                        style={{
                          left: `${timelinePosition(stop.start)}%`,
                          width: `${Math.max(2, timelinePosition(stop.end) - timelinePosition(stop.start))}%`,
                        }}
                      >
                        Пополнение
                      </span>
                    </Tooltip>
                  );
                }
                const order = stop.order_id ? orderById.get(stop.order_id) : undefined;
                const risky = plan?.alerts.some(
                  (alert) => alert.type === "LATE_RISK" && alert.order_id === stop.order_id,
                );
                return (
                  <Tooltip key={`${route.staff_id}-${stop.seq}`} text={`${order?.address ?? stop.location_id} · ${stop.order_id ?? ""}`}>
                    <button
                      onClick={() => stop.order_id && openOrder(stop.order_id)}
                      className={`bar ${risky ? "yellow" : "green"}`}
                      style={{
                        left: `${timelinePosition(stop.start)}%`,
                        width: `${Math.max(2, timelinePosition(stop.end) - timelinePosition(stop.start))}%`,
                      }}
                    >
                      {order?.address ?? stop.order_id}
                    </button>
                  </Tooltip>
                );
              })}
            </div>
          </div>
          );
        })}
        {!loading && routes.length === 0 && (
          <div className="group-row">
            <ChevronRight size={15} /> В плане пока нет назначенных маршрутов
          </div>
        )}
      </div>
    </div>
  );
}
