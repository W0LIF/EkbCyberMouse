import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Plus, RefreshCw, Search, SlidersHorizontal, ToolCase } from "lucide-react";
import { useDispatchData } from "../features/dispatch/DispatchDataContext";
import { Button } from "../shared/ui/Button";
import { Status } from "../shared/ui/Status";
import { PageIntro } from "../shared/ui/PageIntro";

interface OrdersPageProps {
  openOrder: (orderId: string) => void;
  openCreate: () => void;
}

export default function OrdersPage({ openOrder, openCreate }: OrdersPageProps) {
  const [searchParams, setSearchParams] = useSearchParams();
  const query = searchParams.get("q") ?? "";
  const [statusFilter, setStatusFilter] = useState("Все статусы");
  const [profileFilter, setProfileFilter] = useState("Все профили");
  const [sortDescending, setSortDescending] = useState(false);
  const { date, orders, staff, centers, loading, error, refresh } = useDispatchData();
  const staffById = useMemo(
    () => new Map(staff.map((person) => [person.staff_id, person])),
    [staff],
  );
  const centerById = useMemo(
    () => new Map(centers.map((center) => [center.service_center_id, center])),
    [centers],
  );

  const visibleOrders = useMemo(() => {
    const term = query.trim().toLocaleLowerCase("ru");
    return orders
      .filter((order) => {
        const person = order.assigned_staff_id
          ? staffById.get(order.assigned_staff_id)
          : undefined;
        const statusMatches =
          statusFilter === "Все статусы" || order.status === statusFilter;
        const profileMatches =
          profileFilter === "Все профили" ||
          person?.profiles.includes(profileFilter === "3ЛТП" ? "LTP3" : "INSTALL");
        const queryMatches =
          !term ||
          [
            order.order_id,
            order.address,
            order.work_type_code,
            person?.display_name ?? order.assigned_staff_id ?? "",
          ]
            .join(" ")
            .toLocaleLowerCase("ru")
            .includes(term);
        return statusMatches && profileMatches && queryMatches;
      })
      .sort((left, right) =>
        sortDescending
          ? right.order_id.localeCompare(left.order_id)
          : left.order_id.localeCompare(right.order_id),
      );
  }, [orders, staffById, query, statusFilter, profileFilter, sortDescending]);

  const statusOptions = ["Все статусы", ...new Set(orders.map((order) => order.status))];
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
    <div className="screen">
      <PageIntro
        eyebrow={`${orders.length} НАРЯДОВ · ${date}`}
        title="Наряды"
        subtitle="Данные загружены из диспетчерского API"
        actions={
          <>
            <Button icon={<Plus size={16} />} onClick={openCreate}>
              Новый наряд
            </Button>
            <Button
              variant="secondary"
              icon={<RefreshCw size={16} />}
              disabled={loading}
              onClick={() => void refresh()}
            >
              Обновить
            </Button>
          </>
        }
      />
      {error && <div className="card" role="alert">{error}</div>}
      {loading && <div className="card" role="status">Загружаем наряды…</div>}
      <div className="table-filters card">
        <div className="search-small">
          <Search size={16} />
          <input
            value={query}
            onChange={(event) => {
              const nextParams = new URLSearchParams(searchParams);
              if (event.target.value) nextParams.set("q", event.target.value);
              else nextParams.delete("q");
              setSearchParams(nextParams, { replace: true });
            }}
            placeholder="ID, адрес, сотрудник…"
          />
        </div>
        <span className="filter-date">{date}</span>
        <select
          aria-label="Фильтр по статусу"
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value)}
        >
          {statusOptions.map((status) => (
            <option key={status} value={status}>
              {status === "Все статусы" ? status : statusLabel[status] ?? status}
            </option>
          ))}
        </select>
        <select
          aria-label="Фильтр по профилю"
          value={profileFilter}
          onChange={(event) => setProfileFilter(event.target.value)}
        >
          {["Все профили", "3ЛТП", "Инсталляция"].map((profile) => (
            <option key={profile}>{profile}</option>
          ))}
        </select>
        <Button
          variant="ghost"
          icon={<SlidersHorizontal size={15} />}
          onClick={() => setSortDescending((descending) => !descending)}
        >
          {sortDescending ? "Сначала новые" : "Сначала старые"}
        </Button>
      </div>
      <div className="orders-table card">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Тип работ</th>
              <th>Адрес</th>
              <th>Слот</th>
              <th>Сотрудник</th>
              <th>СЦ</th>
              <th>Статус</th>
            </tr>
          </thead>
          <tbody>
            {visibleOrders.map((order) => {
              const person = order.assigned_staff_id
                ? staffById.get(order.assigned_staff_id)
                : undefined;
              const center = person
                ? centerById.get(person.service_center_id)
                : undefined;
              return (
                <tr
                  key={order.order_id}
                  onClick={() => openOrder(order.order_id)}
                  tabIndex={0}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      openOrder(order.order_id);
                    }
                  }}
                >
                  <td><code>{order.order_id}</code></td>
                  <td>
                    <span className="work-type">
                      <ToolCase size={15} />
                      {order.work_type_code} · {order.technology}
                    </span>
                  </td>
                  <td>{order.address}</td>
                  <td>{order.slot.start.slice(11, 16)}–{order.slot.end.slice(11, 16)}</td>
                  <td>{person?.display_name ?? order.assigned_staff_id ?? "—"}</td>
                  <td>{center?.name ?? "—"}</td>
                  <td><Status>{statusLabel[order.status] ?? order.status}</Status></td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {!loading && visibleOrders.length === 0 && (
          <div className="pagination">По заданным условиям наряды не найдены.</div>
        )}
        <div className="pagination">
          <span>{visibleOrders.length} из {orders.length} нарядов</span>
          <span>{date}</span>
        </div>
      </div>
    </div>
  );
}
