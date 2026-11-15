import { AlertCircle, AlertTriangle, Clock3, Info, RefreshCw } from "lucide-react";
import { useDispatchData } from "../features/dispatch/DispatchDataContext";
import { Button } from "../shared/ui/Button";
import { PageIntro } from "../shared/ui/PageIntro";

interface RisksPageProps {
  openOrder: (orderId: string) => void;
}

export default function RisksPage({ openOrder }: RisksPageProps) {
  const { plan, orders, staff, loading, replanning, error, rebuildPlan } =
    useDispatchData();
  const orderById = new Map(orders.map((order) => [order.order_id, order]));
  const staffById = new Map(staff.map((person) => [person.staff_id, person]));
  const staffByOrderId = new Map(
    (plan?.routes ?? []).flatMap((route) =>
      route.stops
        .filter((stop) => stop.type === "VISIT" && stop.order_id)
        .map((stop) => [stop.order_id!, route.staff_id] as const),
    ),
  );
  const lateRisks = (plan?.alerts ?? []).filter(
    (alert) => alert.type === "LATE_RISK" && alert.status === "ACTIVE",
  );
  const unassigned = plan?.unassigned ?? [];

  return (
    <div className="screen">
      <PageIntro
        eyebrow="ТРЕБУЮТ ВНИМАНИЯ"
        eyebrowTone="warn"
        title="Риски и нераспределённые"
        subtitle={`${unassigned.length} нераспределённых · ${lateRisks.length} рисков`}
        actions={
          <Button
            variant="secondary"
            icon={<RefreshCw className={replanning ? "spin" : ""} size={16} />}
            disabled={loading || replanning || !plan}
            onClick={() => void rebuildPlan()}
          >
            {replanning ? "Пересчитываем…" : "Пересчитать план"}
          </Button>
        }
      />
      {error && <div className="card" role="alert">{error}</div>}
      {loading && <div className="card" role="status">Загружаем риски…</div>}
      <div className="two-cols">
        <section className="card issue-column">
          <div className="column-title">
            <span className="risk-icon">
              <Clock3 size={19} />
            </span>
            <div>
              <h2>Риски опоздания</h2>
              <p>{lateRisks.length} активных предупреждений из плана</p>
            </div>
            <b>{lateRisks.length}</b>
          </div>
          {lateRisks.map((alert) => {
            const order = alert.order_id ? orderById.get(alert.order_id) : undefined;
            const staffId = alert.staff_id ??
              (alert.order_id ? staffByOrderId.get(alert.order_id) : undefined);
            return (
              <article className="issue risk" key={alert.alert_id}>
                <div className="issue-top">
                  <code>{alert.order_id ?? alert.alert_id}</code>
                  <span>{order?.slot.start.slice(11, 16) ?? "—"}–{order?.slot.end.slice(11, 16) ?? "—"}</span>
                </div>
                <h3>{order?.address ?? alert.message}</h3>
                <small>{staffId ? staffById.get(staffId)?.display_name ?? staffId : "Сотрудник не указан"}</small>
                <p>
                  <AlertTriangle size={15} />
                  {alert.message}
                </p>
                {order && (
                  <Button variant="secondary" onClick={() => openOrder(order.order_id)}>
                    Открыть наряд
                  </Button>
                )}
              </article>
            );
          })}
          {!loading && lateRisks.length === 0 && (
            <p className="empty-state">Активных рисков опоздания нет.</p>
          )}
        </section>
        <section className="card issue-column">
          <div className="column-title">
            <span className="loose-icon">
              <AlertCircle size={19} />
            </span>
            <div>
              <h2>Нераспределённые</h2>
              <p>Наряды, не назначенные в текущем плане</p>
            </div>
            <b>{unassigned.length}</b>
          </div>
          {unassigned.map((item) => {
            const order = orderById.get(item.order_id);
            return (
              <article className="issue loose" key={item.order_id}>
                <div className="issue-top">
                  <code>{item.order_id}</code>
                  <span>{order?.slot.start.slice(11, 16) ?? "Сегодня"}</span>
                </div>
                <h3>{order?.address ?? "Адрес недоступен"}</h3>
                <p>
                  <Info size={15} />
                  {item.reason_text}
                </p>
                <Button variant="secondary" onClick={() => openOrder(item.order_id)}>
                  Открыть наряд
                </Button>
              </article>
            );
          })}
          {!loading && unassigned.length === 0 && (
            <p className="empty-state">Все наряды распределены.</p>
          )}
        </section>
      </div>
    </div>
  );
}
