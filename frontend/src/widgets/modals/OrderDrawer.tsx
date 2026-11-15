import { MapPin, Package, X } from "lucide-react";
import { useDispatchData } from "../../features/dispatch/DispatchDataContext";
import { Button } from "../../shared/ui/Button";
import { Status } from "../../shared/ui/Status";

interface OrderDrawerProps {
  orderId: string | null;
  close: () => void;
  onExplain: (orderId: string) => void;
  onAssign: (orderId: string) => void;
}

export function OrderDrawer({ orderId, close, onExplain, onAssign }: OrderDrawerProps) {
  const { orders, staff, centers, plan } = useDispatchData();
  const order = orders.find((item) => item.order_id === orderId);
  const staffId = order?.assigned_staff_id ?? null;
  const assignedStaff = staff.find((person) => person.staff_id === staffId);
  const center = centers.find(
    (item) => item.service_center_id === assignedStaff?.service_center_id,
  );
  const visit = plan?.routes
    .find((route) => route.staff_id === staffId)
    ?.stops.find((stop) => stop.type === "VISIT" && stop.order_id === orderId);

  const statusLabel: Record<string, string> = {
    PLANNED: "Запланирован",
    IN_PROGRESS: "В работе",
    DONE: "Выполнен",
    UNASSIGNED: "Не распределён",
    PGP: "ПГП",
    CANCELLED: "Отменён",
    UNPLANNED: "Не запланирован",
  };

  return (
    <>
      <div className="overlay" onClick={close} />
      <aside className="drawer">
        <div className="drawer-head">
          <div>
            <span>ДЕТАЛИ НАРЯДА</span>
            <h2>{order?.order_id ?? "Наряд не выбран"}</h2>
          </div>
          <button onClick={close} aria-label="Закрыть">
            <X size={21} />
          </button>
        </div>
        {order ? (
          <>
            <Status>{statusLabel[order.status] ?? order.status}</Status>
            <div className="drawer-section">
              <h3>Объект</h3>
              <p>
                <MapPin size={16} />
                <span>
                  <b>{order.address}</b>
                  <small>{order.building_id} · {order.technology}</small>
                </span>
              </p>
            </div>
            <div className="drawer-grid">
              <div><span>Тип работ</span><b>{order.work_type_code}</b></div>
              <div><span>Технология</span><b>{order.technology}</b></div>
              <div>
                <span>Слот</span>
                <b>{order.slot.start.slice(11, 16)}–{order.slot.end.slice(11, 16)}</b>
              </div>
              <div>
                <span>Назначенный визит</span>
                <b>{visit ? visit.start.slice(11, 16) : "—"}</b>
              </div>
            </div>
            <div className="drawer-section">
              <h3>Оборудование</h3>
              <div className="equipment">
                <Package size={17} />
                <span>ONT ×{order.required_equipment.ONT}</span>
                <span>Роутер ×{order.required_equipment.ROUTER}</span>
                <span>STB ×{order.required_equipment.STB}</span>
              </div>
            </div>
            <div className="assignment">
              <div>
                <span className="avatar">
                  {(assignedStaff?.display_name ?? staffId ?? "—").slice(0, 2)}
                </span>
                <span>
                  <small>{staffId ? "Назначен" : "Не назначен"}</small>
                  <b>{assignedStaff?.display_name ?? staffId ?? "—"}</b>
                  {center && <small>{center.name}</small>}
                </span>
              </div>
            </div>
            {plan?.unassigned.some((item) => item.order_id === order.order_id) && (
              <div className="drawer-section">
                <Button onClick={() => onAssign(order.order_id)}>
                  Назначить сотрудника
                </Button>
              </div>
            )}
            {visit?.explanation && (
              <div className="drawer-section">
                <h3>Почему назначен</h3>
                <p>{visit.explanation}</p>
                <Button
                  variant="secondary"
                  onClick={() => onExplain(order.order_id)}
                >
                  Подробнее
                </Button>
              </div>
            )}
          </>
        ) : (
          <div className="drawer-section">
            <p>
              {orderId
                ? "Наряд не найден в текущих данных API."
                : "Выберите наряд на карте, в плане или в списке нарядов."}
            </p>
          </div>
        )}
        <div className="drawer-actions">
          <Button variant="secondary" onClick={close}>Закрыть</Button>
        </div>
      </aside>
    </>
  );
}
