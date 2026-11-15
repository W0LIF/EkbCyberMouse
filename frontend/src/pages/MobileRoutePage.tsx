import { useEffect, useMemo, useState } from "react";
import { ListTodo, LogOut, MapPin, RefreshCw, Route, UserRound } from "lucide-react";
import { useDispatchData } from "../features/dispatch/DispatchDataContext";
import { Logo } from "../shared/ui/Logo";
import { Status } from "../shared/ui/Status";
import { Button } from "../shared/ui/Button";

interface MobileRoutePageProps {
  logout: () => void;
}

type MobileTab = "route" | "orders" | "profile";
const STAFF_STORAGE_KEY = "rtk-mobile-staff";

export default function MobileRoutePage({ logout }: MobileRoutePageProps) {
  const [tab, setTab] = useState<MobileTab>("route");
  const [selectedStaffId, setSelectedStaffId] = useState(
    () => localStorage.getItem(STAFF_STORAGE_KEY) ?? "",
  );
  const { date, plan, orders, staff, centers, loading, error, refresh } =
    useDispatchData();
  const routeByStaff = useMemo(
    () => new Map((plan?.routes ?? []).map((route) => [route.staff_id, route])),
    [plan],
  );

  const activeStaffId =
    staff.some((person) => person.staff_id === selectedStaffId)
      ? selectedStaffId
      : plan?.routes[0]?.staff_id ?? staff[0]?.staff_id ?? "";
  useEffect(() => {
    if (activeStaffId) localStorage.setItem(STAFF_STORAGE_KEY, activeStaffId);
  }, [activeStaffId]);

  const person = staff.find((item) => item.staff_id === activeStaffId);
  const route = routeByStaff.get(activeStaffId);
  const center = centers.find((item) => item.service_center_id === person?.service_center_id);
  const orderById = new Map(orders.map((order) => [order.order_id, order]));
  const visits = route?.stops.filter((stop) => stop.type === "VISIT") ?? [];
  const nextVisit = visits.find((stop) => stop.status !== "DONE");
  const nextOrder = nextVisit?.order_id ? orderById.get(nextVisit.order_id) : undefined;
  const completed = visits.filter((stop) => stop.status === "DONE").length;
  const visibleOrders = orders.filter(
    (order) => order.assigned_staff_id === activeStaffId,
  );

  return (
    <div className="mobile-app">
      <header>
        <Logo />
        <button onClick={logout} aria-label="Выйти">
          <LogOut size={19} />
        </button>
      </header>
      <main>
        {error && <div className="card" role="alert">{error}</div>}
        {loading && <div className="card" role="status">Загружаем маршрут…</div>}
        <div className="mobile-greeting">
          <span>{date}</span>
          <h1>{tab === "route" ? "Мой маршрут" : tab === "orders" ? "Мои наряды" : "Профиль"}</h1>
          <label>
            <span>Сотрудник</span>
            <select
              value={activeStaffId}
              onChange={(event) => setSelectedStaffId(event.target.value)}
              aria-label="Выбрать сотрудника"
            >
              {staff.map((item) => (
                <option key={item.staff_id} value={item.staff_id}>
                  {item.display_name ?? item.staff_id}
                </option>
              ))}
            </select>
          </label>
        </div>

        {tab === "route" && (
          <>
            <div className="mobile-progress">
              <div>
                <b>{completed} из {visits.length} выполнено</b>
                <span>{visits.length ? Math.round((completed / visits.length) * 100) : 0}%</span>
              </div>
              <i>
                <span
                  style={{
                    width: `${visits.length ? (completed / visits.length) * 100 : 0}%`,
                  }}
                />
              </i>
              <small>
                {person
                  ? `Смена ${person.shift.start}–${person.shift.end}`
                  : "Сотрудник не выбран"}
              </small>
            </div>
            <div className="next-label">СЛЕДУЮЩИЙ ВИЗИТ</div>
            {nextVisit && nextOrder ? (
              <article className="mobile-visit next">
                <div className="visit-time">
                  <b>{nextVisit.start.slice(11, 16)}</b>
                  <span>– {nextVisit.end.slice(11, 16)}</span>
                </div>
                <div className="mobile-address">
                  <Status>{nextVisit.status === "IN_PROGRESS" ? "В работе" : "Запланирован"}</Status>
                  <h2>{nextOrder.address}</h2>
                  <p>{nextOrder.work_type_code} · {nextOrder.technology}</p>
                  <small>
                    <MapPin size={13} /> {nextOrder.order_id}
                  </small>
                </div>
                <div className="mobile-actions">
                  <a
                    href={`https://yandex.ru/maps/?pt=${nextOrder.lon},${nextOrder.lat}&z=16&l=map`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <Route size={17} />
                    Навигация
                  </a>
                </div>
                <Button
                  variant="secondary"
                  icon={<RefreshCw size={16} />}
                  disabled={loading}
                  onClick={() => void refresh()}
                >
                  Обновить маршрут
                </Button>
              </article>
            ) : (
              <div className="card">
                {route ? "На маршруте нет незавершённых визитов." : "Для сотрудника нет маршрута в текущем плане."}
              </div>
            )}
            <div className="next-label">ДАЛЕЕ ПО МАРШРУТУ</div>
            {visits
              .filter((stop) => stop.order_id !== nextVisit?.order_id)
              .map((stop) => {
                const order = stop.order_id ? orderById.get(stop.order_id) : undefined;
                return (
                  <article className="mobile-visit compact" key={stop.order_id ?? stop.seq}>
                    <div className="visit-time">
                      <b>{stop.start.slice(11, 16)}</b>
                      <span>– {stop.end.slice(11, 16)}</span>
                    </div>
                    <div className="mobile-address">
                      <h2>{order?.address ?? stop.location_id}</h2>
                      <p>{order?.work_type_code ?? stop.order_id}</p>
                    </div>
                  </article>
                );
              })}
          </>
        )}

        {tab === "orders" && (
          <div className="mobile-order-list">
            {visibleOrders.map((order) => (
              <article className="mobile-visit compact" key={order.order_id}>
                <div className="visit-time">
                  <b>{order.slot.start.slice(11, 16)}</b>
                  <span>– {order.slot.end.slice(11, 16)}</span>
                </div>
                <div className="mobile-address">
                  <h2>{order.address}</h2>
                  <p>{order.order_id} · {order.work_type_code}</p>
                </div>
              </article>
            ))}
            {!loading && visibleOrders.length === 0 && (
              <div className="card">У сотрудника нет назначенных нарядов.</div>
            )}
          </div>
        )}

        {tab === "profile" && (
          <article className="mobile-visit">
            <h2>{person?.display_name ?? person?.staff_id ?? "Сотрудник не выбран"}</h2>
            <p>{person?.staff_id}</p>
            <p>{center?.name ?? person?.service_center_id ?? "Сервисный центр не указан"}</p>
            <p>{person?.profiles.join(", ")}</p>
            <p>{person?.technologies.join(", ")}</p>
            <p>{person?.height_permit ? "Допуск к высоте" : "Без допуска к высоте"}</p>
          </article>
        )}
      </main>
      <nav>
        <button className={tab === "route" ? "active" : ""} onClick={() => setTab("route")}>
          <Route size={20} />
          Маршрут
        </button>
        <button className={tab === "orders" ? "active" : ""} onClick={() => setTab("orders")}>
          <ListTodo size={20} />
          Наряды
        </button>
        <button className={tab === "profile" ? "active" : ""} onClick={() => setTab("profile")}>
          <UserRound size={20} />
          Профиль
        </button>
      </nav>
    </div>
  );
}
